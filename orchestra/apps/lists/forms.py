from django import forms
from django.utils.translation import ugettext_lazy as _

from orchestra.core.validators import validate_password
from orchestra.forms.widgets import ReadOnlyWidget


class CleanAddressMixin(object):
    def clean_address_domain(self):
        name = self.cleaned_data.get('address_name')
        domain = self.cleaned_data.get('address_domain')
        if name and not domain:
            msg = _("Domain should be selected for provided address name")
            raise forms.ValidationError(msg)
        elif not name and domain:
            msg = _("Address name should be provided for this selected domain")
            raise forms.ValidationError(msg)
        return domain


class ListCreationForm(CleanAddressMixin, forms.ModelForm):
    password1 = forms.CharField(label=_("Password"),
            widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
            widget=forms.PasswordInput,
            help_text=_("Enter the same password as above, for verification."))
    
    def __init__(self, *args, **kwargs):
        super(ListCreationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].validators.append(validate_password)
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            msg = _("The two password fields didn't match.")
            raise forms.ValidationError(msg)
        return password2
    
    def save(self, commit=True):
        obj = super(ListCreationForm, self).save(commit=commit)
        obj.set_password(self.cleaned_data["password1"])
        return obj


class ListChangeForm(CleanAddressMixin, forms.ModelForm):
    password = forms.CharField(label=_("Password"),
            widget=ReadOnlyWidget('<strong>Unknown password</strong>'),
            help_text=_("List passwords are not stored, so there is no way to see this "
                        "list's password, but you can change the password using "
                        "<a href=\"password/\">this form</a>."))
