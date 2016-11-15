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
from contextlib import contextmanager as _contextmanager
from io import StringIO

import requests
from django.conf import LazySettings
from fabric.api import run, abort, env, put, task, cd
from fabric.context_managers import prefix, lcd, settings as fabsettings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.decorators import serial
from fabric.operations import local
from fabric.utils import puts
from past.builtins import basestring
from requests.auth import HTTPBasicAuth
import sys

localfolder = os.path.realpath(os.path.dirname(__file__))
sys.path.insert(1, localfolder)
# print("Call fab s:<deployment_name> deploy")

if os.path.exists(os.path.expanduser("~/.ssh/config")):
    env.use_ssh_config = True

DO_REQUIREMENTS = True
settings = LazySettings


@task
def s(name):
    """ Load the settings for deployment <name> """
    print("Settings for %s" % name)
    env.name = name
    env.settings_file = "settings_%s" % name
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    os.environ['TAM_SETTINGS'] = "settings_%s" % name
    from django.conf import settings
    globals()['settings'] = settings  # put settings global
    env.REPOSITORY_FOLDER = settings.DEPLOYMENT['FOLDERS']['REPOSITORY_FOLDER']
    env.hosts = settings.DEPLOYMENT['HOST']


def secrets_file_paths():
    """ Return a list of secret files (to be sent) relative to REPOSITORY_FOLDER """
    return [env.settings_file + ".py"]


@_contextmanager
def virtualenv(venv_path=None):
    """
    Put fabric commands in a virtualenv
    """
    if venv_path is None:
        venv_path = settings.DEPLOYMENT['FOLDERS']['VENV_FOLDER']
    with prefix("source %s" % posixpath.join(venv_path, "bin/activate")):
        yield


def get_repository():
    repository_folder = env.REPOSITORY_FOLDER
    if run("test -d %s" % repository_folder, quiet=True).failed:
        puts("Creating repository folder.")
        run("mkdir -p %s" % repository_folder)
    if not exists(posixpath.join(repository_folder, '.git')):
        puts("Cloning from repository.")
        run("git clone %s %s" % (settings.DEPLOYMENT['GIT_REPOSITORY'], repository_folder))


def create_virtualenv():
    venv_folder = settings.DEPLOYMENT['FOLDERS']['VENV_FOLDER']
    if run("test -d %s" % venv_folder, quiet=True).failed:
        run('python3 -m venv %s' % venv_folder)


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
        run('mkdir -p %s' % settings.DEPLOYMENT['FOLDERS']['LOGDIR'])  # create logdir if missing
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
            # update libraries
            run('pip install -U -r %s' % settings.DEPLOYMENT['FOLDERS']['REQUIREMENT_PATH'],
                pty=False)


def update_instance(do_update_requirements=True, justPull=False):
    repository_folder = env.REPOSITORY_FOLDER
    static_folder = settings.DEPLOYMENT['FOLDERS']['STATIC_FOLDER']
    media_folder = settings.DEPLOYMENT['FOLDERS']['MEDIA_FOLDER']
    with cd(repository_folder):
        run("git pull")  # pull the changes
    if justPull:
        return
    with virtualenv():
        with cd(repository_folder):
            if do_update_requirements:
                update_requirements()

            run("python manage.py migrate")

            if run("test -d %s" % static_folder, quiet=True).failed:
                puts("Creating static subfolder for generated assets.")
                run("mkdir -p %s" % static_folder)

            if run("test -d %s" % media_folder, quiet=True).failed:
                puts("Creating media subfolder for user uploaded assets.")
                run("mkdir -p %s" % media_folder)

            run("python manage.py collectstatic --noinput")

            update_database()


def get_gunicorn_command(daemon=True):
    gunicoptions = settings.DEPLOYMENT['GUNICORN']
    foldoptions = settings.DEPLOYMENT['FOLDERS']
    options = [
        '-w %s' % gunicoptions['WORKERS'],
        # --user=$USER --group=$GROUP
        '--log-level=debug',
        '-b 127.0.0.1:%s' % gunicoptions['PORT'],
        '--pid %s' % gunicoptions['PID_FILE'],
        '--log-file %s' % gunicoptions['LOG_FILE'],
        # timeout: upload processes can take some time (default is 30 seconds)
        '-t %s' % gunicoptions['WORKERS_TIMEOUT'],
        '-n %s' % settings.DEPLOYMENT['NAME'],
    ]
    if daemon:
        options.append('--daemon')
    return "{env_path}/bin/gunicorn {options_string} {wsgi_app}".format(
        env_path=foldoptions['VENV_FOLDER'],
        options_string=" ".join(options),
        wsgi_app=settings.DEPLOYMENT['WSGI_APPLICATION'],
    )


def start(daemon=True):
    if settings.DEPLOYMENT['USE_SUPERVISOR']:
        # Supervisor should be set to use this fabfile too
        # the command should be 'fab gunicorn_start_local'
        run('supervisorctl start %s' % settings.DEPLOYMENT['SUPERVISOR_JOBNAME'])
    else:  # directly start remote Gunicorn
        with virtualenv():
            with cd(env.REPOSITORY_FOLDER):
                gunicorn_command = get_gunicorn_command(daemon=daemon)
                run(gunicorn_command)


@task
def stop():
    """ Stop the remote gunicorn instance (eventually using supervisor) """
    if settings.DEPLOYMENT['USE_SUPERVISOR']:
        run('supervisorctl stop %s' % settings.DEPLOYMENT['SUPERVISOR_JOBNAME'])
    else:  # directly start remote Gunicorn
        puts('Sending TERM signal to Gunicorn.')
        gunicorn_pid = int(run('cat %s' % settings.DEPLOYMENT['GUNICORN']['PID_FILE'], quiet=True))
        run("kill %d" % gunicorn_pid)


