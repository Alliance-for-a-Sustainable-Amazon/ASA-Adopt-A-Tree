"""
models.py
Defines the models of the database. Each model a table with each entry representing a column.
"""

import datetime, uuid

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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.IntegerField(default=0, blank=True, help_text="'Number' automatically calculated after entry creation.")
    permanent_tag = models.CharField(max_length=255, null=True, blank=True)
    study = models.CharField(max_length=255, null=True, blank=True)
    family = models.CharField(max_length=255)
    genus = models.CharField(max_length=255)
    species = models.CharField(max_length=255)
    common_name_spanish = models.CharField(max_length=255)
    common_name_english = models.CharField(max_length=255)
    dbh = models.CharField(max_length=255, help_text="Diameter at Breast Height")
    location = models.CharField(max_length=255)
    location_description = models.TextField(blank=True)
    lat = models.CharField(max_length=255, help_text="Latitude")
    long = models.CharField(max_length=255, help_text="Longitude")
    adoption_status = models.CharField(max_length=10, choices=AdoptionChoices.choices, default=AdoptionChoices.ADOPTABLE)
    notes = models.TextField(blank=True, default='')

    # Overrides the save function in order to auto generate an incrementing number for searchability.
    def save(self, *args, **kwargs):
        if not self.number:
            last_tree = Tree.objects.all().order_by('number').last()
            if last_tree:
                self.number = (last_tree.number + 1)
            else:
                self.number = 1
        super().save(*args, **kwargs)

    # Provides Admin display with a green check for 'adopted', or a red x for 'adoptable'.
    @admin.display(
            description = "Adopted?",
            boolean = True,
    )
    def display_adoption_status(self):
        return self.adoption_status == "adopted"

    def __str__(self):
        return f"{self.number}: {self.common_name_english}"

class Donation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.IntegerField(default=0, help_text="'Number' automatically calculated after entry creation.")
    date = models.DateTimeField(default=timezone.now(), help_text="Date is automatically set.")
    donor_id = models.ForeignKey(Donor, on_delete=models.SET_NULL, null=True, blank=True)
    donor_name = models.CharField(max_length=255)
    donor_chosen_name = models.CharField(max_length=255, help_text="Name that will appear on the adopted tree.")
    amount = models.IntegerField()
    payment_method = models.CharField(max_length=255)
    expiration_date = models.DateTimeField(blank=True, null=True, help_text="'Expiration Date' is automatically calculated.")
    tree_id = models.ForeignKey(Tree, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    # Overrides the save function to auto generate listed fields: number, expiration_date
    def save(self, *args, **kwargs):
        # Auto increments number in order to have easy searchability outside of the UUID id. 
        if not self.number:
            last_donation = Donation.objects.all().order_by('number').last()
            if last_donation:
                self.number = (last_donation.number + 1)
            else:
                self.number = 1

        # Automatically adds expiration date to a year after initial donation date.
        if not self.expiration_date:
            self.expiration_date = self.date + timedelta(days=365)

        super().save(*args, **kwargs)

    # Date formating for readability.
    def human_readable_date(self):
        return self.date.strftime("%b %d, %Y - %H:%M")

    def __str__(self):
        return f"${self.amount} donated by {self.donor_name} on {self.human_readable_date()}"

