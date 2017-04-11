# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-21 04:33
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('icu', '0003_auto_20170411_0919'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('msgid', models.CharField(max_length=256)),
                ('msghash', models.CharField(max_length=32)),
                ('fieldname', models.CharField(max_length=127)),
                ('old_value', models.CharField(blank=True, max_length=255, null=True)),
                ('new_value', models.CharField(blank=True, max_length=255, null=True)),
                ('file_edited', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='edit_logs', to='icu.ICUTranslationFile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='icu_editlogs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MessageComment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('msghash', models.CharField(max_length=32)),
                ('body', models.CharField(max_length=1024)),
                ('translation_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='icu.ICUTranslationFile')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='icu_messagecomments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['created'],
                'abstract': False,
            },
        ),
    ]
