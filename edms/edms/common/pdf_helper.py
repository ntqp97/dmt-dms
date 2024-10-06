import os

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from django.conf import settings


def add_watermark_to_pdf(input_pdf, watermark_text, file_type):
    font_dir = os.path.join(settings.BASE_DIR, 'edms', 'static', 'fonts')
    pdfmetrics.registerFont(TTFont('DejaVu', f'{font_dir}/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', f'{font_dir}/DejaVuSans-Bold.ttf'))

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    can.setFont("DejaVu", 50)
    can.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.3))

    can.saveState()
    can.translate(300, 400)
    can.rotate(45)
    can.drawCentredString(0, 0, watermark_text)
    can.restoreState()

    if file_type == "signature_file":
        rect_x, rect_y, rect_width, rect_height = 100, 300, 300, 100
        can.saveState()
        can.translate(rect_x + rect_width / 2, rect_y + rect_height / 2)
        can.rotate(20)

        can.setStrokeColor(Color(1.0, 0.2, 0.2, alpha=0.3))
        can.setLineWidth(5)
        can.roundRect(-rect_width / 2, -rect_height / 2, rect_width, rect_height, 5)

        can.setFillColor(Color(1.0, 0.2, 0.2, alpha=0.3))
        can.setFont("DejaVu-Bold", 30)
        can.drawCentredString(0, rect_height / 6, "VĂN BẢN")
        can.setFont("DejaVu", 20)
        can.drawCentredString(0, -rect_height / 4, "CHƯA CÓ HIỆU LỰC")
        can.restoreState()
    can.save()

    packet.seek(0)
    watermark_pdf = PdfReader(packet)

    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page.merge_page(watermark_pdf.pages[0])
        writer.add_page(page)

    output_pdf = io.BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf
