from django import forms

class ProductCSVImportForm(forms.Form):
    csv_file = forms.FileField()


from django import forms
from .models import ContactMessage, Review

class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'subject': forms.TextInput(attrs={'class': 'form-input'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
        }

class GuestCheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))
    phone_number = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))
    address_line_1 = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))
    city = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))
    state = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))
    postal_code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded px-3 py-2'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields.pop('email')
            self.fields['full_name'].initial = user.get_full_name()
            self.fields['phone_number'].initial = getattr(user, 'phone', '')


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'title', 'review']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select border border-gray-300 rounded px-3 py-2',
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2',
                'placeholder': 'Brief summary of your review',
                'maxlength': '200'
            }),
            'review': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded px-3 py-2',
                'rows': 5,
                'placeholder': 'Tell others about your experience with this product',
                'maxlength': '2000'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].label = 'Your Rating'
        self.fields['title'].label = 'Review Title'
        self.fields['review'].label = 'Your Review'
        self.fields['review'].required = True
        
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating not in [1, 2, 3, 4, 5]:
            raise forms.ValidationError("Rating must be between 1 and 5 stars.")
        return rating
        
    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        if len(title) > 200:
            raise forms.ValidationError("Title cannot exceed 200 characters.")
        # Basic sanitization - remove potentially harmful characters
        if any(char in title for char in ['<', '>', '"', "'"]):
            raise forms.ValidationError("Title contains invalid characters.")
        return title.strip()
        
    def clean_review(self):
        review = self.cleaned_data.get('review')
        if not review or len(review.strip()) < 10:
            raise forms.ValidationError("Review must be at least 10 characters long.")
        if len(review) > 2000:
            raise forms.ValidationError("Review cannot exceed 2000 characters.")
        # Basic sanitization - remove potentially harmful characters
        if any(char in review for char in ['<script', '</script', 'javascript:', 'onclick=']):
            raise forms.ValidationError("Review contains prohibited content.")
        return review.strip()
