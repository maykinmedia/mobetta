# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TranslationFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=512)),
                ('filepath', models.CharField(max_length=1024)),
                ('language_code', models.CharField(max_length=32)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
