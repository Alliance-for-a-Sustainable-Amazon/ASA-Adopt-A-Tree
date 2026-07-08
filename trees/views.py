"""
views.py
This file contains the different views available on the site.

As we are using this django project solely as an admin site currently, there are not many views.
The current view, 'generic_list_view', works but is not set up in the urls.py file.
"""

import json, stripe, traceback, uuid, tempfile, logging
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse, FileResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from decimal import Decimal
from rest_framework.decorators import api_view
from rest_framework.response import Response
from azure.storage.blob import BlobServiceClient
from .serializers import TreeMapSerializer, TreeDetailSerializer
from .services.certificate_generator import generate_certificate
from .services.email_generator import send_certificate_email

from .models import Donor, Tree, Donation

MODEL_MAP = {
    'donors': Donor,
    'trees': Tree,
    'donations': Donation,
}

EXPECTED_API_KEY = settings.DJANGO_API_KEY
AZURE_BLOB_STORAGE = settings.AZURE_BLOB_STORAGE
AZURE_BLOB_CONTAINER = settings.AZURE_BLOB_CONTAINER

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

blob_service_client = BlobServiceClient.from_connection_string(
    settings.AZURE_CONNECTION_STRING
)

container_client = blob_service_client.get_container_client(
    AZURE_BLOB_CONTAINER
)

# Helper function to find if image file exists.
def blob_exists(blob_name):
    try:
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.exists()
    except Exception:
        return False

# Creates a timestamp / count to see if any changes have occurred in the database. Prevents pulling all pins every 30 seconds
# when there are no changes.
@api_view(['GET'])
def tree_updates(request):
    api_key = request.headers.get("X-API-KEY")

    # Requires API calls to have an api key for added security
    if api_key != EXPECTED_API_KEY:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    latest_tree = Tree.objects.order_by("-updated_at").first()

    latest_update = None
    if latest_tree:
        latest_update = latest_tree.updated_at

    tree_count = Tree.objects.count()

    return Response({
        "last_updated": latest_update,
        "tree_count": tree_count
    })

# Creates a view to display all basic tree information for map markers. Also checks for expired adoptions
# and resets said trees to adoptable again before sending out the tree information.
@api_view(['GET'])
def tree_map_data(request):
    api_key = request.headers.get("X-API-KEY")

    # Requires API calls to have an api key for added security
    if api_key != EXPECTED_API_KEY:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    today = timezone.now().date()

    # Gets all unprocessed expired donations
    expired_donations = Donation.objects.filter(
        expiration_date__lt=today,
        expiration_processed=False
    )

    # Allows trees with expired donations to be adoptable again.
    for donation in expired_donations:
        donation.tree_id.adoption_status = "adoptable"
        donation.tree_id.save(update_fields=["adoption_status"])

        donation.expiration_processed = True
        donation.expired_tree_id = donation.tree_id.tag_id
        donation.tree_id = None
        # Don't need tree to be searchable from tree_id anymore
        donation.searchable_tree_id = ""
        donation.save(update_fields=["expiration_processed", "tree_id", "expired_tree_id", "searchable_tree_id"])


    trees = Tree.objects.select_related("donation").all()

    serializer = TreeMapSerializer(trees, many=True)

    return Response(serializer.data)

# Creates a view to display an individual tree's detailed information
@api_view(['GET'])
def tree_detail_data(request, id):
    api_key = request.headers.get("X-API-KEY")

    # Requires API calls to have an api key for added security
    if api_key != EXPECTED_API_KEY:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    tree = get_object_or_404(Tree, id=id)

    serializer = TreeDetailSerializer(tree)

    data = serializer.data

    blob_name = f"{tree.tag_id}.jpg"

    if blob_exists(blob_name):
        data["image_url"] = (f"https://{AZURE_BLOB_STORAGE}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{blob_name}")
    else:
        data["image_url"] = None

    return Response(data)

