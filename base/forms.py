# base/forms.py
from django import forms
from django.contrib.auth.models import User


class IsyaratkuSignUpForm(forms.ModelForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Choose a unique username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'email@example.com'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••'})
    )
    profile_picture = forms.ImageField(required=False)
    agree_to_terms = forms.BooleanField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()
            if self.cleaned_data.get('profile_picture'):
                user.profile.profile_picture = self.cleaned_data['profile_picture']
                user.profile.save()
        return user


from django import forms
from django.contrib.auth.models import User
# Import your Profile model here (adjust the app name to match your project)
from .models import Profile

from django import forms
from django.contrib.auth.models import User
from .models import Profile


class ProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'id': 'avatar-upload-input',
            'accept': 'image/*'
        })
    )

    username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-disabled',
            'readonly': 'readonly'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'input-disabled',
            'readonly': 'readonly'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.username
            self.fields['email'].initial = self.instance.email

            if hasattr(self.instance, 'profile') and self.instance.profile.profile_picture:
                self.fields['profile_picture'].initial = self.instance.profile.profile_picture

    # FIX 1: Force Django to keep the original username
    def clean_username(self):
        return self.instance.username

    # FIX 2: Force Django to keep the original email
    def clean_email(self):
        return self.instance.email

    def save(self, commit=True):
        user = super().save(commit=False)

        # Double-check preservation before saving to the database
        if self.instance.pk:
            user.username = self.instance.username
            user.email = self.instance.email

        if commit:
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)
            if self.cleaned_data.get('profile_picture'):
                profile.profile_picture = self.cleaned_data['profile_picture']
                profile.save()
        return user