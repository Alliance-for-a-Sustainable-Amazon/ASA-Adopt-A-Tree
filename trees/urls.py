from django.urls import path
from .views import (
    tree_map_data, 
    tree_detail_data,
    create_checkout_session,
    stripe_webhook,
    tree_updates
)

app_name = "trees"
urlpatterns = [
    # TODO: Either add these back in or remove them once we decide whether to have a view of the tables on the webapp.
    #path("<uuid:donation_id>/", views.donation_details, name="donation_details"),
    #path('tables/<str:model_name>/', views.generic_list_view, name="generic_table"),
    path('tree-data/', tree_map_data),
    path('tree-detail/<uuid:id>/', tree_detail_data),
    path('create-checkout-session/', create_checkout_session),
    path('stripe-webhook/', stripe_webhook),
    path('tree-updates/', tree_updates)
]