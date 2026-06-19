from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

def generate_report(filename, disease, confidence, severity):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(filename)
    elements = []
    elements.append(Paragraph("AI Medical Diagnosis Report", styles['Title']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<b>Disease Detected:</b> {disease}", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Confidence Level:</b> {severity['confidence_percent']}%", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Severity Stage:</b> {severity['stage']}", styles['Normal']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"<b>Medical Recommendation:</b> {severity['advice']}", styles['Normal']))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Italic']))
    doc.build(elements)
