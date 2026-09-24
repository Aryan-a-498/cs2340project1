from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_jobseekerprofile_commute_and_cart'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobseekerprofile',
            name='location',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
