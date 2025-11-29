from bs4 import BeautifulSoup
import requests
from datetime import datetime, date as date_type
import re
import logging
from typing import Dict, List, Tuple, Union, TypedDict

# DB 모델 가져오기
from django.db import transaction
from apps.meal.models import Restaurant, Course, Menu, CafeteriaMenu, MenuAllergy, MealType

# 로깅 설정
logger = logging.getLogger(__name__)

# 타입 정의
# 코스 메뉴: [메뉴명, [알러지코드들]]
MenuItemType = List[Union[str, List[int]]]  # e.g., ["김치찌개", [1, 5, 6]]
# 코스 데이터: {(코스명, 가격): [메뉴아이템들]}
CourseDataType = Dict[Tuple[str, int], List[MenuItemType]]

# 카페테리아 메뉴 아이템
class CafeteriaMenuItemType(TypedDict):
    menu_name: str
    price: int
    allergy: List[int]

# 카페테리아 데이터
CafeteriaDataType = List[CafeteriaMenuItemType]

common_url = "https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd="

# 식당 코드와 DB 이름 매핑
RESTAURANT_CODE_TO_NAME = {
    "fclt": "카이마루",
    "west": "서맛골",
    "east1": "동맛골 1층",
    "east2": "동맛골 2층",
    "emp": "교수회관"
}

# 시간대 인덱스를 MealType으로 변환
TIME_INDEX_TO_MEAL_TYPE = {
    0: MealType.BREAKFAST,
    1: MealType.LUNCH,
    2: MealType.DINNER
}


def _parse_date(date_str: str) -> date_type:
    """문자열 날짜를 datetime.date 객체로 변환"""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

"""
식당별 perfix

1. 카이마루 : fclt
2. 서맛골 west
3. 동맛골 (동측 학생식당) : east1
4. 동맛골 (동측 교직원 식당) : east2
5. 교수회관 : emp

example : https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd=emp&stt_dt=2025-03-18
"""
#xpath : //*[@id="tab_item_1"]/table/tbody/tr/td[2]/ul

#note : date : '0000-00-00'format.

def current_date() -> str :
    #YYYY-MM-DD
    return datetime.now().strftime("%Y-%m-%d")


def _parser_fclt(menu_list: List[str], time: int) -> CourseDataType:
    #time 파라미터는 west를 파싱할 때 필요해서 형식을 맞추기 위해서 넣었다.
    #menu_lsit : str type으로 되어 있는 string
    #안전한 리스트 처리를 위해 복사
    Menu = [menu.strip() for menu in menu_list]
    #빈 칸 필터링
    Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))
    Menu = list(filter(lambda x: '하루과일' not in x and '글로벌' not in x , Menu))
    #카이마루에서 수요일 저녁마다 고객경영팀에서 하루과일을 제공한다. -> 파싱 x
    Menu = list(filter(lambda x: '고객경영팀' not in x , Menu))
    

    #모든 메뉴가 100원 단위. -> '00원' 이라는 텍스트가 포함된 부분을 찾으면 어디인지 알 수 있다.
    #이걸 기준으로 각 코스를 나누면 된다.
    Courses: CourseDataType = {}
    temp: Tuple[str, int] = ("", 0)
    for txt in Menu:
        #코스 이름이 나온 경우
        if '00원' in txt:
            txt_match = re.match(r"(.+?)\(([\d,]+)원\)", txt.strip())
            course_name = txt_match.group(1)
            course_price = int(txt_match.group(2).replace(",", ""))
            Courses[(course_name, course_price)] = []
            temp = (course_name, course_price)
        #메뉴가 나온 경우.
        else:
            txt_match = re.match(r"(.+?)\(([\d,]+)\)", txt.strip())
            if txt_match:
                menu_name = txt_match.group(1).strip()
                allergy = list(map(int, txt_match.group(2).split(",")))
                Courses[temp].append([menu_name, allergy])
            else:
                Courses[temp].append([txt.strip(), []] )# 괄호가 없으면 빈 리스트 반환

    return Courses


