import { ImageResponse } from "next/og";

export const dynamic = "force-static";

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          fontSize: 64,
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontFamily: "system-ui",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 20,
            marginBottom: 32,
          }}
        >
          <div
            style={{
              background: "linear-gradient(135deg, #f43f5e 0%, #be123c 100%)",
              padding: "16px 24px",
              borderRadius: 16,
              fontWeight: 900,
              fontSize: 32,
            }}
          >
            PDF
          </div>
          <span style={{ fontSize: 48, fontWeight: 800 }}>ILovePDF</span>
        </div>
        <div style={{ fontSize: 28, opacity: 0.8, marginTop: 16 }}>
          Your 100% Private Local PDF Workstation
        </div>
        <div style={{ fontSize: 20, opacity: 0.6, marginTop: 8 }}>
          Merge • Split • Compress • Watermark • OCR • e-Sign
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  );
}
