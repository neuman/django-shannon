# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shannon', '0002_media_original_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='extension',
            field=models.CharField(max_length=50, null=True, blank=True),
            preserve_default=True,
        ),
    ]
