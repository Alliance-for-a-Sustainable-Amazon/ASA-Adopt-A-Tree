"""
admin.py
Registers all models on the admin site.
"""

from django.contrib import admin
from .models import Tree, Donor, Donation

# Reorders and groups all relevant information from the table for easy modification.
@admin.register(Tree)
class TreeAdmin(admin.ModelAdmin):
    # Allows for auto expanded collpasable fields in admin view.
    class Media:
        js = ('admin/js/admin_expand.js',)

    # Allows the primary key (ID) to be displayed without it being editable. 
    readonly_fields = ("id", "number",)

    fieldsets = [
        ("Identifiers", {"fields": ["id", "number"], "classes": ["collapse", "start-open"]}),
        ("Adoption Status", {"fields": ["adoption_status"], "classes": ["collapse"]}),
        ("Tree Information", {"fields": ["common_name_english", "common_name_spanish", "family", "genus", "species", "dbh"], "classes": ["collapse"]}),
        ("Location Information", {"fields": ["lat", "long", "location", "location_description"], "classes": ["collapse"]}),
        ("Study Information", {"fields": ["study", "permanent_tag"], "classes": ["collapse"]}),
        ("Notes", {"fields": ["notes"], "classes": ["collapse"]}),
    ]
    list_display = ["common_name_english", "common_name_spanish", "number", "display_adoption_status"]
    list_filter = ["adoption_status"]
    search_fields = ["number", "common_name_english", "common_name_spanish"]

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    # Allows for auto expanded collpasable fields in admin view.
    class Media:
        js = ('admin/js/admin_expand.js',)
    
    readonly_fields = ("id",)

    fieldsets = [
        ("Identifiers", {"fields": ["id"]}),
        ("Donor Information", {"fields": ["name", "email", "country", "total_donation_amount"]}),
    ]
    list_display = ["name", "email", "total_donation_amount"]
    list_filter = ["country", "total_donation_amount"]
    search_fields = ["name", "email"]

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    # Allows for auto expanded collpasable fields in admin view.
    class Media:
        js = ('admin/js/admin_expand.js',)

    # Allows the primary keys (ID) to be displayed without it being editable. 
    readonly_fields = ("id", "number", "date", "expiration_date")

    fieldsets = [
        ("Identifiers", {"fields": ["id", "number"], "classes": ["collapse", "start-open"]}),
        ("Donation Date and Expiration", {"fields": ["date", "expiration_date"], "classes": ["collapse"]}),
        ("Donation Information", {"fields": ["amount", "payment_method"], "classes": ["collapse"]}),
        ("Donor Information", {"fields": ["donor_id", "donor_name", "donor_chosen_name"], "classes": ["collapse"]}),
        ("Tree Adopted", {"fields": ["tree_id"], "classes": ["collapse"]}),
        ("Notes", {"fields": ["notes"], "classes": ["collapse"]}),
    ]
    list_display = ["donor_name", "number", "amount"]
    list_filter = ["date", "expiration_date", "amount"]
    search_fields = ["donor_name", "number", "tree_id", "donor_chosen_name"]