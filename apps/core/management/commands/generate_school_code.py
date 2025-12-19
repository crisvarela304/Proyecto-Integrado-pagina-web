"""
Management command: generate_school_code
Genera o muestra el código único del colegio para Phone Home Protocol.

Uso:
    python manage.py generate_school_code
    python manage.py generate_school_code --force  # Regenerar código
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import ColegioConfig


class Command(BaseCommand):
    help = 'Genera o muestra el código único del colegio para Phone Home Protocol'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerar el código aunque ya exista',
        )
        parser.add_argument(
            '--nombre',
            type=str,
            help='Nombre del colegio',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='URL pública del colegio',
        )

    def handle(self, *args, **options):
        config = ColegioConfig.get_config()
        
        regenerado = False
        
        # Si se pide forzar, regenerar código
        if options['force']:
            config.codigo = ColegioConfig._generate_code()
            config.registrado_en_directorio = False
            regenerado = True
            self.stdout.write(self.style.WARNING('Código regenerado'))
        
        # Actualizar nombre si se proporciona
        if options['nombre']:
            config.nombre = options['nombre']
            self.stdout.write(f"Nombre actualizado: {options['nombre']}")
        
        # Actualizar URL si se proporciona
        if options['url']:
            config.url = options['url']
            self.stdout.write(f"URL actualizada: {options['url']}")
        
        config.save()
        
        # Mostrar información
        self.stdout.write('')
        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS('CONFIGURACIÓN DEL COLEGIO'))
        self.stdout.write('=' * 50)
        self.stdout.write(f'Código:        {self.style.HTTP_INFO(config.codigo)}')
        self.stdout.write(f'Nombre:        {config.nombre}')
        self.stdout.write(f'URL:           {config.url or "(no configurada)"}')
        self.stdout.write(f'Color 1:       {config.color_primario}')
        self.stdout.write(f'Color 2:       {config.color_secundario}')
        self.stdout.write(f'Registrado:    {"✅ Sí" if config.registrado_en_directorio else "❌ No"}')
        self.stdout.write('=' * 50)
        
        if not config.registrado_en_directorio:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'El colegio aún no está registrado en el Directorio Central.'
            ))
            self.stdout.write(
                'El registro se realizará automáticamente al iniciar el contenedor Docker.'
            )
