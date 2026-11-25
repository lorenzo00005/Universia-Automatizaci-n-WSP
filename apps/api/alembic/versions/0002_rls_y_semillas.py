"""Row Level Security por tenant y datos iniciales (roles, permisos, planes).

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op
from app.domains.permissions.catalog import ROLE_PERMISSIONS, ROLES
from app.models import TENANT_SCOPED_TABLES

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_MATCH = (
    "(tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid"
    " OR current_setting('app.operator', true) = 'on')"
)

# Planes: precio en USD y features con límite (None = sin límite) y período.
PLANS = [
    ("base", "Base", 50, 1),
    ("pro", "Pro", 100, 2),
    ("ilimitado", "Ilimitado", 200, 3),
]
BASE_FEATURES = ["whatsapp.atencion", "asistente.personal", "integraciones"]
PRO_FEATURES = ["contenido.redes", "redes.respuestas", "ads.gestion", "web.sitio"]
# (plan, feature, limit_value, period, fair_use_limit)
FEATURES: list[tuple[str, str, int | None, str | None, int | None]] = [
    *[(p, f, None, None, None) for p in ("base", "pro", "ilimitado") for f in BASE_FEATURES],
    *[(p, f, None, None, None) for p in ("pro", "ilimitado") for f in PRO_FEATURES],
    ("pro", "video.edicion", 5, "week", None),
    ("ilimitado", "video.edicion", None, "week", 40),
    ("pro", "video.duracion_max_seg", 120, None, None),
    ("ilimitado", "video.duracion_max_seg", 120, None, None),
]


def _q(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def upgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} USING {TENANT_MATCH} "
            f"WITH CHECK {TENANT_MATCH}"
        )
    # Cada usuario puede ver sus propias membresías en cualquier tenant (para /me).
    op.execute(
        "CREATE POLICY own_memberships ON memberships FOR SELECT USING "
        "(user_id = nullif(current_setting('app.user_id', true), '')::uuid)"
    )

    for key, name in ROLES.items():
        op.execute(f"INSERT INTO roles (key, name) VALUES ({_q(key)}, {_q(name)})")
    for role, perms in ROLE_PERMISSIONS.items():
        for perm in sorted(perms):
            op.execute(
                f"INSERT INTO role_permissions (role_key, permission) "
                f"VALUES ({_q(role)}, {_q(perm.value)})"
            )
    for key, name, price, order in PLANS:
        op.execute(
            f"INSERT INTO plans (key, name, price_usd, sort_order, is_public) "
            f"VALUES ({_q(key)}, {_q(name)}, {price}, {order}, true)"
        )
    for plan, feature, limit, period, fair in FEATURES:
        op.execute(
            "INSERT INTO plan_features (plan_key, feature, limit_value, period, fair_use_limit) "
            f"VALUES ({_q(plan)}, {_q(feature)}, {_q(limit)}, {_q(period)}, {_q(fair)})"
        )


def downgrade() -> None:
    op.execute("DELETE FROM plan_features")
    op.execute("DELETE FROM plans")
    op.execute("DELETE FROM role_permissions")
    op.execute("DELETE FROM roles")
    op.execute("DROP POLICY IF EXISTS own_memberships ON memberships")
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
