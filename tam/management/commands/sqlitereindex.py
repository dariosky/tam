from django.core.management.base import AppCommand
from django.db import transaction, connection
from django.db import models
from django.core.management.color import no_style

class Command(AppCommand):
	args = ''
	help = 'Check all indexes suggested from models exists and create them if needed.' #@ReservedAssignment

	def handle_app(self, app, **options):
		self.stdout.write("Checking indexes for %s.\n" % app.__name__)
		all_suggested_indexes = []
		models_list = models.get_models(app)
		for model in models_list:
			suggested_indexes = connection.creation.sql_indexes_for_model(model, no_style())
			for index_creation_string in suggested_indexes:
				all_suggested_indexes.append(index_creation_string)

		get_existing_indexes_query = """
			select sql 
			from sqlite_master where type = 'index'
			       and (
			                          (name like 'tam%%')
			                          or name like 'fatturazione%%' 
			           );
		"""
		cursor = connection.cursor() #@UndefinedVariable
		cursor.execute(get_existing_indexes_query)
		existing_indexes = [record[0] + ";" for record in cursor.fetchall()]

		missing_indexes = []
		for index in all_suggested_indexes:
			if index not in existing_indexes:
				missing_indexes.append(index)
		if missing_indexes:
			create_input = raw_input("Create all missing suggested indexes in %s[y,N]? " % app.__name__)
			if create_input.strip().lower() == "y":
				self.stdout.write("Creating missing indexes.")
				for index_creation_query in missing_indexes:
					cursor.execute(index_creation_query)
				transaction.commit_unless_managed()
				self.stdout.write("Indexes created.")
		else:
			self.stdout.write("All indexes checked for %s.\n" % app.__name__)

