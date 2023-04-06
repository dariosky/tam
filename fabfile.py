# coding=utf-8

# Facilitate deployment to server
#
# Deploy will consist of:
#     push changes to GIT repository
#     update dependences (with pip)
#     update db (with migrations)
#     collect static
#     restart webserver (daphne)

import glob
import os
import posixpath
import sys
from contextlib import contextmanager
from functools import wraps

import requests
from django.conf import LazySettings
from fabric.api import run, abort, env, put, task, cd
from fabric.context_managers import prefix, lcd, settings as fabsettings
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.decorators import serial
from fabric.operations import local
from fabric.utils import puts
from requests.auth import HTTPBasicAuth

env.localfolder = localfolder = os.path.realpath(os.path.dirname(__file__))
env.port = 22
if not env.get("NAME") and __name__ != "__main__":
    print("Please call fab specifying a host config file.")
    print("Example: fab -c host.ini")
    sys.exit(1)
sys.path.insert(1, localfolder)
# print("Call fab s:<deployment_name> deploy")

if os.path.exists(os.path.expanduser("~/.ssh/config")):
    env.use_ssh_config = True

DO_REQUIREMENTS = True
settings = LazySettings


@task
def s(name):
    """Load the settings for deployment <name>"""
    print("Settings for %s" % name)
    env.name = name
    env.settings_file = "settings_%s" % name
    os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
    os.environ["TAM_SETTINGS"] = "settings_%s" % name
    from django.conf import settings

    globals()["settings"] = settings  # put settings global
    env.REPOSITORY_FOLDER = settings.DEPLOYMENT["FOLDERS"]["REPOSITORY_FOLDER"]
    env.hosts = settings.DEPLOYMENT["HOST"]


