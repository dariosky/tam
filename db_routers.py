# coding: utf-8

class TamArchiveRouter(object):
    """ A DB router to keep only the 'tamArchiveApp' on 'archive' db """

    def db_for_read(self, model, **hints):
        # dutchtape fix, cause of ticket 14948 in Django 1.2.4
        if not hasattr(model,
                       "_meta"):
            return False

        # use 'archive' connection when reading/writing a model in tamArchive
        if model._meta.app_label == 'tamArchive':
            return 'archive'

    db_for_write = db_for_read  # use same answer for read/write

    def allow_migrate(self, db, model):
        # dutchtape fix, cause of ticket 14948 in Django 1.2.4
        if not hasattr(model,
                       "_meta"):
            return False

        if db == 'archive':
            # if the db Archive use only tamArchive models
            return model._meta.app_label == 'tamArchive'
        elif model._meta.app_label == 'tamArchive':
            # in the other DB put everything else
            return False
