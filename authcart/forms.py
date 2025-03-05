# authapp/forms.py
from django import forms
from ecommerceapp.models import CustomUser
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

from django import forms
from django.contrib.auth.forms import UserCreationForm
from ecommerceapp.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    username = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': 'Last Name',
        'class': 'form-control',
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Email',
        'class': 'form-control',
    }))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Password',
        'class': 'form-control',
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
        'class': 'form-control',
    }))
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
    
from django import forms
from ecommerceapp.models import CustomUser

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["phone", "date_of_birth", "profile_picture"]




# # from django import forms
# # from django.contrib.auth.models import User
# # from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# # from django.contrib.auth import get_user_model
# # user = get_user_model()

# # class SignUpForm(UserCreationForm):
# #     email = forms.EmailField(required=True)

# #     class Meta:
# #         model = User
# #         fields = ('username', 'email', 'password1', 'password2')

# # class LoginForm(AuthenticationForm):
# #     username = forms.CharField(label='Username')
# #     password = forms.CharField(label='Password', widget=forms.PasswordInput)
    
# # def save(self,commit=True):
# #     user=super().save(commit=False)
# #     user.email=self.cleaned_data['email']

# #     if commit:
# #         user.save()
# #     return user

# from django.contrib.auth import get_user_model

# User = get_user_model()

# def authenticate(self, request, username=None, password=None, **kwargs):
#     try:
#         user = User.objects.get(email=username)  # Use email instead of username
#     except User.DoesNotExist:
#         return None
#     # Further authentication logic
#     if user.check_password(password):
#         return user
#     return None

# from django import forms
# from django.contrib.auth import get_user_model
# User = get_user_model()

# class SignUpForm(forms.ModelForm):
#     email = forms.EmailField(required=True)

#     class Meta:
#         model = User  # This ensures the custom User model is used
#         fields = ('username', 'email', 'password1', 'password2')

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']

#         if commit:
#             user.save()
#         return user

# class LoginForm(forms.Form):
#     username = forms.CharField(label='Username')
#     password = forms.CharField(label='Password', widget=forms.PasswordInput)

#     def clean_username(self):
#         username = self.cleaned_data.get('username')
#         # Custom logic to validate username if necessary
#         return username
