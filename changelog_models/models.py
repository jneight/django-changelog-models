# coding=utf-8

import copy

from django.db import models
from django.utils import six, timezone


class HistoryMetaclass(models.base.ModelBase):
    def __new__(cls, classname, bases, classdict):
        # with this, we avoid having to declare HistoryManager in each class inheriting from HistoryMixin
        classdict['_history'] = HistoryManager()
        klass = super(HistoryMetaclass, cls).__new__(cls, classname, bases, classdict)
        # TODO: add checks to avoid unknown attributes in class, etc.
        history_meta = classdict.pop('HistoryMeta', None)
        setattr(klass, '_meta_history', history_meta)
        return klass


class HistoryManager(object):
    def contribute_to_class(self, cls, name):
        """When initializing a model, django tries to call `contribute_to_class` for
        each attribute defined

        """
        # after class got ready, fields can be iterated
        models.signals.class_prepared.connect(self._parent_prepared, sender=cls)

    def _parent_prepared(self, sender, **kwargs):
        """Parent class is ready, so the dynamic class for history can be generated"""
        history_class = self._prepare_history_class(sender)
        setattr(sender, '_history',  history_class)

    def _prepare_history_class(self, sender):
        """The important stuff is handled here, the history class cloning `sender` attributes
        is created and syncdb, makemigrations, etc, will create the table

        """
        if sender._meta.abstract:
            return

        model_name = '{0}_history'.format(sender._meta.object_name)

        # just avoid the creation of duplicate models
        if model_name.lower() in sender._meta.app_config.models:
            return sender._meta.app_config.models.get_model(model_name)

        # this dict will store all the needed data to build a valid cloned model
        history_properties = {
            '__module__': self.__class__.__module__,
        }

        # define the table name for the log
        history_meta = {
            'db_table': '{0}_history'.format(sender._meta.db_table),
            'app_label': sender._meta.app_label,
            'verbose_name': '{0} History'.format(sender._meta.verbose_name),
        }

        for field in sender._meta.fields:
            # copy fields, for now, only flat fields (char, integers, etc)
            if not field.rel:
                field = copy.copy(field)
                history_properties[field.name] = field
            if type(field) == models.AutoField:
                history_properties[field.name] = models.IntegerField()

        # history fields:
        history_properties['history_id'] = models.CharField(max_length=250)
        history_properties['history_timestamp'] = models.DateTimeField()
        history_properties['id'] = models.AutoField(primary_key=True)

        history_properties['Meta'] = type('Meta', (), history_meta)
        model_name = '{0}_history'.format(sender._meta.object_name)

        # the most important stuff, connect the signals to save changes!!
        models.signals.post_save.connect(_post_modification_to_history, sender=sender)
        models.signals.post_delete.connect(_post_modification_to_history, sender=sender)

        # the history class with all ready!
        # history model is now available using apps.get_model
        return type(model_name, (models.Model,), history_properties)


def _post_modification_to_history(instance, **kwargs):
    instance._populate_history()


class HistoryMixin(six.with_metaclass(HistoryMetaclass, models.Model)):
    class Meta:
        abstract = True

    class HistoryMeta:
        # for future django compatibility, it's recommended to create a new Meta class,
        # instead of adding new attributes to existing _meta.
        fields = []
        modified_timestamp = 'modified'

    def _populate_history(self):
        """Copy all the data to the history model and saves it"""
        history = self._history()
        if self._meta_history.modified_timestamp:
            history.history_timestamp = getattr(self, self._meta_history.modified_timestamp)
        else:
            history.history_timestamp = timezone.now()
        for field in history._meta.get_all_field_names():
            if field == history._meta.pk.name:
                continue
            if hasattr(self, field):
                setattr(history, field, getattr(self, field))
        history.history_id = getattr(self, self._meta.pk.name)
        history.save()

