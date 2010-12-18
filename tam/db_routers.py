#coding: utf-8

class TamArchiveRouter(object):
	""" A DB router to keep only the 'tamArchiveApp' on 'archive' db """

	def db_for_read(self, model, **hints):
		if model._meta.app_label == 'tamArchive':
			return 'archive'

	def db_for_write(self, model, **hints):
		if model._meta.app_label == 'tamArchive':
			return 'archive'

	def allow_syncdb(self, db, model):
		if db == 'archive':
			return model._meta.app_label == 'tamArchive'
		elif model._meta.app_label =='tamArchive':
			return False

