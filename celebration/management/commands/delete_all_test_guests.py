from django.core.management.base import BaseCommand
from django.db import models
from celebration.models import Guest, RSVP


class Command(BaseCommand):
    help = 'Delete all test/sample guests and their RSVPs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Actually delete the data (without this flag, just shows what would be deleted)',
        )

    def handle(self, *args, **options):
        # Find all test guests (those with test.local emails or placeholder emails)
        test_guests = Guest.objects.filter(
            models.Q(email__contains='@test.local') | 
            models.Q(email__contains='@uploads.local')
        )
        
        test_count = test_guests.count()
        
        if test_count == 0:
            self.stdout.write(self.style.SUCCESS('No test guests found.'))
            return
        
        self.stdout.write(f'Found {test_count} test guests to delete:')
        for guest in test_guests[:10]:
            self.stdout.write(f'  - {guest.full_name} ({guest.email})')
        if test_count > 10:
            self.stdout.write(f'  ... and {test_count - 10} more')
        
        if not options['confirm']:
            self.stdout.write(self.style.WARNING('\nThis is a dry run. Use --confirm to actually delete.'))
            return
        
        # Delete associated RSVPs first
        rsvp_count = 0
        for guest in test_guests:
            rsvps = RSVP.objects.filter(guest=guest)
            rsvp_count += rsvps.count()
            rsvps.delete()
        
        # Then delete guests
        test_guests.delete()
        
        self.stdout.write(self.style.SUCCESS(f'\nDeleted {test_count} test guests and {rsvp_count} associated RSVPs.'))
        
        # Show remaining
        remaining = Guest.objects.count()
        self.stdout.write(f'Remaining guests: {remaining}')
