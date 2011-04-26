from django.db import connections
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

class SQLLogMiddleware:
	def __init__(self):
		if True or not settings.DEBUG:
			raise MiddlewareNotUsed()
		
	def process_response (self, request, response):
		if connections['default'].queries:
#			time = 0.0
			try:
				qfile=file("querylog.sql", "w")
				for q in connections['default'].queries:
					qfile.write("%s\n"%q['sql'])
	#				time += float(q['time'])
				qfile.close()
			except:
				pass
		return response
