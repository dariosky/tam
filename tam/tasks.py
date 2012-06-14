# coding: utf-8
from celery.task import task
from celery.task import Task
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from celery import registry

def single_instance_task(timeout=60 * 60 * 2):	# 2 hour of default timeout
	""" Stop concurrency using cache,
		from http://stackoverflow.com/questions/4095940/running-unique-tasks-with-celery
	"""
	def task_exc(func):
		def wrapper(*args, **kwargs):
			lock_id = "celery-single-instance-" + func.__name__
			acquire_lock = lambda: cache.add(lock_id, "true", timeout)
			release_lock = lambda: cache.delete(lock_id)
			if acquire_lock():
				try:
					func(*args, **kwargs)
				finally:
					release_lock()
			else:
				print "stop concurrency"
		return wrapper
	return task_exc


@task(name="backup.job")
@single_instance_task(60 * 5)	# 5 minutes timeout
def doBackupTask(user_id):
	user = User.objects.get(id=user_id)
	print "Starting backup"
	from tam.views.backup import doBackup
	doBackup(user)
	print "Fine del backup"


@task(name="movelogs")
#@single_instance_task(60 * 5)	# 5 minutes timeout
#@transaction.commit_manually
def moveLogs(name='movelogs.job'):
	from django.contrib.contenttypes.models import ContentType
	from django.db import connections
	from modellog.actions import logAction
	print "Cominciamo a spostare"
	con = connections['default']
	cursor = con.cursor()
	try:
		cursor.execute("SELECT count(*) from tam_actionlog")
	except:
		print "no table actionlog"
		return
	totalcount = cursor.fetchone()[0]
	print totalcount
	cursor.execute("SELECT * from tam_actionlog")
	count = 0
	chunksize = 500
	oldPercent = None
	usersByID = {}
	while True:
		oldLogsChunk = cursor.fetchmany(chunksize)
		if not oldLogsChunk: break
		for oldlog in oldLogsChunk:
			user_id, content_type_id, object_id, action_type, data, pk, description = oldlog #@UnusedVariable
			user = usersByID.get(user_id, User.objects.get(pk=user_id))
			ct = ContentType.objects.get(id=content_type_id)
			ct_class = ct.model_class()
			try:
				instance = ct_class.objects.get(id=object_id)
			except ct_class.DoesNotExist:
				instance = None
			logAction(action=action_type, instance=instance, description=description, user=user, log_date=data)
			count += 1
			break
		if count == 1: break
		percent = count * 100 / totalcount
		transaction.commit(using="default")
		transaction.commit(using="modellog")
		if oldPercent is None or percent >= oldPercent + 10:
			print "%s%%" % percent,
			oldPercent = percent

	print
	print "Delete table"
	cursor.execute("drop table tam_actionlog")
	from tamArchive.archiveViews import vacuum_db
	vacuum_db()



@task(name='testtask')
def test_task(s='Test'):
	return s

if __name__ == '__main__':
	moveLogs.run()
