# coding=utf-8

"""
assume your user is named "magic_r_user"

cd ~
wget "http://download.redis.io/releases/redis-3.0.7.tar.gz"
tar -xzf redis-3.0.0.tar.gz
mv redis-3.0.0 redis
cd redis
make
make test
create a custom app "listening on port" through the Webfaction management website
    assume we named it magic_r_app
    assume it was assigned port 12345
cp ~/redis/redis.conf ~/webapps/magic_r_app/
vi ~/webapps/magic_r_app/redis.conf
    daemonize yes
    pidfile ~/webapps/magic_r_app/redis.pid
    port 12345
test it
    ~/redis/src/redis-server ~/webapps/magic_r_app/redis.conf
    ~/redis/src/redis-cli -p 12345
    ctrl-d
    cat ~/webapps/magic_r_app/redis.pid | xargs kill
crontab -e
    */1 * * * * /home/magic_r_user/redis/src/redis-server /home/magic_r_user/webapps/magic_r_app/redis.conf &>> /home/magic_r_user/logs/user/cron.log
don't forget to set a password!


"""
import os
import re
import xmlrpc.client

from fabric.api import run, env, cd
from fabric.contrib.files import exists
from fabric.api import settings as fab_settings
import settings


def create_redis_app(app_name):
    server = xmlrpc.client.ServerProxy('https://api.webfaction.com/')
    username, password = os.environ['WEBFACTION_USER'], os.environ['WEBFACTION_PASS']
    session_id, account = server.login(username, password)
    # print(account)
    apps = server.list_apps(session_id)

    redis_app = list(filter(lambda a: a['name'] == ('%s' % app_name), apps))
    if not redis_app:
        print("Creating Redis APP")
        app = server.create_app(session_id,
                                app_name,
                                'custom_app_with_port',
                                )
        redis_app = [app]
    else:
        print("Redis APP already exists")
    # print(redis_app)
    return redis_app[0]['port']


def install_redis(app_name, redis_port):
    redis_port = str(redis_port)
    remote_path = os.path.join("~/webapps/", app_name)
    redis_version = "3.2.4"
    if not exists(remote_path):
        raise Exception("Redis app does not exists. Create it first.")

    with cd(remote_path):
        if not exists("redis.conf"):
            if not exists("redis-%s.tar.gz" % redis_version):
                print("Downloading Redis")
                run('wget "http://download.redis.io/releases/redis-%s.tar.gz"' % redis_version)
            if not exists("redis-%s" % redis_version):
                run('tar -xzf redis-%s.tar.gz' % redis_version)
            if not exists(os.path.join("redis-%s" % redis_version, "src", "redis-cli")):
                with cd('redis-%s' % redis_version):
                    run('make')
                    # run('make test') # this is memory hungry
            files_to_copy = ['src/redis-server', 'src/redis-cli', 'redis.conf']
            for name in files_to_copy:
                run("scp '{src}' '{dst}'".format(
                    src=os.path.join("redis-%s" % redis_version, name),
                    dst=os.path.basename(name),
                ))
            if exists("redis-%s" % redis_version):
                # remove the source files
                run("rm -rf redis-%s" % redis_version)

        webapp_folder = run('echo ~/webapps/{app_name}'.format(**locals()), quiet=True)
        keys = {
            'port': redis_port,
            "daemonize": "yes",
            "pidfile": "{webapp_folder}/redis.pid".format(webapp_folder=webapp_folder),
            "logfile": 'redis.log',
            "requirepass": settings.REDIS_PASSWORD,
        }
        for key, expected_value in keys.items():
            current_value = run('egrep ^{key}\  redis.conf'.format(key=key), quiet=True)
            if not current_value:
                print("Setting {key} to {expected_value}".format(**locals()))
                run("echo '{key} {expected_value}' >> redis.conf".format(**locals()))
            elif current_value != "{key} {expected_value}".format(**locals()):
                print("Updating {key} to {expected_value}".format(**locals()))
                run(r"sed -r -i 's/^({key}) .*$/\1 {expected_value}/' {file}".format(
                    key=key, expected_value=re.escape(expected_value), file='redis.conf'
                ))


def redis_to_crontab(app_name):
    webapp_folder = run('echo ~/webapps/{app_name}'.format(**locals()), quiet=True)
    start_redis_command = '*/1 * * * * {webapp_folder}/redis-server' \
                          ' {webapp_folder}/redis.conf' \
                          ' &>> {webapp_folder}/cron.log'.format(webapp_folder=webapp_folder)
    with fab_settings(warn_only=True): # grep return errorcode when missing
        crontab = run(
            'crontab -l| grep {webapp_folder}/redis-server'.format(webapp_folder=webapp_folder)
        )
        if crontab.return_code != 0:
            run('( crontab -l | grep -v -F "{cmd}" ; echo "{cmd}" ) | crontab -'.format(
                cmd=start_redis_command)
            )


if __name__ == '__main__':
    if os.path.exists(os.path.expanduser("~/.ssh/config")):
        env.use_ssh_config = True
    env.host_string = 'tam'

    app_name = settings.WEBFACTION_REDIS_APPNAME
    # redis_port = create_redis_app(app_name)
    # install_redis(app_name, redis_port)
    # if redis_port != settings.REDIS_PORT:
    #     print("WARNING: Remember to set your REDIS_PORT in settings to %s" % redis_port)
    redis_to_crontab(app_name)
