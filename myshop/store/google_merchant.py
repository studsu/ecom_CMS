"""
Google Merchant Center Feed Generator
Generates XML feeds compatible with Google Shopping requirements
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from .models import Product, Category
import xml.etree.ElementTree as ET
from decimal import Decimal


class GoogleMerchantFeed:
    """
    Generate Google Shopping XML feed for products
    """
    
    def __init__(self):
        self.namespace = {
            '': 'http://www.w3.org/2005/Atom',
            'g': 'http://base.google.com/ns/1.0'
        }
        
    def generate_feed(self, base_url=None):
        """
        Generate complete Google Shopping feed
        """
        if not base_url:
            base_url = getattr(settings, 'SITE_URL', 'https://smokeking.in')
            
        # Create root element
        feed = Element('feed')
        feed.set('xmlns', 'http://www.w3.org/2005/Atom')
        feed.set('xmlns:g', 'http://base.google.com/ns/1.0')
        
        # Feed metadata
        self._add_feed_metadata(feed, base_url)
        
        # Add products
        products = Product.objects.filter(is_active=True).select_related('category')
        
        for product in products:
            self._add_product_entry(feed, product, base_url)
            
        return self._prettify_xml(feed)
    
    def _add_feed_metadata(self, feed, base_url):
        """Add feed metadata elements"""
        
        gmc_settings = getattr(settings, 'GOOGLE_MERCHANT_CENTER', {})
        
        # Title
        title = SubElement(feed, 'title')
        title.text = gmc_settings.get('FEED_TITLE', getattr(settings, 'SITE_NAME', 'SmokeKing') + ' - Product Feed')
        
        # Link
        link = SubElement(feed, 'link')
        link.set('rel', 'self')
        link.set('href', f"{base_url}/google-merchant-feed.xml")
        
        # ID
        id_elem = SubElement(feed, 'id')
        id_elem.text = base_url
        
        # Updated
        updated = SubElement(feed, 'updated')
        updated.text = timezone.now().isoformat()
        
        # Author
        author = SubElement(feed, 'author')
        name = SubElement(author, 'name')
        name.text = getattr(settings, 'SITE_NAME', 'SmokeKing')
    
    def _add_product_entry(self, feed, product, base_url):
        """Add individual product entry to feed"""
        
        entry = SubElement(feed, 'entry')
        
        # Basic entry info - shortened entry ID
        id_elem = SubElement(entry, 'id')
        id_elem.text = f"{base_url}/p/{product.id}"
        
        title = SubElement(entry, 'title')
        title.text = product.name
        
        description = SubElement(entry, 'description')
        description.text = product.short_description or product.description[:160]
        
        link = SubElement(entry, 'link')
        link.set('href', f"{base_url}{product.get_absolute_url()}")
        
        # Google Shopping specific fields
        self._add_google_fields(entry, product, base_url)
    
    def _add_google_fields(self, entry, product, base_url):
        """Add Google Shopping specific fields"""
        
        gmc_settings = getattr(settings, 'GOOGLE_MERCHANT_CENTER', {})
        
        # Required fields
        
        # ID - Keep it short for Google
        g_id = SubElement(entry, '{http://base.google.com/ns/1.0}id')
        g_id.text = f"P{product.id}"
        
        # Title (duplicate for Google)
        g_title = SubElement(entry, '{http://base.google.com/ns/1.0}title')
        title_max_length = gmc_settings.get('TITLE_MAX_LENGTH', 150)
        g_title.text = product.name[:title_max_length]
        
        # Description
        g_description = SubElement(entry, '{http://base.google.com/ns/1.0}description')
        description_text = product.short_description or product.description
        # Strip HTML tags and limit to configured chars
        import re
        clean_desc = re.sub('<[^<]+?>', '', description_text)
        desc_max_length = gmc_settings.get('DESCRIPTION_MAX_LENGTH', 5000)
        g_description.text = clean_desc[:desc_max_length]
        
        # Link
        g_link = SubElement(entry, '{http://base.google.com/ns/1.0}link')
        g_link.text = f"{base_url}{product.get_absolute_url()}"
        
        # Image link
        if product.image or product.images.first():
            g_image_link = SubElement(entry, '{http://base.google.com/ns/1.0}image_link')
            if product.images.first():
                g_image_link.text = f"{base_url}{product.images.first().image.url}"
            else:
                g_image_link.text = f"{base_url}{product.image.url}"
        
        # Availability
        g_availability = SubElement(entry, '{http://base.google.com/ns/1.0}availability')
        availability = 'in stock' if product.stock > 0 else 'out of stock'
        g_availability.text = gmc_settings.get('DEFAULT_AVAILABILITY', availability)
        
        # Price
        g_price = SubElement(entry, '{http://base.google.com/ns/1.0}price')
        currency = gmc_settings.get('CURRENCY', 'INR')
        g_price.text = f"{product.price} {currency}"
        
        # Condition
        g_condition = SubElement(entry, '{http://base.google.com/ns/1.0}condition')
        g_condition.text = gmc_settings.get('DEFAULT_CONDITION', 'new')
        
        # Brand
        g_brand = SubElement(entry, '{http://base.google.com/ns/1.0}brand')
        g_brand.text = gmc_settings.get('DEFAULT_BRAND', getattr(settings, 'SITE_NAME', 'SmokeKing'))
        
        # Explicitly state no GTIN/UPC/EAN exists for this product
        g_identifier_exists = SubElement(entry, '{http://base.google.com/ns/1.0}identifier_exists')
        g_identifier_exists.text = 'no'  # Explicitly state we don't have GTINs
        
        # Since no GTIN, provide MPN as unique identifier
        g_mpn = SubElement(entry, '{http://base.google.com/ns/1.0}mpn')
        g_mpn.text = f"SK{product.id}"
        
        # Add custom label to clarify no official product codes
        g_custom_label = SubElement(entry, '{http://base.google.com/ns/1.0}custom_label_0')
        g_custom_label.text = 'No_GTIN_UPC_EAN'
        
        # Google product category
        g_product_type = SubElement(entry, '{http://base.google.com/ns/1.0}product_type')
        g_product_type.text = product.category.name
        
        # Google category (you might want to map your categories to Google's taxonomy)
        g_google_category = SubElement(entry, '{http://base.google.com/ns/1.0}google_product_category')
        category_mapping = gmc_settings.get('CATEGORY_MAPPING', self._get_google_category_mapping())
        g_google_category.text = category_mapping.get(product.category.name.lower(), 'Home & Garden > Smoking Accessories')
        
        # Additional optional fields
        
        # Additional images
        max_additional_images = gmc_settings.get('MAX_ADDITIONAL_IMAGES', 10)
        for idx, img in enumerate(product.images.all()[1:max_additional_images+1]):
            additional_image = SubElement(entry, '{http://base.google.com/ns/1.0}additional_image_link')
            additional_image.text = f"{base_url}{img.image.url}"
        
        # Shipping
        g_shipping = SubElement(entry, '{http://base.google.com/ns/1.0}shipping')
        g_shipping_country = SubElement(g_shipping, '{http://base.google.com/ns/1.0}country')
        g_shipping_country.text = gmc_settings.get('SHIPPING_COUNTRY', 'IN')
        g_shipping_service = SubElement(g_shipping, '{http://base.google.com/ns/1.0}service')
        g_shipping_service.text = gmc_settings.get('SHIPPING_SERVICE', 'Standard')
        g_shipping_price = SubElement(g_shipping, '{http://base.google.com/ns/1.0}price')
        g_shipping_price.text = gmc_settings.get('SHIPPING_PRICE', '0 INR')
        
        # Age group
        g_age_group = SubElement(entry, '{http://base.google.com/ns/1.0}age_group')
        g_age_group.text = gmc_settings.get('AGE_GROUP', 'adult')
        
        # Gender
        g_gender = SubElement(entry, '{http://base.google.com/ns/1.0}gender')
        g_gender.text = gmc_settings.get('GENDER', 'unisex')
        
    def _get_google_category_mapping(self):
        """
        Map your product categories to Google's product taxonomy
        Update this mapping based on your actual categories
        """
        return {
            'lighters': 'Home & Garden > Smoking Accessories > Lighters',
            'ashtrays': 'Home & Garden > Smoking Accessories > Ashtrays',
            'cigar accessories': 'Home & Garden > Smoking Accessories > Cigar Accessories',
            'pipes': 'Home & Garden > Smoking Accessories > Pipes',
            'rolling papers': 'Home & Garden > Smoking Accessories > Rolling Papers',
            'vaporizers': 'Electronics > Electronics Accessories > Electronic Cigarettes & Vaporizers',
            'grinders': 'Home & Garden > Smoking Accessories',
            'storage': 'Home & Garden > Household Supply Storage',
        }
    
    def _prettify_xml(self, elem):
        """Return a pretty-printed XML string for the Element."""
        rough_string = tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='UTF-8').decode('utf-8')
    
    def generate_feed_file(self, file_path, base_url=None):
        """Generate feed and save to file"""
        feed_content = self.generate_feed(base_url)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(feed_content)
            
        return file_path
    
    def validate_feed(self):
        """Basic feed validation"""
        try:
            feed_content = self.generate_feed()
            ET.fromstring(feed_content)
            return True, "Feed is valid XML"
        except ET.ParseError as e:
            return False, f"XML Parse Error: {str(e)}"
        except Exception as e:
            return False, f"Feed generation error: {str(e)}"


def generate_google_merchant_feed(base_url=None):
    """
    Convenience function to generate Google Merchant Center feed
    """
    generator = GoogleMerchantFeed()
    return generator.generate_feed(base_url)


def validate_google_merchant_feed():
    """
    Convenience function to validate the feed
    """
    generator = GoogleMerchantFeed()
    return generator.validate_feed()


# ─────────────────────────────
# 🌐 DJANGO VIEWS
# ─────────────────────────────

from django.http import HttpResponse
from django.utils import timezone

def google_merchant_feed_view(request):
    """
    Django view to generate and serve Google Merchant Center XML feed
    """
    try:
        # Get the base URL from the request
        base_url = f"{request.scheme}://{request.get_host()}"
        
        # Generate the feed
        feed_content = generate_google_merchant_feed(base_url)
        
        # Return as XML response
        response = HttpResponse(feed_content, content_type='application/xml; charset=utf-8')
        response['Content-Disposition'] = 'inline; filename="google-merchant-feed.xml"'
        
        return response
        
    except Exception as e:
        # Return error in XML format
        error_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<error>
    <message>Error generating feed: {str(e)}</message>
    <timestamp>{timezone.now().isoformat()}</timestamp>
</error>'''
        return HttpResponse(error_xml, content_type='application/xml; charset=utf-8', status=500)