import os

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
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


def convert_float_objects_to_floats(coords):
    return [float(coord) for coord in coords]


def is_positive_integer(string):
    return string.isdigit() and int(string) > 0


def add_image_stamp_to_pdf(stamp_image, coords, page_width, page_height):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    scale_percentage = 0.2

    image = ImageReader(stamp_image)
    x, y, _, _ = coords

    desired_width = page_width * scale_percentage
    desired_height = page_height * scale_percentage

    x_centered = x - (desired_width / 2)
    y_centered = y - (desired_height / 2) - 50

    can.drawImage(image, x_centered, y_centered, desired_width, desired_height, mask='auto')

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def get_signature_field_coordinates(pages, input_pdf=None):
    if input_pdf:
        reader = PdfReader(input_pdf)
        pages = reader.pages
    coordinates_dict = {}
    for index, page in enumerate(pages):
        if "/Annots" in page:
            for annot in page["/Annots"]:
                content_form = annot.get_object().get("/Contents")
                if content_form and is_positive_integer(content_form):
                    if content_form not in coordinates_dict:
                        coordinates_dict[content_form] = []
                    coordinates_dict[content_form].append(annot.get_object().get("/Rect"))
    return coordinates_dict
