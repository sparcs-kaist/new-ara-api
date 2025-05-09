import bs4
from bs4 import BeautifulSoup
import requests
from lxml import etree
import time
from datetime import datetime
import copy
import re
import json

#redis가져오기
from ara import redis
from redis.commands.json import JSON

#일단은 주석 처리하자. from apps.core.models import Meal

common_url = "https://www.kaist.ac.kr/kr/html/campus/053001.html?dvs_cd="
valid_restaurant_names = ["fclt", "west", "east1", "east2", "emp"]

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


def _parser_fclt(menu_list : str, time : int):
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
    Courses = {}
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


def _parser_west(menu_list : str, time : int):
    #서맛골은 조식/중식/석식이 항상 동일한 금액으로 운영이 되고, 일품만 따로 있다.
    #조식 : 3700 / 중식 : 5000원 / 석식 : 5000원 이다. (일품은 변동 금액인듯)
    #time : 조식 : 0 , 중식 : 1, 석식 : 2 -> 파싱을 위해 이 정보가 필요하다. (맨 윗주레 코스 이름 정보가 없고 바로 메뉴로 시작)
    default_label = {0: ("조식", 3700), 1:("중식", 5000), 2:("석식", 5000)}

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
    Courses = {}
    temp = default_label[time]
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
            txt_match = re.match(r"(.+?)(\d+(\.\d+)*)?$", txt.strip())
            if txt_match:
                name = txt_match.group(1).strip()  # 음식 이름 추출
                numbers = txt_match.group(2)      # 숫자 부분 추출
                if numbers:
                    # 숫자를 점(.)으로 구분하고 정수 리스트로 변환
                    numbers_list = list(map(int, numbers.split(".")))
                    Courses[temp].append([name, numbers_list])
                else:
                    # 숫자가 없으면 빈 리스트 반환
                    Courses[temp].append([name, []])
                
    return Courses

def _parser_east1_course(menu_list : str, time : int):
    #menu_lsit : str type으로 되어 있는 string
    #안전한 리스트 처리를 위해 복사
    Menu = [menu.strip() for menu in menu_list]
    #빈 칸 필터링
    Menu = list(filter(lambda x: x != '' and x != ' ' and x != '\n', Menu))
    Menu = list(filter(lambda x: '하루과일' not in x and '글로벌' not in x , Menu))

    #모든 메뉴가 100원 단위. -> '00원' 이라는 텍스트가 포함된 부분을 찾으면 어디인지 알 수 있다.
    #이걸 기준으로 각 코스를 나누면 된다.
    Courses = {}
    for txt in Menu:
        #하루과일 : 파싱 x
        if '하루과일' in txt:
            break #하루과일은 항상 맨 마지막에 있다.
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

def _parser_east1_cafeteria(menu_list : str, time : int) -> list:
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
            return {}

        #카페테리아가 영업하지 않는 날
        if '<Cafeteria>' not in Menu.pop(0):
            return {}
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
            return Menus

    else:
        return {}

def _parser_east2(menu_list : str, time : int):
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
    
    Courses = {}
    for txt in Menu:
        #교수 전용식 정보가 등장하면 break
        if "교수전용" in txt:
            if temp in Courses and time == 2: #점심과 저녁에 '교수 전용'이 있는 위치가 다르다.
                Courses.pop(temp)
            break
        #코스 이름이 나온 경우 - 동맛골 2층은 '<>'로 가격이 둘러쌓여 있음.
        if '00원' in txt:
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

def _merge_price_with_previous(items):
    result = []
    for item in items:
        if '원' in item:  # '00원'이 포함된 항목 확인
            if result:  # 결과 리스트에 이전 항목이 존재하는지 확인
                result[-1] += item  # 앞의 항목과 결합
        else:
            result.append(item)  # 그대로 결과 리스트에 추가
    return result

def _parser_emp(menu_list : str, time : int):
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
    Courses = {}
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

def _crawl_meal(restaurant_name : str ,date : str):
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
    

#redis에 data를 저장할 때 쓰는 key의 규칙 :
#cafeteria_menu_20250324 
#course_menu_20250324 와 같은 형식으로.

