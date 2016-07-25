# coding=utf-8

from django.conf import settings


def common(request):
    return dict(
        TAM_BACKGROUND=settings.TAM_BACKGROUND_COLOR
    )
