from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Inquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('phone', models.CharField(max_length=30)),
                ('email', models.EmailField()),
                ('role', models.CharField(
                    blank=True,
                    choices=[('buyer', 'Buyer'), ('tenant', 'Tenant'), ('investor', 'Investor'), ('other', 'Other')],
                    max_length=20,
                )),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('property', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='property_inquiries',
                    to='properties.property',
                )),
                ('sender', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sent_inquiries',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
