# coding=utf-8

from django.db import models

from changelog_models import models as history_models


class TestModel(history_models.HistoryMixin, models.Model):
    text = models.CharField(max_length=200)
    integer = models.IntegerField()

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class HistoryMeta:
        modified_timestamp = 'modified'


class Test2Model(history_models.HistoryMixin, models.Model):
    text = models.CharField(max_length=200)
    integer = models.IntegerField()

    modified = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    class HistoryMeta:
        modified_timestamp = 'modified'


