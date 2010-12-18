from django.db import connection
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

class SQLLogMiddleware:
	def __init__(self):
		if True or not settings.DEBUG:
			raise MiddlewareNotUsed()
		
	def process_response (self, request, response):
		if connection.queries:
#			time = 0.0
			try:
				qfile=file("querylog.sql", "w")
				for q in connection.queries:
					qfile.write("%s\n"%q['sql'])
	#				time += float(q['time'])
				qfile.close()
			except:
				pass
#			print "*************** FINAL QUERIES: %d ******************" % len(connection.queries)
#			print "time: %f" % time
		return response
