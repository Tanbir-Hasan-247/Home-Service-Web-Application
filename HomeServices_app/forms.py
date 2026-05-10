from django import forms
from .models import *


class stateform(forms.ModelForm):
    class Meta:
        model = State
        fields = "__all__"
        widgets = {
            "country": forms.Select(attrs={"class": "form-select form-select-dark"}),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-dark",
                    "placeholder": "e.g., California",
                }
            ),
        }


class cityform(forms.ModelForm):
    class Meta:
        model = City
        fields = "__all__"
        widgets = {
            "state": forms.Select(attrs={"class": "form-select form-select-dark"}),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control form-control-dark",
                    "placeholder": "e.g., Los Angeles",
                }
            ),
        }


class ServiceCatogoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCatogarys
        fields = ("Name", "img", "Description")