def _parser_west(menu_list: List[str], time: int) -> CourseDataType:
    #서맛골은 조식/중식/석식이 항상 동일한 금액으로 운영이 되고, 일품만 따로 있다.
    #조식 : 3700 / 중식 : 5000원 / 석식 : 5000원 이다. (일품은 변동 금액인듯)
    #time : 조식 : 0 , 중식 : 1, 석식 : 2 -> 파싱을 위해 이 정보가 필요하다. (맨 윗주레 코스 이름 정보가 없고 바로 메뉴로 시작)
    default_label: Dict[int, Tuple[str, int]] = {0: ("조식", 3700), 1:("중식", 5000), 2:("석식", 5000)}

    #menu_lsit : str type으로 되어 있는 string
    #안전한 리스트 처리를 위해 복사
    Menu = [menu.strip() for menu in menu_list]
    #빈 칸 필터링
    Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))
    Menu = list(filter(lambda x: '과일' not in x and '글로벌' not in x , Menu)) #하루과일 없애기
    Menu = list(filter(lambda x: '학생증' not in x, Menu)) #식사시 학생증 소지 안내 없애기

    #토/일요일 같이 영업 안하는 경우.
    if len(Menu) == 0:
        return {}

    #천원의 아침밥 여부 판단.
    if '천원의 아침밥' in Menu[-1]:
        default_label[0] = ("천원의 아침밥", 1000)
        Menu.pop()

    #모든 메뉴가 100원 단위. -> '00원' 이라는 텍스트가 포함된 부분을 찾으면 어디인지 알 수 있다.
    #이걸 기준으로 각 코스를 나누면 된다.
    Courses: CourseDataType = {}
    temp: Tuple[str, int] = default_label[time]
    Courses[temp] = []
    for txt in Menu:
        
        #코스 이름이 나온 경우 (서맛골은 대괄호 안에 가격)
        if '00원' in txt:
            txt_match = re.match(r"(.+?)\[([\d,]+)원\]", txt.strip())
            course_name = txt_match.group(1)
            course_price = int(txt_match.group(2).replace(",", ""))
            Courses[(course_name, course_price)] = []
            temp = (course_name, course_price)
        #메뉴가 나온 경우.
        else:
            # 괄호 안에 숫자들이 있는 경우를 먼저 체크 (쉼표나 점으로 구분)
            # 예: "소고기미역국(5, 6, 16)" or "무말랭이(5,6)" or "콩나물국(5)"
            txt_match = re.match(r"(.+?)\(([\d,.\s]+)\)\s*$", txt.strip())
            if txt_match:
                name = txt_match.group(1).strip()
                numbers_str = txt_match.group(2)
                # 쉼표와 점을 모두 구분자로 처리, 공백 제거
                numbers_str = numbers_str.replace(" ", "").replace(".", ",")
                allergy_list = [int(n) for n in numbers_str.split(",") if n.strip()]
                Courses[temp].append([name, allergy_list])
            else:
                # 괄호가 없거나 숫자가 아닌 경우
                Courses[temp].append([txt.strip(), []])
                
    return Courses

