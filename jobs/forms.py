from django import forms

from .models import JobApplication, JobPosting, Skill


def _comma_separated_terms(value):
    terms = []
    seen = set()
    for raw_term in value.split(','):
        term = raw_term.strip()
        normalized_term = term.casefold()
        if term and normalized_term not in seen:
            terms.append(term)
            seen.add(normalized_term)
    return terms


class CandidateSearchForm(forms.Form):
    skills = forms.CharField(
        required=False,
        label='Skills',
        widget=forms.TextInput(attrs={
            'placeholder': 'Python, Django',
            'autocomplete': 'off',
        }),
    )
    location = forms.CharField(
        required=False,
        label='Location',
        widget=forms.TextInput(attrs={
            'placeholder': 'Atlanta, GA',
            'autocomplete': 'off',
        }),
    )
    projects = forms.CharField(
        required=False,
        label='Project keywords',
        widget=forms.TextInput(attrs={
            'placeholder': 'Analytics, React',
            'autocomplete': 'off',
        }),
    )

    def clean_skills(self):
        return _comma_separated_terms(self.cleaned_data['skills'])

    def clean_location(self):
        return self.cleaned_data['location'].strip()

    def clean_projects(self):
        return _comma_separated_terms(self.cleaned_data['projects'])


class JobPostingForm(forms.ModelForm):
    required_skills = forms.CharField(
        label='Required skills',
        help_text='Separate skills with commas (for example: Python, Django, SQL).',
        widget=forms.TextInput(attrs={
            'placeholder': 'Python, Django, SQL',
        }),
    )

    def __init__(self, *args, recruiter=None, **kwargs):
        self.recruiter = recruiter
        super().__init__(*args, **kwargs)
        company = getattr(recruiter, 'company', None)
        if company is not None:
            self.fields['company_name'].initial = company.name
            self.fields['company_name'].help_text = (
                'This comes from your recruiter account.'
            )
            self.fields['company_name'].widget.attrs.update({
                'readonly': 'readonly',
            })
        if self.instance.pk:
            self.fields['required_skills'].initial = ', '.join(
                self.instance.skills_required.order_by('name').values_list(
                    'name', flat=True
                )
            )

    class Meta:
        model = JobPosting
        fields = (
            'title',
            'company_name',
            'description',
            'location',
            'latitude',
            'longitude',
        )
        labels = {
            'company_name': 'Company',
            'description': 'Job description',
            'location': 'City or neighborhood',
        }
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Junior Software Engineer',
            }),
            'company_name': forms.TextInput(attrs={
                'placeholder': 'Your company name',
            }),
            'description': forms.Textarea(attrs={
                'rows': 7,
                'placeholder': (
                    'Describe the role, responsibilities, team, and what '
                    'success looks like.'
                ),
            }),
            'location': forms.TextInput(attrs={
                'placeholder': 'Atlanta, GA',
            }),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_required_skills(self):
        skill_names = []
        seen = set()
        for value in self.cleaned_data['required_skills'].split(','):
            name = value.strip()
            normalized_name = name.casefold()
            if not name or normalized_name in seen:
                continue
            if len(name) > Skill._meta.get_field('name').max_length:
                raise forms.ValidationError(
                    'Each skill must be 100 characters or fewer.'
                )
            seen.add(normalized_name)
            skill_names.append(name)

        if not skill_names:
            raise forms.ValidationError('Enter at least one required skill.')
        return skill_names

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if latitude is None or longitude is None:
            raise forms.ValidationError('Choose the job location on the map.')
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise forms.ValidationError('Choose a valid job location on the map.')
        return cleaned_data

    def save_skills(self, job_posting):
        skills = []
        for name in self.cleaned_data['required_skills']:
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                skill = Skill.objects.create(name=name)
            skills.append(skill)
        job_posting.skills_required.set(skills)


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
