# coding: utf-8
from StringIO import StringIO
from email.mime.base import MIMEBase
import requests
from django.conf import settings
from django.template.loader import get_template
import os
import logging
from django.utils.safestring import mark_safe

ADMIN_MAIL = ",".join(["%s <%s>" % adm for adm in settings.ADMINS])
logger = logging.getLogger('tam.mail')


def notifyByMail(to=None, subject="",
                 context=None, contextText=None,
                 messageTxtTemplateName=None, messageHtmlTemplateName=None, bcc=None,
                 body=None,
                 reply_to=None,
                 attachments=None,
                 from_email=None,
                 **kwargs):
    """ Warn with a mail when some event occour """
    if not context:
        context = {}
    if attachments is None:
        attachments = []

    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    logo_filename = os.path.join(settings.MEDIA_ROOT, settings.EMAIL_SMALL_LOGO)
    signatureTXT = settings.DATI_CONSORZIO

    signatureHTML = getattr(settings, "DATI_CONSORZIO_HTML", None)
    if signatureHTML is None:
        signatureHTML = settings.DATI_CONSORZIO
    else:
        signatureHTML = mark_safe(signatureHTML)

    context["signatureHTML"] = signatureHTML

    if to is None:
        to = [ADMIN_MAIL]
    if bcc is None:
        bcc = []
    if settings.DEBUG:
        logger.debug("In test, send mail only to ADMIN instead of %s" % to)
        to = [ADMIN_MAIL]
        bcc = []
        subject = "[TEST] " + subject
    context_html = context
    if contextText is None:
        context_text = context_html
    else:
        context_text = contextText
    if body and (messageTxtTemplateName or messageHtmlTemplateName):
        raise Exception("Give the Body OR the template")
    context_html["logofilename"] = os.path.basename(logo_filename)
    if body:
        messageText = body
        htmlMessage = None
    else:
        messageTemplate = get_template(messageTxtTemplateName)
        messageText = messageTemplate.render(context_text)
        if messageHtmlTemplateName:
            htmlTemplate = get_template(messageHtmlTemplateName)
            htmlMessage = htmlTemplate.render(context_html)
        else:  # default html message
            htmlTemplate = get_template("prenotazioni_email/htmlMailTemplate.html")
            htmlMessage = htmlTemplate.render({"message": messageText,  # generic html message
                                               "logofilename": os.path.basename(logo_filename)}
                                              )

    if signatureTXT:
        messageText += u"\n-- \n" + signatureTXT
    mail_data = {'from': from_email,
                 'to': to,
                 'subject': subject,
                 }

    for value, mail_field in (
        (settings.MAIL_TAG, 'o:tag'),
        (bcc, 'bcc'),
        (messageText, 'text'),
        (htmlMessage, 'html'),
    ):
        if value:
            mail_data[mail_field] = value

    with open(logo_filename, 'rb') as f:
        files = [('inline', f)]
        for attachment in attachments:
            if isinstance(attachment, basestring):
                # attachment is a filename
                files.append(
                    ('attachment', open(attachment))
                )
            elif isinstance(attachment, MIMEBase):
                filename = attachment.get_filename()
                content_type = attachment.get_content_type()
                file_like = StringIO(attachment.get_payload())
                files.append(
                    ('attachment', (filename, file_like))
                )
            else:
                raise Exception("What is this attachment? %s" % type(attachment))

        requests.post(
            "https://api.mailgun.net/v3/%s/messages" % settings.MAILGUN_SERVER_NAME,
            auth=("api", settings.MAILGUN_ACCESS_KEY),
            data=mail_data,
            files=files
        )


if __name__ == "__main__":
    notifyByMail(
        to=[ADMIN_MAIL],
        subject="Testing confirm mail",
        context={
        },
        reply_to=settings.EMAIL_CONSORZIO,
        messageTxtTemplateName="prenotazioni_email/conferma.inc.txt",
        messageHtmlTemplateName="prenotazioni_email/conferma.inc.html",

    )
    print "Fine."