def _parser_east1_course(menu_list: List[str], time: int) -> CourseDataType:
    #menu_lsit : str type으로 되어 있는 string
    #안전한 리스트 처리를 위해 복사
    Menu = [menu.strip() for menu in menu_list]
    #빈 칸 필터링
    Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))
    Menu = list(filter(lambda x: '하루과일' not in x and '글로벌' not in x , Menu))

    #2025-05-09 - 동맛골 1층 카페테리아가 식기세척기 고장으로 인해 운영하지 않음
    #이때 '미운영' 이라는 텍스트가 포함되어 있었음.

    #모든 메뉴가 100원 단위. -> '00원' 이라는 텍스트가 포함된 부분을 찾으면 어디인지 알 수 있다.
    #이걸 기준으로 각 코스를 나누면 된다.
    Courses: CourseDataType = {}
    temp: Tuple[str, int] = ("", 0)
    #2025.05 샐러드 메뉴 등장 - 샐러드 처리 로직
    offset = 0
    for line in Menu:
        if '샐러드' in line:
            offset += 1
        else:
            break
    #샐러드 메뉴정보 -> 제거
    for _ in range(offset):
        Menu.pop(0)

    for txt in Menu:
        #하루과일 : 파싱 x
        if '하루과일' in txt:
            break #하루과일은 항상 맨 마지막에 있다.
        if '미운영' in txt:
            break #어떤 이유로 식당이 운영하지 않는경우
        if '이벤트' in txt:
            continue #2025.07.20 초복 이벤트 등 이벤트는 parsing에서 제외
        #코스 이름이 나온 경우
        if ('00원' in txt) or ('<' in txt and '>' in txt): #카페테리아 메뉴까지 같이 처리하기 위해 조건 추가.
            txt_match = re.match(r"<(.+?) (\d+,?\d*)원>", txt.strip()) #코스 이름과 가격은 <> 안에
            #txt match가 실패한 경우 : 카페테리아 메뉴이므로 넘어가기.
            if txt_match:
                pass
            else:
                continue
            course_name = txt_match.group(1).replace(",", "").strip()
            course_price = int(txt_match.group(2).replace(",", ""))
            Courses[(course_name, course_price)] = []
            temp = (course_name, course_price)
        #메뉴가 나온 경우.
        else:
            txt_match = re.match(r"(.+?)\(([\d,]+)\)", txt.strip())
            if txt_match:
                menu_name = txt_match.group(1).strip()
                allergy = list(map(int, txt_match.group(2).split(",")))
                Courses[temp].append([menu_name, allergy])
            else:
                Courses[temp].append( [ txt.strip(), []] )# 괄호가 없으면 빈 리스트 반환
    return Courses

def _parser_east1_cafeteria(menu_list: List[str], time: int) -> CafeteriaDataType:
    #cafeteria_parser는 다른 것과 다르게 리스트를 리턴한다!!
    #note : cafeteria는 점심에만 있다.
    if time == 1:
        #menu_lsit : str type으로 되어 있는 string
        #안전한 리스트 처리를 위해 복사
        Menu = [menu.strip() for menu in menu_list]
        #빈 칸 필터링
        Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))
        Menus = []


        #토/일요일 같이 영업 안하는 경우.
        if len(Menu) == 0:
            return []
        
        #2025.05 샐러드 메뉴 등장 - 샐러드 처리 로직
        offset = 0
        for line in Menu:
            if '샐러드' in line:
                offset += 1
            else:
                break
        #샐러드 메뉴정보 -> 제거
        for _ in range(offset):
            Menu.pop(0)

        #카페테리아가 영업하지 않는 날
        if '<Cafeteria>' not in Menu.pop(0):
            return []
        else:
            for txt in Menu:
                #Cafeterai 메뉴가 끝나면 break
                if ('>' in txt) and ('<' in txt):
                    break
                txt_match = re.match(r"(.+?)\s*(?:\(([\d,]*)\))?\s*([\d,]+)원", txt.strip())
                menu_name = txt_match.group(1).strip()  # 메뉴 이름 추출
                allergy = txt_match.group(2)  # 괄호 내 숫자 목록 추출
                allergy_list = [int(num) for num in allergy.split(",")] if allergy else []  # 숫자 목록을 리스트로 변환
                price = int(txt_match.group(3).replace(",", ""))  # 쉼표 제거 후 가격 정수 변환
                Menus.append({'menu_name' : menu_name, 'price' : price, 'allergy' : allergy_list})
            print(f"최종 결과 : {Menus}")
            return Menus

    else:
        return []

