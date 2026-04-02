from __future__ import annotations

import json

from django import forms

from .models import PhotoSubmission


class RSVPForm(forms.Form):
    ATTENDANCE_CHOICES = [
        ("yes", "Attend"),
        ("no", "Unable to Attend"),
    ]
    MEAL_CHOICES = [
        ("chef", "Chef's Seasonal Selection"),
        ("chicken", "Herb-Roasted Chicken"),
        ("fish", "Citrus Sea Bass"),
        ("veggie", "Garden Risotto"),
    ]

    SKIN_CHOICES = [
        ("porcelain", "Porcelain"),
        ("rosy", "Rosy"),
        ("sienna", "Sienna"),
        ("amber", "Amber"),
        ("espresso", "Espresso"),
    ]
    HAIR_CHOICES = [
        ("midnight", "Midnight"),
        ("espresso", "Espresso"),
        ("chestnut", "Chestnut"),
        ("copper", "Copper"),
        ("honey", "Honey Blonde"),
        ("platinum", "Platinum"),
        ("rose-quartz", "Rose Quartz"),
    ]
    HAIR_STYLES = [
        ("short", "Short sleek"),
        ("long", "Long flowing waves"),
    ]
    OUTFIT_CHOICES = [
        ("champagne", "Champagne Tux / Gown"),
        ("lavender", "Lavender Silk"),
        ("midnight", "Midnight Navy"),
        ("sage", "Sage Garden"),
        ("rose", "Rosewater"),
    ]
    ACCENT_CHOICES = [
        ("na", "None"),
        ("floral", "Garden Florals"),
        ("pocket-square", "Pocket Square"),
        ("veil", "Veil"),
        ("bow-tie", "Bow Tie"),
    ]

    guest_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput(),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "hello@example.com"}),
    )
    attendance_choice = forms.ChoiceField(
        choices=ATTENDANCE_CHOICES,
        widget=forms.RadioSelect,
    )
    party_size = forms.IntegerField(
        label="Party Size",
        min_value=1,
        max_value=6,
        initial=1,
        help_text="Include yourself and all others from your invitation who will attend",
    )
    guest_names_json = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )
    dietary_restrictions = forms.CharField(
        required=False,
        label="Dietary Restrictions / Allergies",
        help_text="",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        attendance = cleaned.get("attendance_choice")
        party_size = cleaned.get("party_size")
        raw_guest_names = (cleaned.get("guest_names_json") or "").strip()

        if attendance != "yes":
            return cleaned

        if not party_size:
            return cleaned

        if not raw_guest_names:
            self.add_error("guest_names_json", "Please enter a name for each person in your party.")
            return cleaned

        try:
            parsed = json.loads(raw_guest_names)
        except json.JSONDecodeError:
            self.add_error("guest_names_json", "Please enter a name for each person in your party.")
            return cleaned

        if not isinstance(parsed, list):
            self.add_error("guest_names_json", "Please enter a name for each person in your party.")
            return cleaned

        names = [str(x).strip() for x in parsed if str(x).strip()]
        if len(names) != party_size:
            self.add_error("guest_names_json", "Please enter a name for each person in your party.")

        return cleaned


class PhotoUploadForm(forms.ModelForm):
    class Meta:
        model = PhotoSubmission
        fields = ["display_name", "email", "image", "caption"]
        widgets = {
            "caption": forms.Textarea(attrs={"rows": 2}),
        }
