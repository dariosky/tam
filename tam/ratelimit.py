# coding=utf-8
from brake.backends import cachebe


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class RateCache(cachebe.CacheBackend):
    def get_client_ip(self, request):
        return get_client_ip(request)
