"""
serializers.py
This file contains the different sets of data that are available via API call. 
"""

from rest_framework import serializers
from django.conf import settings
from .models import Tree

BLOB_STORAGE = settings.AZURE_BLOB_STORAGE
BLOB_CONTAINER = settings.AZURE_BLOB_CONTAINER

# This serializer is used to obtain the bare minimum information to populate the map with tree markers
class TreeMapSerializer(serializers.ModelSerializer):
    local_name = serializers.CharField(source='common_name_spanish')

    class Meta:
        model = Tree
        fields = [
            'id',
            'tag_id',
            'local_name',
            'lat',
            'lng',
            'adoption_status',
        ]

# This serializer is used to populate each marker with the tree details when the user clicks on the tree
class TreeDetailSerializer(serializers.ModelSerializer):
    local_name = serializers.CharField(source='common_name_spanish')
    english_name = serializers.CharField(source='common_name_english')

    donor_name = serializers.CharField(
        source='donation.donor_chosen_name',
        read_only=True,
        default=None
    )

    class Meta:
        model = Tree
        fields = [
            'id',
            'permanent_tag',
            'local_name',
            'english_name',
            'genus',
            'species',
            'lat',
            'lng',
            'dbh',
            'height',
            'adoption_status',
            'donor_name',
            'species_description'
        ]