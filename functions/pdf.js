import { PDFDocument } from 'pdf-lib';

export async function onRequest() {

  const imageUrls = [
    "https://briefhub-wx.pages.dev/images/ASAS_Latest.png",
    "https://briefhub-wx.pages.dev/images/ASAS_Prior.png",
    "https://briefhub-wx.pages.dev/images/FSAS_Latest.png",
    "https://briefhub-wx.pages.dev/images/AUPQ35_Latest.png",
    "https://briefhub-wx.pages.dev/images/AUPQ78_Latest.png",
    "https://briefhub-wx.pages.dev/images/FXFE502_Latest.png",
    "https://briefhub-wx.pages.dev/images/FXFE5782_Latest.png",
    "https://briefhub-wx.pages.dev/images/FBJP_Latest.png",
    "https://briefhub-wx.pages.dev/images/FBOS39_Latest.png",
    "https://briefhub-wx.pages.dev/images/FXJP106_Latest.png",
    "https://briefhub-wx.pages.dev/images/FXJP854_Latest.png",
    "https://briefhub-wx.pages.dev/images/Sakurajima_Ashfall_Latest.png",
    "https://briefhub-wx.pages.dev/images/Kirishimayama_Ashfall_Latest.png"
  ];

  const pdf = await PDFDocument.create();

  for (const url of imageUrls) {
    const res = await fetch(url);
    const imgBytes = await res.arrayBuffer();

    const image = await pdf.embedPng(imgBytes);
    const page = pdf.addPage([image.width, image.height]);

    page.drawImage(image, {
      x: 0,
      y: 0,
      width: image.width,
      height: image.height
    });
  }

  const pdfBytes = await pdf.save();

  return new Response(pdfBytes, {
    headers: {
      "Content-Type": "application/pdf",
      "Content-Disposition": "attachment; filename=weather_charts.pdf"
    }
  });
}
