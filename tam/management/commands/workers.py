# coding=utf-8
import logging
import os
import signal
import subprocess

import psutil as psutil
from django.core.management.base import AppCommand

import settings
from .utils import is_ps_running

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger('tam.deploy')


def stop_process(pid):
    try:
        procs = [psutil.Process(pid)]
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        gone, alive = psutil.wait_procs(procs, timeout=5)
        for p in alive:
            p.kill()
    except psutil.NoSuchProcess:
        logger.info("Process in PID not found")


class Command(AppCommand):
    help = 'Manage the web workers'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('action', nargs='?', type=str,
                            help="start, restart, stop")

    def handle(self, *args, **options):
        pid_file = settings.DEPLOYMENT['WORKERS']['PID_FILE']
        log_file = settings.DEPLOYMENT['WORKERS']['LOG_FILE']
        venv = settings.DEPLOYMENT['FOLDERS']['VENV_FOLDER']
        repo = settings.DEPLOYMENT['FOLDERS']['REPOSITORY_FOLDER']
        threads = settings.DEPLOYMENT['WORKERS']['THREADS']

        if options['action'] == 'start':
            logger.debug("Checking workers status %s" % pid_file)
            running = is_ps_running(pid_file)
            if not running:
                logger.info("Starting worker processes")
                command = ['{venv}/bin/python {repo}/manage.py'.format(repo=repo,
                                                                       venv=venv),
                           'runworker',
                           '--threads %d' % threads,
                           '>> %s' % log_file,
                           '2>&1'
                           ]
                proc = subprocess.Popen(' '.join(command), shell=True,
                                        stdin=None, stdout=None, stderr=None
                                        )
                with open(pid_file, 'w') as f:
                    f.write("%s\n" % proc.pid)
            else:
                logger.info("Workers were already running")

        if options['action'] == 'stop':
            pid = is_ps_running(pid_file)
            if pid:
                logger.info("Stopping Workers processes")
                stop_process(pid)
                os.remove(pid_file)
            else:
                logger.info("Workers are not running")
