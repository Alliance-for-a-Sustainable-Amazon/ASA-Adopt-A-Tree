"""
email_generator.py

Contains the functionality for sending an email with the user's 
generated certificate from their adoption
"""

import logging
from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

def send_certificate_email(
    recipient_email,
    donor_name,
    pdf_bytes
):
    """
    Sends a certificate email with the generated PDF attached

    Parameters:
        recipient_email: Email address provided by the donor on the Stripe checkout
        donor_name: Name of the donor provided during chcekout (not the 'chosen name')
        pdf_bytes: Generated certificate PDF
    """
    try:
        email = EmailMessage(
            subject="Thank you for your 1 year tree adoption",
            body=(
                f"Dear {donor_name}, \n\n"
                f"Thank you for adopting a tree through our Adopt a Tree platform.\n\n"
                f"Every donation helps ensure these trees and property remain safe and continue to benefit the environment.\n\n"
                f"Attached to this email is your Certificate of Adoption as a token of our appreciation."
                f"It includes details of the tree you have adopted and serves as a reminder of the impact your contribution is making.\n\n"
                f"We are grateful for your support and for joining us in perserving our Amazon rainforest.\n\n"
                f"Sincerely,\n"
                f"Alliance for a Sustainable Amazon\n\n"

            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )

        email.attach(
            "Tree_Adoption_Certificate.pdf",
            pdf_bytes,
            "application/pdf"
        )

        email.send()
        
        return True
    except Exception:
        logger.exception(
            f"Failed to send certificate email to {recipient_email}"
        )

        return False
