"""
Utilidades para la gestión de notas.
"""
from django.db import transaction
from django.utils import timezone
from django.db.models import Max
from django.db import connection
from .models import Nota, HistorialNota, EstadoChoices, TipoEventoChoices


@transaction.atomic
def generar_numero_nota():
    """
    Genera un número de nota único en formato NOTA-YYYY-NNNN de forma atómica.
    El formato es: NOTA-2026-0001, NOTA-2026-0002, etc.
    
    Usa SELECT FOR UPDATE para evitar condiciones de carrera.
    """
    año_actual = timezone.now().year
    
    # Usar SELECT FOR UPDATE para bloqueo de filas
    with connection.cursor() as cursor:
        # Buscar el último número de nota del año actual con lock
        cursor.execute("""
            SELECT numero_nota 
            FROM notas_nota 
            WHERE numero_nota LIKE %s 
            ORDER BY numero_nota DESC 
            LIMIT 1 
            FOR UPDATE
        """, [f'NOTA-{año_actual}-%'])
        
        resultado = cursor.fetchone()
        
        if resultado:
            # Extraer el número secuencial y aumentar en 1
            ultimo_numero_str = resultado[0].split('-')[-1]
            ultimo_numero = int(ultimo_numero_str)
            nuevo_numero = ultimo_numero + 1
        else:
            # Primera nota del año
            nuevo_numero = 1
    
    # Formatear con ceros a la izquierda (4 dígitos)
    numero_formateado = f'{nuevo_numero:04d}'
    
    return f'NOTA-{año_actual}-{numero_formateado}'


# Diccionario de transiciones permitidas según .cursorrules
TRANSICIONES_PERMITIDAS = {
    EstadoChoices.INGRESADA: [EstadoChoices.EN_REVISION],
    EstadoChoices.EN_REVISION: [EstadoChoices.ASIGNADA],
    EstadoChoices.ASIGNADA: [EstadoChoices.EN_PROCESO],
    EstadoChoices.EN_PROCESO: [
        EstadoChoices.EN_ESPERA,
        EstadoChoices.DEVUELTA,
        EstadoChoices.RESUELTA
    ],
    EstadoChoices.EN_ESPERA: [EstadoChoices.EN_PROCESO],
    EstadoChoices.DEVUELTA: [EstadoChoices.ASIGNADA],
    EstadoChoices.RESUELTA: [
        EstadoChoices.ARCHIVADA,
        EstadoChoices.EN_PROCESO
    ],
    # ANULADA puede venir desde cualquier estado activo
    # Se maneja como caso especial
}

# Estados activos (no finales)
ESTADOS_ACTIVOS = [
    EstadoChoices.INGRESADA,
    EstadoChoices.EN_REVISION,
    EstadoChoices.ASIGNADA,
    EstadoChoices.EN_PROCESO,
    EstadoChoices.EN_ESPERA,
    EstadoChoices.DEVUELTA,
    EstadoChoices.RESUELTA
]


def es_transicion_permitida(estado_actual, estado_nuevo):
    """
    Valida si una transición de estado es permitida según las reglas de negocio.
    
    Args:
        estado_actual: Estado actual de la nota
        estado_nuevo: Estado al que se quiere transicionar
    
    Returns:
        bool: True si la transición es permitida, False en caso contrario
    """
    # ANULADA puede venir desde cualquier estado activo
    if estado_nuevo == EstadoChoices.ANULADA:
        return estado_actual in ESTADOS_ACTIVOS
    
    # Verificar transiciones normales
    if estado_actual in TRANSICIONES_PERMITIDAS:
        return estado_nuevo in TRANSICIONES_PERMITIDAS[estado_actual]
    
    return False


def crear_registro_historial(nota, usuario, tipo_evento, estado_anterior=None,
                            estado_nuevo=None, responsable_anterior=None,
                            responsable_nuevo=None, descripcion_cambio=None,
                            campos_modificados=None):
    """
    Crea un registro en el historial de la nota.
    
    Args:
        nota: Instancia de Nota
        usuario: Usuario que realiza la acción
        tipo_evento: Tipo de evento (TipoEventoChoices)
        estado_anterior: Estado anterior (opcional)
        estado_nuevo: Estado nuevo (opcional)
        responsable_anterior: Responsable anterior (opcional)
        responsable_nuevo: Responsable nuevo (opcional)
        descripcion_cambio: Descripción del cambio (opcional)
        campos_modificados: Diccionario con campos modificados (opcional)
    """
    HistorialNota.objects.create(
        nota=nota,
        usuario=usuario,
        tipo_evento=tipo_evento,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        responsable_anterior=responsable_anterior,
        responsable_nuevo=responsable_nuevo,
        descripcion_cambio=descripcion_cambio,
        campos_modificados=campos_modificados or {}
    )
