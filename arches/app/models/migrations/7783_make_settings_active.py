import datetime
import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("models", "8085_relational_data_model_handle_dates"),
    ]

    operations = [
        migrations.RunSQL(
            """
            UPDATE graphs set isactive = true where graphid = 'ff623370-fa12-11e6-b98b-6c4008b05c4c'
            """,
            """
            UPDATE graphs set isactive = false where graphid = 'ff623370-fa12-11e6-b98b-6c4008b05c4c'
            """,
        ),
    ]
