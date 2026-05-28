from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import io

def generate_prescription_pdf(prescription, doctor_name, patient_name):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('title', fontSize=20, spaceAfter=6, textColor=colors.HexColor("#2563eb"), fontName="Helvetica-Bold")
    story.append(Paragraph("Digital Prescription", title_style))
    story.append(Spacer(1, 0.4*cm))

    data = [
        ["Prescription ID:", f"#{prescription.id}"],
        ["Patient:", patient_name],
        ["Doctor:", f"Dr. {doctor_name}"],
        ["Date:", prescription.created_at.strftime("%B %d, %Y")],
    ]
    table = Table(data, colWidths=[4*cm, 12*cm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("<b>Diagnosis:</b>", styles["Normal"]))
    story.append(Paragraph(prescription.diagnosis, styles["Normal"]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("<b>Prescribed Medicines:</b>", styles["Normal"]))
    for med in prescription.medicines.split("\n"):
        if med.strip():
            story.append(Paragraph(f"• {med.strip()}", styles["Normal"]))
    story.append(Spacer(1, 0.4*cm))

    if prescription.instructions:
        story.append(Paragraph("<b>Instructions:</b>", styles["Normal"]))
        story.append(Paragraph(prescription.instructions, styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer