import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from src.models.sell_note import SellNote


def generate_sell_note_pdf(sell_note: SellNote) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], fontSize=20, spaceAfter=4)
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    value_style = ParagraphStyle("value", parent=styles["Normal"], fontSize=10)
    section_style = ParagraphStyle(
        "section",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
    )

    elements = []

    # Title + Folio
    elements.append(Paragraph("NOTA DE VENTA", title_style))
    elements.append(Paragraph(f"Folio: <b>{sell_note.folio}</b>", styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Client information
    elements.append(Paragraph("INFORMACIÓN DEL CLIENTE", section_style))
    client_rows = [
        [Paragraph("Razón Social", label_style), Paragraph(sell_note.client.razon_social, value_style)],
        [Paragraph("Nombre Comercial", label_style), Paragraph(sell_note.client.nombre_comercial, value_style)],
        [Paragraph("RFC", label_style), Paragraph(sell_note.client.rfc, value_style)],
        [Paragraph("Correo electrónico", label_style), Paragraph(sell_note.client.correo_electronico, value_style)],
        [Paragraph("Teléfono", label_style), Paragraph(sell_note.client.telefono, value_style)],
    ]
    client_table = Table(client_rows, colWidths=[4.5 * cm, 12 * cm])
    client_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(client_table)

    # Note content (items)
    elements.append(Paragraph("CONTENIDO DE LA NOTA", section_style))
    headers = ["Producto", "Cantidad", "Precio Unitario", "Importe"]
    rows = [headers] + [
        [
            item.product.nombre,
            str(item.cantidad.normalize()),
            f"${item.precio_unitario:,.2f}",
            f"${item.importe:,.2f}",
        ]
        for item in sell_note.items
    ]
    items_table = Table(rows, colWidths=[7 * cm, 3 * cm, 3.5 * cm, 3 * cm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 0.3 * cm))

    # Total
    total_data = [["", "TOTAL:", f"${sell_note.total:,.2f}"]]
    total_table = Table(total_data, colWidths=[10.5 * cm, 3.5 * cm, 2.5 * cm])
    total_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("LINEABOVE", (1, 0), (-1, 0), 1, colors.HexColor("#2c3e50")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(total_table)

    doc.build(elements)
    return buffer.getvalue()
