from __future__ import annotations

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import PhotoUploadForm, RSVPForm
from .models import Guest, PhotoSubmission, RSVP
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
            guest_id = rsvp_form.cleaned_data["guest_id"]
            guest = get_object_or_404(Guest, id=guest_id)
            
            # Check if RSVP already exists
            existing_rsvp = RSVP.objects.filter(guest=guest).first()
            if existing_rsvp:
                # Redirect to existing RSVP page
                return redirect("rsvp-existing", rsvp_id=existing_rsvp.id)
            
            verified = guest.verified
            
            attendance = rsvp_form.cleaned_data["attendance_choice"] == "yes"
            email = rsvp_form.cleaned_data.get("email", "") or guest.email
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
            # Redirect to thank you page
            return redirect("rsvp-thank-you", rsvp_id=response.id)
    else:
        rsvp_form = RSVPForm()

    return render(request, "celebration/rsvp.html", {"rsvp_form": rsvp_form})


def rsvp_thank_you_view(request, rsvp_id):
    """Thank you page after RSVP submission."""
    rsvp = get_object_or_404(RSVP, id=rsvp_id)
    return render(request, "celebration/rsvp_thank_you.html", {"rsvp": rsvp})


def rsvp_existing_view(request, rsvp_id):
    """Page shown when guest already has an RSVP - allows them to change or keep it."""
    rsvp = get_object_or_404(RSVP, id=rsvp_id)
    
    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "change":
            # Update RSVP with new values
            attendance = request.POST.get("attendance_choice") == "yes"
            party_size = int(request.POST.get("party_size", 1))
            message = request.POST.get("message", "")
            
            # Update avatar configs if party size changed
            if party_size != rsvp.party_size:
                default_config = {
                    "skin": "porcelain",
                    "hair": "espresso",
                    "hairStyle": "short",
                    "outfit": "lavender",
                    "accent": "floral",
                    "signature": rsvp.guest.full_name.strip() or "guest-avatar",
                }
                avatar_configs = [default_config.copy() for _ in range(party_size)]
                rsvp.avatar_config = avatar_configs
            
            rsvp.attending = attendance
            rsvp.party_size = party_size
            rsvp.message = message
            rsvp.livestream_requested = not attendance
            rsvp.save()
            
            messages.success(request, "Your RSVP has been updated!")
            return redirect("home")
        
        elif action == "keep":
            # Keep same RSVP, redirect based on attendance
            if rsvp.attending:
                return redirect("chapel")
            else:
                return redirect("livestream")
    
    return render(request, "celebration/rsvp_existing.html", {"rsvp": rsvp})


