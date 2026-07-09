"""
urls.py
This file contains all app specific urls. Each url contains a unique view.
"""

from django.urls import path
from .views import (
    tree_map_data, 
    tree_detail_data,
    create_checkout_session,
    stripe_webhook,
    tree_updates,
    preview_certificate
)

app_name = "trees"
urlpatterns = [
    path('tree-data/', tree_map_data),
    path('tree-detail/<uuid:id>/', tree_detail_data),
    path('create-checkout-session/', create_checkout_session),
    path('stripe-webhook/', stripe_webhook),
    path('tree-updates/', tree_updates),
    path(
        "certificate_preview/",
        preview_certificate,
        name="certificate-preview"
    )
]