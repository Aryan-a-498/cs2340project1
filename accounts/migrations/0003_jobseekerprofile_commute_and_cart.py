from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_jobseekerprofile'),
        ('jobs', '0003_jobposting_company_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobseekerprofile',
            name='skills',
            field=models.ManyToManyField(blank=True, related_name='job_seekers', to='jobs.skill'),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='preferred_latitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='preferred_longitude',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='commute_radius_miles',
            field=models.PositiveIntegerField(
                default=10,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
        migrations.AddField(
            model_name='jobseekerprofile',
            name='cart_jobs',
            field=models.ManyToManyField(blank=True, related_name='in_job_seeker_carts', to='jobs.jobposting'),
        ),
    ]
