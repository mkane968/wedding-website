from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
import json
import csv
from django.utils import timezone

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
            dietary_restrictions = (rsvp_form.cleaned_data.get("dietary_restrictions") or "").strip()
            party_size = rsvp_form.cleaned_data["party_size"]

            if attendance:
                guest_names: list[str] = []
                raw_guest_names = (rsvp_form.cleaned_data.get("guest_names_json") or "").strip()
                if raw_guest_names:
                    try:
                        parsed = json.loads(raw_guest_names)
                        if isinstance(parsed, list):
                            guest_names = [str(x).strip() for x in parsed]
                    except json.JSONDecodeError:
                        guest_names = []
                guest_names = [name for name in guest_names if name]
                if len(guest_names) != party_size:
                    messages.error(request, "Please enter a name for each person in your party.")
                    return render(request, "celebration/rsvp.html", {"rsvp_form": rsvp_form})
            else:
                party_size = 1
                guest_names = [guest.full_name]
            
            def default_hair_style(index: int) -> str:
                if index == 0:
                    return "longButNotTooLong"  # Long 1
                if index == 1:
                    return "shortWaved"  # Short 1
                # For people 3+ alternate Long 1 / Long 2
                # index=2 -> Long 1, index=3 -> Long 2, index=4 -> Long 1, ...
                return "longButNotTooLong" if (index % 2 == 0) else "curvy"

            avatar_configs = []
            for idx in range(party_size):
                avatar_configs.append(
                    {
                        "skin": "porcelain",
                        "hair": "espresso",
                        "hairStyle": default_hair_style(idx),
                        "outfit": "lavender",
                        "accent": "floral",
                        "accessories": "glasses",
                        "accessoriesColor": "black",
                        "signature": guest.full_name.strip() or "guest-avatar",
                    }
                )
            
            response, _ = RSVP.objects.update_or_create(
                guest=guest,
                defaults={
                    "attending": attendance,
                    "party_size": party_size,
                    "guest_names": guest_names,
                    "email": email,
                    "meal_preference": "",
                    "song_request": "",
                    "message": dietary_restrictions,
                    "avatar_config": avatar_configs,
                    "livestream_requested": not attendance,
                },
            )
            if attendance:
                request.session["current_rsvp_id"] = response.id
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
            dietary_restrictions = (request.POST.get("message", "") or "").strip()

            guest_names: list[str] = []
            raw_guest_names = (request.POST.get("guest_names_json", "") or "").strip()
            if raw_guest_names:
                try:
                    parsed = json.loads(raw_guest_names)
                    if isinstance(parsed, list):
                        guest_names = [str(x).strip() for x in parsed]
                except json.JSONDecodeError:
                    guest_names = []
            guest_names = [name for name in guest_names if name]
            if attendance and (not guest_names or len(guest_names) != party_size):
                messages.error(request, "Please enter a name for each person in your party.")
                return redirect("rsvp-existing", rsvp_id=rsvp.id)

            if not attendance:
                party_size = 1
                guest_names = [rsvp.guest.full_name]
            
            # Update avatar configs if party size changed
            if party_size != rsvp.party_size:
                def default_hair_style(index: int) -> str:
                    if index == 0:
                        return "longButNotTooLong"  # Long 1
                    if index == 1:
                        return "shortWaved"  # Short 1
                    return "longButNotTooLong" if (index % 2 == 0) else "curvy"

                avatar_configs = []
                for idx in range(party_size):
                    avatar_configs.append(
                        {
                            "skin": "porcelain",
                            "hair": "espresso",
                            "hairStyle": default_hair_style(idx),
                            "outfit": "lavender",
                            "accent": "floral",
                            "accessories": "glasses",
                            "accessoriesColor": "black",
                            "signature": rsvp.guest.full_name.strip() or "guest-avatar",
                        }
                    )
                rsvp.avatar_config = avatar_configs
            
            rsvp.attending = attendance
            rsvp.party_size = party_size
            rsvp.message = dietary_restrictions
            rsvp.guest_names = guest_names
            rsvp.livestream_requested = not attendance
            rsvp.save()
            
            messages.success(request, "Your RSVP has been updated!")
            if rsvp.attending:
                request.session["current_rsvp_id"] = rsvp.id
            return redirect("home")
        
        elif action == "keep":
            # Keep same RSVP, redirect based on attendance
            if rsvp.attending:
                request.session["current_rsvp_id"] = rsvp.id
                return redirect("chapel")
            else:
                return redirect("livestream")
    
    return render(request, "celebration/rsvp_existing.html", {"rsvp": rsvp})


