# coding: utf-8
from django.core.cache import cache
# from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction, models
import time
import djangotasks


# ===============================================================================
def humanizeTime(sec):
	result = ""
	if sec >= 60:
		mins = sec / 60
		if mins >= 60:
			hr = mins / 60
			mins %= 60
			result += "%d hour " % hr
		if mins:
			result += "%d min " % mins
		sec %= 60
	if sec:
		result += "%d sec " % sec
	return result


def print_timing(func):
	def wrapper(*arg, **kwargs):
		t1 = time.time()
		res = func(*arg, **kwargs)
		t2 = time.time()
		print '%s took %s' % (func.func_name, humanizeTime(t2 - t1))
		return res

	return wrapper


def single_instance_task(timeout=60 * 60 * 2):  # 2 hour of default timeout
	""" Stop concurrency using cache,
		from http://stackoverflow.com/questions/4095940/running-unique-tasks-with-celery
	"""

	def task_exc(func):
		def wrapper(*args, **kwargs):
			lock_id = "task-single-instance-" + func.__name__
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

# ===============================================================================



#============================================================
# Djangotasks uses DB, so each tasktype has a model
class TaskBackup(models.Model):
	user = models.ForeignKey(User)  # the user who starts the backup

	def do(self):
		print 'Starting backup'
		from tam.views.backup import doBackup

		doBackup(self.user)
		print "Fine del backup"

	class Meta:
		app_label = "tam"


djangotasks.register_task(TaskBackup.do, "Run TAM backup")


@single_instance_task(60 * 5)  # 5 minutes timeout
def doBackupTask(user):
	# ... create the backup action object in the DB
	backup_task = TaskBackup(user=user)
	backup_task.save()

	# ...and finally defer the task
	task = djangotasks.task_for_object(backup_task.do)
	djangotasks.run_task(task)


############################################################################

class TaskMovelog(models.Model):
	def do(self):
		moveLogs()

	class Meta:
		app_label = "tam"


djangotasks.register_task(TaskMovelog.do, "Oldlog move")


@single_instance_task(60 * 25)  # 25 minutes timeout
@print_timing
# @transaction.commit_manually
# @transaction.commit_manually(using='modellog')
def moveLogs(name='movelogs.job'):
	from django.contrib.contenttypes.models import ContentType
	from django.db import connections
	from modellog.actions import logAction

	print "Cominciamo a spostare"
	con = connections['default']
	cursor = con.cursor()
	try:
		cursor.execute("SELECT count(*) from tam_actionlog where data>='2012-01-01'")  # sposto solo dal 2012
	except:
		print "no table actionlog"
		con.set_clean()
		return
	totalcount = cursor.fetchone()[0]
	print "Total logs:", totalcount
	count = 0
	chunksize = 500
	oldPercent = None
	usersByID = {}
	ctypeByID = {}
	while True:
		cursor.execute("SELECT * from tam_actionlog where data>='2012-01-01' order by data desc limit %d" % chunksize)
		con.set_clean()
		oldLogsChunk = cursor.fetchall()
		logs_to_delete = []  # lista degli ID da cancellare
		if not oldLogsChunk: break
		for oldlog in oldLogsChunk:
			user_id, content_type_id, object_id, action_type, data, pk, description = oldlog  #@UnusedVariable
			if user_id in usersByID:
				user = usersByID[user_id]
			else:
				user = User.objects.get(pk=user_id)
				usersByID[user_id] = user
			if not content_type_id in ctypeByID:
				ct = ContentType.objects.get(id=content_type_id)
				ctypeByID[content_type_id] = ct
			else:
				ct = ctypeByID[content_type_id]

			ct_class = ct.model_class()
			try:
				instance = ct_class.objects.get(id=object_id)
			except ct_class.DoesNotExist:
				instance = None
			logAction(action=action_type, instance=instance, description=description, user=user, log_date=data)
			logs_to_delete.append(str(pk))
			count += 1

		percent = count * 100 / totalcount
		if logs_to_delete:
			delete_query = "delete from tam_actionlog where id in (%s)" % ",".join(logs_to_delete)
			#print delete_query
			cursor.execute(delete_query)
			con.commit()
		# transaction.commit(using="modellog")
		if oldPercent is None or percent >= oldPercent + 5:
			print "%s%%" % percent,
			oldPercent = percent
		#break
		# fine del chunk

	print
	print "Delete table"
	cursor.execute("drop table tam_actionlog")
	from tamArchive.tasks import vacuum_db

	vacuum_db()
	con.commit()
	print "Fine"


# Djangotasks uses DB, so each tasktype has a model
class TaskArchive(models.Model):
	user = models.ForeignKey(User)  # the user who starts the backup
	end_date = models.DateField()

	def do(self):
		from tamArchive.tasks import do_archiviazione

		do_archiviazione(self.user, self.end_date)

	class Meta:
		app_label = "tam"


djangotasks.register_task(TaskArchive.do, "Run TAM archive")

#@task(name='testtask')
#def test_task(s='Test'):
#	return s

if __name__ == '__main__':
	pass
#	print humanizeTime(3690101)
