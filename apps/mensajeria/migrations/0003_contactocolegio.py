import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("mensajeria", "0002_actualiza_mensajes"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactoColegio",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nombre", models.CharField(max_length=100)),
                ("correo", models.EmailField(max_length=254)),
                ("asunto", models.CharField(max_length=150)),
                ("mensaje", models.TextField()),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-creado_en"],
                "verbose_name": "Contacto del Colegio",
                "verbose_name_plural": "Contactos del Colegio",
            },
        ),
    ]
