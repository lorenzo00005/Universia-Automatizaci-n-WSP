"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

function Verify() {
  const params = useSearchParams();
  const router = useRouter();
  const token = params.get("token");
  const [apiError, setApiError] = useState<string | null>(null);
  const error = token ? apiError : "El link no es válido.";
  const done = useRef(false);

  useEffect(() => {
    if (done.current || !token) return;
    done.current = true;
    api("/auth/verify", { method: "POST", body: JSON.stringify({ token }) })
      .then(() => router.replace("/"))
      .catch((err: Error) => setApiError(err.message));
  }, [token, router]);

  return (
    <Card className="mx-auto max-w-md">
      {error ? (
        <>
          <p>{error}</p>
          <a href="/login" className="mt-4 inline-block text-primary underline">
            Pedir otro link
          </a>
        </>
      ) : (
        <p>Entrando…</p>
      )}
    </Card>
  );
}

export default function VerifyPage() {
  return (
    <Suspense>
      <Verify />
    </Suspense>
  );
}
