from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Company, JobSeekerProfile, User


class CustomUserCreationForm(UserCreationForm):
    company_name = forms.CharField(
        label='Company',
        required=False,
        help_text='Required for recruiter accounts.',
        widget=forms.TextInput(attrs={
            'placeholder': 'Company name',
        }),
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'username',
            'role',
            'company_name',
        )

    def clean_company_name(self):
        return self.cleaned_data['company_name'].strip()

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('role') == User.Role.RECRUITER
            and not cleaned_data.get('company_name')
        ):
            self.add_error(
                'company_name',
                'Enter the company you are recruiting for.',
            )
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        company_name = self.cleaned_data.get('company_name')
        if user.role == User.Role.RECRUITER and company_name:
            company, _created = Company.objects.get_or_create(name=company_name)
            user.company = company
        if commit:
            user.save()
            self.save_m2m()
        return user


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


class JobSeekerProfileForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        help_text='Separate skills with commas (for example: Python, Django, SQL).',
        widget=forms.TextInput(attrs={
            'placeholder': 'Python, Django, SQL',
        }),
    )

    class Meta:
        model = JobSeekerProfile
        fields = ('projects',)
        labels = {'projects': 'Projects'}
        widgets = {
            'projects': forms.Textarea(attrs={
                'rows': 9,
                'placeholder': (
                    'Describe projects you have built, your contribution, '
                    'and the tools you used.'
                ),
            }),
        }
        help_texts = {
            'projects': (
                'Include project names and technologies so recruiters can '
                'find relevant work.'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['skills'].initial = ', '.join(
                self.instance.skills.order_by('name').values_list(
                    'name', flat=True
                )
            )

    def clean_skills(self):
        skill_names = []
        seen = set()
        for value in self.cleaned_data['skills'].split(','):
            name = value.strip()
            normalized_name = name.casefold()
            if not name or normalized_name in seen:
                continue
            if len(name) > 100:
                raise forms.ValidationError(
                    'Each skill must be 100 characters or fewer.'
                )
            seen.add(normalized_name)
            skill_names.append(name)
        return skill_names

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit:
            from jobs.models import Skill

            skills = []
            for name in self.cleaned_data['skills']:
                skill = Skill.objects.filter(name__iexact=name).first()
                if skill is None:
                    skill = Skill.objects.create(name=name)
                skills.append(skill)
            profile.skills.set(skills)
        return profile
