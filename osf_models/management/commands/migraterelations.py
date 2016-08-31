import importlib

import ipdb
from django.core.management import BaseCommand
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
        lookups.update({x[lookup_string]: x['pk'] for x in model.objects.all().values(lookup_string, 'pk')})

    # add the "special" ones
    lookups.update(
        {u'{}:not_system'.format(x['name']): x['pk'] for x in Tag.objects.filter(system=False).values('name', 'pk')})
    lookups.update(
        {u'{}:system'.format(x['name']): x['pk'] for x in Tag.objects.filter(system=True).values('name', 'pk')})
    lookups.update({'_id': x['pk'] for x in CitationStyle.objects.all().values('_id', 'pk')})
    lookups.update({'_id': x['pk'] for x in NotificationSubscription.objects.all().values('_id', 'pk')})
    return lookups


def save_fk_relationships(modm_queryset, django_model, page_size):
    pass


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
                save_fk_relationships(modm_queryset, django_model, page_size)