def _parser_east2(menu_list: List[str], time: int) -> CourseDataType:
    #동맛골 2층은 교수 전용 식이 있다. 교수 전용 식은 보통 마지막에 있기 때문에
    #'교수전용'이라는 텍스트가 발견되면 break하면 된다.
    #menu_lsit : str type으로 되어 있는 string
    #안전한 리스트 처리를 위해 복사
    Menu = [menu.strip() for menu in menu_list]
    #빈 칸 필터링
    Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))

    #토/일요일 같이 영업 안하는 경우.
    if len(Menu) == 0:
        return {}
    if '미운영' in Menu[0]:
        return {}

    #2025-05 샐러드 메뉴 등장 - 샐러드 처리 로직. (샐러드는 항상 맨 윗줄에 있고, 각 줄별로 샐러드 라는 단어 나옴).
    offset = 0
    for line in Menu:
        if '샐러드' in line:
            offset += 1
        else:
            break
    #샐러드 메뉴정보 -> 제거
    for _ in range(offset):
        Menu.pop(0)    

    
    Courses: CourseDataType = {}
    temp: Tuple[str, int] = ("", 0)
    for txt in Menu:
        #교수 전용식 정보가 등장하면 break
        if "교수전용" in txt:
            if temp in Courses and time == 2: #점심과 저녁에 '교수 전용'이 있는 위치가 다르다.
                Courses.pop(temp)
            break
        #코스 이름이 나온 경우 - 동맛골 2층은 '<>'로 가격이 둘러쌓여 있음.
        if '00원' in txt:
            print(txt)
            txt_match = re.match(r"<(.+?) (\d+,?\d*)원>", txt.strip())
            course_name = txt_match.group(1)
            course_price = int(txt_match.group(2).replace(",", ""))
            Courses[(course_name, course_price)] = []
            temp = (course_name, course_price)
        #메뉴가 나온 경우.
        else:
            txt_match = re.match(r"(.+?)\(([\d,]+)\)", txt.strip())
            if txt_match:
                menu_name = txt_match.group(1).strip()
                allergy = list(map(int, txt_match.group(2).split(",")))
                Courses[temp].append([menu_name, allergy])
            else:
                Courses[temp].append([txt.strip(), []] )# 괄호가 없으면 빈 리스트 반환
    return Courses

def _merge_price_with_previous(items: List[str]) -> List[str]:
    result: List[str] = []
    for item in items:
        if '원' in item:  # '00원'이 포함된 항목 확인
            if result:  # 결과 리스트에 이전 항목이 존재하는지 확인
                result[-1] += item  # 앞의 항목과 결합
        else:
            result.append(item)  # 그대로 결과 리스트에 추가
    return result

def _parser_emp(menu_list: List[str], time: int) -> CourseDataType:
    #time 파라미터는 west를 파싱할 때 필요해서 형식을 맞추기 위해서 넣었다.
    #menu_lsit : str type으로 되어 있는 string
    #안전한 리스트 처리를 위해 복사
    Menu = [menu.strip() for menu in menu_list]
    #빈 칸 필터링
    Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))
    Menu = list(filter(lambda x: '이벤트' not in x , Menu)) #이벤트 정보 지우기 (예 : 벚꽃 팝콘)
    Menu = list(filter(lambda x: 'kcal' not in x , Menu)) #칼로리 정보 지우기
    #교수회관 에서도 수요일 저녁마다 고객경영팀에서 하루과일을 제공한다. -> 파싱 x
    Menu = list(filter(lambda x: '고객경영팀' not in x , Menu))
    #교수회관의 경우 위와 같이 parsing하면 코스 이름과 가격이 리스트에서 다른 항목으로 들어간다. ["1층 자율배식", '(5,500원)'] 이런 식으로.
    #리스트 순회하면서 이 2개의 항목 이어붙이기.
    Menu = _merge_price_with_previous(Menu)
    Courses: CourseDataType = {}
    temp: Tuple[str, int] = ("", 0)
    for txt in Menu:
        #코스 이름이 나온 경우
        if '00원' in txt:
            txt_match = re.match(r"(.+?)\(([\d,]+)원\)", txt.strip())
            course_name = txt_match.group(1)
            course_price = int(txt_match.group(2).replace(",", ""))
            Courses[(course_name, course_price)] = []
            temp = (course_name, course_price)
        #메뉴가 나온 경우.
        else:
            txt_match = re.match(r"(.+?)\(([\d,]+)\)", txt.strip())
            if txt_match:
                menu_name = txt_match.group(1).strip()
                allergy = list(map(int, txt_match.group(2).split(",")))
                Courses[temp].append([menu_name, allergy])
            else:
                Courses[temp].append( [txt.strip(), []] )# 괄호가 없으면 빈 리스트 반환
    return Courses

