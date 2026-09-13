"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ScrollReveal from "@/components/ScrollReveal";
import FileDropzone from "@/components/FileDropzone";
import { 
  Combine, Scissors, RotateCw, Minimize2, Stamp, EyeOff, ScanText, FileSpreadsheet,
  Search, Download, CheckCircle, RefreshCw, ArrowLeft, Crop, Hash, Wrench,
  Files, FileText, Code, AlignLeft, FileDown, Layers, FileImage, Lock, Unlock,
  GitCompare, Copy, AlertTriangle, Trash2, X
} from "lucide-react";

interface DocItem {
  id: string;
  filename: string;
  page_count: number;
  sha256: string;
  inspection_warnings?: { warnings?: string[] };
}

export default function ToolWorkspacePage() {
  const params = useParams();
  const toolId = (params?.tool as string) || "merge";

  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(true);
  const [processing, setProcessing] = useState<boolean>(false);
  const [resultOutput, setResultOutput] = useState<any>(null);
  const [resultOutputs, setResultOutputs] = useState<any[]>([]);
  const [compareResult, setCompareResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Tool parameter states
  const [splitMode, setSplitMode] = useState<string>("ranges");
  const [splitRanges, setSplitRanges] = useState<string>("1-2, 3-4");
  const [splitEveryN, setSplitEveryN] = useState<number>(1);
  const [compressQuality, setCompressQuality] = useState<string>("medium");
  const [watermarkText, setWatermarkText] = useState<string>("CONFIDENTIAL");
  const [watermarkOpacity, setWatermarkOpacity] = useState<number>(0.3);
  const [watermarkPosition, setWatermarkPosition] = useState<string>("center");
  const [redactKeywords, setRedactKeywords] = useState<string>("SECRET, CONFIDENTIAL");
  const [ocrLang, setOcrLang] = useState<string>("eng");
  const [rotateAngle, setRotateAngle] = useState<number>(90);
  const [rotateSelection, setRotateSelection] = useState<string>("all");
  const [cropTop, setCropTop] = useState<number>(10);
  const [cropBottom, setCropBottom] = useState<number>(10);
  const [cropLeft, setCropLeft] = useState<number>(10);
  const [cropRight, setCropRight] = useState<number>(10);
  const [pageNumberFormat, setPageNumberFormat] = useState<string>("Page {page} of {total}");
  const [pageNumberPos, setPageNumberPos] = useState<string>("bottom-center");
  const [htmlContent, setHtmlContent] = useState<string>("<h1>Sample Heading</h1><p>This is a converted PDF document generated from HTML.</p>");
  const [protectPassword, setProtectPassword] = useState<string>("");
  const [unlockPassword, setUnlockPassword] = useState<string>("");
  const [annotationText, setAnnotationText] = useState<string>("Approved and Reviewed");
  const [docBId, setDocBId] = useState<string>("");

  // Reorder & Rotate state
  const [pageItems, setPageItems] = useState<{ page_index: number; rotation: number }[]>([]);

  const fetchDocuments = async () => {
    setLoadingDocs(true);
    try {
      const res = await fetch("/api/documents");
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } finally {
      setLoadingDocs(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFilesUpload = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    const newlyUploadedIds: string[] = [];
    for (let i = 0; i < files.length; i++) {
      const formData = new FormData();
      formData.append("file", files[i]);
      try {
        const res = await fetch("/api/documents/upload", { method: "POST", body: formData });
        if (res.ok) {
          const doc = await res.json();
          newlyUploadedIds.push(doc.id);
        }
      } catch {}
    }
    if (newlyUploadedIds.length > 0) {
      if (toolId === "merge") {
        setSelectedDocIds(prev => [...prev, ...newlyUploadedIds]);
      } else {
        setSelectedDocIds([newlyUploadedIds[newlyUploadedIds.length - 1]]);
      }
    }
    await fetchDocuments();
  };

  const handleClearAllDocuments = async () => {
    if (documents.length === 0) return;
    if (!confirm(`Are you sure you want to delete all ${documents.length} files from your store?`)) return;

    try {
      const res = await fetch("/api/documents/clear-all", { method: "DELETE" });
      if (res.ok) {
        setSelectedDocIds([]);
        await fetchDocuments();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleClearSelection = () => {
    setSelectedDocIds([]);
  };

  useEffect(() => {
    if (toolId === "reorder-rotate" && selectedDocIds.length > 0) {
      const doc = documents.find(d => d.id === selectedDocIds[0]);
      if (doc && doc.page_count > 0) {
        setPageItems(Array.from({ length: doc.page_count }, (_, i) => ({ page_index: i, rotation: 0 })));
      }
    }
  }, [selectedDocIds, documents, toolId]);

  const handleRotatePage = (index: number) => {
    setPageItems(prev => {
      const next = [...prev];
      next[index] = { ...next[index], rotation: (next[index].rotation + 90) % 360 };
      return next;
    });
  };

  const handleRunOperation = async () => {
    setProcessing(true);
    setError(null);
    setResultOutput(null);
    setResultOutputs([]);
    setCompareResult(null);

    try {
      let endpoint = "";
      let payload: any = {};

      switch (toolId) {
        case "merge":
          if (selectedDocIds.length < 2) throw new Error("Select at least 2 documents to merge.");
          endpoint = "/api/operations/merge";
          payload = { document_ids: selectedDocIds, output_filename: "merged_document.pdf" };
          break;
        case "split":
          if (selectedDocIds.length === 0) throw new Error("Select a document to split.");
          endpoint = "/api/operations/split";
          payload = { document_id: selectedDocIds[0], mode: splitMode, ranges: splitRanges, pages_per_split: splitEveryN };
          break;
        case "reorder-rotate":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/reorder-rotate";
          payload = { document_id: selectedDocIds[0], pages: pageItems };
          break;
        case "rotate":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/rotate";
          payload = { document_id: selectedDocIds[0], angle: rotateAngle, page_selection: rotateSelection };
          break;
        case "crop":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/crop";
          payload = { document_id: selectedDocIds[0], top_pct: cropTop, bottom_pct: cropBottom, left_pct: cropLeft, right_pct: cropRight };
          break;
        case "page-numbers":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/page-numbers";
          payload = { document_id: selectedDocIds[0], format_str: pageNumberFormat, position: pageNumberPos };
          break;
        case "compress":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/compress";
          payload = { document_id: selectedDocIds[0], quality: compressQuality };
          break;
        case "repair":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/repair";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "pdf-to-pdfa":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/pdf-to-pdfa";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "pdf-to-word":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/pdf-to-word";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "pdf-to-excel":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/pdf-to-excel";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "pdf-to-powerpoint":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/pdf-to-powerpoint";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "pdf-to-images":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/pdf-to-images";
          payload = { document_id: selectedDocIds[0], format: "jpg", dpi: 150 };
          break;
        case "pdf-to-markdown":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/pdf-to-markdown";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "html-to-pdf":
          endpoint = "/api/operations/html-to-pdf";
          payload = { html_content: htmlContent, title: "Converted HTML" };
          break;
        case "convert-office":
          if (selectedDocIds.length === 0) throw new Error("Select an Office document.");
          endpoint = "/api/operations/convert-office";
          payload = { document_id: selectedDocIds[0] };
          break;
        case "watermark":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/watermark";
          payload = { document_id: selectedDocIds[0], text: watermarkText, opacity: watermarkOpacity, position: watermarkPosition };
          break;
        case "redact":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/redact";
          payload = { document_id: selectedDocIds[0], keywords: redactKeywords.split(",").map(k => k.trim()).filter(Boolean) };
          break;
        case "protect":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          if (!protectPassword) throw new Error("Please enter a password.");
          endpoint = "/api/operations/protect";
          payload = { document_id: selectedDocIds[0], password: protectPassword };
          break;
        case "unlock":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          if (!unlockPassword) throw new Error("Please enter password to unlock.");
          endpoint = "/api/operations/unlock";
          payload = { document_id: selectedDocIds[0], password: unlockPassword };
          break;
        case "edit":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/edit";
          payload = { document_id: selectedDocIds[0], annotations: [{ type: "text", page: 1, x: 50, y: 50, content: annotationText, font_size: 14, color: "#e11d48" }] };
          break;
        case "compare":
          if (selectedDocIds.length === 0 || !docBId) throw new Error("Select both Document A and Document B to compare.");
          endpoint = "/api/operations/compare";
          payload = { document_id_a: selectedDocIds[0], document_id_b: docBId };
          break;
        case "ocr":
          if (selectedDocIds.length === 0) throw new Error("Select a document.");
          endpoint = "/api/operations/ocr";
          payload = { document_id: selectedDocIds[0], language: ocrLang };
          break;
        default:
          throw new Error("Unknown tool requested.");
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Operation failed.");
      }

      const data = await res.json();
      if (toolId === "compare") {
        setCompareResult(data);
      } else if (Array.isArray(data)) {
        setResultOutputs(data);
      } else {
        setResultOutput(data);
      }
    } catch (err: any) {
      setError(err.message || "An error occurred.");
    } finally {
      setProcessing(false);
    }
  };

  const getToolTitle = () => {
    const titles: Record<string, string> = {
      "merge": "Merge PDF Documents",
      "split": "Split PDF Pages",
      "reorder-rotate": "Reorder & Rotate Pages",
      "crop": "Crop PDF Margins",
      "rotate": "Rotate PDF Pages",
      "page-numbers": "Add Page Numbers",
      "compress": "Compress PDF Size",
      "repair": "Repair Damaged PDF",
      "pdf-to-pdfa": "Convert to PDF/A ISO Archive",
      "pdf-to-word": "Convert PDF to Word (.docx)",
      "pdf-to-excel": "Convert PDF to Excel (.xlsx)",
      "pdf-to-powerpoint": "Convert PDF to PowerPoint (.pptx)",
      "pdf-to-images": "Export PDF Pages to Images (.zip)",
      "pdf-to-markdown": "Convert PDF to Markdown (.md)",
      "html-to-pdf": "Convert HTML to PDF",
      "convert-office": "Convert Office to PDF",
      "watermark": "Watermark PDF",
      "redact": "Redact Sensitive Content",
      "protect": "Protect PDF with Password",
      "unlock": "Unlock / Decrypt PDF",
      "edit": "Edit / Annotate PDF",
      "compare": "Compare Two PDFs Side-by-Side",
      "ocr": "OCR Searchable PDF Generator",
      "inspect": "PDF Structure Inspector"
    };
    return titles[toolId] || "PDF Workspace";
  };

  return (
    <div className="space-y-6 pb-12">
      <ScrollReveal direction="up">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <Link href="/" className="p-2.5 hover:bg-white dark:hover:bg-slate-800 rounded-xl text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800 transition-colors shadow-sm">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{getToolTitle()}</h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Offline & Local Workspace</p>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Step 1: Input / File Dropzone */}
      {toolId !== "html-to-pdf" && (
        <ScrollReveal direction="up" delay={0.1}>
          <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <h2 className="font-extrabold text-slate-900 dark:text-white text-base">1. Drop or Select File(s)</h2>
              <div className="flex items-center gap-2">
                {selectedDocIds.length > 0 && (
                  <button
                    onClick={handleClearSelection}
                    className="text-xs font-bold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 transition-colors flex items-center gap-1"
                  >
                    <X className="w-3.5 h-3.5" /> Deselect All
                  </button>
                )}
                {documents.length > 0 && (
                  <button
                    onClick={handleClearAllDocuments}
                    className="text-xs font-bold text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 px-2.5 py-1 rounded-lg border border-rose-200 dark:border-rose-800/60 transition-colors flex items-center gap-1"
                    title="Delete all documents from local store"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Clear All Files
                  </button>
                )}
              </div>
            </div>

            <FileDropzone onFilesUploaded={handleFilesUpload} multiple={toolId === "merge"} compact={documents.length > 0} />
            
            {documents.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
                {documents.map((doc) => {
                  const isSelected = selectedDocIds.includes(doc.id);
                  return (
                    <div
                      key={doc.id}
                      onClick={() => {
                        if (toolId === "merge") {
                          setSelectedDocIds(prev => isSelected ? prev.filter(id => id !== doc.id) : [...prev, doc.id]);
                        } else {
                          setSelectedDocIds([doc.id]);
                        }
                      }}
                      className={`p-3.5 rounded-2xl border cursor-pointer transition-all flex items-center justify-between gap-2 ${
                        isSelected 
                          ? "border-rose-500 bg-rose-50/60 dark:bg-rose-950/30 ring-1 ring-rose-500/30" 
                          : "border-slate-200 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-800/50"
                      }`}
                    >
                      <div className="min-w-0">
                        <p className="font-bold text-xs text-slate-900 dark:text-white truncate">{doc.filename}</p>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400">{doc.page_count} pages</p>
                      </div>
                      <input type="checkbox" checked={isSelected} onChange={() => {}} className="accent-rose-600 rounded w-4 h-4" />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </ScrollReveal>
      )}

      {/* Step 2: Tool Config */}
      <ScrollReveal direction="up" delay={0.15}>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm space-y-4">
          <h2 className="font-extrabold text-slate-900 dark:text-white text-base">2. Configure Options</h2>

          {toolId === "html-to-pdf" && (
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block">HTML / Markup Content:</label>
              <textarea
                value={htmlContent}
                onChange={(e) => setHtmlContent(e.target.value)}
                rows={6}
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-3 text-xs font-mono bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>
          )}

          {toolId === "protect" && (
            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Set Password to Encrypt:</label>
              <input
                type="password"
                value={protectPassword}
                onChange={(e) => setProtectPassword(e.target.value)}
                placeholder="Enter password..."
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-sm bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>
          )}

          {toolId === "unlock" && (
            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Enter Password to Remove Encryption:</label>
              <input
                type="password"
                value={unlockPassword}
                onChange={(e) => setUnlockPassword(e.target.value)}
                placeholder="Enter document password..."
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-sm bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              />
            </div>
          )}

          {toolId === "compare" && (
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block">Select Second Document (Document B):</label>
              <select
                value={docBId}
                onChange={(e) => setDocBId(e.target.value)}
                className="w-full border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-sm bg-slate-50/50 dark:bg-slate-800 text-slate-900 dark:text-white"
              >
                <option value="">-- Choose second document --</option>
                {documents.map((d) => (
                  <option key={d.id} value={d.id}>{d.filename}</option>
                ))}
              </select>
            </div>
          )}

          {toolId === "rotate" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Angle:</label>
                <select value={rotateAngle} onChange={(e) => setRotateAngle(parseInt(e.target.value))} className="w-full border rounded-xl p-2.5 text-sm dark:bg-slate-800">
                  <option value={90}>90° Clockwise</option>
                  <option value={180}>180° Flip</option>
                  <option value={270}>270° (90° Counter-Clockwise)</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Pages Selection:</label>
                <select value={rotateSelection} onChange={(e) => setRotateSelection(e.target.value)} className="w-full border rounded-xl p-2.5 text-sm dark:bg-slate-800">
                  <option value="all">All Pages</option>
                  <option value="odd">Odd Pages Only</option>
                  <option value="even">Even Pages Only</option>
                </select>
              </div>
            </div>
          )}

          {toolId === "crop" && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Top Crop %:</label>
                <input type="number" min={0} max={45} value={cropTop} onChange={(e) => setCropTop(parseFloat(e.target.value) || 0)} className="w-full border rounded-xl p-2 text-sm dark:bg-slate-800" />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Bottom Crop %:</label>
                <input type="number" min={0} max={45} value={cropBottom} onChange={(e) => setCropBottom(parseFloat(e.target.value) || 0)} className="w-full border rounded-xl p-2 text-sm dark:bg-slate-800" />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Left Crop %:</label>
                <input type="number" min={0} max={45} value={cropLeft} onChange={(e) => setCropLeft(parseFloat(e.target.value) || 0)} className="w-full border rounded-xl p-2 text-sm dark:bg-slate-800" />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Right Crop %:</label>
                <input type="number" min={0} max={45} value={cropRight} onChange={(e) => setCropRight(parseFloat(e.target.value) || 0)} className="w-full border rounded-xl p-2 text-sm dark:bg-slate-800" />
              </div>
            </div>
          )}

          {toolId === "edit" && (
            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Annotation Note Text:</label>
              <input type="text" value={annotationText} onChange={(e) => setAnnotationText(e.target.value)} className="w-full border rounded-xl p-2.5 text-sm dark:bg-slate-800" />
            </div>
          )}

          {toolId === "ocr" && (
            <div>
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-2">OCR Language:</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {[
                  { lang: "eng", name: "English", flag: "🇺🇸" },
                  { lang: "deu", name: "Deutsch", flag: "🇩🇪" },
                  { lang: "tur", name: "Türkçe", flag: "🇹🇷" },
                  { lang: "spa", name: "Español", flag: "🇪🇸" },
                ].map((item) => (
                  <button
                    key={item.lang}
                    onClick={() => setOcrLang(item.lang)}
                    className={`flex items-center gap-2 px-3 py-2 border rounded-xl text-xs font-bold transition-all ${
                      ocrLang === item.lang
                        ? "bg-rose-50 dark:bg-rose-950/40 border-rose-300 dark:border-rose-700 text-rose-700 dark:text-rose-300"
                        : "bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400"
                    }`}
                  >
                    {item.flag} {item.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {toolId === "page-numbers" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Format Pattern:</label>
                <input type="text" value={pageNumberFormat} onChange={(e) => setPageNumberFormat(e.target.value)} className="w-full border rounded-xl p-2.5 text-sm dark:bg-slate-800" />
              </div>
              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1">Position:</label>
                <select value={pageNumberPos} onChange={(e) => setPageNumberPos(e.target.value)} className="w-full border rounded-xl p-2.5 text-sm dark:bg-slate-800">
                  <option value="bottom-center">Bottom Center</option>
                  <option value="bottom-left">Bottom Left</option>
                  <option value="bottom-right">Bottom Right</option>
                  <option value="top-center">Top Center</option>
                </select>
              </div>
            </div>
          )}

          {toolId === "reorder-rotate" && (
            <div className="space-y-3">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block">Click pages to rotate 90°:</label>
              <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
                {pageItems.map((item, idx) => (
                  <div key={idx} onClick={() => handleRotatePage(idx)} className="p-4 border rounded-2xl bg-slate-50 dark:bg-slate-800 hover:border-rose-400 cursor-pointer text-center space-y-1">
                    <span className="text-xs font-bold block">Page {item.page_index + 1}</span>
                    <span className="text-[11px] text-rose-600 font-bold">{item.rotation}°</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              onClick={handleRunOperation}
              disabled={processing}
              className="bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold px-8 py-3.5 rounded-2xl shadow-lg flex items-center gap-2 text-sm transition-all disabled:opacity-50 hover:scale-[1.02]"
            >
              {processing ? <><RefreshCw className="w-4 h-4 animate-spin" /> Processing...</> : <><CheckCircle className="w-4 h-4" /> Run {getToolTitle()}</>}
            </button>
          </div>
        </div>
      </ScrollReveal>

      {error && (
        <div className="p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 rounded-2xl text-sm font-medium">
          {error}
        </div>
      )}

      {/* Compare Result */}
      {compareResult && (
        <ScrollReveal direction="scale">
          <div className="bg-slate-900 text-white p-6 rounded-3xl space-y-4 shadow-xl border border-slate-800">
            <h3 className="font-black text-lg flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-rose-400" /> Compare Analysis Result
            </h3>
            <div className="flex gap-6 text-sm">
              <span className="bg-slate-800 px-3 py-1.5 rounded-xl">Similarity: <strong>{compareResult.similarity_percentage}%</strong></span>
              <span className="bg-slate-800 px-3 py-1.5 rounded-xl">Doc A: {compareResult.doc_a_pages} pages</span>
              <span className="bg-slate-800 px-3 py-1.5 rounded-xl">Doc B: {compareResult.doc_b_pages} pages</span>
            </div>
            {compareResult.diff_lines?.length > 0 && (
              <div className="bg-slate-950 p-4 rounded-xl font-mono text-xs max-h-60 overflow-y-auto space-y-1">
                {compareResult.diff_lines.map((l: string, i: number) => (
                  <div key={i} className={l.startsWith("+") ? "text-emerald-400" : l.startsWith("-") ? "text-rose-400" : "text-slate-400"}>{l}</div>
                ))}
              </div>
            )}
          </div>
        </ScrollReveal>
      )}

      {/* Output Results */}
      {resultOutput && (
        <ScrollReveal direction="scale">
          <div className="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-300 dark:border-emerald-800 rounded-3xl p-6 space-y-4 shadow-md">
            <div className="flex items-center gap-2 font-bold text-emerald-950 dark:text-emerald-200 text-lg">
              <CheckCircle className="w-6 h-6 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>Operation Completed Successfully!</span>
            </div>
            <div className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-emerald-200 dark:border-emerald-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
              <div>
                <p className="font-extrabold text-sm text-slate-900 dark:text-white">{resultOutput.filename}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">SHA-256: {resultOutput.sha256}</p>
              </div>
              <a
                href={`/api/operations/outputs/${resultOutput.id}/download`}
                download
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 shadow-md shrink-0"
              >
                <Download className="w-4 h-4" /> Download Result File
              </a>
            </div>
          </div>
        </ScrollReveal>
      )}
    </div>
  );
}