def avatar_customization_view(request, rsvp_id):
    """Avatar customization page - builds avatars based on party size."""
    rsvp = get_object_or_404(RSVP, id=rsvp_id)

    def guest_display_name(index: int) -> str:
        raw = rsvp.guest_names if isinstance(rsvp.guest_names, list) else []
        names = [str(x).strip() for x in raw if str(x).strip()]
        if index < len(names):
            return names[index]
        if index == 0:
            return (rsvp.guest.full_name or "").strip() or "Guest 1"
        return f"Guest {index + 1}"
    
    if request.method == "POST":
        # Process avatar configurations from form
        avatar_configs = []
        for i in range(rsvp.party_size):
            accessories = request.POST.get(f"avatar_{i}_accessories", "glasses")
            if accessories not in ("none", "glasses"):
                accessories = "glasses"
            config = {
                "skin": request.POST.get(f"avatar_{i}_skin_tone", "light1"),
                "hair": request.POST.get(f"avatar_{i}_hair_color", "dark1"),
                "hairStyle": request.POST.get(f"avatar_{i}_hair_style", "shortFlat"),
                "clothesType": request.POST.get(f"avatar_{i}_clothes_type", "collarAndSweater"),
                "clothesColor": request.POST.get(f"avatar_{i}_clothes_color", "blue"),
                "facialHair": request.POST.get(f"avatar_{i}_facial_hair", "none"),
                "accessories": accessories,
                "accessoriesColor": "black",
                "signature": request.POST.get(f"avatar_{i}_signature", f"{rsvp.guest.full_name.strip()}-{i+1}" or f"guest-avatar-{i+1}"),
            }
            avatar_configs.append(config)
        
        rsvp.avatar_config = avatar_configs
        rsvp.save()
        
        if rsvp.attending:
            request.session["current_rsvp_id"] = rsvp.id
            messages.success(
                request,
                "You're on the guest list! Head to the chapel to see your seat.",
            )
            return redirect(reverse("chapel") + f"?rsvp_id={rsvp.id}")
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
                "accessories": "glasses",
                "accessoriesColor": "black",
                "signature": rsvp.guest.full_name.strip() or "guest-avatar",
            }
            rsvp.avatar_config = [default_config.copy() for _ in range(rsvp.party_size)]
    
    def default_hair_style(index: int) -> str:
        if index == 0:
            return "longButNotTooLong"  # Long 1
        if index == 1:
            return "shortWaved"  # Short 1
        return "longButNotTooLong" if (index % 2 == 0) else "curvy"

    # Ensure we have configs for all party members and set defaults for missing/empty values
    default_config = {
        "skin": "light1",  # Light skin tone
        "hair": "dark1",  # Dark brown hair
        "hairStyle": "shortFlat",
        "clothesType": "collarAndSweater",
        "clothesColor": "blue",
        "facialHair": "none",
        "accessories": "glasses",
        "accessoriesColor": "black",
    }
    
    for i in range(len(rsvp.avatar_config), rsvp.party_size):
        config = default_config.copy()
        config["hairStyle"] = default_hair_style(i)
        config["signature"] = f"{guest_display_name(i)}-{i+1}"
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
        valid_hair_styles = {
            "longButNotTooLong",
            "curvy",
            "straightAndStrand",
            "shortWaved",
            "shortFlat",
            "sides",
        }
        if ("hairStyle" not in config) or (not config["hairStyle"]) or (config["hairStyle"] not in valid_hair_styles):
            config["hairStyle"] = default_hair_style(i)
        if "clothesType" not in config or not config["clothesType"]:
            config["clothesType"] = "collarAndSweater"
        if "clothesColor" not in config or not config["clothesColor"]:
            config["clothesColor"] = "blue"
        if "facialHair" not in config or not config["facialHair"]:
            config["facialHair"] = "none"
        if "accessories" not in config or not config["accessories"]:
            config["accessories"] = "glasses"
        if "accessoriesColor" not in config or not config["accessoriesColor"]:
            config["accessoriesColor"] = "black"
        if "signature" not in config or not config["signature"]:
            config["signature"] = f"{guest_display_name(i)}-{i+1}"
        config["displayName"] = guest_display_name(i)
        rsvp.avatar_config[i] = config
    
    return render(request, "celebration/avatar_customization.html", {
        "rsvp": rsvp,
        "party_size": rsvp.party_size,
        "avatar_configs": rsvp.avatar_config,
    })


