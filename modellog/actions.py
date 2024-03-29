# coding=utf-8
import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models import signals
from django.utils import timezone

from modellog.models import ActionLog
from tam.middleware import threadlocals

logger = logging.getLogger("tam.action")


def log_action(action, instance=None, description="", user=None, log_date=None):
    if instance:
        content_type = ContentType.objects.get_for_model(instance)
    else:
        content_type = None

    if user is None:
        user = threadlocals.get_current_user()
    # if user.is_superuser and settings.DEBUG:
    # 	return
    if log_date is None:
        log_date = timezone.now()

    modification = ActionLog(
        data=log_date,
        user_id=user.id if user else None,
        action_type=action,
        description=description,
        modelName=content_type.model if instance else None,
        instance_id=instance.id if instance else None,
    )
    if (
        instance
        and modification.modelName == "viaggio"
        and instance.data < log_date.replace(hour=0, minute=0)
    ):
        modification.hilight = True
    logger.debug(modification)
    modification.save()


def traduci(v):
    if v is True:
        return "Vero"
    if v is False:
        return "Falso"
    if v is None:
        return "Nulla"
    return v


def presave_logger(sender, instance, signal, **kwargs):
    """Log actions to db"""
    # logging.debug( "PRESAVE: sender:%s. instance:%s" % (sender._meta.verbose_name, instance) )
    # logging.debug("********** ID: %s ********** "%instance.id)
    try:
        pre_instance = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        instance._changeList = None
        return  # creation time

    instance._changeList = []
    for field in sender._meta.fields:
        fieldname = field.name
        prevalue = getattr(pre_instance, fieldname)
        newvalue = getattr(instance, fieldname)
        if not field.editable:
            continue
        if prevalue != newvalue:
            prevalue = traduci(prevalue)
            newvalue = traduci(newvalue)
            instance._changeList.append(
                "%s: da '%s' a '%s'" % (fieldname, prevalue, newvalue)
            )


def postsave_logger(sender, instance, signal, **kwargs):
    # logging.debug( "POSTSAVE: sender:%s. instance:%s" % (sender._meta.verbose_name, instance) )
    if instance._changeList is None:
        log_action("A", instance, "%s" % instance)
    else:
        if instance._changeList:
            log_action("M", instance, "; ".join(instance._changeList))


def predelete_logger(sender, instance, signal, **kwargs):
    # logging.debug( "DELETE: sender:%s. instance:%s" % (sender._meta.verbose_name, instance) )
    log_action("D", instance, "%s" % instance)


def startLog(ModelClass):
    signals.pre_save.connect(
        presave_logger,
        sender=ModelClass,
        dispatch_uid="%s.%s" % (ModelClass._meta.verbose_name, "pre_save"),
    )
    signals.post_save.connect(
        postsave_logger,
        sender=ModelClass,
        dispatch_uid="%s.%s" % (ModelClass._meta.verbose_name, "post_save"),
    )
    signals.pre_delete.connect(
        predelete_logger,
        sender=ModelClass,
        dispatch_uid="%s.%s" % (ModelClass._meta.verbose_name, "pre_delete"),
    )


def stopLog(ModelClass):
    signals.pre_save.disconnect(
        sender=ModelClass,
        dispatch_uid="%s.%s" % (ModelClass._meta.verbose_name, "pre_save"),
    )
    signals.post_save.disconnect(
        sender=ModelClass,
        dispatch_uid="%s.%s" % (ModelClass._meta.verbose_name, "post_save"),
    )
    signals.pre_delete.disconnect(
        sender=ModelClass,
        dispatch_uid="%s.%s" % (ModelClass._meta.verbose_name, "pre_delete"),
    )