def _crawl_meal(restaurant_name: str, date: str) -> Union[List[Union[CourseDataType, CafeteriaDataType, None]], bool]:
    """
    식당 웹페이지에서 식단 정보를 크롤링
    
    Returns:
        성공 시: [아침데이터, 점심데이터, 저녁데이터] 리스트
        실패 시: False
    """
    #카페테리아가 있는 동맛골 1층만 따로 처리.
    if 'east1' in restaurant_name:
        url = common_url + f"east1&stt_dt={date}"
    else:
        url = common_url + f"{restaurant_name}&stt_dt={date}"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        morning = soup.select('#tab_item_1 > table > tbody > tr > td:nth-child(1)')
        lunch = soup.select('#tab_item_1 > table > tbody > tr > td:nth-child(2)')
        dinner = soup.select('#tab_item_1 > table > tbody > tr > td:nth-child(3)')

        morning_text = ''.join([x.text for x in morning[0].contents]).split('\r')
        lunch_text = ''.join([x.text for x in lunch[0].contents]).split('\r')
        dinner_text = ''.join([x.text for x in dinner[0].contents]).split('\r')

        meal_info = [None, None, None] #아침/점심/저녁

        
        #야채샐러드 & 드레싱 : 공통적으로 매 끼니 나오는 메뉴. (아침 제외)
        """
        샐러드
        야채샐러드&드레싱(1,2,5,6)
        """
        #[아침, 점심, 저녁] 샐러드가 나오는지에 대한 여부
        #parsing함수에 넣기 전에 샐러드 여부를 미리 체크 이후 샐러드는 따로 빼기!
        include_salad = [False, False, False]
        salad_text = "야채샐러드&드레싱"
        if salad_text in morning_text[-1]:
            include_salad[0] = True
            morning_text.pop()
        if salad_text in lunch_text[-1]:
            include_salad[1] = True
            lunch_text.pop()

        if salad_text in dinner_text[-1]:
            include_salad[2] = True
            dinner_text.pop()

        #globals()를 활용한 동적 함수 호출
        #restaurant_name 파라미터로 들어온 것과 대응하는 parser함수를 호출한다.

        meal_info[0] = globals()[f"_parser_{restaurant_name}"](menu_list=morning_text, time = 0)
        meal_info[1] = globals()[f"_parser_{restaurant_name}"](menu_list=lunch_text, time = 1)
        meal_info[2] = globals()[f"_parser_{restaurant_name}"](menu_list=dinner_text, time = 2)

        return meal_info

    else:
        return False
    

def _get_or_create_restaurant(restaurant_name: str) -> Restaurant:
    """식당 객체를 가져오거나 생성"""
    restaurant, _ = Restaurant.objects.get_or_create(restaurant_name=restaurant_name)
    return restaurant


def _has_course_data(restaurant: Restaurant, date: date_type, meal_time: MealType) -> bool:
    """해당 식당/날짜/시간대에 코스 데이터가 있는지 확인"""
    return Course.objects.filter(
        restaurant_id=restaurant,
        date=date,
        meal_time=meal_time.value
    ).exists()


def _has_cafeteria_data(restaurant: Restaurant, date: date_type, meal_time: MealType) -> bool:
    """해당 식당/날짜/시간대에 카페테리아 데이터가 있는지 확인"""
    return CafeteriaMenu.objects.filter(
        restaurant_id=restaurant,
        date=date,
        meal_time=meal_time.value
    ).exists()


