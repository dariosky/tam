# coding=utf-8
import logging

from django.contrib.staticfiles.storage import (CachedFilesMixin,
                                                CachedStaticFilesStorage)
from pipeline.storage import PipelineMixin

logger = logging.getLogger('tam.myCachedFiles')


class MyCachedFilesMixin(CachedFilesMixin):
    def stored_name(self, name, *a, **kw):
        try:
            return super(MyCachedFilesMixin, self).stored_name(name, *a, **kw)
        except ValueError:
            logger.warning('Failed to find file %s. Cannot generate hashed name' % name)
            return name


class PipelineCachedStorage(PipelineMixin, MyCachedFilesMixin, CachedStaticFilesStorage):
    """ A cache storage, who doesn't error if an asset is missing """
    pass
