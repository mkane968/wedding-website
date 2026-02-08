"""
Management command to import guests from a CSV file.

CSV format options:

Option 1 - Simple single column:
- Guest Name (required) - Name as it appears on the invitation

Option 2 - Full format with columns (in any order):
- full_name (required)
- email (optional - will generate placeholder if not provided)
- household_name (optional)
- side (optional: bride, groom, or family)
- relationship (optional)
- invited (optional: true/false, defaults to true)
- verified (optional: true/false, defaults to true)
- notes (optional)

Example CSV (simple):
Guest Name
Mr. and Mrs. John Doe
Ms. Jane Smith

Example CSV (full):
full_name,email,household_name,side,relationship,invited,verified,notes
John Doe,john@example.com,The Doe Family,bride,Cousin,true,true,
"""
import csv
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from celebration.models import Guest


class Command(BaseCommand):
    help = "Import guests from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the CSV file to import",
        )
        parser.add_argument(
            "--skip-duplicates",
            action="store_true",
            help="Skip rows that would create duplicate guests (same name and email)",
        )

    def handle(self, *args, **options):
        csv_file_path = options["csv_file"]
        skip_duplicates = options["skip_duplicates"]

        # Resolve the path - try relative to project root, then absolute
        if not os.path.isabs(csv_file_path):
            project_root = Path(__file__).parent.parent.parent.parent
            csv_file_path = project_root / csv_file_path

        if not os.path.exists(csv_file_path):
            raise CommandError(f'CSV file not found: "{csv_file_path}"')

        self.stdout.write(f'Importing guests from "{csv_file_path}"...')

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        try:
            with open(csv_file_path, "r", encoding="utf-8-sig") as f:  # utf-8-sig handles BOM
                reader = csv.DictReader(f)
                
                # Normalize fieldnames to handle case and whitespace
                normalized_fields = {f.strip().lower(): f for f in reader.fieldnames}
                
                # Check if this is a simple single-column format
                is_simple_format = "guest name" in normalized_fields
                
                if is_simple_format:
                    # Simple format - just guest names
                    guest_name_key = normalized_fields["guest name"]
                else:
                    # Full format - validate required columns (case-insensitive)
                    normalized_field_lower = set(normalized_fields.keys())
                    if "full_name" not in normalized_field_lower and "full name" not in normalized_field_lower:
                        raise CommandError(
                            f'CSV file is missing required column. Expected either "Guest Name" or "full_name". '
                            f'Found columns: {", ".join(reader.fieldnames)}'
                        )

                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                        try:
                            if is_simple_format:
                                # Simple format - extract name and generate email
                                full_name = row.get(guest_name_key, "").strip()
                                
                                if not full_name:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"Row {row_num}: Skipping - empty guest name"
                                        )
                                    )
                                    skipped_count += 1
                                    continue
                                
                                # Generate placeholder email
                                email_slug = slugify(full_name) or f"guest-{Guest.objects.count() + 1}"
                                email = f"{email_slug}@invitation.local"
                                
                                # Set defaults for simple format
                                household_name = None
                                side = ""
                                relationship = ""
                                notes = ""
                                invited = True
                                verified = True
                                
                                # Try to extract household name from patterns like "The X Family"
                                if full_name.startswith("The ") and "Family" in full_name:
                                    household_name = full_name
                            else:
                                # Full format - get all fields
                                full_name = row.get("full_name", "").strip()
                                
                                if not full_name:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"Row {row_num}: Skipping - missing full_name"
                                        )
                                    )
                                    skipped_count += 1
                                    continue
                                
                                # Get email or generate placeholder
                                email = row.get("email", "").strip().lower()
                                if not email:
                                    email_slug = slugify(full_name) or f"guest-{Guest.objects.count() + 1}"
                                    email = f"{email_slug}@invitation.local"

                                # Get optional fields
                                household_name = row.get("household_name", "").strip() or None
                                side = row.get("side", "").strip() or ""
                                relationship = row.get("relationship", "").strip() or ""
                                notes = row.get("notes", "").strip() or ""

                                # Parse boolean fields
                                invited = self._parse_bool(row.get("invited", "true"), default=True)
                                verified = self._parse_bool(row.get("verified", "true"), default=True)

                            # Validate side if provided
                            if side and side not in [choice[0] for choice in Guest.SIDES]:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'Row {row_num}: Invalid side "{side}", using empty string'
                                    )
                                )
                                side = ""

                            # For simple format, check if guest with this exact name already exists
                            # For full format, use name+email as unique constraint
                            if is_simple_format:
                                # Check by name only for simple format
                                guest = Guest.objects.filter(full_name=full_name).first()
                                if guest:
                                    if skip_duplicates:
                                        skipped_count += 1
                                        continue
                                    # Update existing
                                    guest.email = email  # Update email in case it changed
                                    guest.invited = invited
                                    guest.verified = verified
                                    if household_name:
                                        guest.household_name = household_name
                                    guest.save()
                                    updated_count += 1
                                else:
                                    # Create new
                                    guest = Guest.objects.create(
                                        full_name=full_name,
                                        email=email,
                                        household_name=household_name or "",
                                        side=side,
                                        relationship=relationship,
                                        invited=invited,
                                        verified=verified,
                                        notes=notes,
                                    )
                                    created_count += 1
                            else:
                                # Full format - use get_or_create with name+email
                                guest, created = Guest.objects.get_or_create(
                                    full_name=full_name,
                                    email=email,
                                    defaults={
                                        "household_name": household_name or "",
                                        "side": side,
                                        "relationship": relationship,
                                        "invited": invited,
                                        "verified": verified,
                                        "notes": notes,
                                    },
                                )

                                if created:
                                    created_count += 1
                                else:
                                    if skip_duplicates:
                                        skipped_count += 1
                                        continue
                                    # Update existing guest
                                    guest.household_name = household_name or guest.household_name or ""
                                    if side:
                                        guest.side = side
                                    if relationship:
                                        guest.relationship = relationship
                                    guest.invited = invited
                                    guest.verified = verified
                                    if notes:
                                        guest.notes = notes
                                    guest.save()
                                    updated_count += 1

                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"Row {row_num}: Error - {str(e)}")
                            )
                            error_count += 1

        except Exception as e:
            raise CommandError(f"Error reading CSV file: {str(e)}")

        # Summary
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("Import Summary:"))
        self.stdout.write(self.style.SUCCESS(f"  Created: {created_count}"))
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"  Skipped: {skipped_count}"))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"  Errors: {error_count}"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

    def _parse_bool(self, value, default=False):
        """Parse a string value to boolean."""
        if isinstance(value, bool):
            return value
        value = str(value).strip().lower()
        if value in ("true", "1", "yes", "y"):
            return True
        elif value in ("false", "0", "no", "n", ""):
            return False
        return default
