from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("rsvp/", views.rsvp_view, name="rsvp"),
    path("rsvp/<int:rsvp_id>/avatars/", views.avatar_customization_view, name="avatar-customization"),
    path("chapel/", views.chapel_view, name="chapel"),
    path("livestream/", views.livestream_view, name="livestream"),
    path("registry/", views.registry_view, name="registry"),
    path("details/", views.details_view, name="details"),
    path("travel/", views.travel_view, name="travel"),
    path("wedding-party/", views.wedding_party_view, name="wedding-party"),
    path("photos/upload/", views.photo_upload_view, name="photo-upload"),
    path("photos/gallery/", views.gallery_view, name="photo-gallery"),
]
