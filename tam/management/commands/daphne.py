# coding=utf-8
import logging
import os
import signal
import subprocess

import psutil as psutil
from django.core.management.base import AppCommand

import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger('tam.deploy')


def is_ps_running(pid_file):
    pid_folder = os.path.dirname(pid_file)
    if not os.path.isdir(pid_folder):
        logger.debug("Creating pids folder")
        os.makedirs(pid_folder)
    try:
        with open(pid_file) as f:
            content = f.read()
            pid = int(content.strip())
    except Exception as e:
        print(e)
        pid = None
    if pid:
        try:
            psutil.Process(pid)
            return pid
        except psutil.NoSuchProcess:
            logger.info("Process in PID not found")


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
        pid_file = settings.DEPLOYMENT['GUNICORN']['PID_FILE']
        log_file = settings.DEPLOYMENT['GUNICORN']['LOG_FILE']
        port = settings.DEPLOYMENT['GUNICORN']['PORT']
        venv = settings.DEPLOYMENT['FOLDERS']['VENV_FOLDER']

        if options['action'] == 'start':
            logger.debug("Checking daphne status %s" % pid_file)
            running = is_ps_running(pid_file)
            if not running:
                logger.info("Starting Daphne frontend server")
                command = ['%s/bin/daphne' % venv, '-p %d' % port, 'asgi:channel_layer',
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

        if options['action'] == 'stop':
            pid = is_ps_running(pid_file)
            if pid:
                logger.info("Stopping Daphne")
                stop_process(pid)
                os.remove(pid_file)
            else:
                logger.info("Daphne is not running")
