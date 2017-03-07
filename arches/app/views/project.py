'''
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import uuid
from django.views.generic import View, TemplateView
from django.http import HttpResponseNotFound, QueryDict, HttpResponse
from arches.app.utils.JSONResponse import JSONResponse
from arches.app.models import models
from arches.app.models.graph import Graph
from arches.app.models.card import Card
from arches.app.utils.betterJSONSerializer import JSONSerializer, JSONDeserializer
from collections import OrderedDict
from operator import itemgetter

class MobileProjectView(View):

    def get(self, request, mobileprojectid):
        from pprint import pprint as pp
        f = JSONSerializer().serializeToPython(Graph.objects.filter(graphid=uuid.UUID(mobileprojectid)))

        payload = {}

        payload['mobileprojectid']=[]
        resource_models = []

        resource_model = {}
        for graph in f:
            for card in graph['cards']:
                card['widgets'] = []
                card['widgets'] + list(models.CardXNodeXWidget.objects.filter(card_id=card['cardid']))
                if len(card['widgets']) == 0:
                    nodes = models.Node.objects.filter(nodegroup=card['nodegroup_id'])
                    # child_nodes, child_edges = nodes[0].get_child_nodes_and_edges()
                    for node in nodes:
                        widget = models.DDataType.objects.get(pk=node.datatype).defaultwidget
                        if widget:
                            widget_model = models.CardXNodeXWidget()
                            widget_model.node_id = node.nodeid
                            widget_model.card_id = card['cardid']
                            widget_model.widget_id = widget.pk
                            widget_model.config = widget.defaultconfig
                            widget_model.label = node.name
                            card['widgets'].append(widget_model)
            resource_model['graphid'] = graph['graphid']
            resource_model['subtitle'] = graph['subtitle']
            resource_model['name'] = graph['name']
            resource_model['cards'] = graph['cards']

            values = {}
            domains = []

            def get_values(concept, values):
                for subconcept in concept.subconcepts:
                    for value in subconcept.values:
                        values[value.id] = value.value
                    get_values(subconcept, values)
                return values

            for node in graph['nodes']:
                print node['name']
                if node['datatype'] in ['concept', 'concept-list', 'domain-value', 'domain-value-list']:
                    if node['datatype'] in ['concept', 'concept-list']:
                        if node['config'] != None:
                            rdmCollection = node['config']['rdmCollection']
                        try:
                            concept = models.Concept().get(rdmCollection, include_subconcepts=True, semantic=False)
                            rdmCollectionLabel = concept.get_preflabel.value
                            collevtion_values = {}
                            concepts = OrderedDict(sorted(get_values(concept, collection_values).items(), key=itemgetter(1)))
                            values[rdmCollectionLabel] = concepts
                        except:
                            pass
                    elif node['datatype'] in ['domain-value', 'domain-value-list']:
                        concepts = {}
                        if node['config']['options']:
                            for concept in node['config']['options']:
                                concepts[concept['id']] = concept['text']

                        values[node['name']] = OrderedDict(sorted(concepts.items(), key=itemgetter(1)))

                domains.append(values)


            resource_model['domains'] = domains

            resource_models.append(resource_model)
        f = JSONSerializer().serialize(resource_models, indent = 4)

        # f = JSONSerializer().serialize(f, indent=4)


        response = JSONResponse(f, content_type='json/plain')
        response['Content-Disposition'] = 'inline';
        return response
