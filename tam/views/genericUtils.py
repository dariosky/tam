def getActionName(delete, nuovo):
    """ Given two boolean delete and nuovo, return the permission requested for action """
    if delete:
        actionName = "delete"
    else:
        if nuovo:
            actionName = "add"
        else:
            actionName = "change"
    return actionName


def copy_model_instance(obj):
    from django.db.models import AutoField
    initial = dict([(f.name, getattr(obj, f.name))
                    for f in obj._meta.fields
                    if not isinstance(f, AutoField) and
                    not f in obj._meta.parents.values()])
    return obj.__class__(**initial)
