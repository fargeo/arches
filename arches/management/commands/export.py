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
        datatype_map = {
            "string": "TEXT",
            "number": "NUMERIC",
            "resource-instance": "TEXT",
            "file-list": "TEXT",
            "concept": "TEXT",
            "concept-list": "TEXT",
            "resource-instance-list": "TEXT",
            "geojson-feature-collection": "GEOMETRY",
            "domain-value": "TEXT",
            "domain-value-list": "TEXT",
            "date": "timestamp",
            "node-value": "TEXT",
            "boolean": "TEXT",
            "edtf": "TEXT",
            "annotation": "TEXT",
            "url": "TEXT",
        }
        graphs = models.GraphModel.objects.exclude(isresource=False).exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
        schema_name = "arches_relational"
        pre_sql = """
        DROP SCHEMA IF EXISTS %(schema_name)s CASCADE;
        CREATE SCHEMA IF NOT EXISTS %(schema_name)s;
        """ % {'schema_name': schema_name}
        post_sql = """

        """
        def prepend_parent_names(node, name):
            name = "%s-%s" % (node.name, name)
            if node.nodegroup.parentnodegroup is not None:
                prepend_parent_names(models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id), name)
            return name
        for graph in graphs:
            top_node = graph.node_set.get(istopnode=True)
            graph_name_slug = slugify(top_node.name, separator="_")
            pre_sql += """
                CREATE TABLE %(schema_name)s.%(name)s (
                    %(name)s_id uuid,
                    legacy_id text,
                    PRIMARY KEY(%(name)s_id)
                );
                COMMENT ON TABLE %(schema_name)s.%(name)s IS '%(id)s';
            """ % {
                'schema_name': schema_name,
                'name': graph_name_slug,
                'id': graph.pk
            }

            nodes = models.Node.objects.filter(graph_id=graph.pk, istopnode=False)
            for node in nodes:
                if node.is_collector:
                    name = node.name
                    if node.nodegroup.parentnodegroup is not None:
                        parent_node = models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id)
                        name = prepend_parent_names(parent_node, name)
                    name = "%(graph_name)s-%(node_name)s" % {
                        'node_name': name,
                        'graph_name': graph.name
                    }
                    post_sql += """
                        ALTER TABLE %(schema_name)s.%(node_name)s
                            ADD CONSTRAINT %(parent_name)s_fk FOREIGN KEY (%(parent_name)s_id)
                            REFERENCES %(schema_name)s.%(parent_name)s (%(parent_name)s_id);
                    """ % {
                        'schema_name': schema_name,
                        'node_name': slugify(name, separator="_"),
                        'parent_name': graph_name_slug
                    }
                    pre_sql += """
                        CREATE TABLE %(schema_name)s.%(node_name)s (
                            %(node_name)s_id uuid,
                            %(graph_name)s_id uuid,
                            PRIMARY KEY(%(node_name)s_id)
                        );
                        COMMENT ON TABLE %(schema_name)s.%(node_name)s IS '%(node_id)s';
                    """ % {
                        'schema_name': schema_name,
                        'node_name': slugify(name, separator="_"),
                        'node_id': node.pk,
                        'graph_name': graph_name_slug
                    }
                    for member_node in node.nodegroup.node_set.all():
                        if member_node.datatype in datatype_map:
                            post_sql += """
                                ALTER TABLE %(schema_name)s.%(node_name)s
                                    ADD COLUMN %(member_node_name)s %(datatype)s;
                                COMMENT ON COLUMN %(schema_name)s.%(node_name)s.%(member_node_name)s IS '%(member_node_id)s';
                            """ % {
                                'schema_name': schema_name,
                                'node_name': slugify(name, separator="_"),
                                'member_node_name': slugify(member_node.name, separator="_"),
                                'member_node_id': member_node.pk,
                                'datatype': datatype_map[member_node.datatype]
                            }
                    if node.nodegroup.parentnodegroup is not None:
                        parent_node = models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id)
                        parent_name = parent_node.name
                        if parent_node.nodegroup.parentnodegroup is not None:
                            parent_name = prepend_parent_names(models.Node.objects.get(pk=parent_node.nodegroup.parentnodegroup_id), parent_name)
                        parent_name = "%(graph_name)s-%(parent_name)s" % {
                            'parent_name': parent_name,
                            'graph_name': graph.name
                        }
                        post_sql += """
                            ALTER TABLE %(schema_name)s.%(node_name)s
                                ADD COLUMN %(parent_name)s_id uuid;
                            ALTER TABLE %(schema_name)s.%(node_name)s
                                ADD CONSTRAINT %(parent_name)s_fk FOREIGN KEY (%(parent_name)s_id)
                                REFERENCES %(schema_name)s.%(parent_name)s (%(parent_name)s_id);
                        """ % {
                            'schema_name': schema_name,
                            'node_name': slugify(name, separator="_"),
                            'parent_name': slugify(parent_name, separator="_"),
                        }
        print(pre_sql + post_sql)

