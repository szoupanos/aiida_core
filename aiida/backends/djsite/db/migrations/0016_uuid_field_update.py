# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-12 15:28
from __future__ import unicode_literals
from __future__ import absolute_import
from django.db import migrations, models

import aiida.common.utils

REVISION = '1.0.16'
DOWN_REVISION = '1.0.15'


class Migration(migrations.Migration):

    dependencies = [
        ('db', '0015_invalidating_node_hash'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbcomment',
            name='uuid',
            field=models.UUIDField(default=aiida.common.utils.get_new_uuid),
        ),
        migrations.AlterField(
            model_name='dbcomputer',
            name='uuid',
            field=models.UUIDField(default=aiida.common.utils.get_new_uuid),
        ),
        migrations.AlterField(
            model_name='dbgroup',
            name='uuid',
            field=models.UUIDField(default=aiida.common.utils.get_new_uuid),
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='email',
            field=models.EmailField(db_index=True, max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='dbuser',
            name='groups',
            field=models.ManyToManyField(
                blank=True,
                help_text=
                'The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                related_name='user_set',
                related_query_name='user',
                to='auth.Group',
                verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='dbworkflow',
            name='uuid',
            field=models.UUIDField(default=aiida.common.utils.get_new_uuid),
        ),
    ]
