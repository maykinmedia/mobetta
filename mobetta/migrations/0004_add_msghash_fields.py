# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobetta', '0003_messagecomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='editlog',
            name='msghash',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='messagecomment',
            name='msghash',
            field=models.CharField(max_length=32, null=True),
        ),
    ]