# Creates the Stripe checkout session for the user, providing necessary metadata for webhook reading.
@csrf_exempt
def create_checkout_session(request):
    api_key = request.headers.get("X-API-KEY")

    # Requires API calls to have an api key for added security
    if api_key != EXPECTED_API_KEY:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    
    try:
        data = json.loads(request.body)

        tree_id = data.get("tree_id")
        tree_tag_id = data.get("tree_tag_id")

        tree = Tree.objects.get(id=tree_id)

        # Set status on these to 200, even though they are errors in order to bypass Wix generic error message
        if tree.adoption_status == "adopted":
            return JsonResponse(
                {
                    "error": "adopted"
                },
                status=200
            )
        
        # Check both if the timer exists and if the specific time as trees with incomplete adoptions will still have an old
        # reservation timer
        if tree.reserve_until:
            if tree.reserve_until > timezone.now():
                return JsonResponse(
                    {
                        "error": "reserved"
                    },
                    status=200
                )
        
        # Filter for the specific tree instead of using the 'tree' instance in order to bypass save() function. 
        # This prevents 'updated_at' from being updated which would cause pin data to be sent to Wix again
        Tree.objects.filter(id=tree_id).update(reserve_until=timezone.now() + timedelta(minutes=5))

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_creation="always",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "1-Year Tree Adoption ($50 USD)",
                            "description": "Valid for one year from purchase date."
                        },
                        "unit_amount": 5000, # '$50': Stripe sets decimal places
                    },
                    "quantity": 1,
                }
            ],

            custom_fields=[
                {
                    "key": "chosen_name",
                    "label": {
                        "type": "custom",
                        "custom": "Public display name. This defaults to Anonymous."
                    },
                    "type": "text",
                    "optional": True,
                    "text": {
                        "maximum_length": 50
                    }
                }
            ],

            custom_text={
                "submit": {
                    "message": (
                        "Your $50 USD adoption is valid for one year from the purchase date."
                    )
                }
            },

            expires_at=int((timezone.now() + timedelta(minutes=30)).timestamp()),

            #TODO: Change these to actual site urls once they are ready
            success_url="https://www.sustainableamazon.org/payment-results-41818?result=success",
            cancel_url="https://www.sustainableamazon.org/payment-result-41818?result=cancelled",

            #TODO: Uncomment this out once terms and service has been configured. If no consent collection
            # is configured on the organization Stripe page, remove it instead.
            #consent_collection={
            #    "terms_of_service": "required"
            #},

            # This data gets passed through to the webhook. Allows webhook to update tree adoption status and donations
            metadata={
                "tree_id": str(tree_id),
                "tree_tag_id": str(tree_tag_id)
            },

            # Metadata that shows up on the Stripe portal
            payment_intent_data={
                "metadata": {
                    "tree_id": str(tree_id),
                    "tree_tag_id": str(tree_tag_id)
                }
            }
        )

        return JsonResponse({
            "url": session.url
        })
    
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)