@task
def start_local():
    """ Start locally gunicorn instance """
    gunicorn_command = get_gunicorn_command(daemon=False)
    if settings.DEPLOYMENT['USE_SUPERVISOR']:
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
    if run("test -e %s" % settings.DEPLOYMENT['GUNICORN']['PID_FILE'], quiet=True).failed:
        puts("Gunicorn doesn't seems to be running (PID file missing)...")
        start()

    # gunicorn_pid = int(run('cat %s' % GUNICORN_PID_FILE, quiet=True))
    # if not gunicorn_pid:
    # 	abort('ERROR: Gunicorn seems down after the start command.')
    else:
        puts('Gracefully restarting Gunicorn.')
        gunicorn_pid = int(run('cat %s' % settings.DEPLOYMENT['GUNICORN']['PID_FILE'], quiet=True))
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
        local_path = os.path.join(localfolder, filename)
        remote_path = posixpath.join(env.REPOSITORY_FOLDER, filename)
        put(local_path, remote_path)
    if len(secret_files) == 1:
        with cd(env.REPOSITORY_FOLDER):
            run('ln -s -f %s settings_local.py' % secret_files[0])


def run_command_content(daemon=True):
    with open('run_server.template.sh', "r") as f:
        content = f.read()
    return content % dict(
        VENV_FOLDER=settings.DEPLOYMENT['FOLDERS']['VENV_FOLDER'],
        GUNICORN_ARGUMENTS=get_gunicorn_command(daemon),
        FRONT_PID_FILE=settings.DEPLOYMENT['GUNICORN']['PID_FILE'],
        REPOSITORY_FOLDER=env.REPOSITORY_FOLDER,
    )


@task
def create_run_command():
    """ Create the remote_run command to be executed """
    puts("Creating run_server.sh")
    with lcd(localfolder):
        with cd(env.REPOSITORY_FOLDER):
            run_temp_file = StringIO(run_command_content())
            run_temp_file.name = "run_server.sh"  # to show it as fabric file representation
            put(run_temp_file, posixpath.join(env.REPOSITORY_FOLDER, 'run_server.sh'))
            run('chmod +x run_server.sh')


@task
def local_create_run_command(daemon=False):
    puts("Creating run_server.sh command to be run " + (
        "with" if settings.DEPLOYMENT['USE_SUPERVISOR'] else "without") + " supervisor.")
    with lcd(localfolder):
        with open('run_server.sh', 'w') as runner:
            runner.write(run_command_content(daemon=daemon))


@task
def deploy(justPull=False):
    """
    Update the remote instance.

    Pull from git, update virtualenv, create static and restart gunicorn
    """
    is_this_initial = False
    if run("test -d %s/.git" % env.REPOSITORY_FOLDER, quiet=True).failed:
        # destination folder to be created
        message = 'Repository folder doesn\'t exists on destination. Proceed with initial deploy?'
        if not confirm(message):
            abort("Aborting at user request.")
        else:
            initial_deploy()
            is_this_initial = True

    for secret in secrets_file_paths():
        if run("test -e %s" % posixpath.join(env.REPOSITORY_FOLDER, secret), quiet=True).failed:
            send_secrets(ask=True)  # secrets missing

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
    with lcd(localfolder):
        puts("Uploading %s." % posixpath.join(subfolder, mask))
        file_paths = glob.glob(os.path.join(localfolder, subfolder, mask))
        for path in file_paths:
            filename = os.path.basename(path)
            remote_path = posixpath.join(env.REPOSITORY_FOLDER, subfolder, filename)
            put(path, remote_path)


@task
def send_brand():
    """ Upload brand files to the server """
    puts("Uploading brand files")
    brand_folder = settings.DEPLOYMENT['BRAND_FOLDER']
    local_brand_path = os.path.join(localfolder, 'media', 'brand', brand_folder)
    remote_brand_path = posixpath.join(env.REPOSITORY_FOLDER, 'media', 'brand', brand_folder)
    brand_files = os.listdir(local_brand_path)
    run('mkdir -p "%s"' % remote_brand_path)
    for filename in brand_files:
        put(os.path.join(local_brand_path, filename), os.path.join(remote_brand_path, filename))


@task
def get_remote_files():
    """ Go to the server and save locally the changeable files on the server """
    to_be_saved = [
        ('media_secured/', 'media_secured/'),  # the secured files
        ('*.db3', '.')
    ]
    puts("Get remote files")
    for remotepath, localpath in to_be_saved:
        with fabsettings(warn_only=True):
            cmd = "rsync -azv {host}:{root}/{rpath} {lpath}".format(
                host=env.hosts, root=env.REPOSITORY_FOLDER,
                rpath=remotepath, lpath=localpath,
            )
            print(cmd)
            local(cmd)


@task
def set_mailgun_webhooks():
    """ Set webhooks to receive bounced mail from Mailgun """
    webhost = settings.WEBHOST
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


@task
def prepare_webfaction():
    from utils.webfaction_deployment import webfaction_install_redis, create_all_domains, \
        create_all_apps, create_all_websites
    # we start doing all REDIS
    webfaction_install_redis()

    # we then create all needed things in webfaction
    create_all_domains()
    create_all_apps()
    create_all_websites()


if __name__ == '__main__':
    # to debug the fabfile, we can specify the command here
    import sys
    from fabric.main import main

    # sys.argv[1:] = ["s:arte", "set_mailgun_webhooks"]
    sys.argv[1:] = ["s:taxi2beta", "deploy"]
    print(sys.argv)
    main()