def require_settings(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "name" not in env:
            print("Define an environment with the *s* command before calling an action")
            print("Available environments:")
            for setting in glob.glob("settings_*.py"):
                print("\t", setting[len("settings_") : -len(".py")])
            exit(1)
        f(*args, **kwargs)

    return wrapper


def secrets_file_paths():
    """Return a list of secret files (to be sent) relative to REPOSITORY_FOLDER"""
    return [env.settings_file + ".py"]


@contextmanager
def virtualenv(venv_path=None):
    """
    Put fabric commands in a virtualenv
    """
    if venv_path is None:
        venv_path = settings.DEPLOYMENT["FOLDERS"]["VENV_FOLDER"]
    with prefix("source %s" % posixpath.join(venv_path, "bin/activate")):
        yield


def get_repository():
    repository_folder = env.REPOSITORY_FOLDER
    if run("test -d %s" % repository_folder, quiet=True).failed:
        puts("Creating repository folder.")
        run("mkdir -p %s" % repository_folder)
    if not exists(posixpath.join(repository_folder, ".git")):
        puts("Cloning from repository.")
        run(
            "git clone %s %s"
            % (settings.DEPLOYMENT["GIT_REPOSITORY"], repository_folder)
        )


def create_virtualenv():
    venv_folder = settings.DEPLOYMENT["FOLDERS"]["VENV_FOLDER"]
    if run("test -d %s" % venv_folder, quiet=True).failed:
        run("python3 -m venv %s" % venv_folder)


def update_distribute():
    with virtualenv():
        run("pip install -U -q pip distribute")


@task
@require_settings
def initial_deploy():
    """
    Prepare the remote instance with git repository and virtualenv.
    """
    get_repository()
    create_virtualenv()
    update_distribute()  # some package won't install if distriubte is the old one
    with cd(env.REPOSITORY_FOLDER):
        run(
            "mkdir -p %s" % settings.DEPLOYMENT["FOLDERS"]["LOGDIR"]
        )  # create logdir if missing
        run("chmod +x node_modules/.bin/yuglify")
    send_brand()
    set_mailgun_webhooks()


@serial
@require_settings
def update_database():
    with virtualenv():
        with cd(env.REPOSITORY_FOLDER):
            # update database, both standard apps and south migrated
            run("python manage.py migrate")


@task
@require_settings
def update_requirements():
    """Update all libraries in requirements file"""
    with virtualenv():
        with cd(env.REPOSITORY_FOLDER):
            # update libraries
            run(
                "pip install -U --quiet -r %s"
                % settings.DEPLOYMENT["FOLDERS"]["REQUIREMENT_PATH"],
                pty=False,
            )


def update_instance(do_update_requirements=True, justPull=False):
    repository_folder = env.REPOSITORY_FOLDER
    static_folder = settings.DEPLOYMENT["FOLDERS"]["STATIC_FOLDER"]
    media_folder = settings.DEPLOYMENT["FOLDERS"]["MEDIA_FOLDER"]
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

            run("python manage.py collectstatic --noinput -v0")


def daphne(action):
    with virtualenv():
        if env.UWSGI_START_COMMAND:
            print("Starting UWSGI")
            run(env.UWSGI_START_COMMAND)
        else:
            raise RuntimeError("Give me the UWSGI_START_COMMAND to run Daphne")
    with cd(env.REPOSITORY_FOLDER):
        run("python manage.py daphne %s" % action)


@task
@require_settings
def stop():
    """Stop the remote frontend instance"""
    daphne("stop")


@task
@require_settings
def restart():
    """Start/Restart the frontend server"""
    daphne("restart")


@task
@require_settings
def send_secrets(secret_files=None, ask=False):
    """Send the secret settings file that is excluded from VCS"""
    if ask and not confirm("Upload secret settings?"):
        return
    if secret_files is None:
        secret_files = secrets_file_paths()
    if isinstance(secret_files, str):
        secret_files = [secret_files]
    puts("Uploading secrets.")
    for filename in secret_files:
        local_path = os.path.join(localfolder, filename)
        remote_path = posixpath.join(env.REPOSITORY_FOLDER, filename)
        put(local_path, remote_path)
    if len(secret_files) == 1:
        with cd(env.REPOSITORY_FOLDER):
            run("ln -s -f %s settings_local.py" % secret_files[0])


@task
@require_settings
def deploy(justPull=False):
    """
    Update the remote instance.

    Pull from git, update virtualenv, create static and restart the server
    """
    is_this_initial = False
    if run("test -d %s/.git" % env.REPOSITORY_FOLDER, quiet=True).failed:
        # destination folder to be created
        message = "Repository folder doesn't exists on destination. Proceed with initial deploy?"
        if not confirm(message):
            abort("Aborting at user request.")
        else:
            initial_deploy()
            is_this_initial = True

    for secret in secrets_file_paths():
        if not exists(posixpath.join(env.REPOSITORY_FOLDER, secret)):
            send_secrets(ask=True)  # secrets missing

    update_instance(
        do_update_requirements=is_this_initial or DO_REQUIREMENTS, justPull=justPull
    )

    restart()


@task
@require_settings
def discard_remote_git():
    """Discard changes done on remote"""
    with cd(env.REPOSITORY_FOLDER):
        run("git reset --hard HEAD")


def send_file(mask="*.*", subfolder="files", mask_prefix=None):
    if mask_prefix:
        mask = mask_prefix + mask
    run("mkdir -p %s" % posixpath.join(env.REPOSITORY_FOLDER, subfolder))
    with lcd(localfolder):
        puts("Uploading %s." % posixpath.join(subfolder, mask))
        file_paths = glob.glob(os.path.join(localfolder, subfolder, mask))
        for path in file_paths:
            filename = os.path.basename(path)
            remote_path = posixpath.join(env.REPOSITORY_FOLDER, subfolder, filename)
            put(path, remote_path)


@task
@require_settings
def send_brand():
    """Upload brand files to the server"""
    puts("Uploading brand files")
    brand_folder = settings.DEPLOYMENT["BRAND_FOLDER"]
    local_brand_path = os.path.join(localfolder, "media", "brand", brand_folder)
    remote_brand_path = posixpath.join(
        env.REPOSITORY_FOLDER, "media", "brand", brand_folder
    )
    brand_files = os.listdir(local_brand_path)
    run('mkdir -p "%s"' % remote_brand_path)
    for filename in brand_files:
        put(
            os.path.join(local_brand_path, filename),
            os.path.join(remote_brand_path, filename),
        )


@task
@require_settings
def get_remote_files():
    """Go to the server and save locally the changeable files on the server"""
    to_be_saved = [
        ("media_secured/", "media_secured/"),  # the secured files
        ("*.db3", "."),
    ]
    puts("Get remote files")
    for remotepath, localpath in to_be_saved:
        with fabsettings(warn_only=True):
            cmd = "rsync -azv {host}:{root}/{rpath} {lpath}".format(
                host=env.hosts,
                root=env.REPOSITORY_FOLDER,
                rpath=remotepath,
                lpath=localpath,
            )
            print(cmd)
            local(cmd)


@task
@require_settings
def set_mailgun_webhooks():
    """Set webhooks to receive bounced mail from Mailgun"""
    webhost = settings.WEBHOST
    if not webhost:
        raise EnvironmentError("Please define WEBHOST to set MailGun webhooks")
    API_BASE_URL = "https://api.mailgun.net/v3"
    domain = settings.MAILGUN_SERVER_NAME
    auth = HTTPBasicAuth("api", settings.ANYMAIL["MAILGUN_API_KEY"])
    for hook in ["drop", "spam"]:
        response = requests.post(
            "{base}/domains/{domain}/webhooks".format(base=API_BASE_URL, domain=domain),
            auth=auth,
            data=dict(
                id=hook, url="http://{webhost}/webhooks/email/".format(webhost=webhost)
            ),
        )

        if response.status_code == 200:
            puts("MailGun webhooks '%s' created" % hook)
        else:
            puts("%s: %s" % (hook, response.text))


@task
@require_settings
def prepare_webfaction():
    from utils.webfaction_deployment import (
        webfaction_install_redis,
        create_all_domains,
        create_all_apps,
        create_all_websites,
    )

    # we start doing all REDIS
    webfaction_install_redis()

    # we then create all needed things in webfaction
    create_all_domains()
    create_all_apps()
    create_all_websites()


if __name__ == "__main__":
    # to debug the fabfile, we can specify the command here
    import sys
    from fabric.main import main

    # sys.argv[1:] = ["s:arte", "set_mailgun_webhooks"]
    sys.argv[1:] = ["s:taxi2beta", "restart"]
    print(sys.argv)
    main()
