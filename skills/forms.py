from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Skill, SkillOffer, Session, Review, SkillCategory


class SkillCreateForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['name', 'category', 'description', 'difficulty']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Python Programming'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
        }


class SkillOfferForm(forms.ModelForm):
    class Meta:
        model = SkillOffer
        fields = ['skill', 'hourly_rate', 'description', 'available_days', 'available_times', 'is_active']
        widgets = {
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Describe what you will teach, your experience, methodology...'
            }),
            'available_days': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g., Mon-Fri or Weekends'
            }),
            'available_times': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'e.g., 9 AM - 6 PM IST'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_hourly_rate(self):
        rate = self.cleaned_data.get('hourly_rate')
        if rate is not None and rate < 0:
            raise ValidationError('Hourly rate cannot be negative.')
        return rate


class SessionBookingForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['scheduled_date', 'scheduled_time', 'duration', 'notes']
        widgets = {
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duration': forms.Select(
                choices=[(30, '30 min'), (60, '1 hour'), (90, '90 min'), (120, '2 hours'), (180, '3 hours'), (240, '4 hours')],
                attrs={'class': 'form-select'}
            ),
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Any specific topics you want to cover?'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['scheduled_date'].widget.attrs['min'] = timezone.now().date().isoformat()

    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < timezone.now().date():
            raise ValidationError('Cannot book a session in the past.')
        return scheduled_date

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        if duration and (duration < 30 or duration > 240):
            raise ValidationError('Duration must be between 30 and 240 minutes.')
        return duration


class SessionUpdateForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [(i, '★' * i) for i in range(1, 6)]
    rating = forms.ChoiceField(choices=RATING_CHOICES, widget=forms.RadioSelect(attrs={'class': 'star-radio'}))

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Share your experience — what worked well, what could improve?'
            }),
        }

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        return int(rating)