"""
models.py
Defines the models of the database. Each model a table with each entry representing a column.
"""

import uuid

from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.contrib import admin

class Donor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    total_donation_amount = models.IntegerField()

    def __str__(self):
        return f"{self.name}"

class Tree(models.Model):
    # Choices class allows for dropdown capability with adoption status.
    class AdoptionChoices(models.TextChoices):
        # 'stored value', 'Label'
        ADOPTABLE = 'adoptable', 'Adoptable'
        ADOPTED = 'adopted', 'Adopted'

    modified = models.TextField(blank=True, null=True, help_text="'Modified' automatically calculated after entry creation.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Auto generated: Month, Day, Year, Time")
    updated_at = models.DateTimeField(auto_now=True, help_text = "Auto generated: Month, Day, Year, Time")
    reserve_until = models.DateTimeField(null=True, blank=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, help_text="Primary Key (UUID) used for relations.")
    tag_id = models.CharField(max_length=255, default="XXXX-XXXX", blank=True, help_text="Auto generated: scientificNameAbbreviation-permanentTag. Ex: BEEX-0000")
    permanent_tag = models.CharField(max_length=255, help_text="Tree Tag Number: XXXX. <b>Important:</b> If permanent tag is modified, the tag in the corresponding Azure picture must also be changed.")
    study = models.CharField(max_length=255, blank=True, null=True)
    family = models.CharField(max_length=255)
    genus = models.CharField(max_length=255)
    species = models.CharField(max_length=255, blank=True, null=True, help_text="<b>Important:</b> If species is modified, the taxonomy tag in the corresponding Azure picture must also be changed.")
    dbh = models.CharField(max_length=255, blank=True, null=True)
    height = models.CharField(max_length=255, blank=True, null=True)
    common_name_spanish = models.CharField(max_length=255)
    common_name_english = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    location_description = models.TextField(blank=True)
    lat = models.FloatField(default=0, help_text="Latitude: XX.XXXX / -XX.XXXX")
    lng = models.FloatField(default=0, help_text="Longitude: XX.XXXX / -XX.XXXX")
    adoption_status = models.CharField(max_length=10, choices=AdoptionChoices.choices, default=AdoptionChoices.ADOPTABLE)
    species_description = models.TextField(blank=True, default="", help_text="Species facts for Wix page. <b>Important:</b> Seperated by semi-colon. Ex: Fact1; Fact2; Fact3;")
    notes = models.TextField(blank=True, default="")

    # Overrides the save function in order to auto generate a tag number based on provided information
    def save(self, *args, **kwargs):

        if self.genus == '.' or not self.genus:
            genus = 'XX'
        else:
            genus = self.genus[:2]


        if not self.species:
            species = 'XX'
        else:
            # Prevents casing issues
            species_upper = self.species.upper()

            # If tree has unknown species, it will be given 'SP.', 'SPP.' (multiple species in one), or '.'
            if species_upper == 'SP.' or species_upper == 'SPP.' or species_upper =='.':
                species = 'XX'
            else:
                species = self.species[:2]

        # Gets the first part of the tag_id
        sci_name_abbreviated = f"{genus}{species}"
        sci_name_abbreviated = sci_name_abbreviated.upper()

        if self.permanent_tag:
            tag_number = self.permanent_tag
        else:
            self.permanent_tag = "XXXX"
        
        self.tag_id = f"{sci_name_abbreviated}_{tag_number}"
        
        super().save(*args, **kwargs)

    # Provides Admin display with a green check for 'adopted', or a red x for 'adoptable'
    @admin.display(
            description = "Adopted?",
            boolean = True,
    )
    def display_adoption_status(self):
        return self.adoption_status == "adopted"

    def __str__(self):
        return f"{self.tag_id}"

class Donation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.IntegerField(default=0, help_text="'Number' automatically calculated after entry creation.")
    date = models.DateTimeField(default=timezone.now, help_text="Date is automatically set.")
    donor_name = models.ForeignKey(Donor, on_delete=models.SET_NULL, null=True, blank=True, related_name="donations")
    # Foreign keys are not searchable so make a hidden field that allows admins to search.
    searchable_donor_name = models.CharField(max_length=255, default="", blank=True)
    donor_chosen_name = models.CharField(max_length=255, default="Anonymous", help_text="Name that will appear on the adopted tree.")
    stripe_session_id = models.CharField(max_length=255, unique=True, default="")
    stripe_payment_intent = models.CharField(max_length=255, default="")
    amount = models.IntegerField()
    currency = models.CharField(max_length=10, default="")
    payment_method = models.CharField(max_length=255)
    expiration_date = models.DateTimeField(blank=True, null=True, help_text="'Expiration Date' is automatically calculated.")
    expiration_processed = models.BooleanField(default=False)
    tree_id = models.OneToOneField(Tree, on_delete=models.SET_NULL, null=True, blank=True, related_name="donation", help_text="Tag ID of the adopted tree. Automatically set upon adoption.")
    # Foreign keys are not searchable so make a hidden field that allows admins to search.
    searchable_tree_id = models.CharField(max_length=255, default="", blank=True)
    expired_tree_id = models.CharField(max_length=255, default="", blank=True, help_text="Automatically set upon tree expiration.")
    notes = models.TextField(blank=True, default="")

    # Overrides the save function to auto generate listed fields: number, expiration_date
    def save(self, *args, **kwargs):
        # Auto increments number in order to have easy searchability outside of the UUID id
        if not self.number:
            last_donation = Donation.objects.all().order_by('number').last()
            if last_donation:
                self.number = (last_donation.number + 1)
            else:
                self.number = 1

        # Automatically adds expiration date to a year after initial donation date
        if not self.expiration_date:
            self.expiration_date = self.date + timedelta(days=365)

        super().save(*args, **kwargs)

    # Date formating for readability.
    def human_readable_date(self):
        return self.date.strftime("%b %d, %Y - %H:%M")

    def __str__(self):
        return f"${self.amount} donated by {self.donor_name} on {self.human_readable_date()}"

