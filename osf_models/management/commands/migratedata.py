import gc
import importlib
import sys

import ipdb
from django.apps import apps
from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from modularodm import Q as MQ
from osf_models.models import ApiOAuth2Scope
from osf_models.models import BlackListGuid
from osf_models.models import Guid
from osf_models.models import NodeLog
from osf_models.models import Session
from osf_models.models import Tag
from osf_models.models.conference import MailRecord
from osf_models.models.contributor import AbstractBaseContributor
from osf_models.scripts.migrate_nodes import build_pk_caches
from osf_models.utils.order_apps import get_ordered_models

from framework.auth.core import User as MODMUser
from website.files.models import StoredFileNode
from website.models import Node as MODMNode

global modm_to_django
modm_to_django = build_pk_caches()
print('Cached {} MODM to django mappings...'.format(len(modm_to_django.keys())))


def save_bare_models(modm_queryset, django_model, page_size=20000):
    print('Starting {} on {}...'.format(sys._getframe().f_code.co_name, django_model._meta.model.__name__))
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
                if django_instance._natural_key() is not None:
                    # if there's a natural key
                    if django_instance._natural_key() not in hashes:
                        # and that natural key doesn't exist in hashes
                        # add it to hashes and append the object
                        hashes.append(django_instance._natural_key())
                        django_objects.append(django_instance)
                else:
                    # if _natural_key is None add it, it's probably pointing at .pk
                    django_objects.append(django_instance)

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


def save_bare_system_tags(page_size=10000):
    print('Starting save_bare_system_tags...')
    start = timezone.now()

    things = list(MODMNode.find(MQ('system_tags', 'ne', [])).sort(
        '-_id')) + list(MODMUser.find(MQ('system_tags', 'ne', [])).sort(
        '-_id'))

    system_tag_ids = []
    for thing in things:
        for system_tag in thing.system_tags:
            system_tag_ids.append(system_tag)

    unique_system_tag_ids = set(system_tag_ids)

    total = len(unique_system_tag_ids)

    system_tags = []
    for system_tag_id in unique_system_tag_ids:
        system_tags.append(Tag(name=system_tag_id,
                               system=True))

    created_system_tags = Tag.objects.bulk_create(system_tags)

    print('MODM System Tags: {}'.format(total))
    print('django system tags: {}'.format(Tag.objects.filter(system=True).count()))
    print('Done with {} in {} seconds...'.format(
        sys._getframe().f_code.co_name,
        (timezone.now() - start).total_seconds()))


def register_nonexistent_models_with_modm():
    """
    There are guids refering to models that no longer exist.
    We can't delete the guids because then they could be regenerated.
    These models are registered so that anything at all will work.
    :return:
    """
    class DropboxFile(StoredFileNode):
        pass

    class OSFStorageGuidFile(StoredFileNode):
        pass

    class OSFGuidFile(StoredFileNode):
        pass

    class GithubGuidFile(StoredFileNode):
        pass

    class NodeFile(StoredFileNode):
        pass

    class BoxFile(StoredFileNode):
        pass

    class FigShareGuidFile(StoredFileNode):
        pass

    class S3GuidFile(StoredFileNode):
        pass

    class DataverseFile(StoredFileNode):
        pass

    DataverseFile.register_collection()
    NodeFile.register_collection()
    S3GuidFile.register_collection()
    FigShareGuidFile.register_collection()
    BoxFile.register_collection()
    GithubGuidFile.register_collection()
    OSFStorageGuidFile.register_collection()
    OSFGuidFile.register_collection()
    DropboxFile.register_collection()


def merge_duplicate_users():
    print('Starting {}...'.format(sys._getframe().f_code.co_name))
    start = timezone.now()

    from framework.mongo.handlers import database

    duplicates = database.user.aggregate([
        {
            "$group": {
                "_id": "$username",
                "ids": {"$addToSet": "$_id"},
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        },
        {
            "$sort": {
                "count": -1
            }
        }
    ]).get('result')
    # [
    #   {
    #       'count': 5,
    #       '_id': 'duplicated@username.com',
    #       'ids': [
    #           'listo','fidst','hatma','tchth','euser','name!'
    #       ]
    #   }
    # ]
    print('Found {} duplicate usernames.'.format(len(duplicates)))
    for duplicate in duplicates:
        print('Found {} copies of {}'.format(len(duplicate.get('ids')), duplicate.get('_id')))
        if duplicate.get('_id'):
            # _id is an email address, merge users keeping the one that was logged into last
            users = list(MODMUser.find(MQ('_id', 'in', duplicate.get('ids'))).sort('-last_login'))
            best_match = users.pop()
            for user in users:
                print('Merging user {} into user {}'.format(user._id, best_match._id))
                best_match.merge_user(user)
        else:
            # _id is null, set all usernames to their guid
            users = MODMUser.find(MQ('_id', 'in', duplicate.get('ids')))
            for user in users:
                print('Setting username for {}'.format(user._id))
                user.username = user._id
                user.save()
    print('Done with {} in {} seconds...'.format(
        sys._getframe().f_code.co_name,
        (timezone.now() - start).total_seconds()))

class Command(BaseCommand):
    help = 'Migrates data from tokumx to postgres'

    def handle(self, *args, **options):
        # TODO Handle contributors, they're not a direct 1-to-1 they'll need some love

        # it's either this or catch the exception and put them in the blacklistguid table
        register_nonexistent_models_with_modm()

        models = get_ordered_models()
        # guids first, pls
        models.insert(0, models.pop(models.index(Guid)))

        merge_duplicate_users()
        # merged users get blank usernames, running it twice fixes it.
        merge_duplicate_users()

        for django_model in models:
            # TODO REMOVE BLACKLISTGUID FROM THIS LIST
            if issubclass(django_model, AbstractBaseContributor) \
                    or django_model is ApiOAuth2Scope \
                    or django_model is BlackListGuid \
                    or django_model is Session \
                    or django_model is NodeLog \
                    or not hasattr(django_model, 'modm_model_path'):
                continue

            module_path, model_name = django_model.modm_model_path.rsplit('.', 1)
            modm_module = importlib.import_module(module_path)
            modm_model = getattr(modm_module, model_name)
            modm_queryset = modm_model.find(django_model.modm_query)
            page_size = django_model.migration_page_size
            with ipdb.launch_ipdb_on_exception():
                save_bare_models(modm_queryset, django_model, page_size=page_size)

        # Handle system tags, they're on nodes, they need a special migration
        save_bare_system_tags()
