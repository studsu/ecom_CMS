from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404, redirect
from django.forms import ModelForm
from django.forms.widgets import DateInput
from .models import User, UserProfile, UserAddress

class UserLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy("home")

class UserLogoutView(LogoutView):
    template_name = "users/logout.html"
    next_page = reverse_lazy("home")
    http_method_names = ['get', 'post', 'options']
    
    def get(self, request, *args, **kwargs):
        """Show logout confirmation page on GET request"""
        return self.render_to_response(self.get_context_data())

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email')

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "users/signup.html"
    success_url = reverse_lazy("home")
    
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Welcome! Your account has been created successfully.")
        return response

class UserProfileForm(ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'date_of_birth']
        widgets = {
            'date_of_birth': DateInput(attrs={'type': 'date'}),
        }

class UserAddressForm(ModelForm):
    class Meta:
        model = UserAddress
        fields = ['type', 'name', 'street', 'city', 'state', 'postal_code', 'country', 'is_default']

@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = "users/profile.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        context['profile'] = profile
        context['addresses'] = user.addresses.all()
        context['profile_form'] = UserProfileForm(instance=profile)
        context['address_form'] = UserAddressForm()
        return context
    
    def post(self, request, *args, **kwargs):
        user = request.user
        action = request.POST.get('action')
        
        if action == 'update_profile':
            profile, created = UserProfile.objects.get_or_create(user=user)
            form = UserProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
            else:
                messages.error(request, "Please correct the errors below.")
        
        elif action == 'add_address':
            form = UserAddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.user = user
                address.save()
                messages.success(request, "Address added successfully!")
            else:
                messages.error(request, "Please correct the errors in the address form.")
        
        elif action == 'delete_address':
            address_id = request.POST.get('address_id')
            try:
                address = UserAddress.objects.get(id=address_id, user=user)
                address.delete()
                messages.success(request, "Address deleted successfully!")
            except UserAddress.DoesNotExist:
                messages.error(request, "Address not found.")
        
        return redirect('profile')
