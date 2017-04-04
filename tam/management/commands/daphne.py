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
    help = 'Manage the daphne frontend server'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('action', nargs='?', type=str,
                            help="start, restart, stop")

    def handle(self, *args, **options):
        pid_file = settings.DEPLOYMENT['FRONTEND']['PID_FILE']
        log_file = settings.DEPLOYMENT['FRONTEND']['LOG_FILE']
        port = settings.DEPLOYMENT['FRONTEND']['PORT']
        venv = settings.DEPLOYMENT['FOLDERS']['VENV_FOLDER']

        if options['action'] == 'start':
            logger.debug("Checking daphne status %s" % pid_file)
            running = is_ps_running(pid_file)
            if not running:
                logger.info("Starting Daphne frontend server")
                command = ['%s/bin/daphne' % venv, '-p %d' % port,
                           '--http-timeout 30',  # 1 minute timeout
                           'asgi:channel_layer',
                           '>> %s' % log_file,
                           '2>&1'
                           ]
                proc = subprocess.Popen(' '.join(command), shell=True,
                                        stdin=None, stdout=None, stderr=None
                                        )
                with open(pid_file, 'w') as f:
                    f.write("%s\n" % proc.pid)
            else:
                logger.info("Daphne was already running")
        elif options['action'] == 'stop':
            pid = is_ps_running(pid_file)
            if pid:
                logger.info("Stopping Daphne")
                stop_process(pid)
                os.remove(pid_file)
            else:
                logger.info("Daphne is not running")
        else:
            logger.error("Unknown action %s" % options['action'])
            exit(1)
