from django.db import models
from django.utils import timezone


def default_avatar_config() -> list:
    """
    Provide defaults for the three.js avatar preview so RSVP previews
    always have safe values even before guests customize them.
    Returns a list of avatar configs (one per party member).
    """
    return [{
        "skin": "porcelain",
        "hair": "espresso",
        "hairStyle": "short",
        "outfit": "lavender",
        "accent": "floral",
        "signature": "guest-avatar",
    }]


class Guest(models.Model):
    BRIDE_SIDE = "bride"
    GROOM_SIDE = "groom"
    FAMILY_SIDE = "family"
    SIDES = [
        (BRIDE_SIDE, "Bride"),
        (GROOM_SIDE, "Groom"),
        (FAMILY_SIDE, "Family"),
    ]

    full_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    household_name = models.CharField(
        max_length=160,
        blank=True,
        help_text="Optional grouping label to seat families together.",
    )
    side = models.CharField(max_length=24, choices=SIDES, blank=True)
    relationship = models.CharField(max_length=120, blank=True)
    invited = models.BooleanField(default=True)
    verified = models.BooleanField(
        default=True,
        help_text="Unverified guests were not part of the original list but submitted an RSVP.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]
        # Note: unique_together removed since email can be blank
        # Guests are identified by full_name for RSVP search

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email})"


class RSVP(models.Model):
    MEAL_CHOICES = [
        ("chef", "Chef's Seasonal Selection"),
        ("chicken", "Herb-Roasted Chicken"),
        ("fish", "Citrus Sea Bass"),
        ("veggie", "Garden Risotto"),
    ]

    guest = models.ForeignKey(
        Guest,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    attending = models.BooleanField()
    party_size = models.PositiveIntegerField(default=1)
    email = models.EmailField()
    meal_preference = models.CharField(
        max_length=32,
        choices=MEAL_CHOICES,
        blank=True,
    )
    song_request = models.CharField(max_length=160, blank=True)
    message = models.TextField(blank=True)
    avatar_config = models.JSONField(default=default_avatar_config)
    livestream_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def seating_label(self) -> str:
        return self.guest.household_name or self.guest.full_name.split()[0]

    def __str__(self) -> str:
        status = "Attending" if self.attending else "Livestream"
        return f"{self.guest.full_name} – {status}"


def upload_to_photo(instance, filename: str) -> str:
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    return f"wedding_photos/{timestamp}_{filename}"


class PhotoSubmission(models.Model):
    guest = models.ForeignKey(
        Guest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="photos",
    )
    display_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    image = models.ImageField(upload_to=upload_to_photo)
    caption = models.CharField(max_length=200, blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Photo from {self.display_name}"
