from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0005_inquiry_message_inquiryreply'),
    ]

    operations = [
        migrations.AddField(
            model_name='inquiryreply',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
    ]
