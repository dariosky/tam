# coding: utf-8


class SeparateLogRouter(object):
    """A router to control all database operations on models
    in the modellog application in modellog connection"""

    def db_for_read(self, model, **hints):
        "Point all operations on modellog models to 'modellog'"
        if model._meta.app_label == "modellog":
            return "modellog"
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on modellog models to 'modellog'"
        if model._meta.app_label == "modellog":
            return "modellog"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow any relation if a model in myapp is involved"""
        if obj1._meta.app_label == "modellog" or obj2._meta.app_label == "modellog":
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        "Make sure the myapp app only appears on the 'other' db"
        # print "creo %s in %s. App=%s?" % (model, db, model._meta.app_label)
        if db == "modellog":
            return app_label == "modellog"
        elif app_label == "modellog":
            return False
        return None
