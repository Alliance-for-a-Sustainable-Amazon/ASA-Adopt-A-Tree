"""
certificate_generator.py

This file takes the certificate template and generates a customized certificate for each tree adopted.
"""

import requests
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4, landscape
from PIL import Image, ImageDraw
from django.contrib.staticfiles import finders

template_path = finders.find("certificates/ASA_certificate_template.png")

testing_image_path = finders.find("certificates/BEEX-0020.png")

PAGE_WIDTH, PAGE_HEIGHT = landscape(A4)

def generate_certificate(
    donor_name,
    tree_name,
    tree_species,
    tree_perm_id,
    tree_height,
    tree_dbh,
    adoption_date,
    expiration_date,
    tree_image_url,
):
    """
    Generate a PDF certificate for a specific tree adoption.

    Parameters:
        donor_name: Name of the donor displayed on the certificate, 
            this is not the 'chosen donor name'
        tree_name: The local common name of the adopted tree (displayed on the tree's popup)
        tree_species: The species of the adopted tree (displayed on the tree's popup)
        tree_perm_id: The permanent ID attached to the adopted tree
        tree_height: The height of the tree (displayed on the tree's popup)
        tree_dbh: The diameter at breast height (displayed on the tree's popup)
        adoption_date: The date the adoption took place
        expiration_date: The date the adoption will expire
        tree_image_url: The Azure blob storage URL to the image
    """

    buffer = BytesIO()

    # Template size is A4 landscape, so use that to preserve aspect ratio
    canv = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Draw our template
    background = ImageReader(template_path)

    canv.drawImage(
        background,
        0, # x-coord
        0, # y-coord
        width=PAGE_WIDTH,
        height=PAGE_HEIGHT,
        preserveAspectRatio=False
    )

    # Donor name is primary focus so keep it bold and larger than the rest
    canv.setFont("Helvetica-Bold", 30)
    canv.drawString(
        70,
        377,
        donor_name
    )

    # Remove bold and make text smaller for less significant data 
    canv.setFont("Helvetica", 20)
    # Tree ID
    canv.drawCentredString(
        665,
        182,
        f"Tree tag number: {tree_perm_id}"
    )

    # Tree name
    canv.drawString(
        170,
        330,
        tree_name
    )

    # Tree species
    canv.drawString(
        148,
        300,
        tree_species
    )

    # Tree DBH
    canv.drawString(
        316,
        270,
        tree_dbh
    )

    # Tree height
    canv.drawString(
        133,
        239,
        tree_height
    )

    # Tree adoption period
    canv.drawString(
        133,
        208,
        f"{adoption_date} - {expiration_date}"
    )

    # Tree image
    draw_tree_image(
        canv,
        554, # x-coord
        207, # y-coord
        225, #width
        338, #height
        image_url=tree_image_url
    )

    canv.save()

    # Move to beginning of buffer
    buffer.seek(0)

    # Extract the PDF contents
    pdf_bytes = buffer.getvalue()

    buffer.close()

    return pdf_bytes

def draw_tree_image(
    canvas,
    x,
    y,
    width,
    height,
    image_url=None,
    placeholder_path=testing_image_path #TODO: Change this out for production
):
    """
    Draw a given tree image within a provided area of the certificate. 

    Images are scaled proportionally to prevent distortion. If the tree's
    url cannot be loaded, or is not provided, a placeholder image is used instead.

    Parameters:
        canvas: ReportLab canvas object
        x: X-coordinate of the lower-left corner of the image
        y: Y-coordinate of the lower-left corner of the image
        width: Initial width of the image
        height: Initial height of the image
        image_url: Url to the image that is located in the Azure blob storage
        placeholder_path: Local path to fallback image if image_url is not 
            provided or cannot be downloaded
    """
    image_reader = None

    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()

        rounded_image = round_image_corners(
            response.content,
            radius=45
        )

        image_reader = ImageReader(rounded_image)
    except Exception as e:
        if placeholder_path:
            try:
                rounded_placeholder = round_image_corners(
                    placeholder_path,
                    radius=90
                )

                image_reader = ImageReader(rounded_placeholder)
            except Exception:
                image_reader = None

    if image_reader is None:
        canvas.rect(
            x,
            y,
            width,
            height
        )

        canvas.drawCentredString(
            x + width / 2,
            y + height / 2,
            "Image Unavailable"
        )

        return
    
    img_width, img_height = image_reader.getSize()

    scale = min(
        width / img_width,
        height / img_height
    )

    draw_width = img_width * scale
    draw_height = img_height * scale

    # Center image in box
    draw_x = x + (width - draw_width) / 2
    draw_y = y + (height - draw_height) / 2

    canvas.drawImage(
        image_reader,
        draw_x,
        draw_y,
        draw_width,
        draw_height,
        preserveAspectRatio=True,
        mask='auto'
    )

def round_image_corners(image_data, radius=25):
    """
    Apply rounded corners to a given image while preserving transparency.

    The returned image is stored in memory as a PNG so that it can be passed 
    to ReportLab without creating a temporary file.
    """
    # Convert to RGBA to make sure that alpha channel is available
    if isinstance(image_data, bytes):
        image = Image.open(BytesIO(image_data)).convert("RGBA")
    else:
        image = Image.open(image_data).convert("RGBA")

    # Create a mask to keep white pixels visible but make black pixels transparent
    mask = Image.new("L", image.size, 0)

    draw = ImageDraw.Draw(mask)

    # Draw a black rounded rectangle around the image
    draw.rounded_rectangle(
        (0, 0, image.width - 1, image.height - 1),
        radius=radius,
        fill=255
    )

    # Apply the mask to the image's alpha channel
    image.putalpha(mask)

    output = BytesIO()

    # Save as PNG so transparency is reserved
    image.save(output, format = "PNG")
    image.close()

    output.seek(0)

    return output