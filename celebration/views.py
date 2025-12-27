from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import PhotoUploadForm, RSVPForm
from .models import PhotoSubmission, RSVP
from .utils import build_seating_chart, find_or_create_guest


def home(request):
    rsvp_form = RSVPForm()
    photo_form = PhotoUploadForm()
    hero_details = {
        "date": "Saturday, June 13, 2025",
        "locations": [
            ("Ceremony", "Proclamation Presbyterian Church, Bryn Mawr, PA"),
            ("Reception", "Kings Mills, Media, PA"),
        ],
    }
    timeline = [
        ("2:00 PM", "Guest arrival & welcome drinks"),
        ("2:30 PM", "Processional begins"),
        ("3:30 PM", "Garden portraits & lawn games"),
        ("5:00 PM", "Seated dinner and toasts"),
        ("8:00 PM", "Dessert, espresso martinis & dancing"),
    ]
    lodging = [
        {
            "name": "Wayne Hotel",
            "details": "Historic Main Line stay, 10 minutes from the chapel.",
            "link": "https://waynehotel.com",
        },
        {
            "name": "The Inn at Villanova",
            "details": "Modern suites nestled among the trees.",
            "link": "https://www1.villanova.edu/university/inn.html",
        },
        {
            "name": "Airbnb",
            "details": "Curated list of nearby homes and family-friendly stays.",
            "link": "https://www.airbnb.com/s/Villanova--PA",
        },
    ]
    wedding_party = [
        ("Maid of Honor", "Caroline Bentley"),
        ("Best Man", "Anthony Long"),
        ("Parents of the Bride", "Lydia & Matthew Kane"),
        ("Parents of the Groom", "Eleanor & Brian Malkowicz"),
        ("Flower Girl", "Isabella Ruiz"),
        ("Ring Bearer", "Theo Malkowicz"),
    ]

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "rsvp":
            rsvp_form = RSVPForm(request.POST)
            if rsvp_form.is_valid():
                guest, verified = find_or_create_guest(
                    rsvp_form.cleaned_data["full_name"],
                    rsvp_form.cleaned_data["email"],
                )
                attendance = rsvp_form.cleaned_data["attendance_choice"] == "yes"
                response, _ = RSVP.objects.update_or_create(
                    guest=guest,
                    defaults={
                        "attending": attendance,
                        "party_size": rsvp_form.cleaned_data["party_size"],
                        "email": rsvp_form.cleaned_data["email"],
                        "meal_preference": rsvp_form.cleaned_data["meal_preference"],
                        "song_request": rsvp_form.cleaned_data["song_request"],
                        "message": rsvp_form.cleaned_data["message"],
                        "avatar_config": rsvp_form.cleaned_avatar(),
                        "livestream_requested": not attendance,
                    },
                )
                if not verified:
                    messages.info(
                        request,
                        "We didn't see your name on the original list, so we've flagged "
                        "it for review in the admin panel.",
                    )
                if attendance:
                    messages.success(
                        request,
                        "You're on the guest list! Head to the chapel to see your seat.",
                    )
                    return redirect("chapel")
                messages.success(
                    request,
                    "We've saved your RSVP. A livestream reminder will arrive closer to the day.",
                )
                return redirect("livestream")
        elif form_type == "photo":
            photo_form = PhotoUploadForm(request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                guest, _ = find_or_create_guest(photo.display_name, photo.email)
                photo.guest = guest
                photo.save()
                messages.success(
                    request,
                    "Thank you for sharing! Photos appear in the gallery once approved.",
                )
                return redirect(reverse("home") + "#photos")

    gallery_photos = PhotoSubmission.objects.filter(approved=True)[:6]

    context = {
        "hero_details": hero_details,
        "timeline": timeline,
        "lodging": lodging,
        "wedding_party": wedding_party,
        "rsvp_form": rsvp_form,
        "photo_form": photo_form,
        "gallery_photos": gallery_photos,
    }
    return render(request, "celebration/home.html", context)


def rsvp_view(request):
    """Basic RSVP page - collects name, attendance, and party size."""
    if request.method == "POST":
        rsvp_form = RSVPForm(request.POST)
        if rsvp_form.is_valid():
            guest, verified = find_or_create_guest(
                rsvp_form.cleaned_data["full_name"],
                "",
            )
            attendance = rsvp_form.cleaned_data["attendance_choice"] == "yes"
            email = rsvp_form.cleaned_data.get("email", "")
            party_size = rsvp_form.cleaned_data["party_size"]
            
            # Create default avatar configs (one per party member)
            default_config = {
                "skin": "porcelain",
                "hair": "espresso",
                "hairStyle": "short",
                "outfit": "lavender",
                "accent": "floral",
                "signature": guest.full_name.strip() or "guest-avatar",
            }
            avatar_configs = [default_config.copy() for _ in range(party_size)]
            
            response, _ = RSVP.objects.update_or_create(
                guest=guest,
                defaults={
                    "attending": attendance,
                    "party_size": party_size,
                    "email": email,
                    "meal_preference": "",
                    "song_request": "",
                    "message": "",
                    "avatar_config": avatar_configs,
                    "livestream_requested": not attendance,
                },
            )
            if not verified:
                messages.info(
                    request,
                    "We didn't see your name on the original list, so we've flagged "
                    "it for review in the admin panel.",
                )
            # Redirect to avatar customization page
            return redirect("avatar-customization", rsvp_id=response.id)
    else:
        rsvp_form = RSVPForm()

    return render(request, "celebration/rsvp.html", {"rsvp_form": rsvp_form})


def avatar_customization_view(request, rsvp_id):
    """Avatar customization page - builds avatars based on party size."""
    rsvp = get_object_or_404(RSVP, id=rsvp_id)
    
    if request.method == "POST":
        # Process avatar configurations from form
        avatar_configs = []
        for i in range(rsvp.party_size):
            config = {
                "skin": request.POST.get(f"avatar_{i}_skin_tone", "porcelain"),
                "hair": request.POST.get(f"avatar_{i}_hair_color", "espresso"),
                "hairStyle": request.POST.get(f"avatar_{i}_hair_style", "short"),
                "outfit": request.POST.get(f"avatar_{i}_outfit_color", "lavender"),
                "accent": request.POST.get(f"avatar_{i}_accent", "floral"),
                "signature": request.POST.get(f"avatar_{i}_signature", f"{rsvp.guest.full_name.strip()}-{i+1}" or f"guest-avatar-{i+1}"),
            }
            avatar_configs.append(config)
        
        rsvp.avatar_config = avatar_configs
        rsvp.save()
        
        if rsvp.attending:
            messages.success(
                request,
                "You're on the guest list! Head to the chapel to see your seat.",
            )
            return redirect("chapel")
        else:
            messages.success(
                request,
                "We've saved your RSVP. A livestream reminder will arrive closer to the day.",
            )
            return redirect("livestream")
    
    # Ensure avatar_config is a list
    if not isinstance(rsvp.avatar_config, list):
        # Convert old single config to list
        if isinstance(rsvp.avatar_config, dict):
            rsvp.avatar_config = [rsvp.avatar_config]
        else:
            default_config = {
                "skin": "porcelain",
                "hair": "espresso",
                "hairStyle": "short",
                "outfit": "lavender",
                "accent": "floral",
                "signature": rsvp.guest.full_name.strip() or "guest-avatar",
            }
            rsvp.avatar_config = [default_config.copy() for _ in range(rsvp.party_size)]
    
    # Ensure we have configs for all party members
    while len(rsvp.avatar_config) < rsvp.party_size:
        default_config = {
            "skin": "porcelain",
            "hair": "espresso",
            "hairStyle": "short",
            "outfit": "lavender",
            "accent": "floral",
            "signature": f"{rsvp.guest.full_name.strip()}-{len(rsvp.avatar_config)+1}" or f"guest-avatar-{len(rsvp.avatar_config)+1}",
        }
        rsvp.avatar_config.append(default_config.copy())
    
    return render(request, "celebration/avatar_customization.html", {
        "rsvp": rsvp,
        "party_size": rsvp.party_size,
        "avatar_configs": rsvp.avatar_config,
    })


def chapel_view(request):
    """Chapel page - coming soon placeholder."""
    return render(
        request,
        "celebration/coming_soon.html",
        {"page_title": "Chapel"},
    )


def livestream_view(request):
    """Livestream page - coming soon placeholder."""
    return render(
        request,
        "celebration/coming_soon.html",
        {"page_title": "Livestream"},
    )


def registry_view(request):
    """Registry page displaying the Amazon wedding registry."""
    amazon_registry_url = "https://www.amazon.com/wedding/guest-view/1JFYA0F7G59UD"
    return render(
        request,
        "celebration/registry.html",
        {"amazon_registry_url": amazon_registry_url},
    )


def details_view(request):
    """Details page - coming soon placeholder."""
    return render(
        request,
        "celebration/coming_soon.html",
        {"page_title": "Details"},
    )


def travel_view(request):
    """Travel page - coming soon placeholder."""
    return render(
        request,
        "celebration/coming_soon.html",
        {"page_title": "Travel"},
    )


def wedding_party_view(request):
    """Wedding Party page - coming soon placeholder."""
    return render(
        request,
        "celebration/coming_soon.html",
        {"page_title": "Wedding Party"},
    )


def gallery_view(request):
    """Photo gallery page - coming soon placeholder."""
    return render(
        request,
        "celebration/coming_soon.html",
        {"page_title": "Photo Gallery"},
    )


def photo_upload_view(request):
    form = PhotoUploadForm()
    if request.method == "POST":
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            guest, _ = find_or_create_guest(photo.display_name, photo.email)
            photo.guest = guest
            photo.save()
            messages.success(request, "Upload received! We'll share it once it's curated.")
            return redirect("photo-upload")

    return render(
        request,
        "celebration/photo_upload.html",
        {"photo_form": form},
    )


