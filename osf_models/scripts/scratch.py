from __future__ import print_function
from __future__ import unicode_literals

import inspect
from collections import OrderedDict
from collections import deque

from django.apps import apps
from osf_models import models
from osf_models.models import Node
from osf_models.utils.order_apps import sort_dependencies

# def get_ordered_models():
#     all_models = apps.all_models
#     model_mapping = OrderedDict()
#
#     for app_label, model_tuples in all_models.iteritems():
#         if app_label != 'osf_models':
#             continue
#         for model_name, model_class in model_tuples.iteritems():
#             if app_label not in model_mapping.keys():
#                 model_mapping[app_label] = []
#             model_mapping[app_label].append(model_class)
#
#     ordered_list_of_models = sort_dependencies(model_mapping)
#     osf_models = apps.get_app_config('osf_models').get_models(include_auto_created=False)
#
#     return [model for model in ordered_list_of_models if model in osf_models]

def depth_first_sort(graph, start):
    visited, stack = set(), [start]
    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.add(vertex)
            stack.extend(graph[vertex] - visited)
    return visited


def get_dependencies(app_label, model):
    # Add any explicitly defined dependencies
    if hasattr(model, 'natural_key'):
        deps = getattr(model.natural_key, 'dependencies', [])
        print('{} has {} dependencies'.format(model, deps))
        if deps:
            deps = [apps.get_model(*dep.split('.')) for dep in deps]
    else:
        deps = []

    # Now add a dependency for any FK relation with a model that
    # defines a natural key
    for field in model._meta.fields:
        if hasattr(field.rel, 'to'):
            rel_model = field.rel.to
            if hasattr(rel_model, 'natural_key') and rel_model != model:
                deps.append(rel_model)
                print('{} has {} fk dependencies'.format(model, rel_model))
    # Also add a dependency for any simple M2M relation with a model
    # that defines a natural key.  M2M relations with explicit through
    # models don't count as dependencies.
    for field in model._meta.many_to_many:
        if field.rel.through._meta.auto_created:
            rel_model = field.rel.to
            if hasattr(rel_model, 'natural_key') and rel_model != model:
                deps.append(rel_model)
                print('{} has {} m2m dependencies'.format(model, rel_model))
    return set(deps)


def get_ordered_models():
    # models = apps.get_app_config(app_label).get_models(include_auto_created=False)
    models = apps.get_models()
    # import ipdb
    # ipdb.set_trace()
    mapping = {}
    dependencies = deque()
    for model in models:
        mapping[model] = get_dependencies(model._meta.app_label, model)
        model_dependencies = depth_first_sort(mapping, model)
        for mdp in model_dependencies:
            if mdp not in dependencies:
                dependencies.append(mdp)
    return dependencies

#
#
# def get_ordered_models():
#     classes = set([tup[1] for tup in inspect.getmembers(models) if isinstance(tup[1], type)])
#     all_models = set(apps.get_models())
#     relationship_map = {}
#
#     for model in all_models:
#         # relationship_map[model] = set([getattr(field, 'through', field.related_model)
#         #                                for field_name, field in
#         #                                model._meta._forward_fields_map.iteritems()
#         #                                if field.related_model is not model and
#         #                                field.related_model is not None])
#
#         fields = model._meta.fields_map
#         fields.update(model._meta._forward_fields_map)
#         rel_fields = {fname: fvalue for fname, fvalue in fields.iteritems() if fvalue.is_relation and not fname.endswith('_id')}
#         rel_models = [getattr(fvalue, 'through', fvalue.related_model) for fname, fvalue in rel_fields.iteritems() if fvalue.related_model is not model and fvalue.related_model is not None]
#         relationship_map[model] = classes.intersection(rel_models)
#
#     import ipdb
#
#     ipdb.set_trace()
#
#     model_set = depth_first_sort(relationship_map, Node)
#     return classes.intersection(model_set)

# def get_ordered_models():
#     classes = set([tup[1] for tup in inspect.getmembers(models) if isinstance(tup[1], type)])
#     all_models = set(apps.get_models())
#     app_models = classes.intersection(all_models)
#
#     visited = deque()
#     relationship_map = {}
#
#     for model in app_models:
#         relationship_map[model] = set([getattr(field, 'through', field.related_model)
#                                        for field_name, field in
#                                        model._meta._forward_fields_map.iteritems()
#                                        if field.related_model is not model and
#                                        field.related_model is not None])
#
#     def descend(model, relationships):
#         if model in visited:
#             return
#         for rel in relationships:
#             if rel in visited:
#                 continue
#             if rel in relationship_map.keys():
#                 descend(rel, relationship_map[rel])
#
#     for model, relationships in relationship_map.iteritems():
#         descend(model, relationships)

#
#
# def get_ordered_models():
#     classes = set([tup[1] for tup in inspect.getmembers(models) if isinstance(tup[1], type)])
#     all_models = set(apps.get_models())
#     app_models = classes.intersection(all_models)
#
#     Q = deque()
#     T = list()
#     relationship_map = {}
#
#     for model in app_models:
#         relationship_map[model] = set([getattr(field, 'through', field.related_model)
#                                        for field_name, field in
#                                        model._meta._forward_fields_map.iteritems()
#                                        if field.related_model is not model and
#                                        field.related_model is not None])
#
#     while relationship_map:
#         acyclic = False
#         for node, edges in tuple(relationship_map.iteritems()):
#             for edge in edges:
#                 if edge in relationship_map:
#                     break
#                 else:
#                     acyclic = True
#                     del relationship_map[node]
#                     Q.append(node)
#         if not acyclic:
#             raise RuntimeError('Cycled')
#     return Q
#
#
#
#     print('Queue: {}'.format(Q))
#     print('Topological Sorted: {}'.format(T))
#
#
#
#
# def get_model_topology():
#     classes = set([tup[1] for tup in inspect.getmembers(models) if isinstance(tup[1], type)])
#     all_models = set(apps.get_models())
#     app_models = classes.intersection(all_models)
#
#     relationship_map = {}
#     topology = list()
#     for model in app_models:
#         relationship_map[model] = set([getattr(field, 'through', field.related_model)
#                                for field_name, field in
#                                model._meta._forward_fields_map.iteritems()
#                                if field.related_model is not model and
#                                field.related_model is not None])
#
#     level = 0
#     while relationship_map:
#         level += 1
#         print('{}'.format('+'*level))
#         print('Topology: {}'.format(topology))
#         for model, relationships in tuple(relationship_map.iteritems()):
#             # discard self referential relationships
#             relationships.discard(model)
#             # remove relationships that are already in the topology list
#             relationship_map[model] = relationships - set(topology)
#             # if all the relationships are gone
#             if len(relationships) < 1:
#                 print('Removed {}'.format(model))
#                 # add the model to the topology
#                 topology.append(model)
#                 # remove the model from the relationship_map
#                 del relationship_map[model]
#             else:
#                 print('Relationships: {}'.format(relationships))
#
