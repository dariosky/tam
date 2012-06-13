#coding: utf-8
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, HttpResponse
from django.template.context import RequestContext
from glob import glob
from modellog.actions import logAction
import datetime
import gzip
import logging
import os
import time
from django.contrib import messages
from tam.tasks import doBackupTask

def humanizeSize(size):
	size = float(size)
	suffix = "byte"
	if size==0: return "zero"
	if size > 1024:
		size = size / 1024
		suffix = "KB"
		if size > 1024:
			size = size / 1024
			suffix = "MB"
	return "%.2f%s" % (size, suffix)

def getBackupInfo(doCleanup=False):
	""" Return some info needed to do a sqlite backup
		and current backup status.
		doCleanup tell to keep at most backcount backups
	"""
	backcount = 20	# numero di backup da tenere
	dbname = settings.DATABASES['default']['NAME']
	if not os.path.isfile(dbname):
		raise Exception("Impossibile trovare il DB %s." % dbname)
	backupdir = os.path.join(settings.PROJECT_PATH, 'backup')	# backup subfolder
	if not os.path.isdir(backupdir):
		os.makedirs(backupdir)
	backupFilter = os.path.join(backupdir, '*.gz')

	def extractBackupUser(filename):
		""" Cerca di estrarre il nome dell'utente che ha fatto il backup
			Cercando dall'ultimo - al primo . del nome del backup
			"""
		try:
			nomefile = os.path.splitext(os.path.basename(filename))[0]
			return nomefile.split("-")[-1].split(".")[0]
		except:
			return "anonimo"

	backups = [ {
			"filename":filename,
			"date":datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
			"size":humanizeSize(os.path.getsize(filename)),
			"username": extractBackupUser(filename),
			} for filename in glob(backupFilter) ]
	backups.sort()

	if doCleanup and len(backups) > backcount:
		for backup in backups[:-backcount + 1]:
			logging.debug("Cancello il backup: %s" % os.path.basename(backup["filename"]))
			os.unlink(backup["filename"])
	return { "dbname": dbname, "backupdir":backupdir, "backups":backups,
		}

def getbackup(request, backupdate):
	if not request.user.has_perm('tam.get_backup'):
		messages.error(request, "Non hai accesso al download dei backup.")
		return HttpResponseRedirect(reverse("tamBackup"))
	t = time.strptime(backupdate, '%d-%m-%Y-%H%M')
	dataScelta = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min)
	backupInfo = getBackupInfo(doCleanup=True)
	for backup in backupInfo["backups"]:
		if backup["date"].timetuple()[:5] == dataScelta.timetuple()[:5]:
			logAction('G', description='Backup del %s scaricato' % backupdate, user=request.user)
			backup_filename = backup["filename"]
			backupPath = os.path.join(backupInfo["backupdir"], backup_filename)
			responseFile = file(backupPath, 'rb')
			response = HttpResponse(responseFile.read(), mimetype='application/octet-stream') #'application/gzip'
			response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(backup_filename)
			return response
	else:
		messages.error(request, "Backup del %s non trovato." % dataScelta)
		return HttpResponseRedirect(reverse("tamBackup"))


def doBackup(user):
	logAction('B', description='Backup richiesto', user=user)
	username = user.username
	backupInfo = getBackupInfo(doCleanup=True)
	n = datetime.datetime.now()
	newBackupFilename = "%s - tam - %s.db3.gz" % (n.strftime('%Y-%m-%d %H%M'), username)
	backupPath = os.path.join(backupInfo["backupdir"], newBackupFilename)
	logging.debug("%s ===> %s" % (backupInfo["dbname"], backupPath))

	f_in = file(backupInfo["dbname"], "rb")
	real_out = open(backupPath, 'wb')

	dbname = os.path.split(settings.DATABASES['default']['NAME'])[1]
	f_out = gzip.GzipFile(dbname, fileobj=real_out)	# scrivo sul file Gzip il contenuto si chiama sempre tam.db3
	f_out.write(f_in.read())
	f_in.close()
	f_out.close()
	real_out.close()
	return HttpResponseRedirect(reverse("tamBackup"))


def backup(request, template_name="utils/backup.html"):
	if not request.user.has_perm('tam.can_backup'):
		messages.error(request, "Non hai accesso alla gestione dei backup.")
		return HttpResponseRedirect("/")
	if "backup" in request.POST:
		#backupFile = doBackup(request.user)
		doBackupTask.delay(user_id = request.user.id)
		messages.success(request, "Backup del database avviato... sarà pronto tra poco.")
		return HttpResponseRedirect(reverse("tamBackup"))
	backupInfo = getBackupInfo()
	return render_to_response(template_name, {"backupInfo":backupInfo}, context_instance=RequestContext(request))
