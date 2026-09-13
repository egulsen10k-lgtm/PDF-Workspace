"use client";

import { useEffect, useState, useRef, use } from "react";
import { PenTool, CheckCircle, ShieldAlert, Download, RefreshCw, AlertTriangle } from "lucide-react";

export default function SignerPortalPage({ params }: { params: Promise<{ token: string }> }) {
  const resolvedParams = use(params);
  const token = resolvedParams.token;

  const [sigReq, setSigReq] = useState<any>(null);
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [signedOutput, setSignedOutput] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const [consentGiven, setConsentGiven] = useState<boolean>(false);
  const [typedName, setTypedName] = useState<string>("");
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);

  useEffect(() => {
    fetch(`/api/signatures/request/${token}`)
      .then(res => {
        if (!res.ok) throw new Error("Invalid or expired signature access token.");
        return res.json();
      })
      .then(data => {
        setSigReq(data);
        setTypedName(data.signer_name || "");
        return fetch(`/api/documents/${data.document_id}`);
      })
      .then(res => res.json())
      .then(data => setDoc(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  // Setup signature canvas
  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.strokeStyle = "#0f172a";
        ctx.lineWidth = 3;
        ctx.lineCap = "round";
      }
    }
  }, [sigReq]);

  const startDrawing = (e: any) => {
    setIsDrawing(true);
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    ctx?.beginPath();
    ctx?.moveTo(x, y);
  };

  const draw = (e: any) => {
    if (!isDrawing || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX || e.touches?.[0]?.clientX) - rect.left;
    const y = (e.clientY || e.touches?.[0]?.clientY) - rect.top;
    ctx?.lineTo(x, y);
    ctx?.stroke();
  };

  const stopDrawing = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    ctx?.clearRect(0, 0, canvas.width, canvas.height);
  };

  const handleSubmitSignature = async () => {
    if (!consentGiven) {
      setError("You must check the consent agreement checkbox to complete electronic signing.");
      return;
    }

    setSubmitting(true);
    setError(null);

    let dataUrl = "";
    if (canvasRef.current) {
      dataUrl = canvasRef.current.toDataURL("image/png");
    }

    try {
      const res = await fetch("/api/signatures/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          access_token: token,
          consent_given: true,
          consent_text: "I hereby explicitly consent to sign this document electronically for personal/internal record purposes.",
          signature_data: dataUrl,
          typed_name: typedName
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Signature submission failed.");
      }

      const outputData = await res.json();
      setSignedOutput(outputData);
    } catch (err: any) {
      setError(err.message || "Failed to complete signature.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-rose-600" />
        Loading Signer Portal...
      </div>
    );
  }

  if (error && !sigReq) {
    return (
      <div className="max-w-md mx-auto p-6 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-center space-y-3">
        <AlertTriangle className="w-10 h-10 text-rose-600 mx-auto" />
        <h2 className="font-bold text-lg">Invalid Access Token</h2>
        <p className="text-xs text-rose-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Warning banner */}
      <div className="bg-amber-500 text-slate-950 p-3 rounded-xl text-xs font-semibold flex items-center gap-2">
        <ShieldAlert className="w-5 h-5 shrink-0" />
        <span>Simple Self-Hosted Electronic Signature — Personal Record Only (Not a QES certificate).</span>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="border-b pb-4">
          <h1 className="text-2xl font-extrabold text-slate-900">Sign Document</h1>
          <p className="text-xs text-slate-500 mt-1">
            Recipient: <strong>{sigReq.signer_name}</strong> ({sigReq.signer_email}) &bull; Document: <strong>{doc?.filename}</strong>
          </p>
        </div>

        {/* Document Preview Thumbnail */}
        {doc && (
          <div className="bg-slate-100 p-4 rounded-xl flex items-center justify-center">
            <img
              src={`/api/documents/${doc.id}/preview?page=1`}
              alt="Document Page 1"
              className="max-h-[300px] border shadow-sm rounded"
            />
          </div>
        )}

        {!signedOutput ? (
          <div className="space-y-6 pt-2">
            {/* Draw Signature Canvas */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-slate-700">Draw Your Signature:</label>
                <button onClick={clearCanvas} className="text-xs text-rose-600 font-semibold hover:underline">Clear Canvas</button>
              </div>

              <canvas
                ref={canvasRef}
                width={600}
                height={160}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                onTouchStart={startDrawing}
                onTouchMove={draw}
                onTouchEnd={stopDrawing}
                className="w-full bg-slate-50 border-2 border-dashed border-slate-300 rounded-xl cursor-crosshair touch-none"
              />
            </div>

            {/* Electronic Consent Checkbox */}
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={consentGiven}
                  onChange={(e) => setConsentGiven(e.target.checked)}
                  className="mt-0.5 w-4 h-4 accent-rose-600 rounded"
                />
                <span className="text-xs text-slate-700 font-medium leading-relaxed">
                  I explicitly consent to apply my electronic signature to this document for personal/internal record purposes, and understand that an append-only audit log with timestamp, IP address, and document hashes will be generated.
                </span>
              </label>
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs font-medium">
                {error}
              </div>
            )}

            <button
              onClick={handleSubmitSignature}
              disabled={submitting || !consentGiven}
              className="w-full bg-rose-600 hover:bg-rose-700 text-white font-bold py-3 rounded-xl shadow-md text-sm transition-all disabled:opacity-50"
            >
              {submitting ? "Sealing Document Hash..." : "Seal & Complete Signature"}
            </button>
          </div>
        ) : (
          <div className="bg-emerald-50 border border-emerald-300 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 font-bold text-emerald-950 text-lg">
              <CheckCircle className="w-6 h-6 text-emerald-600" />
              <span>Document Signed & Sealed Successfully!</span>
            </div>

            <p className="text-xs text-emerald-900 leading-relaxed">
              Final Sealed PDF Hash (SHA-256): <br />
              <code className="font-mono bg-white px-2 py-1 rounded border border-emerald-300 text-slate-800 font-bold block mt-1">
                {signedOutput.sha256}
              </code>
            </p>

            <div className="pt-2">
              <a
                href={`/api/operations/outputs/${signedOutput.id}/download`}
                download
                className="inline-flex items-center gap-2 bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-6 py-3 rounded-xl shadow-md text-sm transition-all"
              >
                <Download className="w-4 h-4" /> Download Sealed Signed PDF
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
