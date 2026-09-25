from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_company_user_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobseekerprofile',
            name='projects',
            field=models.TextField(blank=True),
        ),
    ]
