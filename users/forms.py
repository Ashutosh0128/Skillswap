from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'First name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Last name'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow same email for current user
        self.user_instance = kwargs.get('instance')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance and User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'location', 'avatar', 'website', 'linkedin', 'github']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 4,
                'placeholder': 'Tell us about yourself, your expertise, what you love to teach...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'City, Country (e.g. Mumbai, India)'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://yourwebsite.com'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://linkedin.com/in/yourprofile'
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control', 'placeholder': 'https://github.com/yourusername'
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }