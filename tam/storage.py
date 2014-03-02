from django.contrib.staticfiles.storage import CachedFilesMixin, StaticFilesStorage
from pipeline.storage import PipelineMixin


class MyCachedFilesMixin(CachedFilesMixin):
	def hashed_name(self, name, *a, **kw):
		try:
			return super(MyCachedFilesMixin, self).hashed_name(name, *a, **kw)
		except ValueError:
			print 'WARNING: Failed to find file %s. Cannot generate hashed name' % (name,)
			return name


class PipelineCachedStorage(PipelineMixin, MyCachedFilesMixin, StaticFilesStorage):
	""" A cache storage, who doesn't error if an asset is missing """
	pass