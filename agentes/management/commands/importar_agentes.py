import openpyxl
from django.core.management.base import BaseCommand

from notas.models import Agente


class Command(BaseCommand):
    help = 'Importa agentes desde un archivo Excel (columnas: legajo, apellido, nombres, dni, activo).'

    def add_arguments(self, parser):
        parser.add_argument('archivo', type=str)

    def handle(self, *args, **options):
        archivo = options['archivo']
        wb = openpyxl.load_workbook(archivo)
        ws = wb.active
        creados = 0
        actualizados = 0
        errores = 0

        for row in ws.iter_rows(min_row=2, values_only=True):
            try:
                legajo, apellido, nombres, dni, activo = row
                if not legajo:
                    continue
                activo_bool = str(activo).strip().upper() in [
                    'SI',
                    'SÍ',
                    'S',
                    'TRUE',
                    '1',
                    'ACTIVO',
                ]
                agente, created = Agente.objects.update_or_create(
                    legajo_numero=str(legajo).strip(),
                    defaults={
                        'apellido': str(apellido or '').strip(),
                        'nombre': str(nombres or '').strip(),
                        'dni': str(dni or '').strip() if dni else None,
                        'activo': activo_bool,
                    },
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1
            except Exception as e:
                self.stderr.write(f'Error en fila {row}: {e}')
                errores += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Importación completa: {creados} creados, '
                f'{actualizados} actualizados, {errores} errores'
            )
        )
