# coding=utf-8

import settings
from tam.management.runner import RunnerCommand


class Command(RunnerCommand):
    help = "Manage the Daphne frontend server"
    name = "Daphne"

    pid_file = settings.DEPLOYMENT["FRONTEND"]["PID_FILE"]
    log_file = settings.DEPLOYMENT["FRONTEND"]["LOG_FILE"]
    port = settings.DEPLOYMENT["FRONTEND"]["PORT"]
    venv = settings.DEPLOYMENT["FOLDERS"]["VENV_FOLDER"]

    command = [
        "{0.venv}/bin/daphne",
        "-p {0.port}",
        "--http-timeout 30",  # 1 minute timeout
        "asgi:channel_layer",
        ">> {0.log_file}",
        "2>&1",
    ]
