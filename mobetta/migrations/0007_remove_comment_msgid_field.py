# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobetta', '0006_msghash_not_null'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='messagecomment',
            name='msgid',
        ),
        migrations.AlterField(
            model_name='editlog',
            name='msgid',
            field=models.CharField(max_length=256),
        ),
    ]
