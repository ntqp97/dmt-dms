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


def add_watermark_to_pdf(input_pdf, watermark_text, asset):
    from edms.documents.models import Document

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

    if asset.file_type == "signature_file" and asset.document.document_category == Document.SIGNING_DOCUMENT:
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
    pages_signatures_map = stamp_signatures_to_pdf(asset, reader.pages)

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        page.merge_page(watermark_pdf.pages[0])
        pages_signatures = pages_signatures_map.get(page_num, [])
        for pages_signature in pages_signatures:
            page.merge_page(pages_signature.pages[0])
        writer.add_page(page)

    output_pdf = io.BytesIO()
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf


def convert_float_objects_to_floats(coords):
    return [float(coord) for coord in coords]


def is_positive_integer(string):
    return string.isdigit() and int(string) > 0


def stamp_signatures_to_pdf(asset, pages):
    from edms.documents.models import Document, DocumentSignature
    pages_signatures_map = {}
    if asset.file_type != "signature_file":
        return pages_signatures_map
    document_signatures_map = get_signature_field_coordinates(pages)
    for page_num, signers_dict in document_signatures_map.items():
        page = pages[page_num]
        page_width = float(page.mediabox.upper_right[0])
        page_height = float(page.mediabox.upper_right[1])

        for signer_position, coordinates in signers_dict.items():
            document_signature = asset.document.signatures.filter(
                order=signer_position,
                is_signature_visible=True).first()
            if not document_signature:
                continue

            if asset.document.document_category in [
                Document.SIGNING_DOCUMENT,
            ] or (
                asset.document.document_category in [
                    Document.IN_PROGRESS_SIGNING_DOCUMENT,
                    Document.COMPLETED_SIGNING_DOCUMENT,
                ] and
                document_signature.signature_status == DocumentSignature.SIGNED
            ):
                user_signature = document_signature.signer.user_signature_entries.filter(is_default=True).first()
                if user_signature:
                    stamp_image = user_signature.signature_image.file.url
                    for coords in coordinates:
                        coords = convert_float_objects_to_floats(coords)
                        if page_num not in pages_signatures_map:
                            pages_signatures_map[page_num] = []
                        pages_signatures_map[page_num].append(
                            add_image_stamp_to_pdf(
                                stamp_image=stamp_image,
                                coords=coords,
                                page_width=page_width,
                                page_height=page_height
                            )
                        )
    return pages_signatures_map


def add_image_stamp_to_pdf(stamp_image, coords, page_width, page_height):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))

    image = ImageReader(stamp_image)
    x_min, y_min, x_max, y_max = get_signature_box(coords, page_width, page_height, 0.2, 0.1)
    can.drawImage(image, x_min, y_min, x_max - x_min, y_max - y_min, mask='auto')

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def get_signature_field_coordinates(pages, input_pdf=None):
    if input_pdf:
        reader = PdfReader(input_pdf)
        pages = reader.pages
    coordinates_dict = {}
    for page_num, page in enumerate(pages):
        if "/Annots" in page:
            for annot in page["/Annots"]:
                signer_num = annot.get_object().get("/Contents")
                if signer_num and is_positive_integer(signer_num):
                    if page_num not in coordinates_dict:
                        coordinates_dict[page_num] = {}
                    if signer_num not in coordinates_dict[page_num]:
                        coordinates_dict[page_num][signer_num] = []
                    coordinates_dict[page_num][signer_num].append(annot.get_object().get("/Rect"))
    return coordinates_dict


def get_signature_box(rect, page_width, page_height, width_ratio, height_ratio):
    x1, y1, x2, y2 = rect

    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    new_width = page_width * width_ratio
    new_height = page_height * height_ratio

    new_x1 = center_x - new_width / 2
    new_y1 = center_y - new_height / 2 - 50
    new_x2 = center_x + new_width / 2
    new_y2 = center_y + new_height / 2

    return new_x1, new_y1, new_x2, new_y2


def get_positions_signature(input_pdf, document_signature):
    reader = PdfReader(input_pdf)
    pages = reader.pages
    sigpage = None
    coords = None
    user_signature = document_signature.signer.user_signature_entries.filter(is_default=True).first()
    signature_img = user_signature.signature_image.file.url
    for page_num, page in enumerate(pages):
        if "/Annots" in page:
            for annot in page["/Annots"]:
                if str(document_signature.order) == annot.get_object().get("/Contents"):
                    sigpage = page_num
                    coords = convert_float_objects_to_floats(annot.get_object().get("/Rect"))
                    break

    if sigpage and coords and signature_img:
        page = pages[sigpage]
        page_width = float(page.mediabox.upper_right[0])
        page_height = float(page.mediabox.upper_right[1])
        signature_box = get_signature_box(coords, page_width, page_height, 0.2, 0.1)
        return sigpage, signature_box, signature_img
    else:
        raise ValueError("Not found sign")
