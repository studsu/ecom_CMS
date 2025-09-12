"""
Django management command to generate Google Merchant Center feed
Usage: python manage.py generate_google_feed
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from store.google_merchant import GoogleMerchantFeed
import os


class Command(BaseCommand):
    help = 'Generate Google Merchant Center XML feed'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: static/google-merchant-feed.xml)',
        )
        parser.add_argument(
            '--base-url',
            type=str,
            help='Base URL for the site (default: from settings or https://smokeking.in)',
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate the feed without generating file',
        )
        parser.add_argument(
            '--quiet',
            action='store_true',
            help='Run silently',
        )
    
    def handle(self, *args, **options):
        try:
            generator = GoogleMerchantFeed()
            
            # Validate only mode
            if options['validate_only']:
                is_valid, message = generator.validate_feed()
                if is_valid:
                    if not options['quiet']:
                        self.stdout.write(
                            self.style.SUCCESS(f'Feed validation passed: {message}')
                        )
                else:
                    raise CommandError(f'Feed validation failed: {message}')
                return
            
            # Set base URL
            base_url = options['base_url'] or getattr(settings, 'SITE_URL', 'https://smokeking.in')
            
            # Set output path
            if options['output']:
                output_path = options['output']
            else:
                static_dir = os.path.join(settings.BASE_DIR, 'static')
                os.makedirs(static_dir, exist_ok=True)
                output_path = os.path.join(static_dir, 'google-merchant-feed.xml')
            
            # Generate feed
            if not options['quiet']:
                self.stdout.write('Generating Google Merchant Center feed...')
            
            feed_path = generator.generate_feed_file(output_path, base_url)
            
            # Validate the generated feed
            is_valid, message = generator.validate_feed()
            if not is_valid:
                raise CommandError(f'Generated feed is invalid: {message}')
            
            if not options['quiet']:
                self.stdout.write(
                    self.style.SUCCESS(f'Google Merchant feed generated successfully!')
                )
                self.stdout.write(f'File: {feed_path}')
                self.stdout.write(f'URL: {base_url}/google-merchant-feed.xml')
                
                # Show stats
                from store.models import Product
                active_products = Product.objects.filter(is_active=True).count()
                self.stdout.write(f'Products included: {active_products}')
        
        except Exception as e:
            raise CommandError(f'Error generating feed: {str(e)}')