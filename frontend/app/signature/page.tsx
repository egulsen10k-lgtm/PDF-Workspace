"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import ScrollReveal from "@/components/ScrollReveal";
import FileDropzone from "@/components/FileDropzone";
import { PenTool, Upload, CheckCircle, Copy, Link as LinkIcon, AlertTriangle } from "lucide-react";

interface DocItem {
  id: string;
  filename: string;
  page_count: number;
}

export default function SignatureStudioPage() {
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>("");
  const [signerName, setSignerName] = useState<string>("Alice Smith");
  const [signerEmail, setSignerEmail] = useState<string>("alice@example.com");
  const [createdReq, setCreatedReq] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      const res = await fetch("/api/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
        if (data.length > 0 && !selectedDocId) setSelectedDocId(data[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFilesUpload = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;

    for (let i = 0; i < files.length; i++) {
      const formData = new FormData();
      formData.append("file", files[i]);
      try {
        const res = await fetch("/api/documents/upload", {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          const doc = await res.json();
          setSelectedDocId(doc.id);
        }
      } catch (err) {
        console.error(err);
      }
    }
    await fetchDocuments();
  };

  const handleCreateRequest = async () => {
    if (!selectedDocId) {
      setError("Please select a document.");
      return;
    }
    setLoading(true);
    setError(null);
    setCreatedReq(null);

    try {
      const res = await fetch("/api/signatures/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: selectedDocId,
          signer_email: signerEmail,
          signer_name: signerName,
          fields: [
            { page: 1, x: 10, y: 75, width: 35, height: 12, type: "signature", label: "Signer Signature" },
            { page: 1, x: 55, y: 75, width: 35, height: 12, type: "date", label: "Date Signed" }
          ]
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create signature request.");
      }

      const data = await res.json();
      setCreatedReq(data);
    } catch (err: any) {
      setError(err.message || "Failed to create request.");
    } finally {
      setLoading(false);
    }
  };

  const signerUrl = createdReq ? `${typeof window !== "undefined" ? window.location.origin : ""}/sign/${createdReq.access_token}` : "";

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      <ScrollReveal direction="up">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-2">
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2 tracking-tight">
            <PenTool className="w-6 h-6 text-rose-600 dark:text-rose-400" /> Simple e-Sign Studio
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-xs">
            Place fields, invite signers with access tokens, record electronic consent, and seal final PDF hashes.
          </p>
        </div>
      </ScrollReveal>

      <ScrollReveal direction="up" delay={0.08}>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-5">
          <h2 className="font-extrabold text-slate-900 dark:text-white text-base border-b border-slate-200 dark:border-slate-800 pb-3">
            1. Upload or Select Target Document
          </h2>

          <FileDropzone
            onFilesUploaded={handleFilesUpload}
            multiple={false}
            title="Drag & drop document to prepare for e-signature"
            subtitle="Uploaded PDF will automatically be selected below"
            compact={documents.length > 0}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Target Document:</label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-sm bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>{d.filename} ({d.page_count} pages)</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Signer Full Name:</label>
              <input
                type="text"
                value={signerName}
                onChange={(e) => setSignerName(e.target.value)}
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-sm bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>

            <div className="sm:col-span-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Signer Email Address:</label>
              <input
                type="email"
                value={signerEmail}
                onChange={(e) => setSignerEmail(e.target.value)}
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-sm bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleCreateRequest}
              disabled={loading || !selectedDocId}
              className="bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold px-6 py-3 rounded-xl shadow-md shadow-rose-900/20 text-xs transition-all disabled:opacity-50 hover:scale-[1.02]"
            >
              {loading ? "Generating Link..." : "Create Signature Link"}
            </button>
          </div>
        </div>
      </ScrollReveal>

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 rounded-2xl text-sm font-medium">
          {error}
        </div>
      )}

      {createdReq && (
        <ScrollReveal direction="scale">
          <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 rounded-3xl p-6 space-y-4 shadow-md">
            <div className="flex items-center gap-2 font-bold text-emerald-950 dark:text-emerald-200 text-lg">
              <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>Signature Request Active!</span>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-emerald-900 dark:text-emerald-300">Signer Shareable Access Link:</label>
              <div className="flex flex-col sm:flex-row items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={signerUrl}
                  className="w-full bg-white dark:bg-slate-900 border border-emerald-300 dark:border-emerald-800 rounded-xl p-2.5 text-xs font-mono text-slate-800 dark:text-slate-200"
                />
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(signerUrl);
                    alert("Link copied to clipboard!");
                  }}
                  className="bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2.5 rounded-xl text-xs font-bold shrink-0 flex items-center gap-1.5 shadow-sm transition-colors"
                >
                  <Copy className="w-4 h-4" /> Copy
                </button>
                <Link
                  href={`/sign/${createdReq.access_token}`}
                  className="bg-slate-900 dark:bg-slate-800 hover:bg-slate-800 dark:hover:bg-slate-700 text-white px-5 py-2.5 rounded-xl text-xs font-bold shrink-0 shadow-sm transition-colors"
                >
                  Open Signer Page
                </Link>
              </div>
            </div>
          </div>
        </ScrollReveal>
      )}
    </div>
  );
}
