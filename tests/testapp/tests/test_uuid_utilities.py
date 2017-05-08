import mock

from django.test import TestCase
from facility_profile.models import Facility
from morango.models import DatabaseIDModel, InstanceIDModel


class UUIDModelMixinTestCase(TestCase):

    def setUp(self):
        self.fac = Facility(name='bob')

    def test_calculate_uuid(self):
        child = Facility.objects.create(name='bob')

        child.uuid_input_fields = 'RANDOM'
        with mock.patch('uuid.uuid4', return_value='random'):
            self.assertEqual(child.calculate_uuid(), 'random')

        child.uuid_input_fields = []
        with self.assertRaises(AssertionError):
            child.calculate_uuid()

        child.uuid_input_fields = ()
        with mock.patch('uuid.uuid4', return_value='random'):
            self.assertEqual(child.calculate_uuid(), 'random')

        child.uuid_input_fields = ('name',)
        self.assertEqual(child.calculate_uuid().hex, '40ce9a3fded95d7198f200c78e559353')

    def test_save_with_id(self):
        ID = '11111111111111111111111111111111'
        self.fac.id = ID
        self.fac.calculate_uuid = mock.Mock()
        self.fac.save()

        self.assertFalse(self.fac.calculate_uuid.called)
        self.assertEqual(ID, Facility.objects.first().id)

    def test_save_without_id(self):
        ID = '40ce9a3fded95d7198f200c78e559353'
        self.fac.calculate_uuid = mock.Mock(return_value=ID)
        self.fac.save()

        self.assertTrue(self.fac.calculate_uuid.called)
        self.assertEqual(Facility.objects.first().id, ID)


class InstanceIDModelTestCase(TestCase):

    def setUp(self):
        DatabaseIDModel.objects.create()
        InstanceIDModel.get_or_create_current_instance()

    def test_creating_same_instance_ID_model(self):
        firstIDModel = InstanceIDModel.objects.first()
        (secondIDModel, _) = InstanceIDModel.get_or_create_current_instance()

        self.assertEqual(firstIDModel, secondIDModel)
        self.assertEqual(InstanceIDModel.objects.count(), 1)

    def test_creating_different_instance_ID_model(self):
        # change system state
        with mock.patch('platform.platform', return_value='platform'):
            with mock.patch('uuid.getnode', return_value=9999999999999):  # fake (random) address
                (IDModel, _) = InstanceIDModel.get_or_create_current_instance()
        self.assertEqual(InstanceIDModel.objects.count(), 2)
        self.assertEqual(IDModel.macaddress, '')  # assert that macaddress was not added
        self.assertEqual(IDModel.id.hex, InstanceIDModel.objects.get(current=True).id)

    def test_only_one_current_instance_ID(self):
        with mock.patch('platform.platform', return_value='platform'):
            InstanceIDModel.get_or_create_current_instance()
        self.assertEqual(len(InstanceIDModel.objects.filter(current=True)), 1)


class DatabaseIDModelTestCase(TestCase):

    def setUp(self):
        self.ID = '40ce9a3fded95d7198f200c78e559353'

    def test_save(self):
        [DatabaseIDModel().save() for _ in range(10)]
        current_id = DatabaseIDModel()
        current_id.calculate_uuid = mock.Mock(return_value=self.ID)
        current_id.save()

        db_models = DatabaseIDModel.objects.filter(current=True)
        self.assertTrue(len(db_models), 1)
        self.assertTrue(db_models[0].id, self.ID)

    def test_manager_create(self):
        [DatabaseIDModel.objects.create() for _ in range(10)]
        DatabaseIDModel.objects.create(id=self.ID)

        db_models = DatabaseIDModel.objects.filter(current=True)
        self.assertTrue(len(db_models), 1)
        self.assertTrue(db_models[0].id, self.ID)