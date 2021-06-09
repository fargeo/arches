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
import textwrap
from arches.app.models.system_settings import settings
from arches.app.models import models
from arches.app.models.concept import Concept, get_preflabel_from_valueid
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
            "concept": "UUID",
            "concept-list": "TEXT",
            "resource-instance-list": "TEXT",
            "geojson-feature-collection": "GEOMETRY",
            "domain-value": "UUID",
            "domain-value-list": "TEXT",
            "date": "TIMESTAMP",
            "node-value": "TEXT",
            "boolean": "BOOLEAN",
            "edtf": "TEXT",
            "annotation": "TEXT",
            "url": "TEXT",
        }
        graphs = models.GraphModel.objects.exclude(isresource=False).exclude(pk=settings.SYSTEM_SETTINGS_RESOURCE_MODEL_ID)
        schema_prefix = "arches_relational"
        pre_sql = textwrap.dedent("""\
        DROP SCHEMA IF EXISTS graph_relational_metadata CASCADE;
        CREATE SCHEMA IF NOT EXISTS graph_relational_metadata;
        CREATE TABLE graph_relational_metadata.graph_relational_metadata (
            graph_model text,
            graph_nodegroup_name text,
            graph_nodegroup_id text,
            graph_is_top_node text,
            graph_node_name text,
            graph_node_id text,
            graph_node_datatype text,
            graph_nodegroup_cardinality text,
            relational_schema text,
            relational_table_name text,
            relational_column_name text,
            relational_column_datatype text
        );
        """)
        post_sql = "\n"
        dml = "\n"
        constrain = "\n"
        def prepend_parent_names(node, name):
            name = f"{node.name}-{name}"
            if node.nodegroup.parentnodegroup_id is not None:
                prepend_parent_names(models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id), name)
            return name
        for graph in graphs:
            top_node = graph.node_set.get(istopnode=True)
            graph_name_slug = slugify(top_node.name, separator="_", max_length=60)
            schema_name = f"{schema_prefix}_{graph_name_slug}"
            pre_sql += textwrap.dedent(f"""
            DROP SCHEMA IF EXISTS {schema_name} CASCADE;
            CREATE SCHEMA IF NOT EXISTS {schema_name};
            CREATE TABLE {schema_name}.{graph_name_slug} (
                {graph_name_slug}_id uuid,
                legacy_id text,
                PRIMARY KEY({graph_name_slug}_id)
            );
            COMMENT ON TABLE {schema_name}.{graph_name_slug} IS '{graph.pk}';
            """)

            resources = models.ResourceInstance.objects.filter(graph_id=graph.pk)
            for resource in resources:
                legacyid = "NULL" if resource.legacyid is None else f"'{resource.legacyid}'"
                dml += textwrap.dedent(f"""
                INSERT INTO {schema_name}.{graph_name_slug} ({graph_name_slug}_id, legacy_id)
                    VALUES ('{resource.pk}'::uuid, {legacyid});
                """)

            nodes = models.Node.objects.filter(graph_id=graph.pk, istopnode=False)
            for node in nodes:
                if node.is_collector:
                    name = node.name
                    if node.nodegroup.parentnodegroup_id is not None:
                        parent_node = models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id)
                        name = prepend_parent_names(parent_node, name)
                    name = slugify(name, separator="_", max_length=60)
                    constrain += textwrap.dedent(f"""
                    ALTER TABLE {schema_name}.{name}
                        ADD CONSTRAINT {graph_name_slug}_fk FOREIGN KEY ({graph_name_slug}_id)
                        REFERENCES {schema_name}.{graph_name_slug} ({graph_name_slug}_id);
                    """)
                    pre_sql += textwrap.dedent(f"""
                    CREATE TABLE {schema_name}.{name} (
                        {name}_id uuid,
                        {graph_name_slug}_id uuid,
                        PRIMARY KEY({name}_id)
                    );
                    COMMENT ON TABLE {schema_name}.{name} IS '{node.pk}';
                    """)
                    tiles = models.TileModel.objects.filter(nodegroup_id=node.pk)
                    for tile in tiles:
                        dml += textwrap.dedent(f"""
                        INSERT INTO {schema_name}.{name} ({name}_id, {graph_name_slug}_id)
                            VALUES ('{tile.pk}'::uuid, '{tile.resourceinstance_id}'::uuid);
                        """)
                    for member_node in node.nodegroup.node_set.all():
                        if member_node.datatype in datatype_map:
                            member_node_name = slugify(member_node.name, separator="_", max_length=60)
                            datatype = datatype_map[member_node.datatype]
                            post_sql += textwrap.dedent(f"""
                            ALTER TABLE {schema_name}.{name}
                                ADD COLUMN {member_node_name} {datatype};
                            COMMENT ON COLUMN {schema_name}.{name}.{member_node_name} IS '{member_node.pk}';

                            INSERT into graph_relational_metadata.graph_relational_metadata (
                                graph_model,
                                graph_nodegroup_name,
                                graph_nodegroup_id,
                                graph_node_name,
                                graph_node_id,
                                graph_node_datatype,
                                graph_nodegroup_cardinality,
                                relational_schema,
                                relational_table_name,
                                relational_column_name,
                                relational_column_datatype
                            ) VALUES (
                                '{top_node.name}',
                                '{node.name}',
                                '{node.pk}',
                                '{member_node.name}',
                                '{member_node.pk}',
                                '{member_node.datatype}',
                                '{node.nodegroup.cardinality}',
                                '{schema_name}',
                                '{name}',
                                '{member_node_name}',
                                '{datatype}'
                            );
                            """)
                            if datatype == "GEOMETRY":
                                post_sql += textwrap.dedent(f"""
                                CREATE INDEX {name}_gix
                                    ON {schema_name}.{name}
                                    USING GIST ({member_node_name});
                                """)
                            options = []
                            if member_node.datatype == "concept":
                                if member_node.config['rdmCollection'] is not None:
                                    options = Concept().get_child_collections_hierarchically(member_node.config['rdmCollection'], offset=0, limit=1000000, query="")
                                    options = [dict(list(zip(["valueto", "depth", "collector"], d))) for d in options]
                                    options = [
                                        dict(list(zip(["id", "text", "conceptid", "language", "type"], d["valueto"].values())), depth=d["depth"], collector=d["collector"])
                                        for d in options
                                    ]
                            if member_node.datatype == "domain-value":
                                options = member_node.config["options"]
                            if member_node.datatype in ["concept", "domain-value"]:
                                domain_table_name = f"d_{node.name}_{member_node_name}"
                                domain_table_name = slugify(domain_table_name, separator="_", max_length=60)
                                pre_sql += textwrap.dedent(f"""
                                CREATE TABLE {schema_name}.{domain_table_name} (
                                    id uuid,
                                    label text,
                                    PRIMARY KEY(id)
                                );
                                """)
                                constrain += textwrap.dedent(f"""
                                ALTER TABLE {schema_name}.{name}
                                    ADD CONSTRAINT {member_node_name}_fk FOREIGN KEY ({member_node_name})
                                    REFERENCES {schema_name}.{domain_table_name} (id);
                                """)
                                for option in options:
                                    domain_id = option['id']
                                    domain_label = option['text']
                                    dml += textwrap.dedent(f"""
                                    INSERT INTO {schema_name}.{domain_table_name} (id, label)
                                        VALUES ('{domain_id}'::uuid, '{domain_label}');
                                    """)

                            for tile in tiles:
                                value = tile.data[str(member_node.pk)]
                                if value is not None:
                                    if datatype == "GEOMETRY":
                                        value = str(value).replace("'", "\"")
                                        value = textwrap.dedent(f"""(
                                            SELECT ST_Collect(ST_GeomFromGeoJSON(feat->>'geometry'))
                                            FROM (
                                                SELECT json_array_elements('{value}'::json->'features') AS feat
                                            ) as f
                                        )""")
                                    elif datatype == "TIMESTAMP":
                                        if value is None:
                                            value = "NULL"
                                        else:
                                            value = str(value)
                                            value = f"'{value}'::timestamp"
                                    elif member_node.datatype in ["concept", "domain-value"]:
                                        value = f"'{value}'::{datatype}"
                                    else:
                                        value = str(value).replace("'", "''")
                                        value = f"'{value}'::{datatype}"
                                    dml += textwrap.dedent(f"""
                                    UPDATE {schema_name}.{name} SET {member_node_name} = {value}
                                        WHERE {name}_id = '{tile.pk}'::uuid;
                                    """)
                    if node.nodegroup.parentnodegroup_id is not None:
                        parent_node = models.Node.objects.get(pk=node.nodegroup.parentnodegroup_id)
                        parent_name = parent_node.name
                        if parent_node.nodegroup.parentnodegroup_id is not None:
                            parent_name = prepend_parent_names(models.Node.objects.get(pk=parent_node.nodegroup.parentnodegroup_id), parent_name)
                        parent_name = slugify(parent_name, separator="_", max_length=60)
                        post_sql += textwrap.dedent(f"""
                        ALTER TABLE {schema_name}.{name}
                            ADD COLUMN {parent_name}_id uuid;
                        """)
                        for tile in tiles:
                            dml += textwrap.dedent(f"""
                            UPDATE {schema_name}.{name} SET {parent_name}_id = '{tile.parenttile_id}'::uuid
                                WHERE {name}_id = '{tile.pk}'::uuid;
                            """)
                        constrain += textwrap.dedent(f"""
                        ALTER TABLE {schema_name}.{name}
                            ADD CONSTRAINT {parent_name}_fk FOREIGN KEY ({parent_name}_id)
                            REFERENCES {schema_name}.{parent_name} ({parent_name}_id);
                        """)
        sql = pre_sql + post_sql + dml + constrain
        print(sql)

