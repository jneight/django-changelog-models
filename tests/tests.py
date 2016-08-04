# coding=utf-8

from django.test import TestCase
from django.apps import apps

from . import models


class HistoryTest(TestCase):
    def test_history_is_registered(self):
        try:
            apps.get_model('tests', 'testmodel_history')
        except LookupError as e:
            self.fail('History model is not correctly registered')

    def test_tablename(self):
        # check table names are correct, history model must end with _history
        test_1 = models.TestModel(text='Test 1', integer=1)
        history = test_1._history

        self.assertEquals(
            history._meta.db_table, '{0}_history'.format(test_1._meta.db_table))
        self.assertEquals(history._meta.app_label, test_1._meta.app_label)

    def test_history_with_save(self):
        test_1 = models.TestModel(text='Test 1', integer=1)

        # object is not saved, nothing should be saved yet.
        self.assertFalse(test_1._history.objects.all().exists())

        test_1.save()
        # just one history is saved
        self.assertEquals(test_1._history.objects.all().count(), 1)

        # check all fields are correctly saved
        history = test_1._history.objects.get(history_id=test_1.pk)

        self.assertEquals(history.text, test_1.text)
        self.assertEquals(history.integer, test_1.integer)
        self.assertEquals(history.history_timestamp, test_1.modified)

        # test update
        test_1.text = 'Test 2'
        test_1.save()

        self.assertEquals(test_1._history.objects.all().count(), 2)

        history = test_1._history.objects.filter(history_id=test_1.pk).latest('modified')

        self.assertEquals(history.text, test_1.text)
        self.assertEquals(history.integer, test_1.integer)
        self.assertEquals(history.history_timestamp, test_1.modified)

        # saving a new object should not modify the previous info
        test_2 = models.TestModel(text='New test ', integer=1)
        test_2.save()
        self.assertEquals(test_1._history.objects.filter(history_id=test_1.id).count(), 2)
        self.assertEquals(test_2._history.objects.filter(history_id=test_2.id).count(), 1)

    def test_history_with_delete(self):
        test_1 = models.TestModel(text='Test 1', integer=1)
        test_1.save()
        self.assertEquals(test_1._history.objects.filter(history_id=test_1.id).count(), 1)
        deleted_id = test_1.id
        test_1.delete()
        self.assertEquals(test_1._history.objects.filter(history_id=deleted_id).count(), 2)
        history = models.TestModel._history.objects.filter(history_id=deleted_id).latest('modified')

        self.assertEquals(history.text, test_1.text)
        self.assertEquals(history.integer, test_1.integer)
        self.assertEquals(history.history_timestamp, test_1.modified)

