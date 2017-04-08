# coding=utf-8
import logging
import os
import signal
import subprocess

import psutil as psutil
from django.core.management.base import AppCommand

from tam.management.commands.utils import is_ps_running

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger('tam.deploy')


def stop_process(pid):
    try:
        if isinstance(pid, psutil.Process):
            pid = pid.pid
        procs = [psutil.Process(pid)]
        os.killpg(os.getpgid(pid), signal.SIGTERM)
        gone, alive = psutil.wait_procs(procs, timeout=5)
        for p in alive:
            p.kill()
    except psutil.NoSuchProcess:
        logger.info("Process in PID not found")


class RunnerCommand(AppCommand):
    help = 'Manage a command to be start/restart/stop'
    name = 'Process'
    command = ['echo Hello world']
    pid_file = None

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('action', nargs='?', type=str,
                            help="start, restart, stop")

    def handle(self, *args, **options):
        if self.pid_file is None:
            print("Please add a pid_file location to the command instances")
            exit(1)
        action_handler_name = 'handle_%s' % options['action']
        handler = getattr(self, action_handler_name, None)
        if handler:
            handler()
        else:
            logger.error("Unknown action %s" % options['action'])
            exit(1)

    def handle_start(self):
        running = is_ps_running(self.pid_file)
        if not running:
            logger.info("Starting {name}".format(name=self.name))
            command = [
                command_part.format(self) for command_part in self.command
            ]
            print(command)

            proc = subprocess.Popen(' '.join(command), shell=True,
                                    stdin=None, stdout=None, stderr=None
                                    )
            with open(self.pid_file, 'w') as f:
                f.write("%s\n" % proc.pid)
        else:
            logger.info("{name} is already running".format(name=self.name))

    def handle_restart(self):
        running_process = is_ps_running(self.pid_file)
        if running_process:
            logger.info("Killing {name}".format(name=self.name))
            running_process.send_signal(signal.SIGTERM)
        self.handle_start()

    def handle_stop(self):
        pid = is_ps_running(self.pid_file)
        if pid:
            logger.info("Stopping {name}".format(name=self.name))
            stop_process(pid)
            os.remove(self.pid_file)
        else:
            logger.info("{name} is not running".format(name=self.name))
