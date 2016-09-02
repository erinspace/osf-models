import importlib

import gc
import ipdb
import sys
from django.core.management import BaseCommand
from django.db import transaction
from django.utils import timezone
from osf_models.models import ApiOAuth2Scope
from osf_models.models import BlackListGuid
from osf_models.models import CitationStyle
from osf_models.models import Guid
from osf_models.models import NotificationSubscription
from osf_models.models import RecentlyAddedContributor
from osf_models.models import Tag
from osf_models.models.contributor import InstitutionalContributor, Contributor, AbstractBaseContributor
from osf_models.utils.order_apps import get_ordered_models


def build_toku_django_lookup_table_cache():
    models = get_ordered_models()
    # ignored models
    models.pop(models.index(Guid))
    models.pop(models.index(BlackListGuid))
    models.pop(models.index(RecentlyAddedContributor))
    models.pop(models.index(Contributor))
    models.pop(models.index(InstitutionalContributor))

    # "special" models
    models.pop(models.index(Tag))
    models.pop(models.index(CitationStyle))
    models.pop(models.index(NotificationSubscription))

    lookups = {}
    for model in models:
        lookup_string = 'guid__{}'.format(model.primary_identifier_name)
        lookup_dict = {x[lookup_string]: x['pk'] for x in model.objects.all().values(lookup_string, 'pk')}
        print('Got {} guids for {}'.format(len(lookup_dict), model._meta.model.__name__))
        lookups.update(lookup_dict)

    # add the "special" ones
    lookups.update(
        {u'{}:not_system'.format(x['name']): x['pk'] for x in Tag.objects.filter(system=False).values('name', 'pk')})
    lookups.update(
        {u'{}:system'.format(x['name']): x['pk'] for x in Tag.objects.filter(system=True).values('name', 'pk')})
    lookups.update({x['_id']: x['pk'] for x in CitationStyle.objects.all().values('_id', 'pk')})
    lookups.update({x['_id']: x['pk'] for x in NotificationSubscription.objects.all().values('_id', 'pk')})
    return lookups


class Command(BaseCommand):
    help = 'Migrations FK and M2M relationships from tokumx to postgres'
    modm_to_django = None

    def handle(self, *args, **options):
        models = get_ordered_models()
        self.modm_to_django = build_toku_django_lookup_table_cache()

        for django_model in models:
            if issubclass(django_model, AbstractBaseContributor) \
                    or django_model is ApiOAuth2Scope \
                    or not hasattr(django_model, 'modm_model_path'):
                continue

            module_path, model_name = django_model.modm_model_path.rsplit('.', 1)
            modm_module = importlib.import_module(module_path)
            modm_model = getattr(modm_module, model_name)
            modm_queryset = modm_model.find(django_model.modm_query)

            page_size = django_model.migration_page_size

            with ipdb.launch_ipdb_on_exception():
                # self.save_fk_relationships(modm_queryset, django_model, page_size)
                self.save_m2m_relationships(modm_queryset, django_model, page_size)


    def save_fk_relationships(self, modm_queryset, django_model, page_size):
        print('Starting {} on {}...'.format(sys._getframe().f_code.co_name, django_model._meta.model.__name__))

        fk_relations = [(field.attname, field.related_model) for field in django_model._meta.get_fields() if
                        field.is_relation and not field.auto_created and field.many_to_one]

        if len(fk_relations) == 0:
            print('{} doesn\'t have foreign keys.'.format(django_model._meta.model.__name__))
            return
        fk_count = 0
        model_count = 0
        model_total = modm_queryset.count()
        while model_count < model_total:
            with transaction.atomic():
                for modm_obj in modm_queryset.sort('_id')[model_count:model_count + page_size]:
                    django_obj = django_model.objects.get(self.modm_to_django[modm_obj._id])
                    for field_name, model in fk_relations:
                        value = getattr(modm_obj, field_name)
                        if value is None:
                            continue
                        if isinstance(value, basestring):
                            # it's guid as a string
                            setattr(django_obj, '{}_id'.format(field_name), self.modm_to_django[value])
                        else:
                            # let's just assume it's a modm model instance
                            setattr(django_obj, '{}_id'.format(field_name), self.modm_to_django[value._id])
                        fk_count += 1
                    django_obj.save()
                    model_count += 1
                    if model_count % page_size == 0 or model_count == model_total:
                        print('Through {} {}s and {} FKs...'.format(model_count, django_model._meta.model.__name__, fk_count))
                        modm_queryset[0]._cache.clear()
                        modm_queryset[0]._object_cache.clear()
                        print('Took out {} trashes'.format(gc.collect()))

                modm_queryset[0]._cache.clear()
                modm_queryset[0]._object_cache.clear()
                print('Took out {} trashes'.format(gc.collect()))


    def save_m2m_relationships(self, modm_queryset, django_model, page_size):
        print('Starting {} on {}...'.format(sys._getframe().f_code.co_name, django_model._meta.model.__name__))
        m2m_relations = [(field.attname, field.related_model) for field in django_model._meta.get_fields() if
                        field.is_relation and not field.auto_created and field.many_to_many]

        if len(m2m_relations) == 0:
            print('{} doesn\'t have any many to many relationships.'.format(django_model._meta.model.__name__))
            return
        m2m_count = 0
        model_count = 0
        model_total = modm_queryset.count()
        while model_count < model_total:
            with transaction.atomic():
                for modm_obj in modm_queryset.sort('-_id')[model_count:model_count + page_size]:
                    django_obj = django_model.objects.get(self.modm_to_django[modm_obj._id])
                    for field_name, model in m2m_relations:
                        django_pks = []

                        try:
                            attr = getattr(django_obj, field_name)
                        except AttributeError:
                            print('DJANGO: {} doesn\'t have a {} attribute.'.format(django_model._meta.model.__name__, field_name))
                            ipdb.set_trace()

                        try:
                            value = getattr(modm_obj, field_name, [])
                        except AttributeError:
                            print('MODM: {} doesn\'t have a {} attribute.'.format(django_model._meta.model.__name__, field_name))
                            ipdb.set_trace()
                        else:
                            for item in value:
                                if isinstance(item, basestring):
                                    django_pks.append(self.modm_to_django[item])
                                elif type(item) == type:
                                    if hasattr(item, '_id'):
                                        str_value = item._id
                                    else:
                                        # wth is it
                                        ipdb.set_trace()
                                    django_pks.append(self.modm_to_django[str_value])
                        if len(django_pks) > 0:
                            attr.add(*django_pks)
                        m2m_count += len(django_pks)
                    model_count += 1
                    if model_count % page_size == 0 or model_count == model_total:
                        print('Through {} {}s and {} m2m'.format(model_count, django_model._meta.model.__name__, m2m_count))
        print('Done with {} in {} seconds...'.format(sys._getframe().f_code.co_name, (timezone.now())))

