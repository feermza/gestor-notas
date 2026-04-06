"""Compatibilidad: bases creadas con el campo `nombre` antes de unificar en `nombres`."""

from django.db import migrations


def rename_nombre_to_nombres(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'agentes_agente'
              AND column_name = 'nombre'
            """
        )
        if c.fetchone():
            c.execute(
                'ALTER TABLE agentes_agente RENAME COLUMN nombre TO nombres'
            )


def noop_reverse(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as c:
        c.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'agentes_agente'
              AND column_name = 'nombres'
            """
        )
        if c.fetchone():
            c.execute(
                'ALTER TABLE agentes_agente RENAME COLUMN nombres TO nombre'
            )


class Migration(migrations.Migration):

    dependencies = [
        ("agentes", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(rename_nombre_to_nombres, noop_reverse),
    ]
