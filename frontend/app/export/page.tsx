"use client";

import { useState } from "react";
import ScrollReveal from "@/components/ScrollReveal";
import { Download, Trash2, HardDrive, ShieldCheck, RefreshCw, FileArchive } from "lucide-react";

export default function ExportBackupPage() {
  const [downloading, setDownloading] = useState<boolean>(false);
  const [cleaning, setCleaning] = useState<boolean>(false);
  const [cleanupMessage, setCleanupMessage] = useState<string | null>(null);

  const handleDownloadZip = async () => {
    setDownloading(true);
    try {
      const res = await fetch("/api/export/full-zip", { method: "POST" });
      if (!res.ok) throw new Error("Failed to generate export ZIP.");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ilovepdf_export_${new Date().toISOString().slice(0,10)}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err: any) {
      alert(err.message || "Failed to download export.");
    } finally {
      setDownloading(false);
    }
  };

  const handleCleanupExpired = async () => {
    setCleaning(true);
    try {
      const res = await fetch("/api/export/cleanup-expired", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setCleanupMessage(`Cleanup complete: Removed ${data.deleted_files_count} expired file(s).`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setCleaning(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <ScrollReveal direction="up">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-2">
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2 tracking-tight">
            <Download className="w-6 h-6 text-rose-600 dark:text-rose-400" /> Export & Local Data Backup
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-xs">
            All user data is owned and stored in local directory <code>./data/storage/</code>. No vendor lock-in.
          </p>
        </div>
      </ScrollReveal>

      {/* Export Section */}
      <ScrollReveal direction="up" delay={0.1}>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 flex items-center justify-center shrink-0">
              <FileArchive className="w-6 h-6 text-rose-600 dark:text-rose-400" />
            </div>
            <div className="space-y-1 flex-1">
              <h2 className="font-extrabold text-slate-900 dark:text-white text-lg">1-Click Full Local Data ZIP Export</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Export all original documents, versioned outputs, and append-only audit JSON logs into a single compressed archive.
              </p>
              <div className="pt-3">
                <button
                  onClick={handleDownloadZip}
                  disabled={downloading}
                  className="bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold px-6 py-3 rounded-xl shadow-md shadow-rose-900/20 text-xs transition-all flex items-center gap-2 disabled:opacity-50 hover:scale-[1.02]"
                >
                  {downloading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Packaging ZIP...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" /> Download Complete Export ZIP
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Retention & Expiry Cleanup */}
      <ScrollReveal direction="up" delay={0.15}>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 flex items-center justify-center shrink-0">
              <Trash2 className="w-6 h-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div className="space-y-1 flex-1">
              <h2 className="font-extrabold text-slate-900 dark:text-white text-lg">Retention & Expired File Cleanup</h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                Trigger instant cleanup of files whose expiration policy date has passed.
              </p>
              <div className="pt-3">
                <button
                  onClick={handleCleanupExpired}
                  disabled={cleaning}
                  className="bg-amber-600 hover:bg-amber-700 text-white font-bold px-6 py-3 rounded-xl shadow-md text-xs transition-all flex items-center gap-2 disabled:opacity-50 hover:scale-[1.02]"
                >
                  {cleaning ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Running Cleanup...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" /> Run Expired File Cleanup Now
                    </>
                  )}
                </button>
              </div>

              {cleanupMessage && (
                <p className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 pt-2">{cleanupMessage}</p>
              )}
            </div>
          </div>
        </div>
      </ScrollReveal>
    </div>
  );
}
