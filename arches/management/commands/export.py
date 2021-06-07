"""
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
"""

import os
import subprocess
from arches.app.models.system_settings import settings
from arches.app.models import models
from arches.management.commands import utils
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from slugify import slugify


class Command(BaseCommand):
    """
    Commands for exporting Arches objects

    """

    def add_arguments(self, parser):
        parser.add_argument("operation", nargs="?")

        parser.add_argument("-d", "--dest", action="store", dest="dest", default="", help="The destination directory of the output")

        parser.add_argument("-t", "--table", action="store", dest="table", default="", help="The table to be exported")

        parser.add_argument("-n", "--name", action="store", dest="name", default="", help="The name of destination file")

    def handle(self, *args, **options):
        if options["operation"] == "shp":
            self.shapefile(dest=options["dest"], table=options["table"])
        if options["operation"] == "schema":
            self.create_relational_schema()

    def shapefile(self, dest, table):
        geometry_types = {
            "linestring": ("'ST_MultiLineString'", "'ST_LineString'"),
            "point": ("'ST_Point'", "'ST_MultiPoint'"),
            "polygon": ("'ST_MultiPolygon'", "'ST_Polygon'"),
        }

        if os.path.exists(dest) == False:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM {0}".format(table))
                row = cursor.fetchall()
                db = settings.DATABASES["default"]
                if len(row) > 0:
                    os.mkdir(dest)
                    for geom_type, st_type in geometry_types.items():
                        cursor.execute("SELECT count(*) FROM {0} WHERE geom_type IN ({1})".format(table, ",".join(st_type)))
                        if cursor.fetchone()[0] > 0:
                            cmd = "pgsql2shp -f {0}/{1} -P {2} -u {3} -g geom {4}".format(
                                dest, geom_type, db["PASSWORD"], db["USER"], db["NAME"]
                            )
                            cmd_process = cmd.split()
                            sql = "select * from {0} where geom_type in ({1});".format(table, ",".join(st_type))
                            cmd_process.append(sql)
                            subprocess.call(cmd_process)
                else:
                    print("No records in table for export")
        else:
            print("Cannot export data. Destination directory, {0} already exists".format(dest))

    def create_relational_schema(self):
        graphs = models.GraphModel.objects.exclude(isresource=False).exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
        sql = ''
        def prepend_parent_names(node, name):
            name = "%s-%s" % (node.name, name)
            if node.nodegroup.parentnodegroup is not None:
                prepend_parent_names(models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id), name)
            return name
        for graph in graphs:
            graph_name_slug = slugify(graph.name, separator="_")
            sql += """
                CREATE TABLE %(name)s (
                    %(name)s_id uuid,
                    legacy_id text,
                    PRIMARY KEY(%(name)s_id)
                );
            """ % {'name': graph_name_slug}
            nodes = models.Node.objects.filter(graph_id=graph.pk, istopnode=False)
            for node in nodes:
                if node.is_collector:
                    name = node.name
                    if node.nodegroup.parentnodegroup is not None:
                        name = prepend_parent_names(models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id), name)
                    name = "%(node_name)s-%(graph_name)s" % {
                        'node_name': name,
                        'graph_name': graph.name
                    }
                    sql += """
                        CREATE TABLE %(node_name)s (
                            %(node_name)s_id uuid,
                            %(graph_name)s_id uuid,
                            PRIMARY KEY(%(node_name)s_id),
                            CONSTRAINT fk_%(graph_name)s
                                FOREIGN KEY(%(graph_name)s_id)
                                REFERENCES %(graph_name)s(%(graph_name)s_id)
                        );
                    """ % {
                        'node_name': slugify(name, separator="_"),
                        'graph_name': graph_name_slug
                    }
        print(sql)
