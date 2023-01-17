from django.conf import settings
from django.http import HttpResponseRedirect


class MaintenanceRedirectMiddleware(object):
    """Move you to another page or show a message if we're in maintenance mode"""

    def process_view(self, request, view_func, view_args, view_kwargs):
        if settings.TAM_MAINTENANCE_URL is True:
            if not request.path.startswith(settings.MEDIA_URL):
                return HttpResponseRedirect(
                    settings.MEDIA_URL + "downtime/maintenance.html"
                )
        elif settings.TAM_MAINTENANCE_URL:
            return HttpResponseRedirect(settings.TAM_MAINTENANCE_URL)
