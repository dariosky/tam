# coding=utf-8

from django.conf import settings


def common(request):
    return dict(
        TAM_BACKGROUND=settings.TAM_BACKGROUND_COLOR,
        TAM_PERMANENT_CLOCK=settings.TAM_PERMANENT_CLOCK,
        GOOGLE_ANALYTICS=settings.GOOGLE_ANALYTICS_ID,
    )
