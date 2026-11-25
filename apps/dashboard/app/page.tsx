"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { api, ApiError, type Me } from "@/lib/api";

const ROLE_LABEL: Record<string, string> = {
  owner: "Dueño",
  admin: "Administrador",
  employee: "Empleado",
};

export default function Home() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);

  useEffect(() => {
    api<Me>("/auth/me")
      .then(setMe)
      .catch((err) => {
        if (err instanceof ApiError && err.status === 401) router.replace("/login");
      });
  }, [router]);

  async function logout() {
    await api("/auth/logout", { method: "POST" });
    router.replace("/login");
  }

  if (!me) return <p className="text-muted">Cargando…</p>;

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Hola{me.name ? `, ${me.name}` : ""}</h1>
          <p className="text-muted">{me.email}</p>
        </div>
        <div className="flex gap-2">
          {me.is_operator && (
            <Link href="/admin">
              <Button variant="outline">Panel interno</Button>
            </Link>
          )}
          <Button variant="ghost" onClick={logout}>
            Salir
          </Button>
        </div>
      </header>

      <Card>
        <h2 className="text-lg font-medium">Tus negocios</h2>
        {me.tenants.length === 0 ? (
          <p className="mt-2 text-muted">Todavía no estás en ningún negocio.</p>
        ) : (
          <ul className="mt-4 divide-y divide-border">
            {me.tenants.map((t) => (
              <li key={t.id} className="flex justify-between py-3">
                <span>{t.name}</span>
                <span className="text-muted">{ROLE_LABEL[t.role] ?? t.role}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
