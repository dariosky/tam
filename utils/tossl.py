# coding=utf-8
import logging
import os
from io import BytesIO, StringIO
from textwrap import dedent

from fabric.api import put, get, env, settings as fab_settings
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
                 domain,
                 webfaction_host=None,
                 include_subdomains=True,
                 ):
        self.REDIRECT_TEMPLATE = dedent("""
            RewriteEngine On
            RewriteCond %{HTTP:X-Forwarded-SSL} !on
            RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,L]
        """)

        if webfaction_host is None:
            raise RuntimeError("Please provide the Webfaction host, we will connect via SSH")
        self.webfaction_host = webfaction_host

        self.domain = domain
        self.include_subdomains = include_subdomains

        # getting all the infos from Webfaction API
        self.api = api = WebFactionAPI()
        self._domains = api.list_domains()
        self._websites = api.list_websites()
        self._certificates = api.list_certificates()
        self._apps = self.api.list_apps()

        # we will create the certificate with the requested name
        # we have 2 modes: a certificate per website, or a collective cert for domain

        websites = list(filter(  # get all the affected websites
            self.is_website_affected,
            self._websites
        ))

        logger.info("Websites affected: %s" % ", ".join([website['name'] for website in websites]))
        self.websites = websites

        self.REDIRECT_TO_SECURE_APP_NAME = 'redirect_to_secure'
        self.LETSENCRYPT_VERIFY_APP_NAME = '_letsencrypt'

        # prepare Fabric
        if os.path.exists(os.path.expanduser("~/.ssh/config")):
            env.use_ssh_config = True
        env.host_string = webfaction_host

    def is_website_affected(self, website):
        """ Tell if the website is affected by the domain change """
        if not self.include_subdomains:
            return self.domain in website['subdomains']
        else:
            dotted_domain = "." + self.domain
            for subdomain in website['subdomains']:
                if subdomain == website or subdomain.endswith(dotted_domain):
                    return True
            return False

    def get_affected_domains(self):
        """ Return a list of all affected domain and subdomains """
        results = []
        dotted_domain = "." + self.domain
        for website in self.websites:
            for subdomain in website['subdomains']:
                if (
                            subdomain == self.domain or
                        (self.include_subdomains and subdomain.endswith(dotted_domain))
                ):
                    results.append(subdomain)

        # sort them by lenght so the shortest domain is the first
        results.sort(key=lambda item: len(item))
        return results

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

        logger.info("Webfaction - http 2 https - %s" % self.domain)

        # we will create a certificate for a bunch of subdomains
        subdomains = self.get_affected_domains()
        logger.info("Domains affected: %s" % subdomains)

        # let's check what are the subdomains still unsecured
        insecured = []
        for subdomain in subdomains:
            if not self.domain_exists_as_secured(subdomain):
                insecured.append(subdomain)
        logger.info("To be secured: %s" % insecured)

        if insecured:
            self.create_certificates(subdomains)
        self.sync_certificates()
        # for website in self.websites:
        #     if website['https'] is True:
        #         continue
        #     secured_website = self.website_exists_as_secure(website)
        #     if not secured_website:
        #         secured_website = self.clone_website_as_secure(website)
        #     self.verify_certificate(secured_website)  # check the certificates are ok

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

    def domain_exists_as_secured(self, subdomain):
        for website in self.websites:
            if website['https'] and website['certificate'] and subdomain in website['subdomain']:
                return True
        return False

    @staticmethod
    def install_acme():
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
        logger.info("Creating a certificate for {}".format(website))
        self.create_le_verification_app()

        certificate_name = self.domain
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

    def create_certificates(self, subdomains):
        self.install_acme()  # acme is a requirement for the certificates
        self.create_le_verification_app()

        for insecure_website in self.websites:
            if insecure_website['https']:
                continue
            if not self.website_verificable(insecure_website):
                insecure_website['website_apps'].append(
                    [self.LETSENCRYPT_VERIFY_APP_NAME, '/.well-known']
                )
                logger.info("Make insecure site verificable %s" % insecure_website['name'])
                self.api.update_website(insecure_website)

        issue_command = [
            ".acme.sh/acme.sh", "--issue"
        ]
        for subdomain in subdomains:
            issue_command += ["-d", subdomain]
        issue_command += ["-w", "~/webapps/%s" % self.LETSENCRYPT_VERIFY_APP_NAME]
        with fab_settings(warn_only=True):
            # let's issue the certificates with acme
            result = run(" ".join(issue_command), quiet=True)
            return_code = result.return_code
            if return_code == 2:
                logger.debug("No need to issue new certificates")
            else:
                logger.info("Something went wrong issuing the new certificates")
                logger.error(result)

    def website_verificable(self, website):
        """ True if the website is LetsEncrypt verificable: it should have the verification app
            on the /.well-known path """
        required_app = [self.LETSENCRYPT_VERIFY_APP_NAME, '/.well-known']
        for app in website['website_apps']:
            if app == required_app:
                return True
        return False

    def sync_certificates(self):
        """ Check all certificates available in acme in the host
            and sync them with the webfaction certificates
        """
        result = run(".acme.sh/acme.sh --list", quiet=True)
        for acme_certificate_description in result.split('\n')[1:]:
            main_domain = acme_certificate_description.split()[0]
            print(main_domain)
            if exists(os.path.join("~/.acme.sh/", main_domain)):
                certificate_cer = self.get_remote_content(
                    os.path.join("~/.acme.sh/", main_domain, main_domain + ".cer")
                )
                certificate_key = self.get_remote_content(
                    os.path.join("~/.acme.sh/", main_domain, main_domain + ".key")
                )
                certificate_ca = self.get_remote_content(
                    os.path.join("~/.acme.sh/", main_domain, "ca.cer")
                )
                certificate_name = self.slugify(main_domain)

                certificate = self._certificates.get(certificate_name)
                if certificate is None \
                    or certificate['certificate'] != certificate_cer \
                    or certificate['private_key'] != certificate_key \
                    or certificate['intermediates'] != certificate_ca:
                    new_certificate = dict(
                        name=certificate_name,
                        certificate=certificate_cer,
                        private_key=certificate_key,
                        intermediates=certificate_ca,
                    )
                    if certificate is None:
                        logger.info("Creating new certificate for %s" % main_domain)
                        self.api.create_certificate(new_certificate)
                    else:
                        logger.info("Updating certificate for %s" % main_domain)
                        self.api.update_certificate(new_certificate)

    def get_remote_content(self, filepath):
        with hide('running'):
            temp = BytesIO()
            get(filepath, temp)
            content = temp.getvalue().decode('utf-8')
        return content.strip()

    def slugify(self, domain):
        """ Slugify the domain to create a certificate name for Webfaction. Simple for now
        (should be alphanumerical)"""
        return domain.replace(".", "_")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    w = WebfactionWebsiteToSsl(
        domain='domain.com',
        webfaction_host='webxxx.webfaction.com'
    )
    w.run()
    # print(w.api.list_certificates())
    # w.redirect_to_secure()
