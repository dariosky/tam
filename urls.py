# coding=utf-8
import os

from django.conf import settings
from django.conf.urls import re_path, include
from django.contrib import admin
from django.views import static

import tam
from tam.views.mainviews import pingview, email_test, errorview

secure_url_regex = settings.SECURE_URL
if secure_url_regex[0] == "/":
    secure_url_regex = "^" + secure_url_regex[1:]

urlpatterns = [
    re_path(r"", include("tam.urls")),
    re_path(r"", include("modellog.urls")),
    re_path(r"^archive/", include("tamArchive.urls")),
    # ( r'', include( 'license.urls' ) ),
    re_path(r"^fatture/", include("fatturazione.urls")),
    re_path(secure_url_regex, include("securestore.urls")),
    re_path(r"^webhooks/", include("tamhooks.urls")),
]

# add pluggable apps URL
for app, desc in settings.PLUGGABLE_APPS.items():
    if "urls" in desc:
        url_regex, import_location = desc["urls"]
        urlpatterns.append(re_path(url_regex, include(import_location)))

admin.autodiscover()
urlpatterns.append(re_path(r"^admin/", admin.site.urls))

# Serve media settings to simulate production, we know in REAL production this won't happend
if settings.DEBUG:
    # media > /media
    urlpatterns.append(
        re_path(
            "^media/" + r"(?P<path>.*)$",
            static.serve,
            {"document_root": os.path.join(os.path.dirname(__file__), "media")},
        )
    )

# *** Serve generated staticfiles, like in production ***
urlpatterns.append(
    re_path(
        "^static/" + r"(?P<path>.*)$",
        static.serve,
        {"document_root": os.path.join(os.path.dirname(__file__), "static")},
    ),
)

handler500 = tam.views.mainviews.errors500
handler404 = tam.views.mainviews.errors400

urlpatterns += [
    re_path("^except/", errorview, name="exception-test"),
    re_path("^500/", handler500, name="error-test"),
    re_path("^404/", handler404, name="404-test"),
    re_path("^ping/", pingview, name="ping-test"),
    re_path("^emailtest/", email_test, name="email-test"),
]
