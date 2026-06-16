"""
admin.py
Registers all models on the admin site.
"""

from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe
from .models import Tree, Donor, Donation
from copy import deepcopy

# Default admin class that allows the collapsible fields of table entries to start open when creating a new table entry,
# but start closed when modifying or viewing an existing entry.
# NOTE: Currently not being used
class StartOpenAdmin(admin.ModelAdmin):
    base_fieldsets = ()

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(self.base_fieldsets or super().get_fieldsets(request, obj))

        # If the object doesn't exist, then we start with every collapsible field open.
        if obj is None:
            for _, opts in fieldsets:
                classes = set(opts.get("classes", ()))
                classes.add("start-open")
                opts["classes"] = tuple(classes)
        else:
            for _, opts in fieldsets:
                classes = set(opts.get("classes", ()))
                if "start-open" not in classes:
                    classes.discard("start-open")
                opts["classes"] = tuple(classes)
        
        return fieldsets

# Reorders and groups all relevant information from the table for easy modification.
@admin.register(Tree)
class TreeAdmin(admin.ModelAdmin):
    # Allows for auto expanded collpasible fields in admin view.
    class Media:
        js = ('admin/js/admin_expand.js',)

    # Allows the primary key (ID) to be displayed without it being editable. 
    readonly_fields = ("id", "tag_id", "created_at", "updated_at", "display_modified")

    def display_modified(self, obj):
        return mark_safe(
            f"""
            <textarea readonly
                style="width:600px;height:100px;">{obj.modified}
             </textarea>
        """
        )
    
    display_modified.short_description = "Modification Log (automatically generated)"

    fieldsets = [
        ("Identifiers", {"fields": ["id", "tag_id"]}),
        ("Date Information", {"fields": ["display_modified", "created_at", "updated_at"]}),
        ("Adoption Status", {"fields": ["adoption_status"]}),
        ("Tree Information", {"fields": ["common_name_spanish", "common_name_english", "family", "genus", "species", "dbh", "height", "species_description"]}),
        ("Location Information", {"fields": ["lat", "lng", "location", "location_description"]}),
        ("Study Information", {"fields": ["study", "permanent_tag"]}),
        ("Notes", {"fields": ["notes"]}),
    ]
    list_display = ["tag_id", "common_name_spanish", "common_name_english", "display_adoption_status"]
    list_filter = ["adoption_status"]
    search_fields = ["id", "tag_id", "common_name_english", "common_name_spanish"]

    def save_model(self, request, obj, form, change):
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
        # Gets the first 6 characters of admin's username
        user_code = request.user.username[:6].upper()

        if change:
            changed_fields = ", ".join(form.changed_data)
            new_entry = (
                f"{timestamp} {user_code} modified ({changed_fields})"
            )
        else:
            new_entry = f"{timestamp} {user_code} initial data entry"

        if obj.modified:
            obj.modified = f"{new_entry}; {obj.modified}"
        else:
            obj.modified = new_entry

        super().save_model(request, obj, form, change)

@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    # Allows for auto expanded collpasible fields in admin view.
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
    # Allows for auto expanded collpasible fields in admin view.
    class Media:
        js = ('admin/js/admin_expand.js',)

    # Allows the primary keys (ID) to be displayed without it being editable. 
    readonly_fields = ("id", "number", "date", "expiration_date", "donor_name", "tree_id", "expired_tree_id", "certificate_sent")

    fieldsets = [
        ("Identifiers", {"fields": ["id", "number"]}),
        ("Donation Date and Expiration", {"fields": ["date", "expiration_date"]}),
        ("Donation Information", {"fields": ["amount", "payment_method"]}),
        ("Donor Information", {"fields": ["donor_name", "donor_chosen_name"]}),
        ("Tree Adopted", {"fields": ["tree_id", "expired_tree_id", "certificate_sent"]}),
        ("Notes", {"fields": ["notes"]}),
    ]
    list_display = ["searchable_donor_name", "number", "amount", "tree_id", "expired_tree_id", "certificate_sent"]
    list_filter = ["date", "expiration_date"]
    search_fields = ["searchable_donor_name", "searchable_tree_id", "number", "donor_chosen_name", "expired_tree_id"]