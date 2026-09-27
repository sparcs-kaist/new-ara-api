from datetime import date, datetime
from typing import Dict, Optional, Tuple

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone

from apps.core.management.scripts.instagram_client import InstagramPost, download_image, fetch_recent_posts
from apps.meal.models import MealType, MenuPhoto, MenuPhotoSource, Restaurant

MealWindows = Dict[str, Tuple[str, str]]


def meal_time_of(moment: datetime, windows: MealWindows) -> Optional[Tuple[date, MealType]]:
    local = timezone.localtime(moment)
    current = local.strftime("%H:%M")
    for meal_time, (start, end) in windows.items():
        if start <= current < end:
            return local.date(), MealType(meal_time)
    return None


def photo_post_id(post: InstagramPost, index: int) -> str:
    return f"{post.post_id}_{index}"


def save_post_photos(restaurant: Restaurant, day: date, meal_time: MealType, post: InstagramPost) -> int:
    # 지운 사진도 다시 가져오지 않는다
    saved_ids = set(MenuPhoto.objects.queryset_with_deleted.filter(
        source_post_id__in=[photo_post_id(post, i) for i in range(len(post.image_urls))],
    ).values_list("source_post_id", flat=True))

    saved = 0
    for index, url in enumerate(post.image_urls):
        source_post_id = photo_post_id(post, index)
        if source_post_id in saved_ids:
            continue
        content = download_image(url)
        if content is None:
            continue
        MenuPhoto.objects.create(
            restaurant=restaurant,
            date=day,
            meal_time=meal_time.value,
            image=ContentFile(content, name=f"{source_post_id}.jpg"),
            source=MenuPhotoSource.INSTAGRAM.value,
            source_post_id=source_post_id,
        )
        saved += 1
    return saved


def crawl_instagram_menu_photos(now: Optional[datetime] = None) -> int:
    windows = settings.MEAL_PHOTO_WINDOWS
    if meal_time_of(now or timezone.now(), windows) is None:
        return 0

    saved = 0
    for username, restaurant_code in settings.MEAL_PHOTO_INSTAGRAM_ACCOUNTS.items():
        restaurant = Restaurant.objects.filter(code=restaurant_code, is_active=True).first()
        if restaurant is None:
            continue
        for post in fetch_recent_posts(username):
            mapped = meal_time_of(post.taken_at, windows)
            if mapped is not None:
                saved += save_post_photos(restaurant, *mapped, post)
    return saved
