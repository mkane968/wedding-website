from django.core.management.base import BaseCommand
from celebration.models import Guest, RSVP


class Command(BaseCommand):
    help = 'Check and remove sample/test guests, keeping only verified invited guests'

    def handle(self, *args, **options):
        # Show current state
        total_guests = Guest.objects.count()
        total_rsvps = RSVP.objects.count()
        verified_guests = Guest.objects.filter(verified=True).count()
        invited_guests = Guest.objects.filter(invited=True).count()
        
        self.stdout.write(f'Current state:')
        self.stdout.write(f'  Total Guests: {total_guests}')
        self.stdout.write(f'  Total RSVPs: {total_rsvps}')
        self.stdout.write(f'  Verified Guests: {verified_guests}')
        self.stdout.write(f'  Invited Guests: {invited_guests}')
        
        # Show sample of guests
        self.stdout.write(f'\nSample guests:')
        for guest in Guest.objects.all()[:20]:
            self.stdout.write(f'  - {guest.full_name} (verified: {guest.verified}, invited: {guest.invited}, email: {guest.email})')
        
        # Delete unverified guests (these are likely test/sample data)
        unverified_guests = Guest.objects.filter(verified=False)
        unverified_count = unverified_guests.count()
        
        if unverified_count > 0:
            self.stdout.write(f'\nFound {unverified_count} unverified guests (likely test data)')
            # Delete associated RSVPs first
            for guest in unverified_guests:
                RSVP.objects.filter(guest=guest).delete()
            # Then delete guests
            unverified_guests.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {unverified_count} unverified guests and their RSVPs'))
        
        # Also delete guests with placeholder emails (likely test data)
        placeholder_guests = Guest.objects.filter(email__contains='@uploads.local')
        placeholder_count = placeholder_guests.count()
        
        if placeholder_count > 0:
            self.stdout.write(f'\nFound {placeholder_count} guests with placeholder emails')
            # Delete associated RSVPs first
            for guest in placeholder_guests:
                RSVP.objects.filter(guest=guest).delete()
            # Then delete guests
            placeholder_guests.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {placeholder_count} guests with placeholder emails and their RSVPs'))
        
        # Final state
        remaining_guests = Guest.objects.count()
        remaining_rsvps = RSVP.objects.count()
        
        self.stdout.write(f'\nFinal state:')
        self.stdout.write(f'  Remaining Guests: {remaining_guests}')
        self.stdout.write(f'  Remaining RSVPs: {remaining_rsvps}')
        
        if remaining_guests > 0:
            self.stdout.write(f'\nRemaining guests:')
            for guest in Guest.objects.all()[:20]:
                self.stdout.write(f'  - {guest.full_name} (verified: {guest.verified}, invited: {guest.invited})')
