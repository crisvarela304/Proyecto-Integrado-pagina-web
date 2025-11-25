from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="foto_perfil",
            field=models.ImageField(blank=True, null=True, upload_to="perfiles/"),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="telefono_apoderado",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="perfilusuario",
            name="telefono_estudiante",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