def _save_course_to_db(restaurant: Restaurant, date: date_type, meal_time: MealType, course_data: dict):
    """코스 메뉴 데이터를 DB에 저장
    
    Args:
        restaurant: Restaurant 모델 인스턴스
        date: datetime.date 객체
        meal_time: MealType enum
        course_data: {(course_name, price): [[menu_name, [allergy_codes]], ...], ...}
    """
    for (course_name, course_price), menu_list in course_data.items():
        # Course 생성
        course = Course.objects.create(
            restaurant_id=restaurant,
            course_name=course_name,
            price=course_price,
            date=date,
            meal_time=meal_time.value
        )
        
        # Menu 및 MenuAllergy 생성
        for menu_item in menu_list:
            menu_name = menu_item[0]
            allergy_list = menu_item[1] if len(menu_item) > 1 else []
            
            menu = Menu.objects.create(
                menu_name=menu_name,
                course_id=course
            )
            
            # 알러지 정보 저장
            for allergen_code in allergy_list:
                MenuAllergy.objects.create(
                    allergen_code=allergen_code,
                    menu_id=menu
                )


def _save_cafeteria_to_db(restaurant: Restaurant, date: date_type, meal_time: MealType, cafeteria_data: list):
    """카페테리아 메뉴 데이터를 DB에 저장
    
    Args:
        restaurant: Restaurant 모델 인스턴스
        date: datetime.date 객체
        meal_time: MealType enum
        cafeteria_data: [{'menu_name': str, 'price': int, 'allergy': [int, ...]}, ...]
    """
    for menu_item in cafeteria_data:
        menu_name = menu_item.get('menu_name', '')
        price = menu_item.get('price')
        allergy_list = menu_item.get('allergy', [])
        
        cafeteria_menu = CafeteriaMenu.objects.create(
            restaurant_id=restaurant,
            menu_name=menu_name,
            price=price,
            date=date,
            meal_time=meal_time.value
        )
        
        # 알러지 정보 저장
        for allergen_code in allergy_list:
            MenuAllergy.objects.create(
                allergen_code=allergen_code,
                cafeteria_menu_id=cafeteria_menu
            )


def _crawl_and_save_course_restaurant(restaurant_code: str, date_str: str) -> str:
    """
    코스 메뉴 식당 크롤링 및 DB 저장
    데이터가 없는 경우에만 저장
    
    Args:
        restaurant_code: 식당 코드 (fclt, west, east1_course, east2, emp)
        date_str: 날짜 문자열 (YYYY-MM-DD 형식)
    
    Returns:
        'updated': 변경사항이 있어 업데이트됨
        'skipped': 변경사항 없음
        'failed': 실패
    """
    # east1_course -> east1 매핑
    if restaurant_code == "east1_course":
        db_restaurant_name = RESTAURANT_CODE_TO_NAME["east1"]
    else:
        db_restaurant_name = RESTAURANT_CODE_TO_NAME[restaurant_code]
    
    date = _parse_date(date_str)
    
    try:
        restaurant = _get_or_create_restaurant(db_restaurant_name)
        
        # 저장이 필요한 시간대 확인 (데이터가 없는 시간대만)
        times_to_save = []
        for time_idx in range(3):
            meal_type = TIME_INDEX_TO_MEAL_TYPE[time_idx]
            if not _has_course_data(restaurant, date, meal_type):
                times_to_save.append(time_idx)
        
        # 모든 시간대에 데이터가 이미 있으면 스킵
        if not times_to_save:
            logger.debug(f"[{restaurant_code}] 이미 데이터 존재 - 스킵")
            return 'skipped'
        
        # 크롤링
        course_plain_data = _crawl_meal(restaurant_name=restaurant_code, date=date_str)
        
        if course_plain_data is False:
            logger.warning(f"[{restaurant_code}] 크롤링 실패")
            return 'failed'
        
        # 데이터가 없는 시간대만 저장
        with transaction.atomic():
            for time_idx in times_to_save:
                meal_type = TIME_INDEX_TO_MEAL_TYPE[time_idx]
                meal_data = course_plain_data[time_idx]
                
                if meal_data:
                    _save_course_to_db(restaurant, date, meal_type, meal_data)
                    logger.info(f"[{restaurant_code}] {meal_type.value} 저장됨")
        
        return 'updated'
            
    except Exception as e:
        logger.error(f"[{restaurant_code}] 코스 메뉴 저장 실패: {str(e)}")
        return 'failed'


