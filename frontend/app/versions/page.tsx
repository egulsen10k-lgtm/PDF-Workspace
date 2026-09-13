"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ScrollReveal from "@/components/ScrollReveal";
import { 
  GitBranch, FileText, Download, Eye, RefreshCw, Layers, 
  ArrowRight, Sparkles, Clock, Copy, Check, ChevronDown, 
  History, CornerDownRight, Tag, Search, ArrowDown, Trash2, AlertCircle
} from "lucide-react";

interface VersionItem {
  id: string;
  version: number;
  filename: string;
  operation_type: string;
  parameters: Record<string, any>;
  file_size: number;
  sha256: string;
  page_count: number;
  created_at: string;
  parent_document_ids: string[];
}

interface DocNode {
  document: {
    id: string;
    filename: string;
    original_filename: string;
    mime_type: string;
    file_size: number;
    sha256: string;
    page_count: number;
    created_at: string;
    expires_at?: string;
    inspection_warnings?: any;
  };
  versions: VersionItem[];
}

export default function DocumentVersionsPage() {
  const [tree, setTree] = useState<DocNode[]>([]);
  const [standaloneOutputs, setStandaloneOutputs] = useState<VersionItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterOp, setFilterOp] = useState<string>("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [previewDoc, setPreviewDoc] = useState<{ id: string; filename: string; page_count: number; is_output?: boolean } | null>(null);
  const [previewPage, setPreviewPage] = useState<number>(1);

  const fetchVersionTree = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/documents/version-tree");
      if (res.ok) {
        const data = await res.json();
        setTree(data.tree || []);
        setStandaloneOutputs(data.standalone_outputs || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const [purgeLoading, setPurgeLoading] = useState<boolean>(false);
  const [purgeResult, setPurgeResult] = useState<any>(null);

  useEffect(() => {
    fetchVersionTree();
  }, []);

  const handlePurgeStale = async () => {
    setPurgeLoading(true);
    setPurgeResult(null);
    try {
      const res = await fetch("/api/operations/outputs/stale", { method: "DELETE" });
      if (res.ok) {
        const data = await res.json();
        setPurgeResult(data);
        await fetchVersionTree(); // Refresh tree after purge
      }
    } catch (err) {
      console.error(err);
    } finally {
      setPurgeLoading(false);
    }
  };

  const copyHash = (hash: string, id: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const getOpBadgeColor = (op: string) => {
    switch (op.toLowerCase()) {
      case "merge": return "bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-800";
      case "split": return "bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 border-purple-300 dark:border-purple-800";
      case "compress": return "bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border-emerald-300 dark:border-emerald-800";
      case "watermark": return "bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800";
      case "redact": return "bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-300 dark:border-rose-800";
      case "edit_pdf":
      case "edit": return "bg-pink-100 dark:bg-pink-950/60 text-pink-700 dark:text-pink-300 border-pink-300 dark:border-pink-800";
      case "ocr": return "bg-violet-100 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300 border-violet-300 dark:border-violet-800";
      case "protect_pdf": return "bg-red-100 dark:bg-red-950/60 text-red-700 dark:text-red-300 border-red-300 dark:border-red-800";
      case "unlock_pdf": return "bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 border-teal-300 dark:border-teal-800";
      case "rotate":
      case "reorder_rotate": return "bg-cyan-100 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border-cyan-300 dark:border-cyan-800";
      case "page_numbers": return "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700";
      default: return "bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border-indigo-300 dark:border-indigo-800";
    }
  };

  const filteredTree = tree.filter(node => {
    const q = searchQuery.toLowerCase();
    const docMatch = node.document.filename.toLowerCase().includes(q) || node.document.sha256.toLowerCase().includes(q);
    const versionMatch = node.versions.some(v => v.filename.toLowerCase().includes(q) || v.operation_type.toLowerCase().includes(q) || v.sha256.toLowerCase().includes(q));
    
    if (filterOp) {
      const hasOp = node.versions.some(v => v.operation_type.toLowerCase() === filterOp.toLowerCase());
      return (docMatch || versionMatch) && hasOp;
    }
    return docMatch || versionMatch;
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Top Header */}
      <ScrollReveal direction="up">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 text-[11px] font-bold mb-2 border border-rose-500/20">
              <GitBranch className="w-3.5 h-3.5" />
              <span>Hierarchical Lineage & Version Control</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white tracking-tight">
              Document Version Trees
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-xs mt-1 leading-relaxed max-w-2xl">
              Each original file is organized as a parent node. All modifications, redactions, watermarks, compression passes, and edits are tracked chronologically underneath.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={handlePurgeStale}
              disabled={purgeLoading}
              className="px-4 py-2.5 text-xs font-bold text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 hover:bg-amber-100 dark:hover:bg-amber-900/50 rounded-xl border border-amber-200 dark:border-amber-800/60 transition-all flex items-center gap-1.5 shadow-sm hover:scale-[1.02] disabled:opacity-50"
              title="Delete version records whose files no longer exist on disk"
            >
              {purgeLoading ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /> Scanning...</>
              ) : (
                <><Trash2 className="w-4 h-4" /> Purge Missing Files</>
              )}
            </button>
            <button
              onClick={fetchVersionTree}
              className="p-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-800 transition-colors shadow-sm"
              title="Refresh Tree"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </ScrollReveal>

      {purgeResult && (
        <ScrollReveal direction="up">
          <div className={`p-4 rounded-2xl text-sm font-medium flex items-start gap-3 border shadow-sm ${
            purgeResult.deleted_outputs > 0 || purgeResult.deleted_documents > 0
              ? "bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-300"
              : "bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-300"
          }`}>
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="font-bold">{purgeResult.message}</p>
              {purgeResult.output_filenames?.length > 0 && (
                <p className="text-xs opacity-80">Removed outputs: {purgeResult.output_filenames.join(", ")}</p>
              )}
              {purgeResult.document_filenames?.length > 0 && (
                <p className="text-xs opacity-80">Removed documents: {purgeResult.document_filenames.join(", ")}</p>
              )}
            </div>
          </div>
        </ScrollReveal>
      )}

      {/* Filters & Search */}
      <ScrollReveal direction="up" delay={0.08}>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              placeholder="Search by document name, version filename, or SHA-256..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-800 rounded-2xl text-xs bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-sm"
            />
          </div>

          <select
            value={filterOp}
            onChange={(e) => setFilterOp(e.target.value)}
            className="border border-slate-200 dark:border-slate-800 rounded-2xl px-4 py-2.5 text-xs bg-white dark:bg-slate-900 font-semibold text-slate-700 dark:text-slate-200 shadow-sm"
          >
            <option value="">All Operation Types</option>
            <option value="compress">Compress</option>
            <option value="watermark">Watermark</option>
            <option value="redact">Redact</option>
            <option value="edit_pdf">Edit / Annotate</option>
            <option value="split">Split</option>
            <option value="rotate">Rotate</option>
            <option value="crop">Crop</option>
            <option value="page_numbers">Page Numbers</option>
            <option value="ocr">OCR</option>
            <option value="protect_pdf">Protect</option>
            <option value="unlock_pdf">Unlock</option>
          </select>
        </div>
      </ScrollReveal>

      {/* Version Trees Board (Side-by-Side File Columns) */}
      {loading ? (
        <div className="p-16 text-center text-slate-500 dark:text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-rose-600 dark:text-rose-400" />
          <p className="text-sm font-semibold">Loading document version trees...</p>
        </div>
      ) : filteredTree.length === 0 ? (
        <div className="p-16 bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 text-center space-y-4 shadow-sm">
          <GitBranch className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto" />
          <h3 className="font-extrabold text-slate-800 dark:text-slate-200 text-base">No Document Trees Found</h3>
          <p className="text-xs text-slate-400 dark:text-slate-500 max-w-sm mx-auto">
            Upload files in the Document Store or run PDF tool operations from the Studio Hub to see versions tracked here.
          </p>
          <Link
            href="/documents"
            className="inline-flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white font-bold px-5 py-2.5 rounded-xl text-xs shadow-md shadow-rose-900/20 transition-all"
          >
            <FileText className="w-4 h-4" /> Go to Document Store
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {filteredTree.map((node, nIdx) => {
            const doc = node.document;
            const versions = node.versions;

            return (
              <ScrollReveal key={doc.id} direction="up" delay={0.05 * (nIdx % 6)}>
                <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-5 hover:shadow-md transition-shadow">
                  
                  {/* 1. Parent Document Header Card (Immutable Base) */}
                  <div className="bg-slate-50 dark:bg-slate-800/80 rounded-2xl p-4 border border-slate-200 dark:border-slate-700/80 space-y-3 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-rose-500/5 rounded-full blur-xl pointer-events-none" />

                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-500 to-rose-700 text-white flex items-center justify-center font-black text-xs shrink-0 shadow-md">
                          PDF
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-extrabold text-slate-900 dark:text-white text-sm truncate max-w-xs">
                              {doc.filename}
                            </span>
                            <span className="text-[10px] bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold px-2 py-0.5 rounded-md">
                              Base Original (v0)
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 dark:text-slate-500">
                            {formatBytes(doc.file_size)} &bull; {doc.page_count} pages &bull; Added {new Date(doc.created_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          onClick={() => { setPreviewDoc({ id: doc.id, filename: doc.filename, page_count: doc.page_count, is_output: false }); setPreviewPage(1); }}
                          className="p-2 text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 rounded-lg border border-slate-200 dark:border-slate-600 transition-colors shadow-xs"
                          title="Preview Original Page"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <a
                          href={`/api/documents/${doc.id}/download`}
                          download
                          className="p-2 text-rose-600 dark:text-rose-400 hover:bg-white dark:hover:bg-slate-700 rounded-lg border border-slate-200 dark:border-slate-600 transition-colors shadow-xs"
                          title="Download Original"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-1 border-t border-slate-200/60 dark:border-slate-700/60">
                      <button
                        onClick={() => copyHash(doc.sha256, doc.id)}
                        className="text-[10px] bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 font-mono px-2 py-0.5 rounded-md border border-slate-200 dark:border-slate-700 flex items-center gap-1 transition-colors"
                      >
                        {copiedId === doc.id ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3 text-slate-400" />}
                        <span>SHA: {doc.sha256.substring(0, 16)}...</span>
                      </button>
                    </div>
                  </div>

                  {/* 2. Nested Versions Lineage Stream Below File */}
                  <div className="space-y-3 pl-3 sm:pl-4 border-l-2 border-dashed border-rose-300 dark:border-rose-900/60 ml-4 relative">
                    {versions.length === 0 ? (
                      <div className="p-4 bg-slate-50/50 dark:bg-slate-800/40 rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 text-center space-y-2">
                        <p className="text-xs text-slate-400 dark:text-slate-500">
                          No modified versions generated yet for this file.
                        </p>
                        <Link
                          href="/tools/watermark"
                          className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-600 dark:text-rose-400 hover:underline"
                        >
                          <span>Edit with Studio Tools</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    ) : (
                      versions.map((ver, vIdx) => {
                        const sizeDiffPct = doc.file_size > 0 
                          ? Math.round(((ver.file_size - doc.file_size) / doc.file_size) * 100) 
                          : 0;

                        return (
                          <div
                            key={ver.id}
                            className="bg-white dark:bg-slate-800/90 rounded-2xl border border-slate-200/80 dark:border-slate-700 p-3.5 space-y-2 shadow-sm relative group hover:border-rose-400/80 dark:hover:border-rose-500/60 transition-all"
                          >
                            {/* Branch Indicator Dot */}
                            <div className="absolute -left-[23px] sm:-left-[27px] top-5 w-3 h-3 rounded-full bg-rose-500 border-2 border-white dark:border-slate-900 ring-2 ring-rose-500/20" />

                            <div className="flex items-start justify-between gap-3">
                              <div className="space-y-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded-md border ${getOpBadgeColor(ver.operation_type)}`}>
                                    {ver.operation_type.replace("_", " ")}
                                  </span>
                                  <span className="text-[10px] bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-mono font-bold px-1.5 py-0.2 rounded">
                                    v{ver.version}
                                  </span>
                                  <span className="font-bold text-xs text-slate-900 dark:text-white truncate max-w-[200px]">
                                    {ver.filename}
                                  </span>
                                </div>

                                <div className="flex items-center gap-3 text-[11px] text-slate-400 dark:text-slate-500 flex-wrap">
                                  <span>{formatBytes(ver.file_size)}</span>
                                  {sizeDiffPct !== 0 && (
                                    <span className={sizeDiffPct < 0 ? "text-emerald-500 font-bold" : "text-amber-500 font-bold"}>
                                      ({sizeDiffPct > 0 ? `+${sizeDiffPct}%` : `${sizeDiffPct}%`})
                                    </span>
                                  )}
                                  <span>{new Date(ver.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                              </div>

                              <div className="flex items-center gap-1.5 shrink-0">
                                <a
                                  href={`/api/operations/outputs/${ver.id}/download`}
                                  download
                                  className="bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 p-2 rounded-xl text-xs font-bold flex items-center gap-1 border border-emerald-200 dark:border-emerald-800/60 shadow-xs transition-colors"
                                  title="Download Versioned Output"
                                >
                                  <Download className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                                </a>
                              </div>
                            </div>

                            <div className="pt-1.5 flex items-center justify-between border-t border-slate-100 dark:border-slate-700/60 text-[10px] text-slate-400">
                              <button
                                onClick={() => copyHash(ver.sha256, ver.id)}
                                className="font-mono hover:text-slate-700 dark:hover:text-slate-200 flex items-center gap-1 transition-colors"
                              >
                                {copiedId === ver.id ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3 text-slate-400" />}
                                <span>SHA: {ver.sha256.substring(0, 14)}...</span>
                              </button>
                              <span className="text-slate-400 dark:text-slate-500">{ver.page_count > 0 ? `${ver.page_count} pgs` : ""}</span>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </div>
      )}

      {/* Standalone / Multi-parent Merged Outputs */}
      {standaloneOutputs.length > 0 && (
        <ScrollReveal direction="up" delay={0.2}>
          <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200/80 dark:border-slate-800 p-6 shadow-sm space-y-4">
            <h2 className="text-lg font-black text-slate-900 dark:text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-500" /> Standalone & Multi-Document Outputs (Merged / Generated)
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {standaloneOutputs.map((out) => (
                <div key={out.id} className="p-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${getOpBadgeColor(out.operation_type)}`}>
                      {out.operation_type}
                    </span>
                    <a
                      href={`/api/operations/outputs/${out.id}/download`}
                      download
                      className="text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1 hover:underline"
                    >
                      <Download className="w-3.5 h-3.5" /> Download
                    </a>
                  </div>
                  <p className="font-extrabold text-xs text-slate-900 dark:text-white truncate">{out.filename}</p>
                  <p className="text-[11px] text-slate-400 font-mono">SHA: {out.sha256.substring(0, 12)}...</p>
                </div>
              ))}
            </div>
          </div>
        </ScrollReveal>
      )}

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
    </div>
  );
}
