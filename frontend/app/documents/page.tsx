"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ScrollReveal from "@/components/ScrollReveal";
import FileDropzone from "@/components/FileDropzone";
import { 
  FileText, Upload, Download, Trash2, ShieldAlert, 
  Calendar, Eye, RefreshCw, AlertTriangle, CheckCircle, Clock, Copy, Check, Sparkles, GitBranch
} from "lucide-react";

interface DocItem {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  sha256: string;
  page_count: number;
  is_original: boolean;
  created_at: string;
  expires_at?: string;
  inspection_warnings?: {
    warnings?: string[];
    has_custom_fonts?: boolean;
    has_interactive_forms?: boolean;
    has_digital_signatures?: boolean;
    is_encrypted?: boolean;
  };
}

export default function DocumentStorePage() {
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [uploading, setUploading] = useState<boolean>(false);
  const [clearing, setClearing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [previewDoc, setPreviewDoc] = useState<DocItem | null>(null);
  const [previewPage, setPreviewPage] = useState<number>(1);
  const [expiryModalDoc, setExpiryModalDoc] = useState<DocItem | null>(null);
  const [expiryDays, setExpiryDays] = useState<number>(30);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/documents");
      if (!res.ok) throw new Error("Failed to fetch document store.");
      const data = await res.json();
      setDocuments(data);
    } catch (err: any) {
      setError(err.message || "Could not connect to backend engine.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFilesUpload = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;

    setUploading(true);
    setError(null);

    for (let i = 0; i < files.length; i++) {
      const formData = new FormData();
      formData.append("file", files[i]);

      try {
        const res = await fetch("/api/documents/upload", {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.detail || "Upload failed");
        }
      } catch (err: any) {
        setError(err.message || "Failed to upload file.");
      }
    }

    setUploading(false);
    await fetchDocuments();
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this file from local storage?")) return;
    try {
      const res = await fetch(`/api/documents/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete document.");
      fetchDocuments();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleClearAll = async () => {
    if (documents.length === 0) return;
    if (!confirm(`Are you sure you want to permanently delete all ${documents.length} files from your local storage? This action cannot be undone.`)) {
      return;
    }

    setClearing(true);
    try {
      const res = await fetch("/api/documents/clear-all", { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to clear documents.");
      const data = await res.json();
      setStatusMessage(data.message);
      setTimeout(() => setStatusMessage(null), 3000);
      await fetchDocuments();
    } catch (err: any) {
      alert(err.message || "Failed to clear all files.");
    } finally {
      setClearing(false);
    }
  };

  const handleUpdateExpiry = async () => {
    if (!expiryModalDoc) return;
    try {
      const res = await fetch(`/api/documents/${expiryModalDoc.id}/expiry`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ days: expiryDays > 0 ? expiryDays : null }),
      });
      if (!res.ok) throw new Error("Failed to update expiration policy.");
      setExpiryModalDoc(null);
      fetchDocuments();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const copyHash = (hash: string, id: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Header */}
      <ScrollReveal direction="up">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">User-Owned Document Store</h1>
            <p className="text-slate-500 dark:text-slate-400 text-xs mt-1">
              Original uploads are preserved immutably. Output operations are versioned.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Link
              href="/versions"
              className="px-3.5 py-2.5 text-xs font-bold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl border border-slate-200 dark:border-slate-700 transition-all flex items-center gap-1.5 shadow-sm"
              title="Open Document Version Trees"
            >
              <GitBranch className="w-4 h-4 text-rose-500" />
              <span>Version Trees Tab</span>
            </Link>

            {documents.length > 0 && (
              <button
                onClick={handleClearAll}
                disabled={clearing}
                className="px-4 py-2.5 text-xs font-bold text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/50 rounded-xl border border-rose-200 dark:border-rose-800/60 transition-all flex items-center gap-1.5 shadow-sm hover:scale-[1.02] disabled:opacity-50"
                title="Clear all files from local store"
              >
                <Trash2 className="w-4 h-4" />
                <span>{clearing ? "Clearing..." : `Clear All Files (${documents.length})`}</span>
              </button>
            )}

            <button
              onClick={fetchDocuments}
              className="p-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-800 transition-colors shadow-sm"
              title="Refresh List"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </ScrollReveal>

      {/* Status banner */}
      {statusMessage && (
        <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 rounded-xl text-xs font-semibold flex items-center gap-2">
          <CheckCircle className="w-4 h-4" /> {statusMessage}
        </div>
      )}

      {/* Drag & Drop Upload Zone */}
      <ScrollReveal direction="up" delay={0.08}>
        <FileDropzone
          onFilesUploaded={handleFilesUpload}
          multiple={true}
          title="Drag & Drop PDFs or Office files to store"
          subtitle="All files are saved immutably to ./data/storage/originals/ with SHA-256 verification"
          compact={documents.length > 0}
        />
      </ScrollReveal>

      {uploading && (
        <div className="p-4 bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300 rounded-xl text-sm flex items-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin" /> Uploading and inspecting document...
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 rounded-xl text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xs font-bold underline">Dismiss</button>
        </div>
      )}

      {/* Document List */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 dark:text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-rose-600 dark:text-rose-400" />
            Loading local store...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center text-slate-500 dark:text-slate-400 space-y-3">
            <FileText className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto" />
            <h3 className="font-bold text-slate-700 dark:text-slate-300">No documents in store</h3>
            <p className="text-xs text-slate-400 dark:text-slate-500">Drag and drop a PDF or Office file above to begin.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {documents.map((doc, idx) => {
              const warnings = doc.inspection_warnings?.warnings || [];
              return (
                <ScrollReveal key={doc.id} direction="up" delay={0.03 * (idx % 10)}>
                  <div className="p-5 hover:bg-slate-50/80 dark:hover:bg-slate-800/50 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-2 flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-extrabold text-slate-900 dark:text-white text-sm truncate max-w-md">{doc.filename}</span>
                        <button
                          onClick={() => copyHash(doc.sha256, doc.id)}
                          className="text-[11px] bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono px-2 py-0.5 rounded-lg border border-slate-200 dark:border-slate-700 flex items-center gap-1 transition-colors"
                          title="Click to copy full SHA-256 hash"
                        >
                          {copiedId === doc.id ? <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
                          <span>SHA: {doc.sha256.substring(0, 12)}...</span>
                        </button>
                        {doc.is_original && (
                          <span className="text-[10px] bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-md font-bold border border-emerald-200 dark:border-emerald-800/60">
                            Original (Immutable)
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
                        <span>Size: {formatBytes(doc.file_size)}</span>
                        <span>Pages: {doc.page_count > 0 ? doc.page_count : "N/A"}</span>
                        <span>Added: {new Date(doc.created_at).toLocaleString()}</span>
                        {doc.expires_at ? (
                          <span className="text-amber-700 dark:text-amber-400 font-semibold flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5" /> Expires: {new Date(doc.expires_at).toLocaleDateString()}
                          </span>
                        ) : (
                          <span className="text-slate-400 dark:text-slate-500">Retention: Permanent</span>
                        )}
                      </div>

                      {/* Warnings tags */}
                      {warnings.length > 0 && (
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          {warnings.map((w, i) => (
                            <span key={i} className="inline-flex items-center gap-1 text-[11px] bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60 px-2 py-0.5 rounded-lg font-medium">
                              <AlertTriangle className="w-3 h-3 shrink-0 text-amber-600 dark:text-amber-400" /> {w}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                      <button
                        onClick={() => { setPreviewDoc(doc); setPreviewPage(1); }}
                        className="p-2.5 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-xs font-bold flex items-center gap-1.5 border border-slate-200 dark:border-slate-700 transition-colors"
                        title="Preview Page"
                      >
                        <Eye className="w-4 h-4 text-slate-500 dark:text-slate-400" /> Preview
                      </button>
                      <a
                        href={`/api/documents/${doc.id}/download`}
                        download
                        className="p-2.5 text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/50 rounded-xl text-xs font-bold flex items-center gap-1.5 border border-rose-200 dark:border-rose-800/60 transition-colors"
                      >
                        <Download className="w-4 h-4 text-rose-600 dark:text-rose-400" /> Download
                      </a>
                      <button
                        onClick={() => setExpiryModalDoc(doc)}
                        className="p-2.5 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-xs font-semibold border border-slate-200 dark:border-slate-700 transition-colors"
                        title="Set Expiry Policy"
                      >
                        <Clock className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                      </button>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="p-2.5 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl text-xs transition-colors"
                        title="Delete document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </ScrollReveal>
              );
            })}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewDoc && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-2xl w-full p-6 space-y-4 shadow-2xl border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
              <h3 className="font-extrabold text-slate-900 dark:text-white text-base">Preview: {previewDoc.filename}</h3>
              <button onClick={() => setPreviewDoc(null)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 font-bold p-1">✕</button>
            </div>

            <div className="bg-slate-100/80 dark:bg-slate-800/80 rounded-2xl p-4 flex items-center justify-center min-h-[360px] border border-slate-200 dark:border-slate-700">
              <img
                src={`/api/documents/${previewDoc.id}/preview?page=${previewPage}`}
                alt="Page Preview"
                className="max-h-[450px] shadow-lg border rounded-lg"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2">
                <button
                  disabled={previewPage <= 1}
                  onClick={() => setPreviewPage(p => Math.max(1, p - 1))}
                  className="px-3.5 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-xs font-bold disabled:opacity-50 transition-colors text-slate-800 dark:text-slate-200"
                >
                  Previous
                </button>
                <span className="text-xs text-slate-600 dark:text-slate-400 font-semibold">Page {previewPage} of {previewDoc.page_count || 1}</span>
                <button
                  disabled={previewPage >= (previewDoc.page_count || 1)}
                  onClick={() => setPreviewPage(p => p + 1)}
                  className="px-3.5 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-xs font-bold disabled:opacity-50 transition-colors text-slate-800 dark:text-slate-200"
                >
                  Next
                </button>
              </div>

              <button
                onClick={() => setPreviewDoc(null)}
                className="bg-slate-900 dark:bg-slate-800 text-white px-5 py-2 rounded-xl text-xs font-bold border border-slate-700"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Expiry Policy Modal */}
      {expiryModalDoc && (
        <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-slate-900 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200 dark:border-slate-800">
            <h3 className="font-extrabold text-slate-900 dark:text-white text-lg">Set File Auto-Expiry</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              Configure local file retention policy for <strong>{expiryModalDoc.filename}</strong>.
            </p>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300">Auto-delete after (Days):</label>
              <input
                type="number"
                value={expiryDays}
                onChange={(e) => setExpiryDays(parseInt(e.target.value) || 0)}
                className="w-full border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl p-2.5 text-sm"
                placeholder="Set 0 to keep permanently"
              />
              <span className="text-[11px] text-slate-400 dark:text-slate-500 block">Set 0 or negative to keep indefinitely without auto-deletion.</span>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setExpiryModalDoc(null)} className="px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-300 rounded-xl text-xs font-bold">
                Cancel
              </button>
              <button onClick={handleUpdateExpiry} className="px-5 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold shadow-md shadow-rose-900/20">
                Save Expiry Policy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
