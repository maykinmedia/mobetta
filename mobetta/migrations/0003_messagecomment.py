# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mobetta', '0002_editlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('msgid', models.CharField(max_length=127)),
                ('body', models.CharField(max_length=1024)),
                ('translation_file', models.ForeignKey(related_name='comments', to='mobetta.TranslationFile')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
    ]
