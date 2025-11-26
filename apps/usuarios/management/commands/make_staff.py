from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Otorga permisos de staff a uno o más usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            'usernames',
            nargs='+',
            type=str,
            help='Nombre(s) de usuario(s) a los que se otorgarán permisos de staff'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='También hacer al usuario superusuario (admin completo)'
        )

    def handle(self, *args, **options):
        usernames = options['usernames']
        make_superuser = options['superuser']
        
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                
                # Otorgar permisos
                user.is_staff = True
                if make_superuser:
                    user.is_superuser = True
                
                user.save()
                
                status = "superusuario" if make_superuser else "staff"
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Usuario "{username}" ahora tiene permisos de {status}'
                    )
                )
                
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Usuario "{username}" no existe'
                    )
                )
