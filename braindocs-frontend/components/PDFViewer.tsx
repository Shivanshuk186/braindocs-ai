"use client";

import { Document, Page, pdfjs } from "react-pdf";
import { useState } from "react";

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function PDFViewer({ file }: { file: string }) {
  const [numPages, setNumPages] = useState(0);

  return (
    <div className="border-4 border-black bg-white p-4 shadow-[8px_8px_0px_0px_#000]">

      <h2 className="font-black mb-3 border-b-2 border-black">
        PDF Preview
      </h2>

      <Document
        file={file}
        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
      >
        {Array.from(new Array(numPages), (_, i) => (
          <Page key={i} pageNumber={i + 1} />
        ))}
      </Document>
    </div>
  );
}