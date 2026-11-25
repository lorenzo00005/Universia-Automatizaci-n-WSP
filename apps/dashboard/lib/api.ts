// Cliente mínimo de la API. Todo pasa por /api en el mismo origen, así la cookie
// de sesión (httpOnly) viaja sola.

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    let detail = "Algo salió mal. Probá de nuevo.";
    try {
      const body = await res.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export type Me = {
  id: string;
  email: string | null;
  name: string;
  is_operator: boolean;
  tenants: { id: string; name: string; role: string; permissions: string[] }[];
};

export type AdminTenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
  timezone: string;
  training_mode: boolean;
  plan_key: string | null;
  subscription_status: string | null;
  members: number;
};

export type Plan = { key: string; name: string; price_usd: number };
