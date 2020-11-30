# coding=utf-8
"""
Facilitate deployment to server

Deploy will consist of:
    push changes to GIT repository
    update dependences (with pip)
    update db (with south)
    collect static
    restart webserver (gunicorn)

"""

# Supervisor commands
#   supervisorctl start/stop/restart <appname>
#   kill the process... not optimal
# Graceful restart gunicorn with a HUP signal
# 	so instead of use supervisor, do a graceful restart with
# kill -s HUP $(cat gunicorn.pid)
import glob
import os
import posixpath
import sys
from contextlib import contextmanager as _contextmanager
from io import StringIO

import requests
from fabric.api import run, abort, env, put, task, cd
from fabric.context_managers import prefix, lcd, settings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.decorators import serial
from fabric.operations import local
from fabric.utils import puts
from past.builtins import basestring
from requests.auth import HTTPBasicAuth

env.localfolder = os.path.realpath(os.path.dirname(__file__))
env.port = 22
if not env.get('NAME') and __name__ != '__main__':
    print("Please call fab specifying a host config file.")
    print("Example: fab -c host.ini")
    sys.exit(1)

if os.path.exists(os.path.expanduser("~/.ssh/config")):
    env.use_ssh_config = True

DO_REQUIREMENTS = True


def perform_env_substitutions():
    """ Do recursive substitution until the value doesn't change
    Change the type of some env variable that should not be string
    """
    for key, value in env.items():
        if isinstance(env[key], basestring):
            old_value = env[key]
            while True:  #
                value = old_value.format(**env)
                if value == old_value:
                    break
                old_value = value
            env[key] = value
    if getattr(env, 'USE_SUPERVISOR', 'False') == 'False':
        env.USE_SUPERVISOR = False


perform_env_substitutions()


def secrets_file_paths():
    """ Return a list of secret files (to be sent) relative to REPOSITORY_FOLDER """
    return [env.SECRETS_FILE]


@_contextmanager
def virtualenv(venv_path=None):
    """
    Put fabric commands in a virtualenv
    """
    if venv_path is None:
        venv_path = env.VENV_FOLDER
    with prefix("source %s" % posixpath.join(venv_path, "bin/activate")):
        yield


def get_repository():
    if run("test -d %s" % env.REPOSITORY_FOLDER, quiet=True).failed:
        puts("Creating repository folder.")
        run("mkdir -p %s" % env.REPOSITORY_FOLDER)
    if not exists(posixpath.join(env.REPOSITORY_FOLDER, '.git')):
        puts("Cloning from repository.")
        run("git clone %s %s" % (env.GIT_REPOSITORY, env.REPOSITORY_FOLDER))


def create_virtualenv():
    if run("test -d %s" % env.VENV_FOLDER, quiet=True).failed:
        run('python3 -m venv %s' % env.VENV_FOLDER)


def update_distribute():
    with virtualenv():
        run('pip install -U -q distribute')


@task
def initial_deploy():
    """
    Prepare the remote instance with git repository and virtualenv.
    """
    get_repository()
    create_virtualenv()
    update_distribute()  # some package won't install if distriubte is the old one
    with cd(env.REPOSITORY_FOLDER):
        run('mkdir -p %s' % env.LOGDIR)  # create the log dir if missing
        run('chmod +x node_modules/.bin/yuglify')
    send_brand()
    create_run_command()
    set_mailgun_webhooks()


@serial
def update_database():
    with virtualenv():
        with cd(env.REPOSITORY_FOLDER):
            # update database, both standard apps and south migrated
            run("python manage.py migrate")


@task
def update_requirements():
    """ Update all libraries in requirements file """
    with virtualenv():
        with cd(env.REPOSITORY_FOLDER):
            run('pip install -U -r %s' % env.REQUIREMENT_PATH)  # update libraries


