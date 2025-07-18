# Generated by Django 5.1.4 on 2025-07-17 20:03

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('client', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='accountant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='clientfinancialyear',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.client'),
        ),
        migrations.AddField(
            model_name='clientservice',
            name='client',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_services', to='client.client'),
        ),
        migrations.AddField(
            model_name='client',
            name='client_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='client.clienttype'),
        ),
        migrations.AddField(
            model_name='clientfinancialyear',
            name='financial_year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.financialyear'),
        ),
        migrations.AddField(
            model_name='client',
            name='financial_years',
            field=models.ManyToManyField(related_name='clients', through='client.ClientFinancialYear', to='client.financialyear'),
        ),
        migrations.AddField(
            model_name='client',
            name='first_financial_year',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='first_fin_year', to='client.financialyear'),
        ),
        migrations.AddField(
            model_name='financialyearsetup',
            name='client_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.clienttype'),
        ),
        migrations.AddField(
            model_name='financialyearsetup',
            name='financial_year',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='client.financialyear'),
        ),
        migrations.AddField(
            model_name='client',
            name='first_month_for_coida_sub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='coida_clients', to='client.month'),
        ),
        migrations.AddField(
            model_name='client',
            name='first_month_for_paye_sub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paye_clients', to='client.month'),
        ),
        migrations.AddField(
            model_name='client',
            name='first_month_for_vat_sub',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='vat_clients', to='client.month'),
        ),
        migrations.AddField(
            model_name='clientservice',
            name='service',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='client_service', to='client.service'),
        ),
        migrations.AddField(
            model_name='client',
            name='client_service',
            field=models.ManyToManyField(related_name='client_services', through='client.ClientService', to='client.service'),
        ),
        migrations.AddField(
            model_name='client',
            name='vat_category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='client.vatcategory'),
        ),
        migrations.AddField(
            model_name='vatsubmissionhistory',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vat_client', to='client.client'),
        ),
        migrations.AddField(
            model_name='vatsubmissionhistory',
            name='marked_notified_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='marked_notified', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vatsubmissionhistory',
            name='marked_paid_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='marked_paid', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vatsubmissionhistory',
            name='marked_submitted_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='marked_submitted', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vatsubmissionhistory',
            name='month',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.month'),
        ),
        migrations.AddField(
            model_name='vatsubmissionhistory',
            name='year',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client.financialyear'),
        ),
        migrations.AlterUniqueTogether(
            name='clientfinancialyear',
            unique_together={('client', 'financial_year')},
        ),
        migrations.AlterUniqueTogether(
            name='financialyearsetup',
            unique_together={('financial_year', 'client_type')},
        ),
        migrations.AlterUniqueTogether(
            name='clientservice',
            unique_together={('client', 'service')},
        ),
        migrations.AlterUniqueTogether(
            name='vatsubmissionhistory',
            unique_together={('client', 'year', 'month')},
        ),
    ]
