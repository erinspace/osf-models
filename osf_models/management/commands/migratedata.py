import gc
import importlib
import sys

from django.apps import apps
from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from osf_models.models import ApiOAuth2Scope
from osf_models.models.contributor import AbstractBaseContributor
from osf_models.scripts.migrate_nodes import build_pk_caches

global modm_to_django
modm_to_django = build_pk_caches()
print('Cached {} MODM to django mappings...'.format(len(modm_to_django.keys())))


def save_bare_models(modm_queryset, django_model, page_size=20000):
    print('Starting {}...'.format(sys._getframe().f_code.co_name))
    count = 0
    total = modm_queryset.count()
    hashes = list()

    while count < total:
        with transaction.atomic():
            django_objects = list()

            offset = count
            limit = (count + page_size) if (count + page_size) < total else total

            page_of_modm_objects = modm_queryset.sort('-_id')[offset:limit]

            for modm_obj in page_of_modm_objects:
                django_instance = django_model.migrate_from_modm(modm_obj)
                if django_instance._natural_key() is not None and django_instance._natural_key() not in hashes:
                    django_objects.append(django_instance)
                    hashes.append(django_instance._natural_key())
                count += 1
                if count % page_size == 0 or count == total:
                    page_finish_time = timezone.now()
                    print('Saving {} {} through {}...'.format(django_model._meta.model.__name__, count - page_size,
                                                              count))
                    saved_django_objects = django_model.objects.bulk_create(django_objects)
                    for django_instance in saved_django_objects:
                        modm_to_django[django_instance._id] = django_instance.pk
                    print('Done with {} {} in {} seconds...'.format(len(saved_django_objects),
                                                                    django_model._meta.model.__name__, (
                                                                        timezone.now() - page_finish_time).total_seconds()))
                    saved_django_objects = []
                    page_of_modm_objects = []
                    print('Took out {} trashes'.format(gc.collect()))


class Command(BaseCommand):
    help = 'Migrates data from tokumx to postgres'

    def handle(self, *args, **options):
        # TODO Handle system tags, they're on nodes, they'll need a special migration
        # TODO Handle contributors, they're not a direct 1-to-1 they'll need some love

        models = apps.get_app_config('osf_models').get_models(include_auto_created=False)
        for django_model in models:

            if issubclass(django_model, AbstractBaseContributor) \
                    or django_model is ApiOAuth2Scope \
                    or not hasattr(django_model, 'modm_model_path'):
                continue
            module_path, model_name = django_model.modm_model_path.rsplit('.', 1)
            modm_module = importlib.import_module(module_path)
            modm_model = getattr(modm_module, model_name)
            modm_queryset = modm_model.find(django_model.modm_query)
            # save_bare_models(modm_queryset, django_model)
            print(modm_queryset.count())
            print(modm_model)
