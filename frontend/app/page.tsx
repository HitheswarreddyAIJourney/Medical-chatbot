"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { loadAuth } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();
  useEffect(() => {
    const auth = loadAuth();
    router.replace(auth ? "/chat" : "/login");
  }, [router]);
  return null;
}
