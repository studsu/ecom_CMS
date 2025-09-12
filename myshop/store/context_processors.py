from .models import Category

def categories_processor(request):
    return {
        'categories': Category.objects.all()
    }


from .models import Cart

def cart_info(request):
    cart_item_count = 0
    cart = None
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            pass
    else:
        session_id = request.session.session_key
        if session_id:
            try:
                cart = Cart.objects.get(session_id=session_id)
            except Cart.DoesNotExist:
                pass

    if cart:
        cart_item_count = cart.items.count()

    return {'cart_item_count': cart_item_count}



from .constants import SITE_NAME
from .models import SiteSettings

def site_name(request):
    return {
        'SITE_NAME': SITE_NAME
    }

def site_settings(request):
    try:
        settings = SiteSettings.objects.get(pk=1)
    except SiteSettings.DoesNotExist:
        settings = None
    return {'SITE_SETTINGS': settings}