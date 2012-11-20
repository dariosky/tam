#coding: utf-8
from django.conf import settings
from django.template import Context
from django.template.loader import get_template
from prenotazioni.views.emailMultiRelated import EmailMultiRelated
import os
from email.MIMEBase import MIMEBase
import logging
from prenotazioni.models import Prenotazione
from django.utils.safestring import mark_safe

ADMIN_MAIL = "dariosky@gmail.com"

def notifyByMail(
		to=None,
		subject="",
		context={},
		contextText=None, 	# if this is none I'll use the normal one
		messageTxtTemplateName=None, messageHtmlTemplateName=None,
		bcc=[ADMIN_MAIL],
		attachments=[],
		** kwargs
	):
	""" Warn with a mail when some event occour """
	signatureTXT = settings.DATI_CONSORZIO

	signatureHTML = getattr(settings, "DATI_CONSORZIO_HTML", None)
	if signatureHTML is None:
		signatureHTML = settings.DATI_CONSORZIO
	else:
		signatureHTML = mark_safe(signatureHTML)

	context["signatureHTML"] = signatureHTML

	if to is None: to = [ADMIN_MAIL]
	if settings.DEBUG:
		to = [ADMIN_MAIL]
		bcc = []
		subject = "[TEST] " + subject
	context_html = Context(context)
	if contextText is None:
		context_text = context_html
	else:
		context_text = Context(contextText)

	messageTemplate = get_template(messageTxtTemplateName)
	messageText = messageTemplate.render(context_text)
	if messageHtmlTemplateName:
		htmlTemplate = get_template(messageHtmlTemplateName)
		htmlMessage = htmlTemplate.render(context_html)
	else:	# default html message
		htmlTemplate = get_template("prenotazioni_email/htmlMailTemplate.html")
		htmlMessage = htmlTemplate.render(Context({"message":messageText}))	# generic html message


	if signatureTXT:
		messageText += "\n-- \n" + signatureTXT

	emailMessage = EmailMultiRelated(
							  body=messageText,
							  subject=subject,
							  to=to,
							  bcc=bcc,
				)

	emailMessage.attach_alternative(htmlMessage, "text/html")

	f = open(os.path.join(settings.MEDIA_ROOT, 'brand/taxilogo_small.jpg'), 'rb')
	logo_content = f.read()
	f.close()
	emailMessage.attach_related("logo", logo_content, 'image/jpeg')

	if attachments:
		# We have a multipart/related message with inline attachments
		# create a container of multipart/mixed and include the related and the attached files
		for attachment in attachments:
			if isinstance(attachment, MIMEBase):
				emailMessage.attach(attachment)
			else:
				emailMessage.attach_file(attachment)
			#emailMessage.attach('event.ics', 'sgnafuz', 'text/calendar')

	if settings.DEBUG:
		print("In test, don't send mail to %s" % to)
		emailMessage.send()
		print htmlMessage
	else:
		logging.debug("Sending mail to %s" % to)
		emailMessage.send()

if __name__ == "__main__":
	prenotazione = Prenotazione.objects.get(id=1)
	notifyByMail(
		to=[prenotazione.owner.email, settings.EMAIL_CONSORZIO],
		subject="Conferma prenotazione TaM n° %d" % prenotazione.id,
		context={
					"prenotazione":prenotazione,
				},

		messageTxtTemplateName="prenotazioni_email/conferma.inc.txt",
		messageHtmlTemplateName="prenotazioni_email/conferma.inc.html",
	)
	print "Fine."
