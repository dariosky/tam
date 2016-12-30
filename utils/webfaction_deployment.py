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
import logging
import os
import re
from urllib.parse import urlparse

from fabric.api import run, env, cd, settings as fab_settings
from fabric.contrib.files import exists

import settings
from wfcli import WebFactionAPI

logger = logging.getLogger('__name__')


def create_redis_app(app_name):
    # print(account)
    api = WebFactionAPI()
    apps = api.list_apps()
    if app_name not in apps:
        print("Creating Redis APP")
        app = api.create_app(app_name, 'custom_app_with_port')
    # print(redis_app)
    return apps[app_name]['port']


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
            "logfile": "{webapp_folder}/redis.log".format(webapp_folder=webapp_folder),
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
    with fab_settings(warn_only=True):  # grep return errorcode when missing
        crontab = run(
            'crontab -l| grep {webapp_folder}/redis-server'.format(webapp_folder=webapp_folder)
            , quiet=True)
        if crontab.return_code != 0:
            run('( crontab -l | grep -v -F "{cmd}" ; echo "{cmd}" ) | crontab -'.format(
                cmd=start_redis_command)
                , quiet=True)


def webfaction_install_redis():
    # we install REDIS as a custom app, then we add it to crontab
    app_name = settings.WEBFACTION['APPS']['redis']
    redis_port = create_redis_app(app_name)
    install_redis(app_name, redis_port)
    if redis_port != settings.WEBFACTION['REDIS_PORT']:
        print("WARNING: Remember to set your REDIS_PORT in settings to %s" % redis_port)
    redis_to_crontab(app_name)


def get_site_hostnames():
    results = {'main': settings.WEBHOST}
    for name, url in (('media', settings.MEDIA_URL), ('static', settings.STATIC_URL)):
        o = urlparse(url)
        if o.hostname:
            results[name] = o.hostname
    return results


def create_all_domains():
    urls = {settings.MEDIA_URL, settings.STATIC_URL}
    results = set(settings.ALLOWED_HOSTS)
    for u in urls:
        o = urlparse(u)
        if o.hostname:
            results.add(o.hostname)
    domains = {s.strip(".") for s in results}
    group_subdomains = {}
    for d in domains:
        splitted = d.split(".")
        domain = ".".join(splitted[-2:])
        if domain not in group_subdomains:
            group_subdomains[domain] = []

        if len(splitted) > 2:
            group_subdomains[domain].append(".".join(splitted[:-2]))
    api = WebFactionAPI()
    existing_domains = api.list_domains()
    for domain, subdomains in group_subdomains.items():
        if domain not in existing_domains or not all(
            [s in existing_domains[domain] for s in subdomains]):
            print("Creating domain {domain} with subdomains {sub}".format(
                domain=domain, sub=subdomains
            ))
            print(api.create_domain(domain, subdomains))


def create_all_apps():
    api = WebFactionAPI()
    webfaction_apps = settings.WEBFACTION['APPS']
    existing_apps = api.list_apps()
    main_app_name = webfaction_apps['main']
    if main_app_name not in existing_apps:
        print("Creating main app")
        main_app = api.create_app(main_app_name, app_type="custom_websockets_app_with_port")
    else:
        main_app = existing_apps[main_app_name]
    if settings.DEPLOYMENT['GUNICORN']['PORT'] != main_app['port']:
        print("WARNING: Remember to change the interface server PORT to %s" % main_app['port'])
        print('Setting settings["DEPLOYMENT"]["GUNICORN"]["PORT"] = %s' % main_app['port'])

    if "media" in webfaction_apps:
        media_app_name = webfaction_apps['media']
        media_folder = settings.DEPLOYMENT['FOLDERS']['MEDIA_FOLDER']
        if media_app_name not in existing_apps:
            print("Creating media app {appname}: {mediafolder}".format(
                appname=media_app_name,
                mediafolder=media_folder,
            ))
            app = api.create_app(media_app_name, app_type="symlink70",
                                 extra_info=media_folder)
    if "static" in webfaction_apps:
        static_app_name = webfaction_apps['static']
        static_folder = settings.DEPLOYMENT['FOLDERS']['STATIC_FOLDER']
        if static_app_name not in existing_apps:
            print("Creating staic app {appname}: {staticfolder}".format(
                appname=static_app_name,
                staticfolder=static_folder,
            ))
            app = api.create_app(static_app_name, app_type="symlink70",
                                 extra_info=static_folder)


def create_all_websites():
    api = WebFactionAPI()
    existing_websites = api.list_websites()

    webfaction_apps = settings.WEBFACTION['APPS']
    # the websites name will be the same of the apps
    main_app_name = webfaction_apps['main']
    websites_ip = api.main_ip()
    if not api.website_exists(main_app_name, existing_websites):
        # the main site have all needs
        apps = [[main_app_name, "/"]]
        if "media" in webfaction_apps:
            apps.append((webfaction_apps['media'], '/media'))
        if "static" in webfaction_apps:
            apps.append((webfaction_apps['static'], '/static'))
        print("Creating main website. %s" % apps)
        api.create_website(
            main_app_name, websites_ip,
            False,
            [settings.WEBHOST],
            "",
            apps
        )

    hosts = get_site_hostnames()
    if not api.website_exists(webfaction_apps['media'], existing_websites) and hosts['media']:
        print("Creating media website.")
        api.create_website(
            webfaction_apps['media'], websites_ip,
            False,
            [hosts['media']],
            "",
            [[webfaction_apps['media'], "/"]]
        )
    if not api.website_exists(webfaction_apps['static'], existing_websites) and hosts['static']:
        print("Creating static website.")
        api.create_website(
            webfaction_apps['static'], websites_ip,
            False,
            [hosts['static']],
            "",
            [[webfaction_apps['static'], "/"]]
        )


if __name__ == '__main__':
    if os.path.exists(os.path.expanduser("~/.ssh/config")):
        env.use_ssh_config = True
    env.host_string = 'tam'

    # we start doing all REDIS
    webfaction_install_redis()

    # we then create all needed subdomains
    create_all_domains()
    create_all_apps()
    create_all_websites()
