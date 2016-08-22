# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mobetta', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('msgid', models.CharField(max_length=127)),
                ('fieldname', models.CharField(max_length=127)),
                ('old_value', models.CharField(max_length=255, null=True, blank=True)),
                ('new_value', models.CharField(max_length=255, null=True, blank=True)),
                ('file_edited', models.ForeignKey(related_name='edit_logs', to='mobetta.TranslationFile')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created'],
            },
        ),
    ]
