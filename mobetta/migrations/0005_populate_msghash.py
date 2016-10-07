# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from mobetta.util import get_hash_from_msgid_context


def populate_msghash_from_msgid(apps, schema_editor):
    EditLog = apps.get_model("mobetta", "EditLog")

    for log in EditLog.objects.all():
        log.msghash = get_hash_from_msgid_context(log.msgid, '')
        log.save()

    MessageComment = apps.get_model("mobetta", "MessageComment")

    for comment in MessageComment.objects.all():
        comment.msghash = get_hash_from_msgid_context(comment.msgid, '')
        comment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mobetta', '0004_add_msghash_fields'),
    ]

    operations = [
        migrations.RunPython(populate_msghash_from_msgid)
    ]
