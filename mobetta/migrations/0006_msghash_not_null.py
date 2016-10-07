# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobetta', '0005_populate_msghash'),
    ]

    operations = [
        migrations.AlterField(
            model_name='editlog',
            name='msghash',
            field=models.CharField(max_length=32),
        ),
        migrations.AlterField(
            model_name='messagecomment',
            name='msghash',
            field=models.CharField(max_length=32),
        ),
    ]
