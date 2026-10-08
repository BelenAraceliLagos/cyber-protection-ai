import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

from app.models.quotation import Quotation

OUTPUT_DIR = "generated_pdfs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_quotation_pdf(
    quotation: Quotation
):

    filename = f"quotation_{quotation.id}.pdf"

    pdf_path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    doc = SimpleDocTemplate(pdf_path)

    styles = getSampleStyleSheet()

    content = []

    title = Paragraph(
        f"""
        <b>Cybersecurity Proposal</b>
        """,
        styles["Title"]
    )

    content.append(title)

    content.append(Spacer(1, 20))

    client_info = Paragraph(
        f"""
        <b>Client:</b>
        {quotation.client.company_name}
        <br/>

        <b>Contact:</b>
        {quotation.client.contact_name}
        <br/>

        <b>Industry:</b>
        {quotation.client.industry}
        """,
        styles["BodyText"]
    )

    content.append(client_info)

    content.append(Spacer(1, 20))

    services_text = ""

    for item in quotation.items:

        services_text += f"""
        • {item.service.name}
        <br/>
        Quantity: {item.quantity}
        <br/>
        Price: ${item.price}
        <br/><br/>
        """

    services_paragraph = Paragraph(
        services_text,
        styles["BodyText"]
    )

    content.append(services_paragraph)

    content.append(Spacer(1, 20))

    total = Paragraph(
        f"""
        <b>Total:</b> ${quotation.total}
        """,
        styles["Heading2"]
    )

    content.append(total)

    content.append(Spacer(1, 30))

    ai_content = Paragraph(
        quotation.generated_text.replace("\n", "<br/>"),
        styles["BodyText"]
    )

    content.append(ai_content)

    doc.build(content)

    return pdf_path