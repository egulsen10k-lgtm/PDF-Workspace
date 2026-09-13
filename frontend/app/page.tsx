"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import ScrollReveal from "@/components/ScrollReveal";
import FileDropzone from "@/components/FileDropzone";
import { 
  Combine, Scissors, RotateCw, Minimize2, Stamp, EyeOff, ScanText, FileSpreadsheet,
  Search, PenTool, ShieldAlert, ArrowRight, FileText, ShieldCheck, HardDrive,
  History, Sparkles, Layers, Lock, Unlock, FileImage, FileDown, AlignLeft,
  Crop, Hash, Wrench, Copy, Code, GitCompare, Files
} from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState<string | null>(null);

  const handleQuickUpload = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    for (let i = 0; i < files.length; i++) {
      const formData = new FormData();
      formData.append("file", files[i]);
      try { await fetch("/api/documents/upload", { method: "POST", body: formData }); } catch {}
    }
    setUploadSuccessMessage(`Uploaded ${files.length} file(s)! Redirecting to store...`);
    setTimeout(() => router.push("/documents"), 800);
  };

  const toolGroups = [
    {
      group: "Organize PDF",
      tools: [
        { id: "merge", title: "Merge PDF", desc: "Combine multiple PDFs into one ordered document.", icon: Combine, color: "from-blue-500 to-indigo-600", badge: "Multi-file", href: "/tools/merge" },
        { id: "split", title: "Split PDF", desc: "Extract page ranges into independent PDF files.", icon: Scissors, color: "from-indigo-500 to-purple-600", badge: "Range Select", href: "/tools/split" },
        { id: "reorder-rotate", title: "Reorder & Rotate", desc: "Rearrange pages and apply 90°/180°/270° rotations.", icon: RotateCw, color: "from-teal-400 to-emerald-600", badge: "Visual", href: "/tools/reorder-rotate" },
        { id: "crop", title: "Crop PDF", desc: "Crop margins or select crop areas by percentage.", icon: Crop, color: "from-orange-400 to-amber-600", badge: "Margin Trim", href: "/tools/crop" },
        { id: "rotate", title: "Rotate PDF", desc: "Rotate all or specific pages at any angle.", icon: RotateCw, color: "from-cyan-400 to-sky-600", badge: "Bulk Rotate", href: "/tools/rotate" },
        { id: "page-numbers", title: "Page Numbers", desc: "Add custom page numbers with position and font.", icon: Hash, color: "from-slate-500 to-slate-700", badge: "Stamps", href: "/tools/page-numbers" },
      ]
    },
    {
      group: "Optimize & Repair PDF",
      tools: [
        { id: "compress", title: "Compress PDF", desc: "Reduce file size with 3 quality levels.", icon: Minimize2, color: "from-emerald-500 to-green-600", badge: "3 Levels", href: "/tools/compress" },
        { id: "repair", title: "Repair PDF", desc: "Recover data from damaged or corrupt PDFs.", icon: Wrench, color: "from-rose-500 to-red-600", badge: "Auto-Fix", href: "/tools/repair" },
        { id: "pdf-to-pdfa", title: "PDF to PDF/A", desc: "Convert to ISO-standard PDF/A for long-term archiving.", icon: Files, color: "from-violet-500 to-purple-700", badge: "ISO Archive", href: "/tools/pdf-to-pdfa" },
      ]
    },
    {
      group: "Convert PDF",
      tools: [
        { id: "pdf-to-word", title: "PDF to Word", desc: "Export PDF text structure into editable DOCX.", icon: FileText, color: "from-blue-600 to-blue-700", badge: "DOCX Export", href: "/tools/pdf-to-word" },
        { id: "pdf-to-excel", title: "PDF to Excel", desc: "Extract tabular data into multi-sheet XLSX.", icon: FileSpreadsheet, color: "from-green-600 to-emerald-700", badge: "XLSX Tables", href: "/tools/pdf-to-excel" },
        { id: "pdf-to-powerpoint", title: "PDF to PowerPoint", desc: "Turn PDF pages into editable slide decks.", icon: Layers, color: "from-orange-500 to-red-600", badge: "PPTX Slides", href: "/tools/pdf-to-powerpoint" },
        { id: "pdf-to-images", title: "PDF to Images", desc: "Export each page as high-res JPG/PNG in a ZIP.", icon: FileImage, color: "from-pink-500 to-rose-600", badge: "JPG/PNG ZIP", href: "/tools/pdf-to-images" },
        { id: "pdf-to-markdown", title: "PDF to Markdown", desc: "Extract text, headings, and tables to Markdown files.", icon: Code, color: "from-slate-500 to-slate-700", badge: ".md Export", href: "/tools/pdf-to-markdown" },
        { id: "html-to-pdf", title: "HTML to PDF", desc: "Convert HTML markup or rich text to PDF.", icon: AlignLeft, color: "from-amber-500 to-orange-600", badge: "HTML Input", href: "/tools/html-to-pdf" },
        { id: "convert-office", title: "Office to PDF", desc: "Convert DOCX, XLSX, PPTX to PDF via LibreOffice.", icon: FileDown, color: "from-sky-400 to-blue-600", badge: "LibreOffice", href: "/tools/convert-office" },
      ]
    },
    {
      group: "Edit PDF",
      tools: [
        { id: "edit", title: "Edit / Annotate PDF", desc: "Add text notes, shapes, highlights at exact coordinates.", icon: PenTool, color: "from-indigo-500 to-purple-600", badge: "Annotations", href: "/tools/edit" },
        { id: "watermark", title: "Watermark PDF", desc: "Stamp custom text overlays with opacity and position.", icon: Stamp, color: "from-amber-400 to-orange-600", badge: "Custom Grid", href: "/tools/watermark" },
        { id: "forms", title: "PDF Forms & Fill", desc: "Detect AcroForm fields and fill interactive PDF forms.", icon: Copy, color: "from-emerald-400 to-teal-600", badge: "AcroForms", href: "/tools/forms" },
      ]
    },
    {
      group: "PDF Security",
      tools: [
        { id: "protect", title: "Protect PDF", desc: "Encrypt PDF with a password to secure access.", icon: Lock, color: "from-rose-600 to-red-700", badge: "AES-256", href: "/tools/protect" },
        { id: "unlock", title: "Unlock PDF", desc: "Remove password encryption if you know the password.", icon: Unlock, color: "from-amber-500 to-yellow-600", badge: "Decrypt", href: "/tools/unlock" },
        { id: "redact", title: "Redact PDF", desc: "Permanently blackout sensitive keywords and areas.", icon: EyeOff, color: "from-slate-700 to-slate-900", badge: "Blackout", href: "/tools/redact" },
      ]
    },
    {
      group: "PDF Intelligence",
      tools: [
        { id: "ocr", title: "OCR PDF", desc: "Recognize scanned text with local Tesseract engine.", icon: ScanText, color: "from-purple-500 to-violet-600", badge: "Tesseract", href: "/tools/ocr" },
        { id: "compare", title: "Compare PDF", desc: "Side-by-side text diff with similarity percentage.", icon: GitCompare, color: "from-cyan-500 to-blue-600", badge: "Unified Diff", href: "/tools/compare" },
        { id: "inspect", title: "PDF Inspector", desc: "Analyze fonts, forms, signatures & encryption.", icon: Search, color: "from-slate-600 to-slate-800", badge: "Structure Alert", href: "/tools/inspect" },
      ]
    },
    {
      group: "e-Sign",
      tools: [
        { id: "signature", title: "e-Sign Studio", desc: "Place fields, collect consent, seal final PDF hash.", icon: PenTool, color: "from-rose-600 to-pink-600", badge: "Seal Cert", href: "/signature" },
      ]
    }
  ];

  return (
    <div className="space-y-12 pb-12">
      {/* Hero */}
      <ScrollReveal direction="up" duration={0.6}>
        <div className="relative overflow-hidden rounded-3xl bg-slate-950 p-8 sm:p-12 text-white border border-slate-800 shadow-2xl">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-rose-500/15 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-4xl space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-rose-500/10 text-rose-300 text-xs font-semibold border border-rose-500/20 backdrop-blur-md">
              <Sparkles className="w-3.5 h-3.5 text-rose-400" />
              <span>100% Local &bull; 30+ Tools &bull; Offline &bull; Append-Only Audit Log</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-black tracking-tight leading-tight">
              Every PDF Tool You Need. <br />
              <span className="bg-gradient-to-r from-rose-400 via-rose-300 to-amber-300 bg-clip-text text-transparent">
                Private, Local & Auditable.
              </span>
            </h1>
            <p className="text-slate-300 text-base sm:text-lg leading-relaxed max-w-3xl">
              Original documents are preserved immutably. Every transformation creates a versioned output with SHA-256 integrity hashing and complete audit event logging.
            </p>
            <div className="flex flex-wrap gap-4 pt-2">
              <Link href="/documents" className="inline-flex items-center gap-2 bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white px-6 py-3 rounded-2xl font-bold text-sm transition-all shadow-lg shadow-rose-900/30 hover:scale-[1.02]">
                <FileText className="w-4 h-4" /> Open Document Store
              </Link>
              <Link href="/signature" className="inline-flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-2xl font-bold text-sm transition-all border border-slate-700 hover:border-slate-600 shadow-md">
                <PenTool className="w-4 h-4 text-rose-400" /> e-Sign Studio
              </Link>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Quick Dropzone */}
      <ScrollReveal direction="up" delay={0.1}>
        <div className="space-y-3">
          <FileDropzone onFilesUploaded={handleQuickUpload} multiple title="Quick Drag & Drop File Ingestion" subtitle="Drop files anywhere here to instantly upload & store locally" />
          {uploadSuccessMessage && (
            <div className="p-3 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 rounded-xl text-xs font-semibold text-center">
              {uploadSuccessMessage}
            </div>
          )}
        </div>
      </ScrollReveal>

      {/* Feature Badges */}
      <ScrollReveal direction="up" delay={0.15}>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { title: "Immutable Storage", desc: "Originals preserved with SHA-256 hashes.", icon: HardDrive, color: "text-blue-500 bg-blue-50 dark:bg-blue-950/40 dark:text-blue-400" },
            { title: "Versioned Outputs", desc: "Every operation generates a new versioned file.", icon: Layers, color: "text-indigo-500 bg-indigo-50 dark:bg-indigo-950/40 dark:text-indigo-400" },
            { title: "e-Sign Certificate", desc: "Consent timestamp & sealed PDF hash.", icon: ShieldCheck, color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/40 dark:text-emerald-400" },
            { title: "Append-Only Audit", desc: "Tamper-evident event logging.", icon: History, color: "text-purple-500 bg-purple-50 dark:bg-purple-950/40 dark:text-purple-400" },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm flex items-start gap-3.5 hover:shadow-md transition-shadow">
                <div className={`p-2.5 rounded-xl ${item.color} shrink-0`}><Icon className="w-5 h-5" /></div>
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-white text-sm">{item.title}</h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollReveal>

      {/* Tool Groups */}
      {toolGroups.map((group, gIdx) => (
        <div key={group.group} className="space-y-5">
          <ScrollReveal direction="up" delay={0.1}>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-black text-slate-900 dark:text-white tracking-tight">{group.group}</h2>
              <span className="text-[11px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2.5 py-1 rounded-full border border-slate-200 dark:border-slate-700">{group.tools.length} tools</span>
            </div>
          </ScrollReveal>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {group.tools.map((tool, idx) => {
              const Icon = tool.icon;
              return (
                <ScrollReveal key={tool.id} direction="scale" delay={0.04 * (idx % 4)}>
                  <Link
                    href={tool.href}
                    className="group bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200/80 dark:border-slate-800 hover:border-rose-400/80 dark:hover:border-rose-500/60 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col justify-between h-full relative overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-rose-50/0 to-rose-50/30 dark:from-rose-950/0 dark:to-rose-950/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                    <div className="space-y-3 relative z-10">
                      <div className="flex items-center justify-between">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${tool.color} text-white flex items-center justify-center shadow-md group-hover:scale-110 transition-transform duration-300`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-slate-700">{tool.badge}</span>
                      </div>
                      <div>
                        <h3 className="font-extrabold text-slate-900 dark:text-white text-sm group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">{tool.title}</h3>
                        <p className="text-slate-500 dark:text-slate-400 text-xs mt-1 leading-relaxed">{tool.desc}</p>
                      </div>
                    </div>
                    <div className="pt-4 flex items-center justify-between text-xs font-bold text-rose-600 dark:text-rose-400 relative z-10 border-t border-slate-100 dark:border-slate-800 mt-3">
                      <span>Launch</span>
                      <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </Link>
                </ScrollReveal>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
