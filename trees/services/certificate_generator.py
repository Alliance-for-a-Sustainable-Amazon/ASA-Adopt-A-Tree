"""
certificate_generator.py

This file takes the certificate template and generates a customized certificate for each tree adopted.
"""

import requests, os
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
    canv.setFont("Helvetica", 14)
    # Tree ID
    canv.drawCentredString(
        687,
        190,
        f"Tree tag number: {tree_perm_id}"
    )

    canv.setFont("Helvetica", 20)
    # Tree name
    canv.drawString(
        245,
        340,
        tree_name
    )

    # Tree species
    canv.drawString(
        143,
        309,
        tree_species
    )

    # Tree DBH
    confirmed_tree_dbh = dot_for_null_check(tree_dbh)
    canv.drawString(
        293,
        279,
        confirmed_tree_dbh
    )

    # Tree height
    confirmed_tree_height = dot_for_null_check(tree_height)
    canv.drawString(
        129,
        248,
        confirmed_tree_height
    )

    # Tree adoption period
    canv.drawString(
        129,
        218,
        f"{adoption_date} - {expiration_date}"
    )

    # Tree image
    draw_tree_image(
        canv,
        574, # x-coord
        150, # y-coord
        225, #width
        450, #height
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

    # TODO: Remove this 
    image_url = testing_image_path

    try:
        # Checks whether file is from thee web or local. Used for local development.
        if image_url.startswith(("http://", "https://")):
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            image_data = response.content
        elif os.path.isfile(image_url):
            with open(image_url, "rb") as f:
                image_data = f.read()
        else:
            raise ValueError("image_url must be a valid URL or local file path")

        rounded_image = round_image_corners(
            image_data,
            radius=100
        )

        image_reader = ImageReader(rounded_image)
    except Exception as e:
        print("Tree image error: ", e)

        # Checks whether file is from thee web or local. Used to load 'no image' local file.
        if placeholder_path.startswith(("http://", "https://")):
            response = requests.get(placeholder_path, timeout=10)
            response.raise_for_status()
            image_data = response.content
        elif os.path.isfile(placeholder_path):
            with open(placeholder_path, "rb") as f:
                image_data = f.read()
        else:
            raise ValueError("image_url must be a valid URL or local file path")

        if placeholder_path:
            try:
                rounded_placeholder = round_image_corners(
                    placeholder_path,
                    radius=45
                )

                image_reader = ImageReader(rounded_placeholder)
            except Exception:
                image_reader = None

    # If local placeholder fails, draw the "No Image" text instead. This is mostly a sanity check and should not occur.
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

def round_image_corners(image_data, radius):
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

    border_size = 10 # Increase for a thicker frame

    # Create a larger transparent canvas
    framed = Image.new(
        "RGBA",
        (
            image.width + border_size * 2,
            image.height + border_size * 2
        ),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(framed)

    # Prevents white pixels being seen around corners
    inset = 2

    draw.rounded_rectangle(
        (
            inset,
            inset,
            framed.width - inset - 1,
            framed.height - inset - 1
        ),
        radius=radius + border_size,
        outline=(39, 93, 54, 255),
        width=border_size
    )

    # Paste the rounded image into the center
    framed.paste(
        image,
        (border_size, border_size),
        image
    )

    output = BytesIO()

    # Save as PNG so transparency is reserved
    framed.save(output, format="PNG", optimize=False)

    output.seek(0)

    return output

def dot_for_null_check(param):
    """
        Helper function that formats unknown fields that are deonatated with a '.' to say 'Unknown' for a 
        better user experience.

        Parameters:
            param: String passed in from database
    """
    if param == ".":
        param = "Unknown"

    return param