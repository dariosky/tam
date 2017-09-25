# coding=utf-8

from django.conf import settings


def common(request):
    return dict(
        settings=settings,
    )
