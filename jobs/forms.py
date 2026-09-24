from django import forms

from .models import JobApplication


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('cover_note',)
        labels = {'cover_note': 'Note to the recruiter'}
        widgets = {
            'cover_note': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': (
                    'Briefly share why this role interests you and what you '
                    'would bring to the team.'
                ),
            }),
        }


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ('status',)
