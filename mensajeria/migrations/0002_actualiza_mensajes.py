from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mensajeria', '0001_initial'),
    ]

    operations = [
        # Ajustes en configuraciones existentes
        migrations.RemoveField(
            model_name='configuracionmensajeria',
            name='recibir_notificaciones',
        ),
        migrations.RemoveField(
            model_name='configuracionmensajeria',
            name='sonido_notificaciones',
        ),
        migrations.RemoveField(
            model_name='configuracionmensajeria',
            name='mostrar_estado_online',
        ),
        migrations.RemoveField(
            model_name='configuracionmensajeria',
            name='auto_responder',
        ),
        migrations.RemoveField(
            model_name='configuracionmensajeria',
            name='mensaje_auto_responder',
        ),
        migrations.AddField(
            model_name='configuracionmensajeria',
            name='limite_adjuntos_por_minuto',
            field=models.PositiveIntegerField(default=5, help_text='Límite de archivos por minuto'),
        ),
        migrations.AddField(
            model_name='configuracionmensajeria',
            name='notificaciones_activas',
            field=models.BooleanField(default=True),
        ),

        # Las tablas antiguas de conversacion/mensaje/notificacion ya no son compatibles
        migrations.DeleteModel(
            name='Mensaje',
        ),
        migrations.DeleteModel(
            name='Conversacion',
        ),
        migrations.DeleteModel(
            name='Notificacion',
        ),

        # Nuevos modelos alineados con la implementación actual
        migrations.CreateModel(
            name='Conversacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('ultimo_mensaje_en', models.DateTimeField(blank=True, null=True)),
                ('no_leidos_alumno', models.PositiveIntegerField(default=0)),
                ('no_leidos_profesor', models.PositiveIntegerField(default=0)),
                ('alumno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversaciones_como_alumno', to=settings.AUTH_USER_MODEL)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversaciones_como_profesor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Conversación',
                'verbose_name_plural': 'Conversaciones',
                'ordering': ['-ultimo_mensaje_en', '-creado_en'],
            },
        ),
        migrations.AddConstraint(
            model_name='conversacion',
            constraint=models.UniqueConstraint(fields=('alumno', 'profesor'), name='unique_alumno_profesor_conversacion'),
        ),
        migrations.CreateModel(
            name='ConfiguracionSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.CharField(max_length=100, unique=True)),
                ('valor', models.TextField()),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuración del Sistema',
                'verbose_name_plural': 'Configuraciones del Sistema',
                'ordering': ['clave'],
            },
        ),
        migrations.CreateModel(
            name='RateLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('tipo_accion', models.CharField(max_length=50)),
                ('ip_address', models.GenericIPAddressField()),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rate_limits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Límite de Tasa',
                'verbose_name_plural': 'Límites de Tasa',
            },
        ),
        migrations.CreateModel(
            name='Mensaje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asunto', models.CharField(blank=True, max_length=150)),
                ('contenido', models.TextField()),
                ('adjunto', models.FileField(blank=True, null=True, upload_to='mensajeria/adjuntos/', validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'], message='Solo se permiten archivos PDF, JPG, PNG, DOC, DOCX')])),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('leido', models.BooleanField(default=False)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_enviados', to=settings.AUTH_USER_MODEL)),
                ('conversacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes', to='mensajeria.conversacion')),
                ('receptor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='mensajes_recibidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Mensaje',
                'verbose_name_plural': 'Mensajes',
                'ordering': ['fecha_creacion'],
            },
        ),
        migrations.AddIndex(
            model_name='mensaje',
            index=models.Index(fields=['conversacion', 'fecha_creacion'], name='mensaje_conversacion_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='mensaje',
            index=models.Index(fields=['autor', 'fecha_creacion'], name='mensaje_autor_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='mensaje',
            index=models.Index(fields=['receptor', 'fecha_creacion'], name='mensaje_receptor_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='ratelimit',
            index=models.Index(fields=['usuario', 'timestamp'], name='ratelimit_usuario_timestamp_idx'),
        ),
        migrations.AddIndex(
            model_name='ratelimit',
            index=models.Index(fields=['ip_address', 'timestamp'], name='ratelimit_ip_timestamp_idx'),
        ),
    ]
