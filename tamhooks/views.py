# coding=utf-8
import hashlib
import hmac
import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from markViews import public

logger = logging.getLogger(__name__)


def verify(api_key, token, timestamp, signature):
    return signature == hmac.new(
        key=api_key,
        msg='{}{}'.format(timestamp, token),
        digestmod=hashlib.sha256).hexdigest()


@public
@csrf_exempt
def mail_report(request):
    # print verify(api_key=settings.MAILGUN_ACCESS_KEY,
    #              )
    status = 400
    response = "Hi"
    if request.method == 'POST':
        g = request.POST.get
        timestamp, token, signature = g('timestamp'), g('token'), g('signature')
        if verify(settings.MAILGUN_ACCESS_KEY,
                  token, timestamp, signature
                  ):
            status = 200
            event, recipient, reason = g('event'), g('recipient'), g('reason')
            logger.error(
                "Webhooks mail: {event} mail to {recipient} for {reason}".format(**locals()))
        else:
            status = 406  # unacceptable
            logger.warning("Webhooks not signed correctly")

        response = "Hi webhook"
    return HttpResponse(response, status=status, content_type='text/plain')
