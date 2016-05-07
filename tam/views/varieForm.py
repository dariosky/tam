# coding: utf-8

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.urlresolvers import reverse
from tam.models import Viaggio, Passeggero
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from tam.widgets import MySplitDateTimeField, MySplitDateWidget


class AutoCompleteForm(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = kwargs.pop('widget', AutoCompleteWidget)
        self.can_fast_create = kwargs.pop('can_fast_create', True)
        super(AutoCompleteForm, self).__init__(*args, **kwargs)

    def clean(self, value):
        #        logging.debug("form clean %s" % value)
        if not value:
            return None
        # find the client given fielname, case insensitive
        results = self.queryset.filter(**{self.widget.fieldname + "__iexact": value})

        if len(results) == 0:
            if self.can_fast_create is False:
                raise ValidationError("Deve esistere")
            newobj = self.queryset.model.objects.create(**{self.widget.fieldname: value})
            return newobj  # doesn't exist
        else:
            return results[0]  # use the first result


class AutoCompleteWidget(forms.widgets.Widget):
    # DEPRECATED: use AutoCompleteUIWidget
    class Media:
        js = [staticfiles_storage.url('js/jquery-autocomplete/jquery.autocomplete.min.js')]
        css = {
            'all': [staticfiles_storage.url('js/jquery-autocomplete/jquery.autocomplete.css')]
        }

    lookup_url = None

    def __init__(self, lookup_url, Model, fieldname, **kwargs):
        super(AutoCompleteWidget, self).__init__(**kwargs)
        self.lookup_url = lookup_url
        self.Model = Model
        self.fieldname = fieldname

    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        else:
            try:
                value = getattr(self.Model.objects.get(id=value), self.fieldname)
            except:
                value = ""
        final_attrs = self.build_attrs(attrs, name=name, value=value)
        final_attrs['class'] = 'autocomplete_widget'
        id = final_attrs.get('id', 'id_%s' % name)

        js = """
            <script type="text/javascript">
                window.onload = function(){
                    $("#%(id)s").autocomplete( "%(lookup_url)s", {minChars:2} );
                }
            </script>
        """ % {"id": id, 'lookup_url': self.lookup_url}
        return mark_safe(
            "<input%(attrs)s /> %(js)s" % {"attrs": forms.widgets.flatatt(final_attrs), "js": js})


class AutoCompleteUIWidget(forms.widgets.Widget):
    lookup_url = None

    def __init__(self, lookup_url, Model, fieldname, **kwargs):
        super(AutoCompleteUIWidget, self).__init__(**kwargs)
        self.lookup_url = lookup_url
        self.Model = Model
        self.fieldname = fieldname

    def render(self, name, value, attrs=None):
        if value is None:
            value = ""
        else:
            try:
                value = getattr(self.Model.objects.get(id=value), self.fieldname)
            except:
                value = ""
        final_attrs = self.build_attrs(attrs, name=name, value=value)
        final_attrs['class'] = 'autocomplete_widget'
        this_id = final_attrs.get('id', 'id_%s' % name)

        js = """
            <script type="text/javascript">
                window.onload = function(){
                    $("#%(id)s").autocomplete(
                                {
                                    source: function( request, response ) {
                                                $.getJSON( "%(lookup_url)s", {
                                                    q: extractLast( request.term )
                                                }, response );
                                            },
                                    minLength: 2
                                }
                    );
                }
            </script>
        """ % {"id": this_id, 'lookup_url': self.lookup_url}
        return mark_safe(
            "<input%(attrs)s /> %(js)s" % {"attrs": forms.widgets.flatatt(final_attrs), "js": js})


class ViaggioForm(forms.ModelForm):
    class Media:
        js = [staticfiles_storage.url('js/nuovaCorsaPag1.js'),
              staticfiles_storage.url('js/timeWidgets.js')]

    data = MySplitDateTimeField(label="Data e ora", date_input_formats=[_('%d/%m/%Y')],
                                time_input_formats=[_('%H:%M')],
                                widget=MySplitDateWidget())
    data.widget.widgets[0].format = '%d/%m/%Y'

    privato = forms.BooleanField(initial=False, required=False)  # privato checkbox
    #    cliente=AutoCompleteForm(queryset=Cliente.objects.filter(attivo=True), required=False,
    #                                    widget=AutoCompleteWidget(
    #                                                                lookup_url=reverse('tamGetCliente'),
    #                                                                Model=Cliente,
    #                                                                fieldname='nome'
    #                                                            )
    #                                )

    # cliente=ModelChoiceField('cliente', widget=CustomJQueryACWidget('cliente'))
    # passeggero=forms.CharField("Passeggero", required=False) # Charfield with autocomplete, if doesn't exist I'll create a new Passeggero
    passeggero = AutoCompleteForm(queryset=Passeggero.objects, required=False,
                                  widget=AutoCompleteWidget(
                                      lookup_url=reverse('tamGetPasseggero'),
                                      Model=Passeggero,
                                      fieldname='nome',
                                  )
                                  )

    esclusivo = forms.TypedChoiceField(
        coerce=lambda s: s == 'True',  # serve, perché il dato mi arriva qui come stringa
        choices=((False, 'Collettivo'), (True, 'Taxi')),
        widget=forms.RadioSelect
    )

    def clean(self):
        data = self.cleaned_data
        if not data.get("privato") and not data["cliente"]:
            raise forms.ValidationError("Se il cliente non è un privato, va specificato.")
        if data.get("privato"):
            data["cliente"] = None
        return data

    class Meta:
        model = Viaggio
        fields = ["data", "da", "a", "cliente", "passeggero", "numero_passeggeri", "esclusivo",
                  "privato", "padre"]


class ViaggioForm2(forms.ModelForm):
    def clean_prezzo(self):
        prezzo = self.cleaned_data.get("prezzo")
        if prezzo >= 10000:
            raise ValidationError(_(
                u"Sono felice per te, ma per ora il prezzo massimo concesso da TaM è di 9.999 euro")
            )
        return prezzo

    class Meta:
        model = Viaggio
        exclude = ViaggioForm.Meta.fields + ["padre", "pagato", "costo_sosta", "luogoDiRiferimento"]
