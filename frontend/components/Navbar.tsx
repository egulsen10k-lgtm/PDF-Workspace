"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import ThemeToggle from "@/components/ThemeToggle";
import { 
  ShieldAlert, Wrench, PenTool, History, Download, HardDrive, 
  Sparkles, LogOut, GitBranch, ChevronDown, Combine, Scissors, 
  RotateCw, Crop, Hash, Minimize2, FileText, FileSpreadsheet, 
  Layers, FileImage, FileDown, Stamp, Lock, Unlock, EyeOff 
} from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuth();
  const [isToolsOpen, setIsToolsOpen] = useState(false);

  const toolCategories = [
    {
      title: "Organize",
      items: [
        { label: "Merge", href: "/tools/merge", icon: Combine },
        { label: "Split", href: "/tools/split", icon: Scissors },
        { label: "Reorder & Rotate", href: "/tools/reorder-rotate", icon: RotateCw },
        { label: "Crop", href: "/tools/crop", icon: Crop },
        { label: "Page Numbers", href: "/tools/page-numbers", icon: Hash },
      ]
    },
    {
      title: "Convert",
      items: [
        { label: "PDF to Word", href: "/tools/pdf-to-word", icon: FileText },
        { label: "PDF to Excel", href: "/tools/pdf-to-excel", icon: FileSpreadsheet },
        { label: "PDF to PPTX", href: "/tools/pdf-to-powerpoint", icon: Layers },
        { label: "PDF to Images", href: "/tools/pdf-to-images", icon: FileImage },
        { label: "HTML/Office to PDF", href: "/tools/convert-office", icon: FileDown },
      ]
    },
    {
      title: "Security & Edit",
      items: [
        { label: "Protect", href: "/tools/protect", icon: Lock },
        { label: "Unlock", href: "/tools/unlock", icon: Unlock },
        { label: "Redact", href: "/tools/redact", icon: EyeOff },
        { label: "Watermark", href: "/tools/watermark", icon: Stamp },
        { label: "Edit/Annotate", href: "/tools/edit", icon: PenTool },
      ]
    }
  ];

  const navItems = [
    { label: "Studio Hub", href: "/", icon: Wrench },
    { label: "My Store", href: "/documents", icon: HardDrive },
    { label: "Versions", href: "/versions", icon: GitBranch },
    { label: "Audit Logs", href: "/audit", icon: History },
  ];

  if (pathname === "/login") return null;

  return (
    <header className="w-full bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800 sticky top-0 z-[100] transition-all shadow-sm">
      <div className="bg-gradient-to-r from-amber-500 via-rose-500 to-amber-500 text-slate-950 px-4 py-1 text-[10px] font-semibold flex items-center justify-center gap-2">
        <ShieldAlert className="w-3 h-3" />
        <span>Personal & Low-Stakes Use Only: 100% Local Storage.</span>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 group">
          <div className="bg-gradient-to-br from-rose-500 to-rose-700 text-white px-2 py-1 rounded-lg font-black text-sm shadow-lg flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> PDF
          </div>
          <span className="font-extrabold text-sm text-slate-900 dark:text-white">ILovePDF <span className="text-rose-600">Premium</span></span>
        </Link>

        <nav className="flex items-center gap-4">
          <div 
            className="relative"
            onMouseEnter={() => setIsToolsOpen(true)}
            onMouseLeave={() => setIsToolsOpen(false)}
          >
            <button className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:text-rose-600 transition-colors py-2">
              <Sparkles className="w-4 h-4 text-rose-500" /> PDF Tools <ChevronDown className="w-3 h-3" />
            </button>
            
            {isToolsOpen && (
              <div className="absolute top-full left-[-220px] w-[620px] pt-3 animate-in fade-in zoom-in-95 duration-200">
                <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-3xl border border-slate-200/80 dark:border-slate-800/80 rounded-3xl p-6 shadow-2xl grid grid-cols-3 gap-6">
                  {toolCategories.map((cat) => (
                    <div key={cat.title}>
                      <h4 className="text-[10px] uppercase tracking-widest font-black text-rose-600 dark:text-rose-400 mb-3">{cat.title}</h4>
                      <div className="space-y-1">
                        {cat.items.map((item) => (
                          <Link key={item.href} href={item.href} className="flex items-center gap-2.5 p-2 rounded-xl hover:bg-rose-50 dark:hover:bg-rose-950/40 text-xs font-medium text-slate-700 dark:text-slate-300 transition-colors">
                            <item.icon className="w-3.5 h-3.5 text-rose-500" /> {item.label}
                          </Link>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:text-rose-600 transition-colors">
                <Icon className="w-3.5 h-3.5" /> <span className="hidden md:inline">{item.label}</span>
              </Link>
            );
          })}

          <div className="pl-2 border-l border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <ThemeToggle />
            {isAuthenticated && (
              <button onClick={logout} className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors"><LogOut className="w-4 h-4" /></button>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
}