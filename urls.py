# coding=utf-8
from django.conf.urls import url, include
from django.conf import settings
import os
from django.views import static
from django.contrib import admin
import tam

from tam.views.mainviews import pingview, email_test, errorview

secure_url_regex = settings.SECURE_URL
if secure_url_regex[0] == "/":
    secure_url_regex = "^" + secure_url_regex[1:]

urlpatterns = [
    url(r"", include("tam.urls")),
    url(r"", include("modellog.urls")),
    url(r"^archive/", include("tamArchive.urls")),
    # ( r'', include( 'license.urls' ) ),
    url(r"^fatture/", include("fatturazione.urls")),
    url(secure_url_regex, include("securestore.urls")),
    url(r"^webhooks/", include("tamhooks.urls")),
]

# add pluggable apps URL
for app, desc in settings.PLUGGABLE_APPS.items():
    if "urls" in desc:
        url_regex, import_location = desc["urls"]
        urlpatterns.append(url(url_regex, include(import_location)))

admin.autodiscover()
urlpatterns.append(url(r"^admin/", include(admin.site.urls)))

# Serve media settings to simulate production, we know in REAL production this won't happend
if settings.DEBUG:
    # media > /media
    urlpatterns.append(
        url(
            "^media/" + r"(?P<path>.*)$",
            static.serve,
            {"document_root": os.path.join(os.path.dirname(__file__), "media")},
        )
    )

# *** Per servire i staticfiles generati, come in produzione ***
# urlpatterns += patterns('',
#                         ("^static/" + r'(?P<path>.*)$', 'django.views.static.serve',
#                          {'document_root': os.path.join(os.path.dirname(__file__), "static")}),
# )

handler500 = tam.views.mainviews.errors500
handler404 = tam.views.mainviews.errors400

urlpatterns += [
    url("^except/", errorview, name="exception-test"),
    url("^500/", handler500, name="error-test"),
    url("^404/", handler404, name="404-test"),
    url("^ping/", pingview, name="ping-test"),
    url("^emailtest/", email_test, name="email-test"),
]
