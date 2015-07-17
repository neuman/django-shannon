# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shannon', '0003_media_extension'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='media',
            name='extension',
        ),
        migrations.AddField(
            model_name='media',
            name='assumed_extension',
            field=models.CharField(default=b'', max_length=50),
            preserve_default=True,
        ),
    ]
