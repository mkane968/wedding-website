from django.contrib import admin

from .models import Guest, PhotoSubmission, RSVP


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "household_name", "side", "invited", "verified")
    search_fields = ("full_name", "email", "household_name")
    list_filter = ("side", "invited", "verified")


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ("guest", "attending", "party_size", "meal_preference", "created_at")
    list_filter = ("attending", "meal_preference", "livestream_requested")
    search_fields = ("guest__full_name", "guest__email")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PhotoSubmission)
class PhotoSubmissionAdmin(admin.ModelAdmin):
    list_display = ("display_name", "approved", "created_at")
    list_filter = ("approved",)
    search_fields = ("display_name", "email")
