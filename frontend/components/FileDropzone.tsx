"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { UploadCloud, FileText, Sparkles, AlertCircle } from "lucide-react";

interface FileDropzoneProps {
  onFilesUploaded: (files: FileList | File[]) => Promise<void> | void;
  accept?: string;
  multiple?: boolean;
  title?: string;
  subtitle?: string;
  compact?: boolean;
  className?: string;
}

export default function FileDropzone({
  onFilesUploaded,
  accept = ".pdf,.docx,.xlsx,.pptx",
  multiple = false,
  title = "Drag & Drop your PDF or Office files here",
  subtitle = "Supports PDF, DOCX, XLSX, PPTX (Up to 100MB)",
  compact = false,
  className = "",
}: FileDropzoneProps) {
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    // Only set dragging false if leaving the container
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragging(false);
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      setIsUploading(true);
      try {
        await onFilesUploaded(files);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setIsUploading(true);
      try {
        await onFilesUploaded(files);
      } finally {
        setIsUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = "";
      }
    }
  };

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
      className={`relative rounded-3xl border-2 border-dashed transition-all duration-300 cursor-pointer flex flex-col items-center justify-center text-center overflow-hidden group ${
        isDragging
          ? "border-rose-500 bg-rose-50/80 dark:bg-rose-950/30 ring-4 ring-rose-500/20 scale-[1.01]"
          : "border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-slate-900/60 hover:border-rose-400 dark:hover:border-rose-500/60 hover:bg-rose-50/30 dark:hover:bg-rose-950/10 shadow-sm"
      } ${compact ? "p-4 sm:p-6" : "p-8 sm:p-12"} ${className}`}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Subtle Background Glow when dragging */}
      {isDragging && (
        <div className="absolute inset-0 bg-gradient-to-br from-rose-500/10 to-indigo-500/10 animate-pulse pointer-events-none" />
      )}

      <div className="relative z-10 flex flex-col items-center space-y-3">
        <div
          className={`rounded-2xl flex items-center justify-center transition-transform duration-300 ${
            isDragging
              ? "bg-rose-600 text-white scale-110 shadow-lg shadow-rose-900/40"
              : "bg-white dark:bg-slate-800 text-rose-600 dark:text-rose-400 border border-slate-200 dark:border-slate-700 shadow-md group-hover:scale-105"
          } ${compact ? "w-10 h-10" : "w-16 h-16"}`}
        >
          {isUploading ? (
            <div className="w-6 h-6 border-2 border-rose-500 border-t-transparent rounded-full animate-spin" />
          ) : isDragging ? (
            <Sparkles className={compact ? "w-5 h-5" : "w-8 h-8"} />
          ) : (
            <UploadCloud className={compact ? "w-5 h-5" : "w-8 h-8"} />
          )}
        </div>

        <div className="space-y-1">
          <p className="font-extrabold text-sm sm:text-base text-slate-900 dark:text-white group-hover:text-rose-600 dark:group-hover:text-rose-400 transition-colors">
            {isUploading ? "Uploading & Inspecting PDF..." : isDragging ? "Drop your files right here!" : title}
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {isUploading ? "Processing local storage blob..." : subtitle}
          </p>
        </div>

        <div className="pt-1">
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-[11px] font-bold bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 shadow-sm group-hover:border-rose-300 dark:group-hover:border-rose-700 transition-colors">
            <FileText className="w-3.5 h-3.5 text-rose-500" />
            <span>Or click to browse files</span>
          </span>
        </div>
      </div>
    </div>
  );
}
