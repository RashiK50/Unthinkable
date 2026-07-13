import { CheckSquare, LayoutDashboard, LogOut, Mic } from "lucide-react";
import { NavLink, Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/app/AuthProvider";
import { cn } from "@/lib/cn";
import { supabase } from "@/lib/supabase";

const nav = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/meetings", label: "Meetings", icon: Mic },
];

export function AppLayout() {
  const { session, loading } = useAuth();

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-zinc-500">Loading…</div>;
  }
  if (!session) return <Navigate to="/login" replace />;

  return (
    <div className="flex min-h-screen">
      <aside className="fixed inset-y-0 hidden w-52 flex-col border-r border-zinc-800 bg-zinc-950 p-4 md:flex">
        <div className="mb-8 flex items-center gap-2 px-2">
          <CheckSquare className="text-indigo-400" size={20} aria-hidden />
          <span className="text-base font-bold tracking-tight">MeetIQ</span>
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-indigo-500/15 text-indigo-300"
                    : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200",
                )
              }
            >
              <Icon size={16} aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-zinc-800 pt-3">
          <p className="mb-2 truncate px-3 text-xs text-zinc-500">{session.user.email}</p>
          <button
            onClick={() => supabase.auth.signOut()}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
          >
            <LogOut size={16} aria-hidden />
            Sign out
          </button>
        </div>
      </aside>

      {/* Mobile top bar */}
      <div className="fixed inset-x-0 top-0 z-40 flex items-center justify-between border-b border-zinc-800 bg-zinc-950/95 px-4 py-3 backdrop-blur md:hidden">
        <div className="flex items-center gap-2">
          <CheckSquare className="text-indigo-400" size={18} aria-hidden />
          <span className="font-bold">MeetIQ</span>
        </div>
        <div className="flex gap-4">
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn("text-sm", isActive ? "text-indigo-300" : "text-zinc-400")
              }
            >
              {label}
            </NavLink>
          ))}
        </div>
      </div>

      <main className="flex-1 px-4 pb-12 pt-16 md:ml-52 md:px-8 md:pt-8">
        <div className="mx-auto max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
