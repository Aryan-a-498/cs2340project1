import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_jobseekerprofile_location'),
        ('jobs', '0003_jobposting_company_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cover_note', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('reviewing', 'Reviewing'), ('shortlisted', 'Shortlisted'), ('not_selected', 'Not selected')], default='submitted', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='accounts.jobseekerprofile')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='jobs.jobposting')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='jobapplication',
            constraint=models.UniqueConstraint(fields=('job', 'applicant'), name='unique_job_application'),
        ),
    ]
