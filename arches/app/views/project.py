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

    def get(self, request):
        graph_ids = [uuid.UUID('ccbd1537-ac5e-11e6-84a5-026d961c88e6'), uuid.UUID('3caf329f-b8f7-11e6-84a5-026d961c88e6')]
        f = JSONSerializer().serializeToPython(Graph.objects.filter(graphid__in=graph_ids))
        project = models.FieldProject()
        project.name = 'City of Z'
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
            resource_model['nodes'] = graph['nodes']
            resource_model['cards'] = graph['cards']

            values = {}
            domains = []

            resource_models.append(resource_model)

        widgets = models.Widget.objects.all()
        widget_details = [{'name': widget.name, 'component': widget.component, 'template': widget.template, 'id':widget.widgetid} for widget in widgets]
        config = {
            'resource_models': resource_models,
            'widget_details': widget_details,
        }
        project.config = config
        projects = [project]
        f = JSONSerializer().serialize(projects, indent = 4)
        # f = JSONSerializer().serialize(f, indent=4)
        response = JSONResponse(f, content_type='json/plain')
        response['Content-Disposition'] = 'inline';
        return response
