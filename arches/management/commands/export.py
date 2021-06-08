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
            "number": "TEXT",
            "resource-instance": "TEXT",
            "file-list": "TEXT",
            "concept": "TEXT",
            "concept-list": "TEXT",
            "resource-instance-list": "TEXT",
            "geojson-feature-collection": "TEXT",
            "domain-value": "TEXT",
            "domain-value-list": "TEXT",
            "date": "TEXT",
            "node-value": "TEXT",
            "boolean": "TEXT",
            "edtf": "TEXT",
            "annotation": "TEXT",
            "url": "TEXT",
        }
        graphs = models.GraphModel.objects.exclude(isresource=False).exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
        schema_prefix = "arches_relational"
        pre_sql = ""
        post_sql = """

        """
        dml = """

        """
        constrain = """

        """
        def prepend_parent_names(node, name):
            name = f"{node.name}-{name}"
            if node.nodegroup.parentnodegroup_id is not None:
                prepend_parent_names(models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id), name)
            return name
        for graph in graphs:
            top_node = graph.node_set.get(istopnode=True)
            graph_name_slug = slugify(top_node.name, separator="_", max_length=60)
            schema_name = f"{schema_prefix}_{graph_name_slug}"
            pre_sql += f"""
                DROP SCHEMA IF EXISTS {schema_name} CASCADE;
                CREATE SCHEMA IF NOT EXISTS {schema_name};
                CREATE TABLE {schema_name}.{graph_name_slug} (
                    {graph_name_slug}_id uuid,
                    legacy_id text,
                    PRIMARY KEY({graph_name_slug}_id)
                );
                COMMENT ON TABLE {schema_name}.{graph_name_slug} IS '{graph.pk}';
            """

            resources = models.ResourceInstance.objects.filter(graph_id=graph.pk)
            for resource in resources:
                legacyid = "NULL" if resource.legacyid is None else f"'{resource.legacyid}'"
                dml += f"""
                    INSERT INTO {schema_name}.{graph_name_slug} ({graph_name_slug}_id, legacy_id)
                        VALUES ('{resource.pk}'::uuid, {legacyid});
                """

            nodes = models.Node.objects.filter(graph_id=graph.pk, istopnode=False)
            for node in nodes:
                if node.is_collector:
                    name = node.name
                    if node.nodegroup.parentnodegroup_id is not None:
                        parent_node = models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id)
                        name = prepend_parent_names(parent_node, name)
                    name = slugify(name, separator="_", max_length=60)
                    constrain += f"""
                        ALTER TABLE {schema_name}.{name}
                            ADD CONSTRAINT {graph_name_slug}_fk FOREIGN KEY ({graph_name_slug}_id)
                            REFERENCES {schema_name}.{graph_name_slug} ({graph_name_slug}_id);
                    """
                    pre_sql += f"""
                        CREATE TABLE {schema_name}.{name} (
                            {name}_id uuid,
                            {graph_name_slug}_id uuid,
                            PRIMARY KEY({name}_id)
                        );
                        COMMENT ON TABLE {schema_name}.{name} IS '{node.pk}';
                    """
                    tiles = models.TileModel.objects.filter(nodegroup_id=node.pk)
                    for tile in tiles:
                        dml += f"""
                            INSERT INTO {schema_name}.{name} ({name}_id, {graph_name_slug}_id)
                            VALUES ('{tile.pk}'::uuid, '{tile.resourceinstance_id}'::uuid);
                        """
                    for member_node in node.nodegroup.node_set.all():
                        if member_node.datatype in datatype_map:
                            member_node_name = slugify(member_node.name, separator="_", max_length=60)
                            datatype = datatype_map[member_node.datatype]
                            post_sql += f"""
                                ALTER TABLE {schema_name}.{name}
                                    ADD COLUMN {member_node_name} {datatype};
                                COMMENT ON COLUMN {schema_name}.{name}.{member_node_name} IS '{member_node.pk}';
                            """
                            for tile in tiles:
                                value = tile.data[str(member_node.pk)]
                                # if datatype = "geojson-feature-collection"
                                dml += f"""
                                    UPDATE {schema_name}.{name} SET {member_node_name} = '{value}'
                                        WHERE {name}_id = '{tile.pk}'::uuid;
                                """
                    if node.nodegroup.parentnodegroup_id is not None:
                        parent_node = models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id)
                        parent_name = parent_node.name
                        if parent_node.nodegroup.parentnodegroup_id is not None:
                            parent_name = prepend_parent_names(models.Node.objects.get(pk=parent_node.nodegroup.parentnodegroup_id), parent_name)
                        parent_name = slugify(parent_name, separator="_", max_length=60)
                        post_sql += f"""
                            ALTER TABLE {schema_name}.{name}
                                ADD COLUMN {parent_name}_id uuid;
                        """
                        for tile in tiles:
                            dml += f"""
                                UPDATE {schema_name}.{name} SET {parent_name}_id = '{tile.parenttile_id}'::uuid
                                    WHERE {name}_id = '{tile.pk}'::uuid;
                            """
                        constrain += f"""
                            ALTER TABLE {schema_name}.{name}
                                ADD CONSTRAINT {parent_name}_fk FOREIGN KEY ({parent_name}_id)
                                REFERENCES {schema_name}.{parent_name} ({parent_name}_id);
                        """
        print(pre_sql + post_sql + dml + constrain)

