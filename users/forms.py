from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model


# class CustomUserCreationForm(UserCreationForm):

#     class Meta:
#         model = get_user_model()
#         fields = ('email', )


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = get_user_model()
        fields = ('email', 'job_title')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name == "job_title":
                self.fields[field_name].required = False

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add 'form-control' class to all form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
