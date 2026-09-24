from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import JobSeekerProfile, User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'role')


class CommutePreferenceForm(forms.ModelForm):
    class Meta:
        model = JobSeekerProfile
        fields = (
            'location',
            'preferred_latitude',
            'preferred_longitude',
            'commute_radius_miles',
        )
        widgets = {
            'location': forms.TextInput(
                attrs={'placeholder': 'e.g. Midtown Atlanta, GA'}
            ),
            'preferred_latitude': forms.HiddenInput(),
            'preferred_longitude': forms.HiddenInput(),
            'commute_radius_miles': forms.NumberInput(
                attrs={'min': 1, 'max': 100, 'class': 'radius-input'}
            ),
        }

    def clean_location(self):
        return self.cleaned_data['location'].strip()

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('preferred_latitude')
        longitude = cleaned_data.get('preferred_longitude')
        if latitude is None or longitude is None:
            raise forms.ValidationError('Choose your commute center on the map.')
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise forms.ValidationError('Choose a valid location on the map.')
        return cleaned_data
