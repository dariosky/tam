from django.core.management.base import BaseCommand, CommandError, AppCommand
from django.db import connections, transaction, connection
from south.db import DEFAULT_DB_ALIAS
from django.core.management.sql import sql_indexes
from django.db.models.loading import get_apps
from django.db import models

class Command(AppCommand):
	args = ''
	help = 'Check all indexes suggested from models exists and create them if needed.' #@ReservedAssignment

	def handle_app(self, app, **options):
		self.stdout.write("Checking indexes.\n")
		suggested_index =  sql_indexes(app, self.style, connections[options.get('database', DEFAULT_DB_ALIAS)])
		self.stdout.write("style: %s\n"% self.style)
		self.stdout.write(suggested_index.__repr__()+"\n")
#		get_indexes_query = """
#			select * 
#			from sqlite_master where type = 'index'
#			       and (
#			                          (name like 'tam%%')
#			                          or name like 'fatturazione%%' 
#			           );
#		"""
#		cursor = connection.cursor()
#		cursor.execute(get_indexes_query)
#		for index in cursor.fetchall():
#			self.stdout.write(index.__repr__()+"\n")
		#transaction.commit_unless_managed()
		
