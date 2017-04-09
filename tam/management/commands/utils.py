# coding=utf-8
import logging
import os

import psutil

logger = logging.getLogger('tam.deploy')


def get_pid(pid_file):
    pid_folder = os.path.dirname(pid_file)
    if not os.path.isdir(pid_folder):
        logger.debug("Creating pids folder")
        os.makedirs(pid_folder)

    pid = None
    try:
        if os.path.isfile(pid_file):
            with open(pid_file) as f:
                content = f.read()
                pid = int(content.strip())
    except Exception as e:
        print(e)
    return pid


def is_ps_running(pid_file):
    pid = get_pid(pid_file)

    if pid:
        try:
            process = psutil.Process(pid)
            return process
        except psutil.NoSuchProcess:
            logger.info("Process in PID not found")
            os.remove(pid_file)
