from django import forms
from django.contrib.admin import widgets
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from orchestra.admin.forms import AdminFormMixin
from orchestra.admin.utils import admin_change_url

from .models import Order


class BillSelectedOptionsForm(AdminFormMixin, forms.Form):
    billing_point = forms.DateField(initial=timezone.now,
            label=_("Billing point"), widget=widgets.AdminDateWidget,
            help_text=_("Date you want to bill selected orders"))
    fixed_point = forms.BooleanField(initial=False, required=False,
            label=_("fixed point"),
            help_text=_("Deisgnates whether you want the billing point to be an "
                        "exact date, or adapt it to the billing period."))
    is_proforma = forms.BooleanField(initial=False, required=False,
            label=_("Pro-forma, billing simulation"),
            help_text=_("O."))
    create_new_open = forms.BooleanField(initial=False, required=False,
            label=_("Create a new open bill"),
            help_text=_("Deisgnates whether you want to put this orders on a new "
                        "open bill, or allow to reuse an existing one."))


def selected_related_choices(queryset):
    for order in queryset:
        verbose = '<a href="{order_url}">{description}</a> '
        verbose += '<a class="account" href="{account_url}">{account}</a>'
        verbose = verbose.format(
            order_url=admin_change_url(order), description=order.description,
            account_url=admin_change_url(order.account), account=str(order.account)
        )
        yield (order.pk, mark_safe(verbose))


class BillSelectRelatedForm(AdminFormMixin, forms.Form):
    selected_related = forms.ModelMultipleChoiceField(label=_("Related"),
            queryset=Order.objects.none(), widget=forms.CheckboxSelectMultiple,
            required=False)
    billing_point = forms.DateField(widget=forms.HiddenInput())
    fixed_point = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    is_proforma = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    create_new_open = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    
    def __init__(self, *args, **kwargs):
        super(BillSelectRelatedForm, self).__init__(*args, **kwargs)
        queryset = kwargs['initial'].get('related_queryset', None)
        if queryset:
            self.fields['selected_related'].queryset = queryset
        self.fields['selected_related'].choices = selected_related_choices(queryset)


class BillSelectConfirmationForm(AdminFormMixin, forms.Form):
    billing_point = forms.DateField(widget=forms.HiddenInput())
    fixed_point = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    is_proforma = forms.BooleanField(widget=forms.HiddenInput(), required=False)
    create_new_open = forms.BooleanField(widget=forms.HiddenInput(), required=False)
