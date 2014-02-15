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
from StringIO import StringIO
import glob
import os
from fabric.api import run, abort, env, put, task, cd
from fabric.context_managers import prefix, lcd
from fabric.contrib.files import exists
import posixpath
from fabric.contrib.console import confirm
from fabric.decorators import serial
from fabric.operations import local
from fabric.utils import puts
from contextlib import contextmanager as _contextmanager


@task
def hosts(filename):
	"""
	 	Set the hosts to ones in filename.hosts
	"""
	filepath = os.path.join(os.path.dirname(__file__), filename + ".hosts")
	if not os.path.isfile(filepath):
		raise Exception("Hosts file not found %s" % filepath)
	host_list = [l.strip() for l in file(filepath, 'r').readlines() if not l.strip().startswith("#")]
	env.hosts = host_list
	return host_list


if not env.hosts:
	hosts('default')

env.localfolder = os.path.realpath(os.path.dirname(__file__))
env.port = 22
# env.user = 'dariosky'

if os.path.exists(os.path.expanduser("~/.ssh/config")):
	env.use_ssh_config = True

REPOSITORY_FOLDER = '~/projects/tam'  # the manage.py is here
VENV_FOLDER = '~/.environments/tam'
GIT_REPOSITORY = "git@bitbucket.org:dariosky/tam.git"
REQUIREMENT_PATH = posixpath.join(REPOSITORY_FOLDER, 'requirements.txt')

STATIC_FOLDER = posixpath.join(REPOSITORY_FOLDER, 'static')  # Static folder will be filled by django collectstatic
MEDIA_FOLDER = posixpath.join(REPOSITORY_FOLDER, 'media')  # This is for UGC
RUN_GUNICORN_COMMAND = posixpath.join(REPOSITORY_FOLDER, 'run_gunicorn')

LOGDIR = posixpath.join(REPOSITORY_FOLDER, 'logs')
GUNICORN_PID_FILE = posixpath.join(LOGDIR, 'gunicorn.pid')
GUNICORN_LOGFILE = posixpath.join(LOGDIR, 'gunicorn.log')
GUNICORN_WORKERS = 6
GUNICORN_WORKERS_TIMEOUT = 360  # in seconds - keep high to handle large files upload
GUNICORN_PORT = os.environ.get('GUNICORN_PORT', 80)
USE_SUPERVISOR = False
SUPERVISOR_JOBNAME = 'tam'  # This is needed only if USE_SUPERVISOR is True
DO_REQUIREMENTS = False


def secrets_file_paths():
	""" Return a list of secret files (to be sent) relative to REPOSITORY_FOLDER """
	return ["settings_local.py"]


@_contextmanager
def virtualenv(venv_path=VENV_FOLDER):
	"""
	Put fabric commands in a virtualenv
	"""
	with prefix("source %s" % posixpath.join(venv_path, "bin/activate")):
		yield


def get_repository():
	if run("test -d %s" % REPOSITORY_FOLDER, quiet=True).failed:
		puts("Creating repository folder.")
		run("mkdir -p %s" % REPOSITORY_FOLDER)
	if not exists(posixpath.join(REPOSITORY_FOLDER, '.git')):
		puts("Cloning from repository.")
		run("git clone %s %s" % (GIT_REPOSITORY, REPOSITORY_FOLDER))


def create_virtualenv():
	if run("test -d %s" % VENV_FOLDER, quiet=True).failed:
		run('virtualenv %s' % VENV_FOLDER)


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
	run('mkdir -p %s' % LOGDIR)  # create the log dir if missing
	create_run_command()


@serial
def update_database():
	with virtualenv():
		with cd(REPOSITORY_FOLDER):
			# update database, both standard apps and south migrated
			run("python manage.py syncdb")
			run("python manage.py migrate")


@task
def update_requirements():
	""" Update all libraries in requirements file """
	with virtualenv():
		with cd(REPOSITORY_FOLDER):
			run('pip install -U -r %s' % REQUIREMENT_PATH)  # update libraries


def update_instance(do_update_requirements=True):
	with cd(REPOSITORY_FOLDER):
		run("git pull")  # pull the changes
	with virtualenv():
		with cd(REPOSITORY_FOLDER):
			if do_update_requirements:
				update_requirements()

			run("python manage.py syncdb")

			if run("test -d %s" % STATIC_FOLDER, quiet=True).failed:
				puts("Creating static subfolder for generated assets.")
				run("mkdir -p %s" % STATIC_FOLDER)

			if run("test -d %s" % MEDIA_FOLDER, quiet=True).failed:
				puts("Creating media subfolder for user uploaded assets.")
				run("mkdir -p %s" % MEDIA_FOLDER)

			run("python manage.py collectstatic --noinput")

			update_database()


def get_gunicorn_command(daemon=True):
	options = [
		'-w %d' % GUNICORN_WORKERS,  # --user=$USER --group=$GROUP
		'--log-level=debug',
		'-b 127.0.0.1:%d' % GUNICORN_PORT,
		'--pid %s' % GUNICORN_PID_FILE,
		'--log-file=%(log)s' % {'log': GUNICORN_LOGFILE},
		'-t %d' % GUNICORN_WORKERS_TIMEOUT,  # timeout, upload processes can take some time (default is 30 seconds)
	]
	if daemon:
		options.append('--daemon')
	return "{env_path}/bin/gunicorn {options_string} {wsgi_app}".format(
		env_path=VENV_FOLDER,
		options_string=" ".join(options),
		wsgi_app="wsgi:application",
	)