def chapel_view(request):
    """Chapel page - displays interactive 3D seating chart."""
    session_rsvp_id = request.session.get("current_rsvp_id")
    if session_rsvp_id:
        try:
            session_rsvp = RSVP.objects.get(id=session_rsvp_id)
            if session_rsvp.attending:
                cfgs = (
                    session_rsvp.avatar_config
                    if isinstance(session_rsvp.avatar_config, list)
                    else ([session_rsvp.avatar_config] if isinstance(session_rsvp.avatar_config, dict) else [])
                )
                first_cfg = cfgs[0] if cfgs and isinstance(cfgs[0], dict) else {}
                if "clothesType" not in first_cfg:
                    return redirect("avatar-customization", rsvp_id=session_rsvp.id)
        except RSVP.DoesNotExist:
            pass

    # Get current user's RSVP ID from URL parameter or use most recent
    current_rsvp_id = request.GET.get('rsvp_id')
    if not current_rsvp_id and session_rsvp_id:
        current_rsvp_id = str(session_rsvp_id)

    current_rsvp = None
    has_explicit_current = False
    if current_rsvp_id:
        try:
            current_rsvp = RSVP.objects.get(id=current_rsvp_id, attending=True)
            has_explicit_current = True
        except RSVP.DoesNotExist:
            current_rsvp = None

    # Build seating:
    # - Always show the *current party* (all avatars) together.
    # - Show everyone else capped to 1 avatar per RSVP to avoid clutter.
    base_qs = (
        RSVP.objects.filter(attending=True)
        .select_related("guest")
        .order_by("-created_at")
    )

    current_seats = []
    if current_rsvp and has_explicit_current:
        current_seats = build_seating_chart([current_rsvp])

    # Cap chapel to 30 most recent *attending RSVPs* (not seats).
    other_rsvp_limit = 30 - (1 if (current_rsvp and has_explicit_current) else 0)
    other_rsvp_limit = max(0, other_rsvp_limit)
    others_qs = base_qs
    if current_rsvp and has_explicit_current:
        others_qs = others_qs.exclude(id=current_rsvp.id)
    other_seats = build_seating_chart(
        others_qs[:other_rsvp_limit],
        max_seats_per_rsvp=1,
        start_seat_idx=len(current_seats),
    )

    seating = current_seats + other_seats

    # Count attendees
    attendee_count = len(seating)

    # If no explicit current RSVP, use the most recent attending RSVP for context.
    if not current_rsvp:
        current_rsvp = base_qs.first()
    
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
    itinerary = [
        {
            "time": "3:00 PM",
            "title": "Wedding Ceremony",
            "location": "Proclamation Presbyterian Church",
            "address_lines": ["278 S Bryn Mawr Ave", "Bryn Mawr, PA"],
        },
        {
            "time": "5:00 PM",
            "title": "Cocktail Hour",
            "location": "Kings Mills",
            "address_lines": ["6000 Pennell Rd", "Media, PA"],
        },
        {
            "time": "6-10 p.m.",
            "title": "Reception",
            "location": "Kings Mills",
            "address_lines": ["6000 Pennell Rd", "Media, PA"],
            "note": (
                "Enjoy an evening of dinner and dancing! We will be serving a buffet with entree choices "
                "of roast beef, chicken marsala, and baked ziti. Chicken fingers and "
                "fries will be available for kids 9 and under."
            ),
        },
    ]
    wedding_party = {
        "brides_side": [
            "Alison Kane (Maid of Honor)",
            "Hayley Kane",
            "Kiera Lucash",
            "Becca Capitao",
            "Stephanie Patterson",
            "Elizabeth Reth",
        ],
        "grooms_side": [
            "Michael Malkowicz (Best Man)",
            "Ryan Simms",
            "Rob Lowry",
            "Matthew Andraka",
        ],
    }
    context = {
        "date_label": "Saturday, June 13, 2026",
        "itinerary": itinerary,
        "wedding_party": wedding_party,
        "show_wedding_party": False,
    }
    return render(request, "celebration/details.html", context)


def travel_view(request):
    hotel_block = {
        "name": "Hilton hotel block",
        "booking_url": (
            "https://www.hilton.com/en/book/reservation/rooms/?ctyhocn=PHLTSGI&arrivalDate=2026-06-12"
            "&departureDate=2026-06-14&groupCode=KAN&room1NumAdults=1&cid=OM%2CWW%2CHILTONLINK%2CEN%2CDirectLink"
        ),
        "contact_phone": "5709054477",
        "contact_phone_display": "(570) 905-4477",
    }
    return render(request, "celebration/travel.html", {"hotel_block": hotel_block})


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


def rsvp_status_view(request):
    """API endpoint to check if a guest already has an RSVP."""
    guest_id = (request.GET.get("guest_id") or "").strip()
    if not guest_id.isdigit():
        return JsonResponse({"exists": False})

    guest = Guest.objects.filter(id=int(guest_id)).first()
    if not guest:
        return JsonResponse({"exists": False})

    existing_rsvp = RSVP.objects.filter(guest=guest).order_by("-created_at").first()
    if not existing_rsvp:
        return JsonResponse({"exists": False})

    return JsonResponse(
        {
            "exists": True,
            "rsvp_id": existing_rsvp.id,
            "attending": bool(existing_rsvp.attending),
            "party_size": int(existing_rsvp.party_size),
        }
    )


