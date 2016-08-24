# coding=utf-8
from django.db import connections
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed


class SQLLogMiddleware:
    def __init__(self):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()

    def process_response(self, request, response):
        if connections['default'].queries:
            #			time = 0.0
            qfile = open("querylog.sql", "w")
            rows = []
            for q in connections['default'].queries:
                sql = q['sql']
                time = q['time']
                rows.append((time, sql))

            rows.sort(reverse=True)
            qfile.write("\n".join(["/*{:>10}*/ {}".format(*row) for row in rows]))
            qfile.close()
        return response
