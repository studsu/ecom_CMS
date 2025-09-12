from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "title", "comment"]
        widgets = {
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5}),
            "title": forms.TextInput(attrs={"placeholder": "Title (optional)"}),
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Write your review..."}),
        }

    def clean_rating(self):
        r = self.cleaned_data["rating"]
        if r < 1 or r > 5:
            raise forms.ValidationError("Rating must be between 1 and 5.")
        return r

