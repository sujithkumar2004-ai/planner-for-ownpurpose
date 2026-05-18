"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem("finalplanner_token");
      if (!token && !pathname.startsWith("/login")) {
        router.push("/login");
      } else {
        setIsAuthenticated(true);
      }
    };

    checkAuth();
  }, [pathname, router]);

  if (!isAuthenticated && !pathname.startsWith("/login")) {
    // Show a minimal loading state while checking auth
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-zinc-800 border-t-purple-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  return <>{children}</>;
}
