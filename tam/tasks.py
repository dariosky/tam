# coding: utf-8
from celery.task import task
from celery.task import Task
from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from celery import registry

@task(name="backup.job")
def doBackupTask(user_id):
	lock_id = "tasklock"
	cache.delete(lock_id)
	LOCK_EXPIRE = 60 * 60 # Lock expires in 60 minutes
	user = User.objects.get(id=user_id)
	print "Esisteva la chiave %s? %s" % (lock_id, cache.get(lock_id))
	acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
	release_lock = lambda: cache.delete(lock_id)
	if acquire_lock():
		try:
			print "Starting backup"
			from tam.views.backup import doBackup
			#doBackup(user.username)
			import time
			time.sleep(10)
			print "Fine del backup"
		finally:
			release_lock()
	else:
		print "TASK is already in progress"

@task(name="movelogs")
@transaction.commit_manually
def moveLogs():
	from django.contrib.contenttypes.models import ContentType
	from django.db import connections
	from modellog.actions import logAction
	print "Cominciamo a spostare"
	con = connections['default']
	cursor = con.cursor()
	cursor.execute("SELECT * from tam_actionlog")
	logs = cursor.fetchall()
	print dir(con)
	return
	print len(logs), "***********************"

	for oldlog in logs:
		print "sposto", oldlog
		user_id, content_type_id, object_id, action_type, data, pk, description = oldlog #@UnusedVariable
		user = User.objects.get(pk=user_id)
		ct = ContentType.objects.get(id=content_type_id)
		ct_class = ct.model_class()
		try:
			instance = ct_class.objects.get(id=object_id)
		except ct_class.DoesNotExist:
			instance = None
#			messageLines.append("%s fatta da %s" % (action_type, user))
		logAction(action=action_type, instance=instance, description=description, user=user, log_date=data)
	transaction.commit(using="modellog")
	cursor.execute("drop table tam_actionlog")
	con.commit()
	from tamArchive.archiveViews import vacuum_db #@Reimport
	vacuum_db()
	con.commit()
