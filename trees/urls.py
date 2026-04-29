from django.urls import path
from . import views

app_name = "trees"
urlpatterns = [
    # TODO: Either add these back in or remove them once we decide whether to have a view of the tables on the webapp.
    #path("<uuid:donation_id>/", views.donation_details, name="donation_details"),
    #path('tables/<str:model_name>/', views.generic_list_view, name="generic_table"),
]