# Listens for successful stripe payment and then creates new donation and donor (if they don't exist), 
# as well as updates tree adoption status for tree ID passed in
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    
    except ValueError:
        return HttpResponse(status=400)
    
    except stripe.error.SignatureVerificationError:
        print("Invalid Stripe signature")
        return HttpResponse(status=400)
    
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        print("PAYMENT SUCCESSFUL")
        
        try:
            stripe_session_id = session["id"]

            existing_donation = Donation.objects.filter(
                stripe_session_id=stripe_session_id
            ).exists()

            if existing_donation:
                print("Donation already processed.")
                return HttpResponse(status=200)
            
            metadata = session["metadata"]

            try:
                tree_id = uuid.UUID(metadata["tree_id"])
            except (KeyError, ValueError):
                print("Invalid tree ID")
                return HttpResponse(status=400)

            # Gets chosen name from the custom field.
            chosen_name = None
            if session["custom_fields"]:
                for field in session["custom_fields"]:
                    if field["key"] == "chosen_name":
                        if field["text"]:
                            chosen_name = field["text"]["value"]
                        
                        break
            


            
            customer_details = session["customer_details"]

            customer_email = customer_details["email"]
            customer_name = customer_details["name"]

            country = None

            if customer_details["address"]:
                country = customer_details["address"]["country"]

            payment_intent_id = session["payment_intent"]

            if not payment_intent_id:
                print("No payment intent found")
                return HttpResponse(status=400)

            payment_method = ""

            payment_intent = stripe.PaymentIntent.retrieve(
                payment_intent_id,
                expand=["payment_method"]
            )

            payment_method_obj = payment_intent["payment_method"]

            if payment_method_obj:
                payment_method = payment_method_obj["type"]

            if not customer_email:
                print("No customer email")
                return HttpResponse(status=400)
            
            # Prevents any database changes from being permanent if there is an error in one of the steps.
            # NOTE: This does not stop the donation from coming through. Must provide refund if there is an issue here. 
            with transaction.atomic():
                user, created = Donor.objects.get_or_create(
                    email=customer_email,

                    # Defaults only get set if user does not exist already
                    defaults={
                        "name": customer_name,
                        "country": country,
                        "total_donation_amount": 0
                    }
                )

                if created:
                    print("Created new user")
                else:
                    print("Existing user found")

                try:
                    # Locks tree ID during this process
                    tree = Tree.objects.select_for_update().get(
                        id=tree_id
                    )
                except Tree.DoesNotExist:
                    transaction.set_rollback(True)

                    print("Tree does not exist.")
                    # Must return status 200 to prevent continues webhook calls.
                    return HttpResponse(status=200)
                
                # If tree is already adopted, return status 200 so that webhook does not retry, but rollback any table entry creations.
                if tree.adoption_status == "adopted":
                    transaction.set_rollback(True)

                    print("Tree already adopted")
                    return HttpResponse(status=200)

                donation_amount = Decimal(session["amount_total"]) / Decimal("100")

                donation = Donation.objects.create(
                    donor_name=user,
                    searchable_donor_name=user.name,
                    tree_id=tree,
                    searchable_tree_id=tree.tag_id,
                    stripe_session_id=stripe_session_id,
                    stripe_payment_intent=session["payment_intent"],
                    amount=donation_amount,
                    currency=session["currency"],
                    payment_method=payment_method,
                    # Updates the donor_chosen_name if it is provided. Otherwise nothing is set and the model
                    # defaults it to Anonymous.
                    **(
                        {"donor_chosen_name": chosen_name}
                        if chosen_name
                        else {}
                    )
                )

                print("Donation created")

                user.total_donation_amount += donation_amount
                user.save()

                
                tree.adoption_status = "adopted"
                # Reset the reserve timer for future adoptions
                tree.reserve_until = None
                tree.save()
                
                print("Tree adoption updated")

                image_url = None
                blob_name = f"{tree.tag_id}.jpg"

                # Only send the image url if it exists
                if blob_exists(blob_name):
                    image_url = (f"https://{AZURE_BLOB_STORAGE}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{blob_name}")


                # Make dates human readable 
                format_adoption_date = donation.date.strftime("%d/%m/%Y")
                format_expiration_date = donation.expiration_date.strftime("%d/%m/%Y")

                try:
                    # Generate the user's certificate AFTER database changes to ensure PDF and email aren't sent
                    # if there is some issue and database queries are voided
                    pdf_bytes = generate_certificate(
                        donor_name=customer_name,
                        tree_name=tree.common_name_spanish,
                        tree_species=f"{tree.genus} {tree.species}",
                        tree_perm_id=tree.permanent_tag,
                        tree_height=tree.height,
                        tree_dbh=tree.dbh,
                        adoption_date=format_adoption_date,
                        expiration_date=format_expiration_date,
                        tree_image_url=image_url,
                    )

                    email_sent = send_certificate_email(
                        recipient_email=customer_email,
                        donor_name=customer_name,
                        pdf_bytes=pdf_bytes
                    )

                    # 'certificate_sent' defaults to False. Only call the save function if that has changed
                    if email_sent:
                        donation.certificate_sent = True
                        donation.save(update_fields=["certificate_sent"])
                # If an exception is hit, log it but don't return anything to allow the database modifications to go through still
                except Exception:
                    logger.exception(f"Certificate generation failed for donation {donation.id}")

                return HttpResponse(status=200)
        
        except Exception as e:
            print("Webhook Error:")
            traceback.print_exc()
            return HttpResponse(status=500)


    return HttpResponse(status=200)

# TODO: Remove this one certificate generation is complete
# Creates a preview page of the certificate for testing
def preview_certificate(request):
    temp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    )

    image_url = None
    blob_name = "BEEX_0020.jpg"

    # Only send the image url if it exists
    #if blob_exists(blob_name):
    #    image_url = (f"https://{AZURE_BLOB_STORAGE}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{blob_name}")

    pdf_bytes = generate_certificate(
        donor_name="John Smith",
        tree_name="Castaña (Brazil Nut)",
        tree_species="Testing Species",
        tree_perm_id="XXXX",
        tree_height="100cm",
        tree_dbh="30cm",
        adoption_date="06/12/2026",
        expiration_date="06/12/2027",
        tree_image_url=image_url,
    )

    temp_file.write(pdf_bytes)
    
    return FileResponse(
        open(temp_file.name, "rb"),
        "application/pdf"
    )

# TODO: Currently this table is not being used on the site. Either set it up, or remove it for final production.
# Generic table view for all models. Locked behind admin access due to sensitive information in some tables.
@staff_member_required
def generic_list_view(request, model_name):
    model_class = MODEL_MAP.get(model_name.lower())
    if not model_class:
        raise Http404("No table found.")

    objects = model_class.objects.all()

    paginator = Paginator(objects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    headers = [field.verbose_name.capitalize() for field in model_class._meta.fields]
    field_names = [field.name for field in model_class._meta.fields]

    context = {
        'objects': page_obj,
        'headers': headers,
        'field_names': field_names,
        'title': model_class._meta.verbose_name_plural.capitalize(),
    }

    return render(request, 'trees/generic_table.html', context)