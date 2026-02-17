# Generated manually for adding Solidity support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='generatedast',
            name='language',
            field=models.CharField(blank=True, default='rust', max_length=50, null=True),
        ),
    ]
