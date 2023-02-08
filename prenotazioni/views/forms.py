from django import forms
from django.conf import settings
from django.forms.widgets import Input
from django.utils.translation import gettext as _, ngettext

from prenotazioni.models import Prenotazione
from tam import tamdates
from tam.widgets import MySplitDateTimeField, MySplitDateWidget


class NumberInput(Input):
    input_type = "number"


class FormPrenotazioni(forms.ModelForm):
    def clean_pax(self):
        """Pulizia numero di pax"""
        value = self.cleaned_data["pax"]
        if value > 50:
            raise forms.ValidationError(_("Sicuro del numero di persone?"))
        return value

    def clean_is_arrivo(self):
        value = self.cleaned_data["is_arrivo"]
        if value not in (True, False):
            raise forms.ValidationError(
                _("Devi specificare se la corsa è un arrivo o una partenza.")
            )
        return value

    def clean_is_collettivo(self):
        value = self.cleaned_data["is_collettivo"]
        if value not in (True, False):
            raise forms.ValidationError(_("Questo campo è obbligatorio."))
        return value

    def clean(self):
        """Controlli di validità dell'intera form"""
        cleaned_data = self.cleaned_data
        ora = tamdates.ita_now()

        notice_func = getattr(settings, "PRENOTAZIONI_PREAVVISO_NEEDED_FUNC", None)
        rdate = cleaned_data.get("data_corsa")
        if notice_func and rdate:
            notice_max = notice_func(rdate, cleaned_data)
            if ora > notice_max:
                delta = rdate - notice_max
                hours = delta.seconds / 60 / 60 + delta.days * 24
                raise forms.ValidationError(
                    ngettext(
                        "Il preavviso minimo per questa corsa è di un'ora",
                        "Il preavviso minimo per questa corsa è di {hours} ore",
                        hours,
                    ).format(hours=int(hours))
                )

    def __init__(self, *args, **kwargs):
        super(FormPrenotazioni, self).__init__(*args, **kwargs)
        # self.fields['attachment'] = forms.FileField(
        # label=_("Allegato"),
        # required=False,
        # help_text=_("Allega un file alla richiesta (facoltativo).")
        # )

        for field_name in self.fields:
            field = self.fields.get(field_name)
            if field:
                if field_name == "pax":
                    field.widget = NumberInput(attrs={"min": "1", "max": "50"})
                if type(field.widget) in (forms.TextInput, forms.DateInput):
                    field.widget = forms.TextInput(attrs={"placeholder": field.label})
                elif type(field.widget) in (forms.DateTimeInput,):
                    data = MySplitDateTimeField(
                        label=field.label,
                        date_input_formats=[_("%d/%m/%Y")],
                        time_input_formats=[_("%H:%M")],
                        help_text=field.help_text,
                        widget=MySplitDateWidget(),
                    )
                    data.widget.widgets[0].format = "%d/%m/%Y"
                    self.fields[field_name] = data
                    field.widget = MySplitDateTimeField()

    class Meta:
        model = Prenotazione
        fields = [
            "cliente",
            "data_corsa",
            "pax",
            "is_collettivo",
            "is_arrivo",
            "luogo",
            "pagamento",
            "note_camera",
            "note_cliente",
            "note",
            "attachment",
        ]
        # fields = '__all__'
        widgets = {
            "is_arrivo": forms.RadioSelect,
            "is_collettivo": forms.RadioSelect,
            "pagamento": forms.RadioSelect,
        }
