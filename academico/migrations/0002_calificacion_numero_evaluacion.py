from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academico', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='calificacion',
            name='numero_evaluacion',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterUniqueTogether(
            name='calificacion',
            unique_together={('estudiante', 'asignatura', 'curso', 'numero_evaluacion')},
        ),
    ]
