"use client";

import { useEffect, useState } from "react";
import ScrollReveal from "@/components/ScrollReveal";
import { History, Search, RefreshCw, Filter, ShieldCheck } from "lucide-react";

interface AuditLogItem {
  id: string;
  event_type: string;
  document_id?: string;
  output_id?: string;
  signature_request_id?: string;
  timestamp: string;
  document_hash?: string;
  client_ip?: string;
  user_agent?: string;
  details: any;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterEventType, setFilterEventType] = useState<string>("");

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let url = "/api/audit/logs?limit=200";
      if (filterEventType) url += `&event_type=${filterEventType}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [filterEventType]);

  const filteredLogs = logs.filter(log => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      log.event_type.toLowerCase().includes(q) ||
      (log.document_id && log.document_id.toLowerCase().includes(q)) ||
      (log.document_hash && log.document_hash.toLowerCase().includes(q)) ||
      JSON.stringify(log.details).toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 pb-12">
      <ScrollReveal direction="up">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div>
            <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2 tracking-tight">
              <History className="w-6 h-6 text-rose-600 dark:text-rose-400" /> Append-Only Audit Event Log
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-xs mt-1">
              Complete local tamper-evident event stream with document hashes and timestamps.
            </p>
          </div>

          <button
            onClick={fetchLogs}
            className="p-2.5 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-800 shrink-0 self-start sm:self-auto transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </ScrollReveal>

      {/* Filters & Search */}
      <ScrollReveal direction="up" delay={0.1}>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              placeholder="Search by Document ID, SHA-256 Hash, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-800 rounded-xl text-xs bg-white dark:bg-slate-900 text-slate-900 dark:text-white"
            />
          </div>

          <select
            value={filterEventType}
            onChange={(e) => setFilterEventType(e.target.value)}
            className="border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-2.5 text-xs bg-white dark:bg-slate-900 font-semibold text-slate-700 dark:text-slate-200"
          >
            <option value="">All Event Types</option>
            <option value="DOCUMENT_UPLOADED">DOCUMENT_UPLOADED</option>
            <option value="PDF_MERGED">PDF_MERGED</option>
            <option value="PDF_SPLIT">PDF_SPLIT</option>
            <option value="PDF_COMPRESSED">PDF_COMPRESSED</option>
            <option value="PDF_WATERMARKED">PDF_WATERMARKED</option>
            <option value="PDF_REDACTED">PDF_REDACTED</option>
            <option value="SIGNATURE_REQUEST_CREATED">SIGNATURE_REQUEST_CREATED</option>
            <option value="SIGNATURE_SEALED">SIGNATURE_SEALED</option>
            <option value="DOCUMENT_EXPORTED">DOCUMENT_EXPORTED</option>
            <option value="DOCUMENT_DELETED">DOCUMENT_DELETED</option>
          </select>
        </div>
      </ScrollReveal>

      {/* Logs Table */}
      <ScrollReveal direction="up" delay={0.15}>
        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-slate-500 dark:text-slate-400">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-rose-600 dark:text-rose-400" />
              Loading audit log stream...
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="p-12 text-center text-slate-400 dark:text-slate-500">
              No audit events found matching filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="p-3.5">Timestamp (UTC)</th>
                    <th className="p-3.5">Event Type</th>
                    <th className="p-3.5">Document ID / Output ID</th>
                    <th className="p-3.5">Document SHA-256 Hash</th>
                    <th className="p-3.5">Client IP</th>
                    <th className="p-3.5">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-[11px]">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors">
                      <td className="p-3.5 text-slate-500 dark:text-slate-400 whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="p-3.5 font-sans">
                        <span className="bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 px-2 py-0.5 rounded-md font-bold border border-rose-200 dark:border-rose-800/60">
                          {log.event_type}
                        </span>
                      </td>
                      <td className="p-3.5 text-slate-600 dark:text-slate-400">
                        {log.document_id ? log.document_id.substring(0, 8) + "..." : log.output_id ? log.output_id.substring(0, 8) + "..." : "-"}
                      </td>
                      <td className="p-3.5 text-slate-800 dark:text-slate-200 font-bold">
                        {log.document_hash ? log.document_hash.substring(0, 16) + "..." : "-"}
                      </td>
                      <td className="p-3.5 text-slate-500 dark:text-slate-400">{log.client_ip || "127.0.0.1"}</td>
                      <td className="p-3.5 text-slate-600 dark:text-slate-400 max-w-xs truncate font-sans">
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </ScrollReveal>
    </div>
  );
}
