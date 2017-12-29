# coding=utf-8
import logging

from django.core.management.base import AppCommand

from codapresenze.models import CodaPresenze
from codapresenze.views import dequeue
from tam.tamdates import ita_now

logger = logging.getLogger('tam.tasks.end_of_day')


class Command(AppCommand):
    help = 'Do the cleanup jobs for the end of the day'
    name = 'End of day tasks'

    def handle(self, *app_labels, **options):
        logger.info("End of Day tasks: starting")

        now = ita_now()

        if now.hour < 19 or (now.hour == 19 and now.minute < 45):
            raise Exception("Please come back after 19:45 CET")

        for place in CodaPresenze.objects.all():
            logger.info(f"Forced de-queuing of {place.utente}")
            dequeue(place)
