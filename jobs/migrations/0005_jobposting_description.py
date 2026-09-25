from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_jobapplication'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobposting',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
