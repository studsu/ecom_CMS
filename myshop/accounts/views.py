from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('confirm_password'):
            self.add_error('confirm_password', "Passwords do not match")
        phone = cleaned_data.get("phone")
        if not phone:
            self.add_error('phone', "Phone number is required")
        return cleaned_data

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('product_list')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form, 'non_field_errors': form.non_field_errors})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('product_list')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form, 'non_field_errors': form.non_field_errors})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')


from django.contrib.auth.decorators import login_required
from django.contrib import messages
from store.models import Order, BulkOrder
from django import forms
from django.shortcuts import render, redirect

class ProfileForm(forms.Form):
    shipping_address = forms.CharField(widget=forms.Textarea, label="Default Shipping Address", required=True)

@login_required
def profile_view(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    bulk_orders = BulkOrder.objects.filter(user=user).order_by('-created_at')
    form = ProfileForm(initial={'shipping_address': user.profile.shipping_address if hasattr(user, 'profile') else ''})
    return render(request, 'accounts/profile.html', {'form': form, 'orders': orders, 'bulk_orders': bulk_orders})

from .models import Profile  # make sure this is imported

@login_required
def update_profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            # ✅ Safely get or create the user's profile
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.shipping_address = form.cleaned_data['shipping_address']
            profile.save()
            messages.success(request, "Shipping address updated.")
    return redirect('profile')





from store.models import Order
from django.shortcuts import get_object_or_404

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'accounts/order_detail.html', {'order': order})