def update_instance(do_update_requirements=True, justPull=False):
    with cd(env.REPOSITORY_FOLDER):
        run("git pull")  # pull the changes
    if justPull:
        return
    with virtualenv():
        with cd(env.REPOSITORY_FOLDER):
            if do_update_requirements:
                update_requirements()

            run("python manage.py migrate")

            if run("test -d %s" % env.STATIC_FOLDER, quiet=True).failed:
                puts("Creating static subfolder for generated assets.")
                run("mkdir -p %s" % env.STATIC_FOLDER)

            if run("test -d %s" % env.MEDIA_FOLDER, quiet=True).failed:
                puts("Creating media subfolder for user uploaded assets.")
                run("mkdir -p %s" % env.MEDIA_FOLDER)

            run("python manage.py collectstatic --noinput")

            update_database()


def get_gunicorn_command(daemon=True):
    options = [
        '-w %s' % env.GUNICORN_WORKERS,  # --user=$USER --group=$GROUP
        '--log-level=debug',
        '-b 127.0.0.1:%s' % env.GUNICORN_PORT,
        '--pid %s' % env.GUNICORN_PID_FILE,
        '--log-file %(log)s' % {'log': env.GUNICORN_LOGFILE},
        '-t %s' % env.GUNICORN_WORKERS_TIMEOUT,
        '-n %s' % env.NAME,
        # timeout, upload processes can take some time (default is 30 seconds)
    ]
    if daemon:
        options.append('--daemon')
    return "{env_path}/bin/gunicorn {options_string} {wsgi_app}".format(
        env_path=env.VENV_FOLDER,
        options_string=" ".join(options),
        wsgi_app=env.WSGI_APPLICATION,
    )


def start(daemon=False):
    if env.USE_SUPERVISOR:
        # Supervisor should be set to use this fabfile too
        # the command should be 'fab gunicorn_start_local'
        run('supervisorctl start %s' % env.SUPERVISOR_JOBNAME)
    else:  # directly start remote Gunicorn
        with virtualenv():
            with cd(env.REPOSITORY_FOLDER):
                gunicorn_command = get_gunicorn_command(daemon=True)
                run(gunicorn_command)


@task
def stop():
    """ Stop the remote gunicorn instance (eventually using supervisor) """
    if env.USE_SUPERVISOR:
        run('supervisorctl stop %s' % env.SUPERVISOR_JOBNAME)
    else:  # directly start remote Gunicorn
        puts('Sending TERM signal to Gunicorn.')
        gunicorn_pid = int(run('cat %s' % env.GUNICORN_PID_FILE, quiet=True))
        run("kill %d" % gunicorn_pid)


@task
def start_local():
    """ Start locally gunicorn instance """
    gunicorn_command = get_gunicorn_command(daemon=False)
    if env.USE_SUPERVISOR:
        # abort("You should not start_local if you would like to use Supervisor.")
        process = None
        try:
            process = local(gunicorn_command)
        except Exception as e:
            print("EXCEPTION: %s" % e)
            if process is not None:
                import signal

                process.send_signal(signal.SIGTERM)
    else:
        with lcd(env.REPOSITORY_FOLDER):
            local(gunicorn_command)


@task
def restart():
    """ Start/Restart the remote gunicorn instance (eventually using supervisor) """
    if run("test -e %s" % env.GUNICORN_PID_FILE, quiet=True).failed:
        puts("Gunicorn doesn't seems to be running (PID file missing)...")
        start()

    # gunicorn_pid = int(run('cat %s' % GUNICORN_PID_FILE, quiet=True))
    # if not gunicorn_pid:
    # 	abort('ERROR: Gunicorn seems down after the start command.')
    else:
        puts('Gracefully restarting Gunicorn.')
        gunicorn_pid = int(run('cat %s' % env.GUNICORN_PID_FILE, quiet=True))
        run("kill -s HUP %d" % gunicorn_pid)


