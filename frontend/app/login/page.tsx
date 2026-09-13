"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import ScrollReveal from "@/components/ScrollReveal";
import ThemeToggle from "@/components/ThemeToggle";
import { Lock, Key, ShieldCheck, Sparkles, AlertCircle, ArrowRight } from "lucide-react";

export default function LoginPage() {
  const [password, setPassword] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;

    setLoading(true);
    setError(null);

    const success = await login(password);
    if (success) {
      router.push("/");
    } else {
      setError("Invalid local master password. (Default is admin123)");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center p-4">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>

      <ScrollReveal direction="scale">
        <div className="max-w-md w-full bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-2xl space-y-6">
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 bg-rose-500/10 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 rounded-2xl flex items-center justify-center mx-auto mb-3 border border-rose-500/30 shadow-md">
              <Lock className="w-6 h-6" />
            </div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
              Personal File Vault Access
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Enter your local master password to unlock your private PDF studio & user-owned files.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                Local Master Password:
              </label>
              <div className="relative">
                <Key className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter master password..."
                  required
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-sm font-mono text-slate-900 dark:text-white focus:ring-2 focus:ring-rose-500 outline-none transition-all"
                />
              </div>
              <span className="text-[11px] text-slate-400 dark:text-slate-500 mt-1 block">
                Default: <code className="text-rose-600 dark:text-rose-400 font-bold">admin123</code> (Configurable via <code>.env</code>)
              </span>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 rounded-xl text-xs font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold py-3 rounded-xl shadow-lg shadow-rose-900/20 text-xs transition-all flex items-center justify-center gap-2 disabled:opacity-50 hover:scale-[1.02]"
            >
              {loading ? "Authenticating..." : "Unlock Personal Store"}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Privacy Footnote */}
          <div className="pt-4 border-t border-slate-100 dark:border-slate-800/80 text-center">
            <div className="inline-flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>100% Private & Local Storage</span>
            </div>
          </div>
        </div>
      </ScrollReveal>
    </div>
  );
}
