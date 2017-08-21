# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-11 18:42
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('quizzes', '0007_auto_20170810_1627'),
    ]

    operations = [
        migrations.CreateModel(
            name='Evaluation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('out_of', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='StudentMark',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField(blank=True, null=True)),
                ('evaluation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quizzes.Evaluation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='marks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__username', 'evaluation'],
            },
        ),
    ]