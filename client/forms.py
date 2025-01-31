from django import forms
from .models import ClientType, Client


class ClientTypeForm(forms.ModelForm):
    class Meta:
        model = ClientType
        fields = ['name']


class ClientAddForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name not in ['name', 'client_type', 'month_end', 'last_day']:
                self.fields[field_name].required = False

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
