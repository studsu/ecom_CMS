from django import forms
from .models import Order


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'email', 'phone', 'shipping_name', 'shipping_address_line_1',
            'shipping_address_line_2', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country', 'payment_method', 'notes'
        ]
        
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number',
                'required': True
            }),
            'shipping_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name for delivery',
                'required': True
            }),
            'shipping_address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'House/Building Number, Street Name',
                'required': True
            }),
            'shipping_address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment, Landmark (Optional)',
            }),
            'shipping_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
                'required': True
            }),
            'shipping_state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province',
                'required': True
            }),
            'shipping_postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal/ZIP Code',
                'required': True
            }),
            'shipping_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Special delivery instructions (optional)',
                'rows': 3
            }),
        }
        
        labels = {
            'email': 'Email Address',
            'phone': 'Phone Number',
            'shipping_name': 'Full Name',
            'shipping_address_line_1': 'Address Line 1',
            'shipping_address_line_2': 'Address Line 2',
            'shipping_city': 'City',
            'shipping_state': 'State/Province',
            'shipping_postal_code': 'Postal Code',
            'shipping_country': 'Country',
            'payment_method': 'Payment Method',
            'notes': 'Special Instructions',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make certain fields required
        self.fields['email'].required = True
        self.fields['phone'].required = True
        self.fields['shipping_name'].required = True
        self.fields['shipping_address_line_1'].required = True
        self.fields['shipping_city'].required = True
        self.fields['shipping_state'].required = True
        self.fields['shipping_postal_code'].required = True