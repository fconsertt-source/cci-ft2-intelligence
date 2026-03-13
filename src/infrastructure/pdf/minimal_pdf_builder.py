from datetime import datetime


def build_minimal_pdf(text: str) -> bytes:
    safe_text = text.replace("(", "\\(").replace(")", "\\)")

    creation = datetime.utcnow().strftime("D:%Y%m%d%H%M%SZ")

    pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R
   /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
72 720 Td
({safe_text}) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font
   /Subtype /Type1
   /BaseFont /Helvetica
   /Encoding /WinAnsiEncoding >>
endobj
6 0 obj
<< /Producer (GuardianFT2)
   /CreationDate ({creation})
   /Title (Fallback PDF) >>
endobj
xref
0 7
0000000000 65535 f
trailer
<< /Size 7 /Root 1 0 R /Info 6 0 R >>
startxref
0
%%EOF
"""
    return pdf.encode("latin-1", errors="ignore")