def avatar_customization_view(request, rsvp_id):
    """Avatar customization page - builds avatars based on party size."""
    rsvp = get_object_or_404(RSVP, id=rsvp_id)
    
    if request.method == "POST":
        # Process avatar configurations from form
        avatar_configs = []
        for i in range(rsvp.party_size):
            config = {
                "skin": request.POST.get(f"avatar_{i}_skin_tone", "light1"),
                "hair": request.POST.get(f"avatar_{i}_hair_color", "dark1"),
                "hairStyle": request.POST.get(f"avatar_{i}_hair_style", "shortFlat"),
                "clothesType": request.POST.get(f"avatar_{i}_clothes_type", "collarAndSweater"),
                "clothesColor": request.POST.get(f"avatar_{i}_clothes_color", "blue"),
                "facialHair": request.POST.get(f"avatar_{i}_facial_hair", "none"),
                "accessories": request.POST.get(f"avatar_{i}_accessories", "none"),
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
                "skin": "light2",
                "hair": "dark1",  # Dark brown hair
                "hairStyle": "shortFlat",
                "clothesType": "collarAndSweater",
                "clothesColor": "blue",
                "facialHair": "none",
                "accessories": "none",
                "signature": rsvp.guest.full_name.strip() or "guest-avatar",
            }
            rsvp.avatar_config = [default_config.copy() for _ in range(rsvp.party_size)]
    
    # Ensure we have configs for all party members and set defaults for missing/empty values
    default_config = {
        "skin": "light1",  # Light skin tone
        "hair": "dark1",  # Dark brown hair
        "hairStyle": "shortFlat",
        "clothesType": "collarAndSweater",
        "clothesColor": "blue",
        "facialHair": "none",
        "accessories": "none",
    }
    
    for i in range(len(rsvp.avatar_config), rsvp.party_size):
        config = default_config.copy()
        config["signature"] = f"{rsvp.guest.full_name.strip()}-{i+1}" or f"guest-avatar-{i+1}"
        rsvp.avatar_config.append(config)
    
    # Ensure all existing configs have the required fields with defaults
    for i, config in enumerate(rsvp.avatar_config):
        if not isinstance(config, dict):
            config = {}
        # Set defaults for any missing fields
        if "skin" not in config or not config["skin"]:
            config["skin"] = "light2"
        if "hair" not in config or not config["hair"]:
            config["hair"] = "dark1"
        if "hairStyle" not in config or not config["hairStyle"]:
            config["hairStyle"] = "shortFlat"
        if "clothesType" not in config or not config["clothesType"]:
            config["clothesType"] = "collarAndSweater"
        if "clothesColor" not in config or not config["clothesColor"]:
            config["clothesColor"] = "blue"
        if "facialHair" not in config or not config["facialHair"]:
            config["facialHair"] = "none"
        if "accessories" not in config or not config["accessories"]:
            config["accessories"] = "none"
        if "signature" not in config or not config["signature"]:
            config["signature"] = f"{rsvp.guest.full_name.strip()}-{i+1}" or f"guest-avatar-{i+1}"
        rsvp.avatar_config[i] = config
    
    return render(request, "celebration/avatar_customization.html", {
        "rsvp": rsvp,
        "party_size": rsvp.party_size,
        "avatar_configs": rsvp.avatar_config,
    })


def chapel_view(request):
    """Chapel page - displays interactive 3D seating chart."""
    # Get only the 30 most recent RSVPs
    attending_rsvps = RSVP.objects.filter(attending=True).select_related("guest").order_by("-created_at")[:30]
    
    # Build seating chart from RSVPs
    seating = build_seating_chart(attending_rsvps)
    
    # Count attendees
    attendee_count = sum(rsvp.party_size for rsvp in attending_rsvps)
    
    # Get current user's RSVP ID from URL parameter or use most recent
    current_rsvp_id = request.GET.get('rsvp_id')
    if current_rsvp_id:
        try:
            current_rsvp = RSVP.objects.get(id=current_rsvp_id, attending=True)
        except RSVP.DoesNotExist:
            current_rsvp = attending_rsvps.first() if attending_rsvps else None
    else:
        current_rsvp = attending_rsvps.first() if attending_rsvps else None
    
    return render(
        request,
        "celebration/chapel.html",
        {
            "seating": seating,
            "attendee_count": attendee_count,
            "current_rsvp_id": current_rsvp.id if current_rsvp else None,
        },
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


def guest_search_view(request):
    """API endpoint to search for guests by name."""
    from django.http import JsonResponse
    
    query = request.GET.get("q", "").strip()
    
    if not query or len(query) < 2:
        return JsonResponse({"guests": []})
    
    # Search for guests whose name contains the query (case-insensitive)
    # Also search in household_name for better matching
    from django.db.models import Q
    
    guests = Guest.objects.filter(
        Q(full_name__icontains=query) | Q(household_name__icontains=query)
    ).order_by("full_name")[:10]  # Limit to 10 results
    
    results = [
        {
            "id": guest.id,
            "name": guest.full_name,
            "email": guest.email,
            "household": guest.household_name or "",
        }
        for guest in guests
    ]
    
    return JsonResponse({"guests": results})

