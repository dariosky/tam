# coding: utf-8
from threading import Thread

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
from tam.tasks import single_instance_task
import sys
import subprocess
from tam import tamdates


def humanizeSize(size):
    size = float(size)
    suffix = "byte"
    if size == 0:
        return "zero"
    if size > 1024:
        size /= 1024
        suffix = "KB"
        if size > 1024:
            size /= 1024
            suffix = "MB"
    return "%.2f%s" % (size, suffix)


def getBackupInfo(doCleanup=False):
    """ Return some info needed to do a sqlite backup
        and current backup status.
        doCleanup tell to keep at most backcount backups
    """
    backcount = 10  # numero di backup da tenere
    dbname = settings.DATABASES['default']['NAME']
    backupdir = os.path.join(settings.PROJECT_PATH, 'backup')  # backup subfolder
    if not os.path.isdir(backupdir):
        os.makedirs(backupdir)

    def extractBackupUser(filename):
        """ Cerca di estrarre il nome dell'utente che ha fatto il backup
            Cercando dall'ultimo - al primo . del nome del backup
            """
        try:
            nomefile = os.path.splitext(os.path.basename(filename))[0]
            return nomefile.split("-")[-1].split(".")[0]
        except:
            return "anonimo"

    backupFiles = glob(os.path.join(backupdir, '*.db3.gz'))  # sqlitefiles
    backupFiles += glob(os.path.join(backupdir, '*.pgdump'))  # postgres
    backups = [{
                   "filename": filename,
                   "date": datetime.datetime.fromtimestamp(os.path.getmtime(filename)),
                   "size": humanizeSize(os.path.getsize(filename)),
                   "username": extractBackupUser(filename),
               } for filename in backupFiles]
    backups.sort()

    if doCleanup and len(backups) > backcount:
        for backup in backups[:-backcount + 1]:
            logging.debug("Cancello il backup: %s" % os.path.basename(backup["filename"]))
            os.unlink(backup["filename"])
    return {"dbname": dbname, "backupdir": backupdir, "backups": backups, }


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
            response = HttpResponse(responseFile.read(),
                                    content_type='application/octet-stream')  # 'application/gzip'
            response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(
                backup_filename)
            return response
    else:
        messages.error(request, "Backup del %s non trovato." % dataScelta)
        return HttpResponseRedirect(reverse("tamBackup"))


def doBackupSqlite(targetFile, sourceFile):
    if not os.path.isfile(sourceFile):
        raise Exception("Impossibile trovare il DB %s." % sourceFile)
    f_in = file(sourceFile, "rb")
    real_out = open(targetFile, 'wb')

    dbname = os.path.split(sourceFile)[1]
    f_out = gzip.GzipFile(dbname,
                          fileobj=real_out)  # scrivo sul file Gzip il contenuto si chiama sempre tam.db3
    f_out.write(f_in.read())
    f_in.close()
    f_out.close()
    real_out.close()


def doBackupPostgre(targetFile, dbName,
                    host=None, port=None,
                    username=None, password=None):
    # SET PGPASSWORD=<PassWord>
    # C:\Programmi\PostgreSQL\9.2\bin
    # pg_dump.exe -F c -h localhost -p 5432 -U tam -f c:\artebackup.sql artetam
    pg_dump_prefix = getattr(settings, 'PG_DUMP_PREFIX', '')
    pgdump_command = 'pg_dump.exe' if 'win' in sys.platform else 'pg_dump'
    args = []
    if host:
        args.append('--username=%s' % username)
    if password:
        # args.append('--password')	# force password request
        os.putenv('PGPASSWORD', password)  # use password from env
    if host:
        args.append('--host=%s' % host)
    if port:
        args.append('--port=%s' % port)
    args.append('-F c')  # use the custom format
    args.append("-w")  # no password prompt
    args.append('-f "%s"' % targetFile)  # specify the output file path
    if dbName:
        args.append(dbName)
    command = "\"%s%s\" %s" % (pg_dump_prefix, pgdump_command, " ".join(args))
    print "Starting process"
    print command
    print subprocess.check_output(command, shell=True)
    print "End of the process"


def doBackup(user):
    backupInfo = getBackupInfo(doCleanup=True)

    logAction('B', description='Backup richiesto', user=user)
    username = user.username

    dbType = settings.DATABASES['default']['ENGINE']

    n = tamdates.ita_now()
    newBackupFilename = "%s - tam - %s" % (n.strftime('%Y-%m-%d %H%M'), username)
    backupPath = os.path.join(backupInfo["backupdir"], newBackupFilename)
    logging.debug("%s ===> %s" % (backupInfo["dbname"], backupPath))

    if dbType == 'django.db.backends.sqlite3':
        doBackupSqlite(targetFile=backupPath + ".db3.gz", sourceFile=backupInfo["dbname"])
    elif dbType == 'django.db.backends.postgresql_psycopg2':
        doBackupPostgre(
            targetFile=backupPath + ".pgdump",
            dbName=settings.DATABASES['default']['NAME'],
            host=settings.DATABASES['default']['HOST'],
            port=settings.DATABASES['default']['PORT'],
            username=settings.DATABASES['default']['USER'],
            password=settings.DATABASES['default']['PASSWORD'],
        )
    else:
        raise Exception("Impossibile fare backup di %s" % dbType)

    return backupPath


@single_instance_task(60 * 5)  # 5 minutes timeout
def spawn_backup_thread(*args, **kwargs):
    t = Thread(target=doBackup, args=args, kwargs=kwargs, name='backup')
    t.setDaemon(True)
    t.start()


def backup(request, template_name="utils/backup.html"):
    if not request.user.has_perm('tam.can_backup'):
        messages.error(request, "Non hai accesso alla gestione dei backup.")
        return HttpResponseRedirect("/")
    if "backup" in request.POST:
        # backupFile = doBackup(request.user)
        spawn_backup_thread(request.user)
        messages.success(request, "Backup del database avviato... sarà pronto tra poco.")
        return HttpResponseRedirect(reverse("tamBackup"))
    backupInfo = getBackupInfo()
    return render_to_response(template_name, {"backupInfo": backupInfo},
                              context_instance=RequestContext(request))


if __name__ == '__main__':
    from django.contrib.auth.models import User

    user = User.objects.get(id=1)
    # doBackup(user)
    spawn_backup_thread(user)
