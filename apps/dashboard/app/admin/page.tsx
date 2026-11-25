"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api, ApiError, type AdminTenant, type Plan } from "@/lib/api";

const EMPTY = { name: "", slug: "", plan_key: "base", owner_email: "", owner_name: "" };

export default function AdminPage() {
  const router = useRouter();
  const [tenants, setTenants] = useState<AdminTenant[] | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [form, setForm] = useState(EMPTY);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [t, p] = await Promise.all([
        api<AdminTenant[]>("/admin/tenants"),
        api<Plan[]>("/admin/plans"),
      ]);
      setTenants(t);
      setPlans(p);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) router.replace("/login");
      else if (err instanceof ApiError && err.status === 403) router.replace("/");
    }
  }, [router]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/admin/tenants", { method: "POST", body: JSON.stringify(form) });
      setForm(EMPTY);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo crear.");
    }
  }

  const field = (key: keyof typeof EMPTY) => ({
    value: form[key],
    onChange: (e: { target: { value: string } }) => setForm({ ...form, [key]: e.target.value }),
  });

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Panel interno</h1>
        <Link href="/" className="text-sm text-primary underline">
          Volver
        </Link>
      </header>

      <Card>
        <h2 className="text-lg font-medium">Dar de alta un negocio</h2>
        <form onSubmit={onSubmit} className="mt-4 grid gap-3 sm:grid-cols-2">
          <Input placeholder="Nombre del negocio" required {...field("name")} />
          <Input
            placeholder="identificador-sin-espacios"
            required
            pattern="[a-z0-9][a-z0-9-]{1,78}"
            {...field("slug")}
          />
          <Input placeholder="Email del dueño" type="email" required {...field("owner_email")} />
          <Input placeholder="Nombre del dueño" {...field("owner_name")} />
          <select
            className="h-10 rounded-md border border-border bg-card px-3 text-sm"
            {...field("plan_key")}
          >
            {plans.map((p) => (
              <option key={p.key} value={p.key}>
                {p.name} (USD {p.price_usd})
              </option>
            ))}
          </select>
          <Button type="submit">Crear negocio</Button>
          {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        </form>
      </Card>

      <Card>
        <h2 className="text-lg font-medium">Negocios</h2>
        {!tenants ? (
          <p className="mt-2 text-muted">Cargando…</p>
        ) : tenants.length === 0 ? (
          <p className="mt-2 text-muted">Todavía no hay negocios.</p>
        ) : (
          <table className="mt-4 w-full text-left text-sm">
            <thead className="text-muted">
              <tr>
                <th className="py-2">Negocio</th>
                <th>Plan</th>
                <th>Estado</th>
                <th>Equipo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {tenants.map((t) => (
                <tr key={t.id}>
                  <td className="py-2">
                    {t.name}
                    <span className="block text-xs text-muted">{t.slug}</span>
                  </td>
                  <td>{t.plan_key ?? "—"}</td>
                  <td>{t.subscription_status ?? t.status}</td>
                  <td>{t.members}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
