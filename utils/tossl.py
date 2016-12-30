# coding=utf-8
import logging
import os
from io import BytesIO, StringIO
from textwrap import dedent

from fabric.api import put, get, env
from fabric.context_managers import hide
from fabric.contrib.files import exists, is_link
from fabric.operations import run

from wfcli import WebFactionAPI

logger = logging.getLogger('wfcli.redirect_to_secure')


class WebfactionWebsiteToSsl():
    """ Do all is needed to move a domain to https

    This uses Lets Encrypt and the webfaction APIs
    """

    def __init__(self,
                 domain=None,
                 website=None,
                 webfaction_host=None):
        self.REDIRECT_TEMPLATE = dedent("""
            RewriteEngine On
            RewriteCond %{HTTP:X-Forwarded-SSL} !on
            RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
        """)

        if webfaction_host is None:
            raise RuntimeError("Please provide the Webfaction host, we will connect via SSH")
        self.webfaction_host = webfaction_host
        if not any([domain, website]) or all([domain, website]):
            logger.error("Please choose a domain OR a website")
            exit(1)
        self.domain = domain

        self.api = api = WebFactionAPI()
        self._domains = api.list_domains()
        self._websites = api.list_websites()
        self._certificates = api.list_certificates()
        self._apps = self.api.list_apps()

        # we will create the certificate with the requested name
        # we have 2 modes: a certificate per website, or a collective cert for domain
        self.request_name = website or domain
        self.request_type = "website" if website else "domain"

        websites = []  # the websites the user choosed
        if website:
            for w in self._websites:
                if w['name'] == website:
                    websites.append(w)
                self.domain = w['subdomains']
            if not website:
                logger.error("Cannot find website: %s" % website)
                exit(1)

        if domain:
            websites = list(filter(
                lambda w: domain in w['subdomains'],
                self._websites
            ))

        print("Apply to websites: %s" % ", ".join([website['name'] for website in websites]))
        self.websites = websites

        self.REDIRECT_TO_SECURE_APP_NAME = 'redirect_to_secure'
        self.LETSENCRYPT_VERIFY_APP_NAME = '_letsencrypt'

        # prepare Fabric
        if os.path.exists(os.path.expanduser("~/.ssh/config")):
            env.use_ssh_config = True
        env.host_string = webfaction_host

        # ask the APIs
        self.api.list_websites()

    def redirect_to_secure(self):
        existing_apps = self._apps
        if self.REDIRECT_TO_SECURE_APP_NAME in existing_apps:
            app = existing_apps[self.REDIRECT_TO_SECURE_APP_NAME]
        else:
            logger.info("Creating redirect app: %s" % self.REDIRECT_TO_SECURE_APP_NAME)
            app = self.api.create_app(
                app_name=self.REDIRECT_TO_SECURE_APP_NAME,
                app_type='static_php70',
            )
        name = app['name']
        filepath = os.path.join('webapps', name, '.htaccess')

        if exists(filepath):
            with hide('running'):
                temp = BytesIO()
                get(filepath, temp)
                current_redirection = temp.getvalue().decode('utf-8')
                if current_redirection != self.REDIRECT_TEMPLATE:
                    update_redirection = True
                    logger.info("Updating .htaccess")
                else:
                    update_redirection = False
        else:
            update_redirection = True
            logger.info("Creating .htaccess")
        if update_redirection:
            put(StringIO(self.REDIRECT_TEMPLATE), remote_path=filepath)

    def run(self):
        # install acme on the remote server -
        # create an app to verify the LE certificate
        # create Static/CGI/PHP-7.0 with the domain name _letsencrypt
        # add the app on the (non http website) on the /.well-known path

        # here's an hack to make acme.sh run on the .well-known like it was the root
        # from the app path:
        # ln -s . .well-known
        # acme.sh --issue -d {domain} -w .

        # we should have the certs now
        # create the certificate if it is missing using the cert, key and intermediate
        # create the https website with the new certificate

        # redirect all the http traffic to https (in .htaccess
        # RewriteEngine On
        # RewriteCond %{HTTP:X-Forwarded-SSL} !on
        # RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
        self.install_acme()

        for website in self.websites:
            if not website['https']:
                continue
            secured_website = self.website_exists_as_secure(website)
            if not secured_website:
                secured_website = self.clone_website_as_secure(website)
            self.verify_certificate(secured_website)  # check the certificates are ok

        logger.info("Webfaction - http 2 https - %s" % self.domain)

    def website_exists_as_secure(self, website):
        """" Return true if the website has an equivalent that is secure """
        if website['https']:
            logger.info("website %s is already secured, skip" % website['name'])
            return website
        ignored_fields = ('https', 'name', 'id')  # changes in these fields are ignored
        clean = {k: v for k, v in website.items() if k not in ignored_fields}
        for other in self._websites:
            if other['id'] == website['id']:
                continue
            other_clean = {k: v for k, v in other.items() if k not in ignored_fields}
            if clean == other_clean:
                logger.info("website {wname} is already secured as {wsname}, skip".format(
                    wname=website['name'], wsname=other['name']
                ))
                return other
        return None

    def install_acme(self):
        if not exists('~/.acme.sh/acme.sh'):
            logger.info("Installing acme.sh")
            run('curl https://get.acme.sh | sh')

    def clone_website_as_secure(self, website):
        logger.info("Creating a secure version of website: %s" % website['name'])
        certificate = self.add_certificate(website)
        old = website
        print(old)
        new = self.api.create_website(
            old['name'],
            ip=old['ip'],
            enable_https=True,
            subdomains=old['subdomains'],
            apps=old['website_apps'],
        )
        return new

    def add_certificate(self, website):
        logger.info("Creating a certificate for {type} {name}".format(
            type=self.request_type, name=self.request_name)
        )
        self.create_le_verification_app()


        certificate_name = self.request_name
        return certificate_name

    def verify_certificate(self, website):
        # do we have a certificate for the website?
        # is it associated with the website?
        certificate_name = website['name']
        if certificate_name not in self._certificates:
            certificate = self.add_certificate(website)

    def create_le_verification_app(self):
        """ Create the let's encrypt app to verify the ownership of the domain """
        if self.LETSENCRYPT_VERIFY_APP_NAME in self._apps:
            logger.debug(
                "The LE verification APP already exists as %s" % self.LETSENCRYPT_VERIFY_APP_NAME
            )
            verification_app = self._apps[self.LETSENCRYPT_VERIFY_APP_NAME]
        else:
            logger.info("Creating the identity-verification app for let's encrypt")
            verification_app = self.api.create_app(
                self.LETSENCRYPT_VERIFY_APP_NAME,
                'static_php70',
            )
            self._apps[self.LETSENCRYPT_VERIFY_APP_NAME] = verification_app

        # LE use the .well-known subfolder of the domain to do its verifications.
        # we will mount the app in the .well-known path, so we apply an hack to serve
        # the app-folder/.well-known on root
        app_root = os.path.join('~/webapps', self.LETSENCRYPT_VERIFY_APP_NAME)
        well_known_folder = os.path.join(app_root, '.well-known')

        if not is_link(well_known_folder):
            logger.info("Preparing static app for the verification")
            run('ln -s {app_root} {well_known_folder}'.format(**locals()))
        return verification_app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    w = WebfactionWebsiteToSsl(
        domain='old.dariosky.it',
        # website = 'dariosky_old',
        webfaction_host='dariosky',
    )
    w.run()
    # print(w.api.list_certificates())
    # w.redirect_to_secure()
