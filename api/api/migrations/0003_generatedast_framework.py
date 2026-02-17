from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_generatedast_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='generatedast',
            name='framework',
            field=models.CharField(blank=True, default='unknown', max_length=50, null=True),
        ),
    ]