# --- Dashboard (custom admin panel for RSVP tracking) ---


def dashboard_login_view(request):
    """Custom login for the RSVP dashboard (uses same Django User as admin)."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("dashboard")
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get("next") or reverse("dashboard")
            return redirect(next_url)
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm(request)
    return render(request, "celebration/dashboard_login.html", {"form": form})


def dashboard_logout_view(request):
    """Log out from dashboard and redirect to main site."""
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("home")


@login_required(login_url="/dashboard/login/")
def dashboard_home_view(request):
    """Dashboard home: stats and RSVP list (staff only)."""
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view the dashboard.")
        return redirect("home")
    all_rsvps = RSVP.objects.select_related("guest")
    total = all_rsvps.count()
    attending = all_rsvps.filter(attending=True)
    attending_count = attending.count()
    not_attending_count = all_rsvps.filter(attending=False).count()
    total_guests = sum(r.party_size for r in attending)

    status_filter = (request.GET.get("status") or "all").strip()
    sort_key = (request.GET.get("sort") or "date").strip()
    sort_dir = (request.GET.get("dir") or "desc").strip()

    rsvps = all_rsvps
    if status_filter == "attending":
        rsvps = rsvps.filter(attending=True)
    elif status_filter == "not_attending":
        rsvps = rsvps.filter(attending=False)
    else:
        status_filter = "all"

    sort_map = {
        "guest": "guest__full_name",
        "status": "attending",
        "date": "created_at",
    }
    order_field = sort_map.get(sort_key, "created_at")
    if sort_key not in sort_map:
        sort_key = "date"

    if sort_dir not in {"asc", "desc"}:
        sort_dir = "desc"

    prefix = "" if sort_dir == "asc" else "-"
    rsvps = rsvps.order_by(f"{prefix}{order_field}", "-created_at")

    # Guests who are invited but have no RSVP yet
    responded_guest_ids = RSVP.objects.values_list("guest_id", flat=True)
    not_responded = (
        Guest.objects.filter(invited=True)
        .exclude(id__in=responded_guest_ids)
        .order_by("full_name")
    )
    not_responded_count = not_responded.count()
    context = {
        "rsvps": rsvps,
        "total_rsvps": total,
        "attending_count": attending_count,
        "not_attending_count": not_attending_count,
        "total_guests": total_guests,
        "not_responded": not_responded,
        "not_responded_count": not_responded_count,
        "status_filter": status_filter,
        "sort": sort_key,
        "dir": sort_dir,
    }
    return render(request, "celebration/dashboard.html", context)


@login_required(login_url="/dashboard/login/")
def dashboard_export_rsvps_csv_view(request):
    if not request.user.is_staff:
        return redirect("home")

    status_filter = (request.GET.get("status") or "all").strip()
    sort_key = (request.GET.get("sort") or "date").strip()
    sort_dir = (request.GET.get("dir") or "desc").strip()

    rsvps = RSVP.objects.select_related("guest")
    if status_filter == "attending":
        rsvps = rsvps.filter(attending=True)
    elif status_filter == "not_attending":
        rsvps = rsvps.filter(attending=False)
    else:
        status_filter = "all"

    sort_map = {
        "guest": "guest__full_name",
        "status": "attending",
        "date": "created_at",
    }
    order_field = sort_map.get(sort_key, "created_at")
    if sort_key not in sort_map:
        sort_key = "date"

    if sort_dir not in {"asc", "desc"}:
        sort_dir = "desc"
    prefix = "" if sort_dir == "asc" else "-"
    rsvps = rsvps.order_by(f"{prefix}{order_field}", "-created_at")

    def safe_cell(value: str) -> str:
        v = (value or "").strip()
        if v and v[0] in ("=", "+", "-", "@"):
            return "'" + v
        return v

    filename = f"rsvps-{timezone.localdate().isoformat()}.csv"
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(resp)
    writer.writerow(
        [
            "Invitation",
            "Who's Coming",
            "Status",
            "Party Size",
            "Dietary Restrictions / Allergies",
            "Submitted At",
        ]
    )
    for r in rsvps:
        who = ", ".join(r.guest_names or []) if r.guest_names else ""
        status = "Attending" if r.attending else "Not Attending"
        writer.writerow(
            [
                safe_cell(r.guest.full_name),
                safe_cell(who),
                status,
                r.party_size,
                safe_cell(r.message),
                timezone.localtime(r.created_at).strftime("%Y-%m-%d %H:%M"),
            ]
        )

    return resp

