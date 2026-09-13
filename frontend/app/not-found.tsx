import Link from "next/link";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-4 text-center">
      <div className="bg-white dark:bg-slate-900 rounded-3xl p-10 border border-slate-200 dark:border-slate-800 shadow-2xl max-w-md w-full space-y-6">
        <div className="text-8xl font-black bg-gradient-to-br from-rose-500 to-rose-700 bg-clip-text text-transparent">
          404
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-black text-slate-900 dark:text-white">Page Not Found</h1>
          <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </div>
        <div className="pt-2">
          <Link
            href="/"
            className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold py-3 rounded-xl shadow-lg text-sm transition-all"
          >
            <Home className="w-4 h-4" /> Back to Studio Hub
          </Link>
        </div>
      </div>
    </div>
  );
}
