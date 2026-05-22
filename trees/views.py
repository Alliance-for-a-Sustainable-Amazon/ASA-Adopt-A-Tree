"""
views.py
This file contains the different views available on the site.

As we are using this django project solely as an admin site currently, there are not many views.
The current view, 'generic_list_view', works but is not set up in the urls.py file.
"""

import json, stripe, traceback, uuid
from django.shortcuts import render, get_object_or_404
from django.template import loader
from django.http import HttpResponse, Http404, JsonResponse
from django.core.paginator import Paginator
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from decimal import Decimal
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import TreeMapSerializer, TreeDetailSerializer

from .models import Donor, Tree, Donation

MODEL_MAP = {
    'donors': Donor,
    'trees': Tree,
    'donations': Donation,
}

stripe.api_key = settings.STRIPE_SECRET_KEY

# Creates a view to display all basic tree information for map markers
@api_view(['GET'])
def tree_map_data(request):
    trees = Tree.objects.select_related('donation').all()

    serializer = TreeMapSerializer(trees, many=True)

    return Response(serializer.data)

# Creates a view to display an individual tree's detailed information
@api_view(['GET'])
def tree_detail_data(request, id):
    tree = get_object_or_404(Tree, id=id)

    serializer = TreeDetailSerializer(tree)

    return Response(serializer.data)

# Creates the Stripe checkout session for the user, providing necessary metadata for webhook reading.
@csrf_exempt
def create_checkout_session(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)
    
    try:
        data = json.loads(request.body)

        tree_id = data.get("tree_id")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            customer_creation="always",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Tree Adoption",
                        },
                        "unit_amount": 5000, # '$50': Stripe sets decimal places
                    },
                    "quantity": 1,
                }
            ],

            #TODO: Change these to actual site urls once they are ready
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",

            # This data gets passed through to the webhook. Allows webhook to update tree adoption status and donations
            metadata={
                "tree_id": str(tree_id)
                #TODO: Add donor chosen name
            },

            # Metadata that shows up on the Stripe portal
            payment_intent_data={
                "metadata": {
                    "tree_id": str(tree_id)
                    #TODO: Add donor chosen name
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

            #TODO: Add donor chosen name
            
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

                Donation.objects.create(
                    donor_id=user,
                    tree_id=tree,
                    stripe_session_id=stripe_session_id,
                    stripe_payment_intent=session["payment_intent"],
                    amount=donation_amount,
                    currency=session["currency"],
                    donor_name=customer_name,
                    #TODO: Add donor chosen name
                    payment_method=payment_method
                )

                print("Donation created")

                user.total_donation_amount += donation_amount
                user.save()

                
                tree.adoption_status = "adopted"
                tree.save()
                
                print("Tree adoption updated")
                return HttpResponse(status=200)
        
        except Exception as e:
            print("Webhook Error:")
            traceback.print_exc()
            return HttpResponse(status=500)


    return HttpResponse(status=200)


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