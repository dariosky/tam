# coding=utf-8
import logging

from django.apps import AppConfig

logger = logging.getLogger("tam.appconfig")


class TamConfig(AppConfig):
    name = "tam"
    verbose_name = "TAM Taxi Manager"

    def ready(self):
        # from django.conf import settings
        # from tam.middleware.prevent_multisession import register_session_limit
        #
        # if settings.FORCE_SINGLE_DEVICE_SESSION:
        #     logger.info("Register single session check on login")
        #     register_session_limit()
        pass
