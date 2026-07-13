import { CheckSquare } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "@/app/AuthProvider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { supabase } from "@/lib/supabase";

const highlights = [
  "AI reports: decisions, risks, deadlines",
  "Action-item tracking with owners",
  "Chat with any meeting transcript",
  "Meeting health scoring",
];

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { session } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (session) return <Navigate to="/dashboard" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setNotice(null);
    setBusy(true);
    try {
      if (mode === "login") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        navigate("/dashboard");
      } else {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
        if (data.session) navigate("/dashboard");
        else setNotice("Check your inbox to confirm your email, then sign in.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-center bg-zinc-900 p-12 lg:flex">
        <div className="mb-6 flex items-center gap-2">
          <CheckSquare className="text-indigo-400" size={26} aria-hidden />
          <span className="text-xl font-bold">MeetIQ</span>
        </div>
        <h1 className="max-w-md text-3xl font-semibold leading-tight">
          Transform meetings into structured business intelligence.
        </h1>
        <ul className="mt-8 space-y-3 text-sm text-zinc-400">
          {highlights.map((h) => (
            <li key={h} className="flex items-center gap-2">
              <span className="h-1 w-1 rounded-full bg-indigo-400" aria-hidden />
              {h}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-center p-6">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-4">
          <div className="mb-6">
            <h2 className="text-xl font-semibold">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h2>
            <p className="mt-1 text-sm text-zinc-400">
              {mode === "login" ? "Sign in to your workspace" : "Start analyzing your meetings"}
            </p>
          </div>
          <div>
            <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-zinc-400">
              Email
            </label>
            <Input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="password" className="mb-1.5 block text-xs font-medium text-zinc-400">
              Password
            </label>
            <Input
              id="password"
              type="password"
              required
              minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-xs text-rose-400">{error}</p>}
          {notice && <p className="text-xs text-emerald-400">{notice}</p>}
          <Button type="submit" disabled={busy} className="w-full">
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Sign up"}
          </Button>
          <p className="text-center text-xs text-zinc-500">
            {mode === "login" ? (
              <>
                No account?{" "}
                <Link to="/signup" className="text-indigo-400 hover:underline">
                  Sign up
                </Link>
              </>
            ) : (
              <>
                Already registered?{" "}
                <Link to="/login" className="text-indigo-400 hover:underline">
                  Sign in
                </Link>
              </>
            )}
          </p>
        </form>
      </div>
    </div>
  );
}
