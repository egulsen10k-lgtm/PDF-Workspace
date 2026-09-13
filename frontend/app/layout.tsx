import "./globals.css";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/context/AuthContext";

export const metadata = {
  title: {
    default: "ILovePDF Personal — Private PDF Tool & e-Signature Studio",
    template: "%s | ILovePDF Personal",
  },
  description:
    "Your 100% local, private PDF workstation. Merge, split, compress, watermark, redact, OCR, convert Office to PDF, and collect electronic signatures — all stored locally in your user-owned storage.",
  keywords: [
    "pdf merger",
    "pdf splitter",
    "compress pdf",
    "watermark pdf",
    "redact pdf",
    "ocr pdf",
    "convert docx to pdf",
    "electronic signature",
    "pdf editor local",
    "private pdf tool",
    "self-hosted pdf",
  ],
  authors: [{ name: "ILovePDF Personal Local Edition" }],
  robots: "noindex, nofollow",
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "ILovePDF Personal",
    title: "ILovePDF Personal — Your Private PDF Workstation",
    description:
      "100% local, auditable PDF processing: merge, split, compress, watermark, redact, OCR, and simple e-signatures with append-only audit logging.",
  },
  twitter: {
    card: "summary_large_image",
    title: "ILovePDF Personal — Private PDF Workstation",
    description:
      "Local PDF merge, split, compress, watermark, redact, OCR & e-signatures. No cloud uploads. No vendor lock-in.",
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon.png", sizes: "32x32", type: "image/png" },
    ],
    apple: { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
  },
  manifest: "/manifest.json",
  metadataBase: new URL("http://localhost:3000"),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
        <meta name="theme-color" content="#0f172a" />
        <meta name="msapplication-TileColor" content="#be123c" />
        <meta httpEquiv="X-Content-Type-Options" content="nosniff" />
        <meta httpEquiv="X-Frame-Options" content="DENY" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function(){
                var theme = localStorage.getItem('theme');
                if(theme === 'light'){
                  document.documentElement.classList.remove('dark');
                } else {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
            {children}
          </main>
          <footer className="border-t border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-900/60 py-6 text-center text-xs text-slate-500 dark:text-slate-400">
            ILovePDF Personal Replacement &bull; Local Immutable Store &bull; Append-Only Audit Logging &bull; Next.js 15 + FastAPI
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}