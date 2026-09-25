from django import forms
from django.utils import timezone

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

    def save(self, commit=True):
        # Keep the pipeline's "time in stage" accurate when edited from the review page.
        if 'status' in self.changed_data:
            self.instance.status_changed_at = timezone.now()
        return super().save(commit)
