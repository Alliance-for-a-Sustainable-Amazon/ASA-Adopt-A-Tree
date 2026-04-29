"""
views.py
This file contains the different views available on the site.

As we are using this django project solely as an admin site currently, there are not many views.
The current view, 'generic_list_view', works but is not set up in the urls.py file.
"""

from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, Http404
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required

from .models import Donor, Tree, Donation

MODEL_MAP = {
    'donors': Donor,
    'trees': Tree,
    'donations': Donation,
}

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