import openpyxl
from django.core.management.base import BaseCommand

from agentes.models import Agente


class Command(BaseCommand):
    help = (
        "Importa agentes desde Excel (columnas: legajo, apellido, nombres, dni, activo). "
        "Ejecutar desde la raíz del proyecto: python manage.py importar_agentes <ruta/al/archivo.xlsx>"
    )

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=str)

    def handle(self, *args, **options):
        archivo = options["archivo"]
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
                activo_rrhh = str(activo).strip().upper() in [
                    "SI",
                    "SÍ",
                    "S",
                    "TRUE",
                    "1",
                    "ACTIVO",
                ]
                legajo_str = str(legajo).strip()
                dni_val = str(dni or "").strip() or None

                agente = Agente.objects.filter(legajo=legajo_str).first()
                if agente:
                    agente.apellido = str(apellido or "").strip()
                    agente.nombres = str(nombres or "").strip()
                    agente.dni = dni_val
                    agente.activo_rrhh = activo_rrhh
                    agente.agente_activo = activo_rrhh
                    agente.save(
                        update_fields=[
                            "apellido",
                            "nombres",
                            "dni",
                            "activo_rrhh",
                            "agente_activo",
                        ]
                    )
                    actualizados += 1
                else:
                    agente = Agente(
                        legajo=legajo_str,
                        apellido=str(apellido or "").strip(),
                        nombres=str(nombres or "").strip(),
                        dni=dni_val,
                        activo_rrhh=activo_rrhh,
                        agente_activo=activo_rrhh,
                        is_active=False,
                        rol=None,
                        email=None,
                    )
                    agente.set_unusable_password()
                    agente.save()
                    creados += 1
            except Exception as e:
                self.stderr.write(f"Error en fila {row}: {e}")
                errores += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completa: {creados} creados, "
                f"{actualizados} actualizados, {errores} errores"
            )
        )