#api에서 내보낼 json형식으로 곧바로 redis에 저장하기 (model이 따로 없어서 Serializer를 거치지 않는다!)
def crawl_daily_meal(date : str):
    digit_8_date = date.replace("-", "") #날짜를 key에 활용하기 위해서 8자리 형식으로 변환.
    restaurant_names = {"fclt" : "카이마루", "west" : "서맛골", "east1" : "동맛골 1층", "east2" : "동맛골 2층", "emp" : "교수회관"}
    #최종적으로 저장할 dictionary : (cafeteria_meal/ course_meal)
    #dictonary의 기본 format setting
    cafeteria_meal = {'date' : date}
    course_meal = {'date' : date}

    #자세한 형식이 궁금하다면 Notion의 학식 API 문서 참고.
    for rest_name in restaurant_names:
        cafeteria_meal[rest_name] = {'name' : restaurant_names[rest_name], 'type' : "cafeteria", 
                                     'morning_menu' : [] , 'lunch_menu' : [], 'dinner_menu' : []}
        course_meal[rest_name] = {'name' : restaurant_names[rest_name], 'type' : "cafeteria", 
                                     'morning_menu' : [] , 'lunch_menu' : [], 'dinner_menu' : []}

    Course_restaurant = ["fclt", "west", "east1_course", "east2", "emp"]
    Cafeteria_restaurant = ["east1_cafeteria"]

    #카페테리아 정보 가공
    for cafeteria_name in Cafeteria_restaurant:
        #데이터 가져와서 가공하기
        cafeteria_plain_data = _crawl_meal(restaurant_name= cafeteria_name, date=date)
        
        #'cafeteria_meal['east1'] 에만 추가하면 된다. cafeteria crawl 함수는 리스트를 반환하므로 바로 넣어주면 된다.
        if cafeteria_plain_data[0]:
            cafeteria_meal['east1']['morning_menu'] = cafeteria_plain_data[0]
        if cafeteria_plain_data[1]:
            cafeteria_meal['east1']['lunch_menu'] = cafeteria_plain_data[1]
        if cafeteria_plain_data[2]:
            cafeteria_meal['east1']['dinner_menu'] = cafeteria_plain_data[2]

    #코스메뉴 정보 가공
    for course_name in Course_restaurant:
        course_plain_data = _crawl_meal(restaurant_name=course_name, date= date)
        if (course_name == "east1_course"):
            cur_name = "east1"
        else:
            cur_name = course_name
        #아침/점심/저녁밥이 나온다면..
        if course_plain_data[0]:
            course_meal[cur_name]['morning_menu'] = []
            for (course_name, course_price) , menu_li in course_plain_data[0].items():
                course_meal[cur_name]['morning_menu'].append({'course_name' : course_name,
                                                         'price' : course_price,
                                                         'menu_list' : menu_li})
        if course_plain_data[1]:
            course_meal[cur_name]['lunch_menu'] = []
            for (course_name, course_price) , menu_li in course_plain_data[1].items():
                course_meal[cur_name]['lunch_menu'].append({'course_name' : course_name,
                                                         'price' : course_price,
                                                         'menu_list' : menu_li})
        if course_plain_data[2]:
            course_meal[cur_name]['dinner_menu'] = []
            for (course_name, course_price) , menu_li in course_plain_data[2].items():
                course_meal[cur_name]['dinner_menu'].append({'course_name' : course_name,
                                                         'price' : course_price,
                                                         'menu_list' : menu_li})
    #pretty_print (디버깅용)
    """
    import pprint
    pprint.pprint(course_meal)"
    """
    #redis에 저장하기
    digit_8_date = date.replace("-", "") #날짜를 key에 활용하기 위해서 8자리 형식으로 변환.
    cafeteria_key = 'cafeteria_menu' + digit_8_date
    course_key = 'course_menu' + digit_8_date

    pipe = redis.pipeline()
    pipe.json().set(cafeteria_key ,'.', cafeteria_meal)
    pipe.json().set(course_key ,'.', course_meal)
    pipe.execute()

    print("celery가 일하고 있어요!")
    return


if __name__ == '__main__':
    print("식단 크롤링 시작")
    res = crawl_daily_meal(date = current_date())
    print(res)
