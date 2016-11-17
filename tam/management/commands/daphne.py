# coding=utf-8
import logging
import os
import subprocess

import psutil as psutil
from django.core.management.base import AppCommand

import settings

logging.basicConfig()
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
            p = psutil.Process(pid)
            print("Process is ", p.status())
            return True
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

        if options['action'] == 'start':
            print("Checking daphne status %s" % pid_file)
            running = is_ps_running(pid_file)
            if not running:
                logger.info("Starting Daphne frontend server")
                command = ['daphne', '-p %d' % port, 'asgi:channel_layer' '>> %s' % log_file, '2>&1']
                proc = subprocess.Popen(command, shell=True,
                                        stdin=None, stdout=None, stderr=None
                                        )
                with open(pid_file, 'w') as f:
                    f.write("%s\n" % proc.pid)
            else:
                logger.info("Daphne is running")
