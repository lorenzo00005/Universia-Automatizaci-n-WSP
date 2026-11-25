"""Catálogo de permisos y permisos por rol.

Es la semilla inicial: la migración la copia a `role_permissions`, y desde ahí se puede
ajustar por base sin tocar código. A nivel membresía se pueden sumar o negar permisos.
"""

from enum import StrEnum


class Perm(StrEnum):
    AGENDA_VER = "agenda.ver"
    AGENDA_GESTIONAR = "agenda.gestionar"
    FINANZAS_VER = "finanzas.ver"
    FINANZAS_REGISTRAR = "finanzas.registrar"
    CRM_VER = "crm.ver"
    CRM_GESTIONAR = "crm.gestionar"
    CONOCIMIENTO_VER = "conocimiento.ver"
    CONOCIMIENTO_GESTIONAR = "conocimiento.gestionar"
    TAREAS_GESTIONAR = "tareas.gestionar"
    INTEGRACIONES_EJECUTAR = "integraciones.ejecutar"
    APROBACIONES_DECIDIR = "aprobaciones.decidir"
    CONVERSACIONES_TOMAR = "conversaciones.tomar"
    EQUIPO_GESTIONAR = "equipo.gestionar"
    AUDITORIA_VER = "auditoria.ver"
    FACTURACION_GESTIONAR = "facturacion.gestionar"


ROLES: dict[str, str] = {
    "owner": "Dueño",
    "admin": "Administrador",
    "employee": "Empleado",
}

ALL_PERMS = frozenset(Perm)

ROLE_PERMISSIONS: dict[str, frozenset[Perm]] = {
    "owner": ALL_PERMS,
    "admin": ALL_PERMS - {Perm.FACTURACION_GESTIONAR},
    "employee": frozenset(
        {
            Perm.AGENDA_VER,
            Perm.AGENDA_GESTIONAR,
            Perm.CRM_VER,
            Perm.CRM_GESTIONAR,
            Perm.CONOCIMIENTO_VER,
            Perm.CONVERSACIONES_TOMAR,
        }
    ),
}
