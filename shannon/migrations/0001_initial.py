# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import shannon.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('original_file', models.FileField(null=True, upload_to=shannon.models.get_file_path, blank=True)),
                ('internal_file', models.FileField(null=True, upload_to=b'/', blank=True)),
                ('title', models.CharField(max_length=500, null=True, blank=True)),
                ('medium', models.CharField(blank=True, max_length=3, null=True, choices=[(b'TXT', b'Text'), (b'VID', b'Video'), (b'AUD', b'Audio'), (b'IMG', b'Image'), (b'MUL', b'Multimedia'), (b'DAT', b'Data')])),
                ('status', models.CharField(blank=True, max_length=1, null=True, choices=[(b'U', b'Unconverted'), (b'Q', b'In Conversion Queue'), (b'I', b'In Progress'), (b'C', b'Converted'), (b'E', b'Error')])),
                ('blurb', models.TextField(default=b'', null=True, blank=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
