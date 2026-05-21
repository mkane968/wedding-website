from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Guest


class DashboardAddGuestTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="staff",
            password="testpass123",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="guest",
            password="testpass123",
            is_staff=False,
        )

    def test_add_guest_requires_login(self):
        response = self.client.get(reverse("dashboard-add-guest"))
        self.assertRedirects(response, "/dashboard/login/?next=/dashboard/guests/add/")

    def test_add_guest_requires_staff(self):
        self.client.login(username="guest", password="testpass123")
        response = self.client.get(reverse("dashboard-add-guest"))
        self.assertRedirects(response, reverse("home"))

    def test_staff_can_add_guest(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(
            reverse("dashboard-add-guest"),
            {"full_name": "New Guest"},
        )
        self.assertRedirects(response, reverse("dashboard"))

        guest = Guest.objects.get(full_name="New Guest")
        self.assertTrue(guest.invited)
        self.assertTrue(guest.verified)
        self.assertTrue(guest.email.endswith("@invitation.local"))

    def test_duplicate_name_is_rejected(self):
        Guest.objects.create(full_name="Existing Guest", email="existing@example.com", invited=True)
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(
            reverse("dashboard-add-guest"),
            {"full_name": "Existing Guest"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A guest with this name already exists.")
        self.assertEqual(Guest.objects.filter(full_name__iexact="Existing Guest").count(), 1)


class GuestSearchTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_search_only_returns_invited_guests(self):
        Guest.objects.create(full_name="Invited Person", email="invited@example.com", invited=True)
        Guest.objects.create(full_name="Uninvited Person", email="uninvited@example.com", invited=False)

        response = self.client.get(reverse("guest-search"), {"q": "Person"})
        self.assertEqual(response.status_code, 200)
        names = [g["name"] for g in response.json()["guests"]]
        self.assertIn("Invited Person", names)
        self.assertNotIn("Uninvited Person", names)
