from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.models import ProductImage
import os
import shutil


class Command(BaseCommand):
    help = 'Move existing gallery images from gallery subfolder to main product folder'

    def handle(self, *args, **options):
        moved_count = 0
        error_count = 0

        self.stdout.write('Starting gallery image path migration...')

        for product_image in ProductImage.objects.all():
            if product_image.image and 'gallery/' in product_image.image.name:
                try:
                    old_path = product_image.image.path
                    old_name = product_image.image.name

                    # Generate new path without gallery subfolder
                    filename = os.path.basename(old_name)
                    new_name = old_name.replace('/gallery/', '/')
                    new_path = os.path.join(settings.MEDIA_ROOT, new_name)

                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)

                    # Move the file if it exists
                    if os.path.exists(old_path):
                        shutil.move(old_path, new_path)

                        # Update the image field
                        product_image.image.name = new_name
                        product_image.save(update_fields=['image'])

                        moved_count += 1
                        self.stdout.write(f'Moved: {old_name} -> {new_name}')
                    else:
                        self.stdout.write(f'Warning: File not found: {old_path}')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(f'Error moving {product_image.image.name}: {e}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Gallery path migration complete! '
                f'Moved: {moved_count} images, Errors: {error_count}'
            )
        )

        # Try to remove empty gallery directories
        try:
            for root, dirs, files in os.walk(os.path.join(settings.MEDIA_ROOT, 'products', 'images')):
                if root.endswith('/gallery') and not files:
                    os.rmdir(root)
                    self.stdout.write(f'Removed empty directory: {root}')
        except Exception as e:
            self.stdout.write(f'Note: Could not remove empty directories: {e}')