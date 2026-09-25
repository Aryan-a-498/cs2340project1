import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_company_user_company'),
        ('jobs', '0005_jobposting_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='job_postings', to='accounts.company'),
        ),
    ]