@task
def send_secrets(secret_files=None, ask=False):
    """ Send the secret settings file that is excluded from VCS """
    if ask and not confirm("Upload secret settings?"):
        return
    if secret_files is None:
        secret_files = secrets_file_paths()
    if isinstance(secret_files, basestring):
        secret_files = [secret_files]
    puts("Uploading secrets.")
    for filename in secret_files:
        local_path = os.path.join(env.localfolder, filename)
        remote_path = posixpath.join(env.REPOSITORY_FOLDER, filename)
        put(local_path, remote_path)
    if len(secret_files) == 1:
        with cd(env.REPOSITORY_FOLDER):
            run('ln -s -f %s settings_local.py' % secret_files[0])


def run_command_content(daemon=True):
    default_args = "--workers={GUNICORN_WORKERS} --log-level=warning -t {GUNICORN_WORKERS_TIMEOUT}" \
                   " -n {NAME}"
    if daemon:
        default_args += " --daemon"
    env.GUNICORN_ARGUMENTS = default_args.format(**env)
    env.WSGI_APPLICATION = "wsgi:application"

    # prepare the variables
    content = """#!/bin/bash
GUNICORN_CMD={VENV_FOLDER}/bin/gunicorn
GUNICORN_ARGS="{GUNICORN_ARGUMENTS}"
LOG_PATH={GUNICORN_LOGFILE}
PID_PATH={GUNICORN_PID_FILE}
PORT={GUNICORN_PORT}
NAME={NAME}

cd {REPOSITORY_FOLDER}
sh {VENV_FOLDER}/bin/activate

start_server () {{
  if [ -f $PID_PATH ]; then
    if [ "$(ps -p `cat $PID_PATH` | wc -l)" -gt 1 ]; then
       echo "A server is already running on port $PORT"
       return
    else
        echo "We have the PID but not the process deleting PID and restarting"
        rm $PID_PATH
    fi
  fi
  #cd $PROJECTLOC
  echo "starting gunicorn on port $PORT"
  exec $GUNICORN_CMD $GUNICORN_ARGS -b 127.0.0.1:$PORT --log-file $LOG_PATH --pid $PID_PATH {WSGI_APPLICATION}
}}

stop_server () {{
  if [ -f $PID_PATH ] && [ "$(ps -p `cat $PID_PATH` | wc -l)" -gt 1 ]; then
    echo "stopping server on port $PORT"
    kill -9  `cat $PID_PATH`
    rm $PID_PATH
  else
    if [ -f $PID_PATH ]; then
      echo "server not running"
      rm $PID_PATH
    else
      echo "No pid file found for server"
    fi
  fi
}}

case "$1" in
'start')
  start_server
  ;;
'stop')
  stop_server
  ;;
'restart')
  stop_server
  sleep 2
  start_server
  ;;
*)
  echo "Usage: $0 {{ start | stop | restart }}"
  ;;
esac

exit 0
#exec $GUNICORN_CMD $GUNICORN_ARGS -b 127.0.0.1:$PORT --log-file $LOG_PATH --pid $PID_PATH {WSGI_APPLICATION}
    """
    return content.format(**env)


@task
def create_run_command():
    """ Create the remote_run command to be executed """
    puts("Creating run_server.")
    with lcd(env.localfolder):
        with cd(env.REPOSITORY_FOLDER):
            run_temp_file = StringIO(run_command_content())
            run_temp_file.name = "run_server"  # to show it as fabric file representation
            put(run_temp_file, posixpath.join(env.REPOSITORY_FOLDER, 'run_server'))
            run('chmod +x run_server')


@task
def local_create_run_command():
    puts("Creating run_server command to be run with supervisor.")
    with lcd(env.localfolder):
        with open('run_server', 'w') as runner:
            runner.write(run_command_content())


@task
def local_create_run_command():
    gunicorn_command = get_gunicorn_command(daemon=False)
    puts("Creating run_server command to be run " + (
        "with" if env.USE_SUPERVISOR else "without") + " supervisor.")
    with lcd(env.localfolder):
        with open('run_server', 'w') as runner:
            runner.write(run_command_content())


