# coding=utf-8
import logging

import settings
from tam.management.runner import RunnerCommand

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("tam.deploy")


class Command(RunnerCommand):
    help = "Manage the Channels workers"
    name = "Workers"

    pid_file = settings.DEPLOYMENT["WORKERS"]["PID_FILE"]
    log_file = settings.DEPLOYMENT["WORKERS"]["LOG_FILE"]
    venv = settings.DEPLOYMENT["FOLDERS"]["VENV_FOLDER"]
    repo = settings.DEPLOYMENT["FOLDERS"]["REPOSITORY_FOLDER"]
    threads = settings.DEPLOYMENT["WORKERS"]["THREADS"]

    command = [
        "{0.venv}/bin/python {0.repo}/manage.py",
        "runworker",
        "--threads {0.threads}",
        ">> {0.log_file}",
        "2>&1",
    ]
