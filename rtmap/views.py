# coding=utf-8
import json

from django.conf import settings
from django.views.generic import TemplateView


class Overview(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['RTMAP_SETTINGS_JSON'] = json.dumps(settings.RTMAP)
        return context

    template_name = "rtmap/overview.html"
