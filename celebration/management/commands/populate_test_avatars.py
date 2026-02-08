import random
from django.core.management.base import BaseCommand
from celebration.models import Guest, RSVP

# Avatar customization options
SKIN_TONES = ["light1", "porcelain", "rosy", "sienna", "medium1", "amber", "dark1", "espresso"]
HAIR_COLORS = ["dark1", "dark2", "brown1", "brown2", "brown3", "red", "blonde1", "blonde2"]
HAIR_STYLES = ["shortWaved", "longButNotTooLong", "straightAndStrand", "sides", "shortFlat", "curvy"]
CLOTHES_TYPES = ["collarAndSweater", "blazerAndShirt", "shirtVNeck"]
CLOTHES_COLORS = ["pink", "blue", "purple", "green", "red", "black"]
FACIAL_HAIR_OPTIONS = ["none", "beard", "mustache"]
ACCESSORIES_OPTIONS = ["none", "glasses"]
EYES_OPTIONS = ["default"]
MOUTH_OPTIONS = ["smile"]

# Sample first names for variety
FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn",
    "Sam", "Dakota", "Blake", "Cameron", "Drew", "Emery", "Finley", "Hayden",
    "Jamie", "Kai", "Logan", "Noah", "Parker", "Reese", "Sage", "Tyler",
    "Emma", "Olivia", "Sophia", "Isabella", "Charlotte", "Amelia", "Mia", "Harper",
    "Evelyn", "Abigail", "Emily", "Elizabeth", "Mila", "Ella", "Avery", "Sofia",
    "Camila", "Aria", "Scarlett", "Victoria", "Madison", "Luna", "Grace", "Chloe",
    "Penelope", "Layla", "Riley", "Zoey", "Nora", "Lily", "Eleanor", "Hannah",
    "Lillian", "Addison", "Aubrey", "Ellie", "Stella", "Natalie", "Zoe", "Leah",
    "Hazel", "Violet", "Aurora", "Savannah", "Audrey", "Brooklyn", "Bella", "Claire",
    "Skylar", "Lucy", "Paisley", "Everly", "Anna", "Caroline", "Nova", "Genesis",
    "Aaliyah", "Kennedy", "Kinsley", "Allison", "Maya", "Sarah", "Madelyn", "Adeline",
    "Alexa", "Ariana", "Elena", "Gabriella", "Naomi", "Alice", "Sadie", "Hailey",
    "Eva", "Emilia", "Autumn", "Quinn", "Nevaeh", "Piper", "Ruby", "Serenity",
    "Willow", "Everleigh", "Cora", "Kaylee", "Lydia", "Peyton", "Aubree", "Arianna"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Sanchez",
    "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams",
    "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards",
    "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers",
    "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey", "Reed", "Kelly",
    "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson", "Brooks",
    "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross"
]


class Command(BaseCommand):
    help = 'Populate 150 test guests with randomized avatar configurations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=150,
            help='Number of guests to create (default: 150)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Clear existing test data (optional - comment out if you want to keep existing)
        self.stdout.write('Clearing existing guests and RSVPs...')
        RSVP.objects.all().delete()
        Guest.objects.all().delete()
        
        self.stdout.write(f'Creating {count} guests with randomized avatars...')
        
        created_count = 0
        for i in range(count):
            # Generate random name
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            full_name = f"{first_name} {last_name}"
            
            # Create guest
            guest = Guest.objects.create(
                full_name=full_name,
                email=f"{first_name.lower()}.{last_name.lower()}{i}@test.local",
                invited=True,
                verified=True,
            )
            
            # Generate random avatar config
            avatar_config = [{
                "skin": random.choice(SKIN_TONES),
                "hair": random.choice(HAIR_COLORS),
                "hairStyle": random.choice(HAIR_STYLES),
                "clothesType": random.choice(CLOTHES_TYPES),
                "clothesColor": random.choice(CLOTHES_COLORS),
                "facialHair": random.choice(FACIAL_HAIR_OPTIONS),
                "accessories": random.choice(ACCESSORIES_OPTIONS),
                "eyes": random.choice(EYES_OPTIONS),
                "mouth": random.choice(MOUTH_OPTIONS),
                "signature": f"{full_name}-1",
            }]
            
            # Create RSVP (all attending)
            RSVP.objects.create(
                guest=guest,
                attending=True,
                party_size=1,
                email=guest.email,
                avatar_config=avatar_config,
            )
            
            created_count += 1
            if created_count % 25 == 0:
                self.stdout.write(f'Created {created_count} guests...')
        
        # Calculate rows needed
        seats_per_row = 6
        total_seats = RSVP.objects.filter(attending=True).count()
        rows_needed = (total_seats + seats_per_row - 1) // seats_per_row
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} guests with RSVPs!\n'
                f'Total seats: {total_seats}\n'
                f'Rows needed: {rows_needed} (at {seats_per_row} seats per row)'
            )
        )
