from decimal import Decimal
from django.conf import settings
from .models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False, variant=None):
        """
        Add a product to the cart or update its quantity.
        """
        # Create unique cart key including variant if specified
        if variant:
            cart_key = f"{product.id}_{variant.id}"
            price = str(variant.final_price)
        else:
            cart_key = str(product.id)
            price = str(product.get_price)

        if cart_key not in self.cart:
            self.cart[cart_key] = {
                'product_id': product.id,
                'variant_id': variant.id if variant else None,
                'quantity': 0,
                'price': price
            }
        if override_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity

        self.save()

    def save(self):
        """Mark the session as "modified" to make sure it gets saved."""
        self.session.modified = True

    def remove(self, product, variant=None):
        """
        Remove a product from the cart.
        """
        if variant:
            cart_key = f"{product.id}_{variant.id}"
        else:
            cart_key = str(product.id)

        if cart_key in self.cart:
            del self.cart[cart_key]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products
        from the database.
        """
        from .models import ProductVariant

        # Get unique product IDs from cart items
        product_ids = set()
        variant_ids = set()

        for item in self.cart.values():
            if isinstance(item, dict) and 'product_id' in item:
                product_ids.add(item['product_id'])
                if item.get('variant_id'):
                    variant_ids.add(item['variant_id'])
            else:
                # Handle legacy cart format (product_id as key)
                try:
                    product_ids.add(int(item) if isinstance(item, str) else item)
                except:
                    continue

        # Get product and variant objects
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        variants = {v.id: v for v in ProductVariant.objects.filter(id__in=variant_ids)} if variant_ids else {}

        cart = self.cart.copy()
        for key, item in cart.items():
            if isinstance(item, dict) and 'product_id' in item:
                # New format with variant support
                product_id = item['product_id']
                variant_id = item.get('variant_id')

                if product_id in products:
                    item['product'] = products[product_id]
                    if variant_id and variant_id in variants:
                        item['variant'] = variants[variant_id]
                    else:
                        item['variant'] = None

                    item['price'] = Decimal(item['price'])
                    item['total_price'] = item['price'] * item['quantity']
                    yield item
            else:
                # Handle legacy format for backward compatibility
                try:
                    product_id = int(key)
                    if product_id in products:
                        legacy_item = {
                            'product_id': product_id,
                            'variant_id': None,
                            'product': products[product_id],
                            'variant': None,
                            'quantity': item.get('quantity', 1) if isinstance(item, dict) else 1,
                            'price': Decimal(item.get('price', products[product_id].get_price) if isinstance(item, dict) else products[product_id].get_price),
                        }
                        legacy_item['total_price'] = legacy_item['price'] * legacy_item['quantity']
                        yield legacy_item
                except:
                    continue

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Calculate the total cost of the items in the cart.
        """
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        """
        Remove cart from session.
        """
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_item_count(self):
        """
        Get total number of unique items in cart.
        """
        return len(self.cart)

    def update_quantity(self, product, quantity, variant=None):
        """
        Update the quantity of a product in the cart.
        """
        if variant:
            cart_key = f"{product.id}_{variant.id}"
        else:
            cart_key = str(product.id)

        if cart_key in self.cart:
            if quantity <= 0:
                self.remove(product, variant)
            else:
                self.cart[cart_key]['quantity'] = quantity
                self.save()

    def get_available_stock(self, product, variant=None):
        """
        Get available stock for a product/variant combination.
        """
        if variant:
            return variant.stock_quantity
        elif product.manage_stock:
            return product.stock_quantity
        else:
            return float('inf')  # Unlimited stock

    def validate_quantity(self, product, quantity, variant=None):
        """
        Validate if requested quantity is available in stock.
        Returns (is_valid, available_stock, error_message)
        """
        available_stock = self.get_available_stock(product, variant)

        if available_stock == float('inf'):
            return True, available_stock, None

        # Check current cart quantity for this product/variant
        current_cart_quantity = self.get_cart_quantity(product, variant)

        if quantity > available_stock:
            return False, available_stock, f"Only {available_stock} items available"

        if current_cart_quantity + quantity > available_stock:
            remaining = available_stock - current_cart_quantity
            return False, remaining, f"Only {remaining} more items can be added (already have {current_cart_quantity} in cart)"

        return True, available_stock, None

    def get_cart_quantity(self, product, variant=None):
        """
        Get current quantity of a product/variant in the cart.
        """
        if variant:
            cart_key = f"{product.id}_{variant.id}"
        else:
            cart_key = str(product.id)

        if cart_key in self.cart:
            return self.cart[cart_key].get('quantity', 0)
        return 0