def start():
	if USE_SUPERVISOR:
		# Supervisor should be set to use this fabfile too
		# the command should be 'fab gunicorn_start_local'
		run('supervisorctl start %s' % SUPERVISOR_JOBNAME)
	else:  # directly start remote Gunicorn
		with virtualenv():
			with cd(REPOSITORY_FOLDER):
				gunicorn_command = get_gunicorn_command()
				run(gunicorn_command)


@task
def stop():
	""" Stop the remote gunicorn instance (eventually using supervisor) """
	if USE_SUPERVISOR:
		run('supervisorctl stop %s' % SUPERVISOR_JOBNAME)
	else:  # directly start remote Gunicorn
		puts('Sending TERM signal to Gunicorn.')
		gunicorn_pid = int(run('cat %s' % GUNICORN_PID_FILE, quiet=True))
		run("kill %d" % gunicorn_pid)


@task
def start_local():
	""" Start locally gunicorn instance """
	gunicorn_command = get_gunicorn_command(daemon=False)
	if USE_SUPERVISOR:
		#abort("You should not start_local if you would like to use Supervisor.")
		process = None
		try:
			process = local(gunicorn_command)
		except Exception as e:
			print "EXCEPTION: %s" % e
			if process is not None:
				import signal

				process.send_signal(signal.SIGTERM)
	else:
		with lcd(REPOSITORY_FOLDER):
			local(gunicorn_command)


@task
def restart():
	""" Start/Restart the remote gunicorn instance (eventually using supervisor) """
	if run("test -e %s" % GUNICORN_PID_FILE, quiet=True).failed:
		puts("Gunicorn doesn't seems to be running (PID file missing)...")

		start()

	# gunicorn_pid = int(run('cat %s' % GUNICORN_PID_FILE, quiet=True))
	# if not gunicorn_pid:
	# 	abort('ERROR: Gunicorn seems down after the start command.')
	else:
		puts('Gracefully restarting Gunicorn.')
		gunicorn_pid = int(run('cat %s' % GUNICORN_PID_FILE, quiet=True))
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
		remote_path = posixpath.join(REPOSITORY_FOLDER, filename)
		put(local_path, remote_path)


def run_command_content():
	gunicorn_command = get_gunicorn_command(daemon=False)
	return '#!/bin/bash\n' + 'exec %s' % gunicorn_command


@task
def create_run_command():
	""" Create the remote_run command to be executed """
	puts("Creating run_server.")
	with lcd(env.localfolder):
		with cd(REPOSITORY_FOLDER):
			run_temp_file = StringIO(run_command_content())
			run_temp_file.name = "run_server"  # to show it as fabric file representation
			put(run_temp_file, posixpath.join(REPOSITORY_FOLDER, 'run_server'))
			run('chmod +x run_server')


@task
def local_create_run_command():
	puts("Creating run_server command to be run with supervisor.")
	with lcd(REPOSITORY_FOLDER):
		with file(posixpath.join(REPOSITORY_FOLDER, 'run_server'), 'w') as runner:
			runner.write(run_command_content())


@task
def local_create_run_command():
	gunicorn_command = get_gunicorn_command(daemon=False)
	puts("Creating run_server command to be run with supervisor.")
	with lcd(REPOSITORY_FOLDER):
		with file(posixpath.join(REPOSITORY_FOLDER, 'run_server'), 'w') as runner:
			runner.write('#!/bin/bash\n')
			runner.write('exec %s' % gunicorn_command)


@task
def deploy():
	"""
	Update the remote instance.

	Pull from git, update virtualenv, create static and restart gunicorn
	"""
	is_this_initial = False
	if run("test -d %s/.git" % REPOSITORY_FOLDER, quiet=True).failed:  # destination folder to be created
		message = 'Repository folder doesn\'t exists on destination. Proceed with initial deploy?'
		if not confirm(message):
			abort("Aborting at user request.")
		else:
			initial_deploy()
			is_this_initial = True

	for secret in secrets_file_paths():
		if run("test -e %s" % posixpath.join(REPOSITORY_FOLDER, secret), quiet=True).failed:  # secrets missing
			message = 'Some secret doesn\'t exists on destination. Proceed with initial deploy?'
			send_secrets(ask=True)

	update_instance(do_update_requirements=is_this_initial or DO_REQUIREMENTS)

	restart()


@task
def discard_remote_git():
	"""Discard changes done on remote """
	with cd(REPOSITORY_FOLDER):
		run('git reset --hard HEAD')


@task
def send_file(mask='*.*', subfolder='files', mask_prefix=None):
	if mask_prefix:
		mask = mask_prefix + mask
	run('mkdir -p %s' % posixpath.join(REPOSITORY_FOLDER, subfolder))
	with lcd(env.localfolder):
		puts("Uploading %s." % posixpath.join(subfolder, mask))
		file_paths = glob.glob(os.path.join(env.localfolder, subfolder, mask))
		for path in file_paths:
			filename = os.path.basename(path)
			remote_path = posixpath.join(REPOSITORY_FOLDER, subfolder, filename)
			put(path, remote_path)