@task
def deploy(justPull=False):
    """
    Update the remote instance.

    Pull from git, update virtualenv, create static and restart gunicorn
    """
    is_this_initial = False
    if run("test -d %s/.git" % env.REPOSITORY_FOLDER,
           quiet=True).failed:  # destination folder to be created
        message = 'Repository folder doesn\'t exists on destination. Proceed with initial deploy?'
        if not confirm(message):
            abort("Aborting at user request.")
        else:
            initial_deploy()
            is_this_initial = True

    for secret in secrets_file_paths():
        if run("test -e %s" % posixpath.join(env.REPOSITORY_FOLDER, secret),
               quiet=True).failed:  # secrets missing
            message = 'Some secret doesn\'t exists on destination. Proceed with initial deploy?'
            if confirm(message):
                send_secrets(ask=True)
            else:
                abort("Aborting at user request.")

    update_instance(do_update_requirements=is_this_initial or DO_REQUIREMENTS, justPull=justPull)

    restart()


@task
def discard_remote_git():
    """Discard changes done on remote """
    with cd(env.REPOSITORY_FOLDER):
        run('git reset --hard HEAD')


def send_file(mask='*.*', subfolder='files', mask_prefix=None):
    if mask_prefix:
        mask = mask_prefix + mask
    run('mkdir -p %s' % posixpath.join(env.REPOSITORY_FOLDER, subfolder))
    with lcd(env.localfolder):
        puts("Uploading %s." % posixpath.join(subfolder, mask))
        file_paths = glob.glob(os.path.join(env.localfolder, subfolder, mask))
        for path in file_paths:
            filename = os.path.basename(path)
            remote_path = posixpath.join(env.REPOSITORY_FOLDER, subfolder, filename)
            put(path, remote_path)


@task
def send_brand():
    """ Upload brand files to the server """
    puts("Uploading brand files")
    local_brand_path = os.path.join(env.localfolder, 'media', 'brand', env.BRAND_FOLDER)
    remote_brand_path = posixpath.join(env.REPOSITORY_FOLDER, 'media', 'brand', env.BRAND_FOLDER)
    brand_files = os.listdir(local_brand_path)
    run('mkdir -p "%s"' % remote_brand_path)
    for filename in brand_files:
        put(os.path.join(local_brand_path, filename), os.path.join(remote_brand_path, filename))


@task
def get_remote_files():
    """ Go to the server and save locally the changeavle files on the server """
    to_be_saved = [
        ('media_secured/', 'media_secured/'),  # the secured files
        ('*.db3', '.')
    ]
    puts("Get remote files")
    for remotepath, localpath in to_be_saved:
        with settings(warn_only=True):
            cmd = "rsync -azv {host}:{root}/{rpath} {lpath}".format(
                host=env.hosts, root=env.REPOSITORY_FOLDER,
                rpath=remotepath, lpath=localpath,
            )
            print(cmd)
            local(cmd)


@task
def set_mailgun_webhooks():
    """ Set webhooks to receive bounced mail from Mailgun """
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    os.environ['TAM_SETTINGS'] = env.TAM_SETTINGS
    from django.conf import settings
    webhost = getattr(env, 'WEBHOST', None)
    if not webhost:
        raise EnvironmentError("Please define WEBHOST to set MailGun webhooks")
    API_BASE_URL = 'https://api.mailgun.net/v3'
    domain = settings.MAILGUN_SERVER_NAME
    auth = HTTPBasicAuth('api', settings.MAILGUN_ACCESS_KEY)
    for hook in ['drop', 'spam']:
        response = requests.post("{base}/domains/{domain}/webhooks".format(
            base=API_BASE_URL, domain=domain
        ), auth=auth,
            data=dict(id=hook, url='http://{webhost}/webhooks/email/'.format(webhost=webhost)))

        if response.status_code == 200:
            puts("MailGun webhooks '%s' created" % hook)
        else:
            puts("%s: %s" % (hook, response.text))


if __name__ == '__main__':
    # to debug the fabfile, we can specify the command here
    import sys
    from fabric.main import main

    sys.argv[1:] = ["-c", "arte.ini", "set_mailgun_webhooks"]
    print(sys.argv)
    main()