def _crawl_and_save_cafeteria_restaurant(restaurant_code: str, date_str: str) -> str:
    """
    카페테리아 식당 크롤링 및 DB 저장
    데이터가 없는 경우에만 저장
    
    Args:
        restaurant_code: 식당 코드 (east1_cafeteria)
        date_str: 날짜 문자열 (YYYY-MM-DD 형식)
    
    Returns:
        'updated': 새로 저장됨
        'skipped': 이미 데이터 존재
        'failed': 실패
    """
    db_restaurant_name = RESTAURANT_CODE_TO_NAME["east1"]
    date = _parse_date(date_str)
    
    try:
        restaurant = _get_or_create_restaurant(db_restaurant_name)
        
        # 카페테리아는 점심만 있음
        lunch_type = TIME_INDEX_TO_MEAL_TYPE[1]
        
        # 이미 데이터가 있으면 스킵
        if _has_cafeteria_data(restaurant, date, lunch_type):
            logger.debug(f"[{restaurant_code}] 이미 데이터 존재 - 스킵")
            return 'skipped'
        
        # 크롤링
        cafeteria_plain_data = _crawl_meal(restaurant_name=restaurant_code, date=date_str)
        
        if cafeteria_plain_data is False:
            logger.warning(f"[{restaurant_code}] 크롤링 실패")
            return 'failed'
        
        # 점심 데이터만 저장
        lunch_data = cafeteria_plain_data[1] if len(cafeteria_plain_data) > 1 else None
        
        if lunch_data and isinstance(lunch_data, list) and len(lunch_data) > 0:
            with transaction.atomic():
                _save_cafeteria_to_db(restaurant, date, lunch_type, lunch_data)
                logger.info(f"[{restaurant_code}] {lunch_type.value} 저장됨")
            return 'updated'
        
        return 'skipped'
            
    except Exception as e:
        logger.error(f"[{restaurant_code}] 카페테리아 메뉴 저장 실패: {str(e)}")
        return 'failed'


def crawl_daily_meal(date: str):
    """
    일일 식단 크롤링 메인 함수
    각 식당별로 독립적으로 크롤링 및 저장
    데이터가 없는 경우에만 저장 (있으면 스킵)
    """
    logger.info(f"=== 식단 크롤링 시작: {date} ===")
    
    results = {
        'updated': [],
        'skipped': [],
        'failed': []
    }
    
    # 코스 메뉴 식당 처리
    Course_restaurant = ["fclt", "west", "east1_course", "east2", "emp"]
    for course_code in Course_restaurant:
        result = _crawl_and_save_course_restaurant(course_code, date)
        results[result].append(course_code)
    
    # 카페테리아 식당 처리
    Cafeteria_restaurant = ["east1_cafeteria"]
    for cafeteria_code in Cafeteria_restaurant:
        result = _crawl_and_save_cafeteria_restaurant(cafeteria_code, date)
        results[result].append(cafeteria_code)
    
    # 결과 로깅
    logger.info(f"=== 식단 크롤링 완료: {date} ===")
    logger.info(f"업데이트: {results['updated']}")
    logger.info(f"스킵 (변경없음): {results['skipped']}")
    if results['failed']:
        logger.warning(f"실패: {results['failed']}")
    
    return results


if __name__ == '__main__':
    # Django 설정이 필요한 경우
    import django
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ara.settings")
    django.setup()
    
    print("식단 크롤링 시작")
    res = crawl_daily_meal(date=current_date())
    print(f"결과: {res}")
