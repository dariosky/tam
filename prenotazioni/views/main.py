# coding: utf-8
from __future__ import unicode_literals

import os
from collections import OrderedDict
from email import Encoders
from email.mime.base import MIMEBase
import datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.fields import TypedChoiceField
from django.forms.widgets import Input
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as _, ungettext

from markViews import prenotazioni
from prenotazioni.models import Prenotazione
from prenotazioni.util import prenotaCorsa
from prenotazioni.views.tam_email import notifyByMail
from tam import tamdates
from tam.models import Viaggio, Cliente
from tam.tamdates import parse_datestring, MONTH_NAMES
from tam.views.tamviews import SmartPager
from tam.widgets import MySplitDateTimeField, MySplitDateWidget


class NumberInput(Input):
    input_type = 'number'


def inviaMailPrenotazione(prenotazione, azione, attachments=None, extra_context=None):
    if not attachments:
        attachments = []
    if azione == "create":
        subject = "Conferma prenotazione TaM n° %d" % prenotazione.id
        prenotazione_suffix = "effettuata"
    elif azione == "update":
        subject = "Modifica prenotazione TaM n° %d" % prenotazione.id
        prenotazione_suffix = "modificata"
    elif azione == "delete":
        subject = "Annullamento prenotazione TaM n° %d" % prenotazione.id
        prenotazione_suffix = "cancellata"
    else:
        raise Exception("Azione mail non valida %s" % azione)

    azione = ""
    context = {"prenotazione": prenotazione,
               "azione": prenotazione_suffix,
               }
    if extra_context:
        context.update(extra_context)

    from_email = getattr(settings, 'PRENOTAZIONI_FROM_EMAIL', None)
    if settings.DEBUG and False:
        print "Sono in test. non invio la mail da {from_email}".format(from_email=from_email)
    else:
        notifyByMail(
            to=[prenotazione.owner.email, settings.EMAIL_CONSORZIO],
            from_email=from_email,
            subject=subject,
            context=context,
            attachments=attachments,
            reply_to=settings.EMAIL_CONSORZIO,
            messageTxtTemplateName="prenotazioni_email/conferma.inc.txt",
            messageHtmlTemplateName="prenotazioni_email/conferma.inc.html",
        )


class FormPrenotazioni(forms.ModelForm):
    def clean_pax(self):
        """ Pulizia numero di pax """
        value = self.cleaned_data['pax']
        if value > 50:
            raise forms.ValidationError(_("Sicuro del numero di persone?"))
        return value

    def clean_is_arrivo(self):
        value = self.cleaned_data['is_arrivo']
        if value not in (True, False):
            raise forms.ValidationError(
                _("Devi specificare se la corsa è un arrivo o una partenza."))
        return value

    def clean_is_collettivo(self):
        value = self.cleaned_data['is_collettivo']
        if value not in (True, False):
            raise forms.ValidationError(_("Questo campo è obbligatorio."))
        return value

    def clean(self):
        """ Controlli di validità dell'intera form """
        cleaned_data = self.cleaned_data
        ora = tamdates.ita_now()

        notice_func = getattr(settings, 'PRENOTAZIONI_PREAVVISO_NEEDED_FUNC', None)
        if notice_func:
            rdate = cleaned_data['data_corsa']
            notice_max = notice_func(rdate)
            if ora > notice_max:
                hours = (rdate - notice_max).seconds / 60 / 60
                raise forms.ValidationError(
                    ungettext(
                        "Il preavviso minimo per questa corsa è di un'ora",
                        "Il preavviso minimo per questa corsa è di {hours} ore",
                        hours).format(
                        hours=hours
                    )
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
                if field_name == 'pax':
                    field.widget = NumberInput(attrs={'min': "1", 'max': "50"})
                if type(field.widget) in (forms.TextInput, forms.DateInput):
                    field.widget = forms.TextInput(attrs={'placeholder': field.label})
                elif type(field.widget) in (forms.DateTimeInput,):
                    data = MySplitDateTimeField(
                        label=field.label,
                        date_input_formats=[_('%d/%m/%Y')],
                        time_input_formats=[_('%H:%M')],
                        help_text=field.help_text,
                        widget=MySplitDateWidget()
                    )
                    data.widget.widgets[0].format = '%d/%m/%Y'
                    self.fields[field_name] = data
                    field.widget = MySplitDateTimeField()

    class Meta:
        model = Prenotazione
        fields = ['cliente', 'data_corsa',
                  'pax', 'is_collettivo', 'is_arrivo',
                  'luogo',
                  'pagamento', 'note_camera', 'note_cliente',
                  'note', 'attachment',
                  ]
        # fields = '__all__'
        widgets = {
            'is_arrivo': forms.RadioSelect,
            'is_collettivo': forms.RadioSelect,
            'pagamento': forms.RadioSelect,
        }


@prenotazioni
@transaction.atomic  # commit solo se tutto OK
def prenota(request, id_prenotazione=None, template_name='prenotazioni/main.html'):
    utentePrenotazioni = request.user.prenotazioni

    previous_values = {}
    if id_prenotazione:
        try:
            prenotazione = Prenotazione.objects.get(id=id_prenotazione)
        except Prenotazione.DoesNotExist:
            messages.error(
                request,
                _("La prenotazione non esiste.")
            )
            return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))
        if prenotazione.owner <> utentePrenotazioni:
            messages.error(
                request,
                _("La prenotazione non è stata fatta da te, non puoi accedervi.")
            )
            return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))
        editable = prenotazione.is_editable()
        if not editable:
            messages.warning(
                request,
                _("La prenotazione non è più modificabile.")
            )
            # return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))
    else:
        prenotazione = None
        editable = True

    form = FormPrenotazioni(request.POST or None, request.FILES or None, instance=prenotazione)
    if prenotazione:
        form.initial["data_corsa"] = prenotazione.data_corsa.astimezone(
            tamdates.tz_italy)  # inizialmente forzo la corsa

    # deciso se mostrare o meno la scelta dei clienti:
    clienti_attivi = utentePrenotazioni.clienti
    if clienti_attivi.count() == 0:
        messages.error(
            request,
            _("Non hai alcun cliente abilitato.")
        )
        return HttpResponseRedirect(reverse('login'))

    if clienti_attivi.count() > 1:
        form.fields["cliente"].editable = True
        form.fields["cliente"].queryset = utentePrenotazioni.clienti
        form.fields["cliente"].label = ''
        cliente_unico = None
    else:
        # del forms.fields['cliente']
        del form.fields['cliente']
        cliente_unico = clienti_attivi.all()[0]

    if request.method == "POST" and prenotazione:
        # salvo i valori precedenti e consento la cancellazione
        for key in form.fields:
            if key != "attachment":
                previous_values[key] = getattr(prenotazione, key)

        if "delete" in request.POST:
            inviaMailPrenotazione(prenotazione, "delete")
            id_prenotazione = prenotazione.id  # salvo per il messaggio finale
            prenotazione.delete()
            messages.success(request, _("Prenotazione n°%d annullata.") % id_prenotazione)
            return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))

    if form.is_valid() and editable:
        request_attachment = form.cleaned_data['attachment']
        attachment = None
        # del form.cleaned_data['attachment']

        if request_attachment:
            # destination = tempfile.NamedTemporaryFile(delete=False)
            attachment = MIMEBase('application', "octet-stream")
            # print "Write to %s" % destination.name
            attachment.set_payload(request_attachment.read())
            Encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                'attachment; filename="%s"' % os.path.basename(request_attachment.name)
            )
        # for chunk in attachment.chunks():
        # destination.write(chunk)
        # destination.close()

        if id_prenotazione is None:
            prenotazione = Prenotazione(
                owner=utentePrenotazioni,
                **form.cleaned_data
            )
            if clienti_attivi.count() == 1:
                prenotazione.cliente = cliente_unico

            viaggio = prenotaCorsa(prenotazione)
            prenotazione.viaggio = viaggio
            if request_attachment:
                prenotazione.had_attachment = True  # creata con allegato
            prenotazione.save()

            inviaMailPrenotazione(prenotazione,
                                  "create",
                                  attachments=[attachment] if attachment else []
                                  )
            messages.success(
                request,
                _(
                    "Prenotazione n° %d effettuata, a breve riceverai una mail di conferma.") % prenotazione.id
            )
            return HttpResponseRedirect(reverse('tamPrenotazioni'))
        else:  # salvo la modifica
            changes = {}  # dizionario con i cambiamenti al form
            for key in form.cleaned_data:
                def humanValue(pythonValue, choices):
                    for k, v in choices:
                        if k == pythonValue:
                            return v

                oldValue = previous_values.get(key)
                newValue = form.cleaned_data[key]

                field = form.fields[key]
                if isinstance(field, TypedChoiceField):
                    oldValue = humanValue(oldValue, field.choices)
                    newValue = humanValue(newValue, field.choices)

                if newValue <> oldValue:
                    changes[key] = (field.label, oldValue, newValue)
                    # messages.success(
                    # request,
                    # "Cambiato %s da %s a %s" % (form.fields[key].label,
                    # oldValue,
                    # newValue)
                    # )
            if changes or attachment:
                stringhe_cambiamenti = []
                for key in changes:
                    (label, oldValue, newValue) = changes[key]
                    stringhe_cambiamenti.append(
                        "Cambiato %s da %s a %s" % (label, oldValue, newValue))

                cambiamenti = "\n".join(stringhe_cambiamenti)
                inviaMailPrenotazione(prenotazione,
                                      "update",
                                      attachments=[attachment] if attachment else [],
                                      extra_context={"cambiamenti": cambiamenti}
                                      )

                if request_attachment and not prenotazione.had_attachment:
                    prenotazione.had_attachment = True  # aggiunto l'allegato
                prenotazione.save()
                messages.success(request, _("Modifica eseguita."))
            return HttpResponseRedirect(
                reverse('tamPrenotazioni-edit',
                        kwargs={"id_prenotazione": prenotazione.id}
                        ),
            )

    return render(request,
                  template_name,
                  {
                      "utentePrenotazioni": utentePrenotazioni,
                      "form": form,
                      "editable": editable,
                      "prenotazione": prenotazione,
                      "cliente_unico": cliente_unico,
                      "logo_consorzio": settings.TRANSPARENT_SMALL_LOGO,
                  },
                  )


@prenotazioni
def cronologia(request, template_name='prenotazioni/cronologia.html'):
    utentePrenotazioni = request.user.prenotazioni
    clienti_attivi = utentePrenotazioni.clienti.all()
    if len(clienti_attivi) == 1:
        cliente_unico = clienti_attivi[0]
    else:
        cliente_unico = None

    filtroCliente = request.GET.get('cliente', None)
    cliente_selezionato = None
    if filtroCliente is not None:
        if filtroCliente != "all":
            try:
                codice_cliente = int(filtroCliente)
                cliente_selezionato = Cliente.objects.get(id=codice_cliente)
                if cliente_selezionato not in clienti_attivi:
                    messages.error(request, _('Non sei abilitato a vedere questo cliente.'))
                    return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))
            except ValueError:
                filtroCliente = None
            except Cliente.DoesNotExist:
                messages.error(request, _('Il cliente non esiste.'))
                return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))

    adesso = tamdates.ita_now().replace(second=0, microsecond=0)
    data_inizio = (adesso - datetime.timedelta(days=60)).replace(hour=0, minute=0)
    data_fine = None

    filtroData = request.GET.get('data', 'next')
    if filtroData is not None:
        if filtroData == 'cur':  # mese corrente
            data_inizio = adesso.replace(hour=0, minute=0, day=1)
            data_fine = (data_inizio + datetime.timedelta(days=32)).replace(hour=0, minute=0, day=1)
        elif filtroData == 'prev':  # mese precedente
            data_fine = adesso.replace(hour=0, minute=0, day=1)  # vado a inizio mese
            data_inizio = (data_fine - datetime.timedelta(days=1)).replace(
                day=1)  # vado a inizio del mese precedente
        elif filtroData == 'day':  # tutta oggi
            data_inizio = adesso.replace(hour=0, minute=0)  # da mezzanotte...
            data_fine = adesso.replace(hour=23, minute=59)  # fino a fine giornata
        elif filtroData == 'next':  # prossime corse
            # prendo il minore tra 2 ore fa e mezzanotte scorsa e per i prossimi 15 giorni
            data_ScorsaMezzanotte = adesso.replace(hour=0, minute=0)
            data_DueOreFa = adesso - datetime.timedelta(hours=2)
            data_inizio = min(data_ScorsaMezzanotte, data_DueOreFa)
            data_fine = adesso + datetime.timedelta(days=15)
        elif filtroData == 'adv':  # filtro avanzato da data - a data
            start_string = request.GET.get('dstart')
            end_string = request.GET.get('dend')
            try:
                data_inizio = tamdates.parse_datestring(start_string).replace(hour=0, minute=0)
                data_fine = tamdates.parse_datestring(end_string).replace(hour=23,
                                                                          minute=59)  # fino a fine giornata
            except AttributeError:
                messages.warning(request,
                                 _(
                                     "Errore nel processare l'intervallo di date {start}-{end}.").format(
                                     start=start_string, end=end_string)
                                 )
                return HttpResponseRedirect(reverse('tamCronoPrenotazioni'))

    viaggi = Viaggio.objects.filter(cliente__in=utentePrenotazioni.clienti.all())

    if cliente_selezionato:  # filtro ulteriormente
        viaggi = viaggi.filter(cliente=cliente_selezionato)

    viaggi = viaggi.filter(data__gte=data_inizio)
    if data_fine: viaggi = viaggi.filter(data__lte=data_fine)
    viaggi = viaggi.order_by("-data")

    # print "Ho %d viaggi da mostrare" % viaggi.count()

    # divido viaggi in pagine
    paginator = Paginator(viaggi, 50, orphans=5)  # pagine da tot viaggi
    page = request.GET.get("page", 1)
    try:
        page = int(page)
    except:
        page = 1
    s = SmartPager(page, paginator.num_pages)
    paginator.smart_page_range = s.results
    try:
        thisPage = paginator.page(page)
        viaggi = thisPage.object_list
    except:
        messages.warning(request, _("La pagina %d è vuota.") % page)
        thisPage = None
        viaggi = []
    # ----------------------

    return render(
        request,
        template_name,
        {
            "utentePrenotazioni": utentePrenotazioni,
            "prenotazioni": prenotazioni,
            "viaggi": viaggi,
            "cliente_unico": cliente_unico,
            "clienti_attivi": clienti_attivi,
            "cliente_selezionato": cliente_selezionato,

            "current_date_filter": filtroData,
            "data_inizio": data_inizio.strftime('%d/%m/%Y') if data_inizio else "",
            "data_fine": data_fine.strftime('%d/%m/%Y') if data_fine else "",

            "paginator": paginator,
            "thisPage": thisPage,
            "logo_consorzio": settings.TRANSPARENT_SMALL_LOGO,
        },
    )


def attachments_list(request):
    get_mese = request.GET.get('mese', None)
    oggi = tamdates.ita_today()
    quick_month_names = [MONTH_NAMES[(oggi.month - 3) % 12],
                         MONTH_NAMES[(oggi.month - 2) % 12],
                         MONTH_NAMES[(oggi.month - 1) % 12]]  # current month
    quick_month_names.reverse()

    if get_mese:
        if get_mese == "cur":
            data_start = oggi.replace(day=1)
            data_end = (data_start + datetime.timedelta(days=32)).replace(
                day=1) - datetime.timedelta(days=1)
        elif get_mese == 'prev':
            data_end = oggi.replace(day=1) - datetime.timedelta(days=1)  # vado a fine mese scorso
            data_start = data_end.replace(day=1)  # vado a inizio del mese precedente
        elif get_mese == 'prevprev':  # due mesi fa
            data_end = (oggi.replace(day=1) - datetime.timedelta(days=1)).replace(
                day=1) - datetime.timedelta(
                days=1)  # vado a inizio mese scorso
            data_start = data_end.replace(day=1)  # vado a inizio di due mesi fa
        else:
            raise Exception("Unexpected get mese fatture %s" % get_mese)
    else:
        data_start = parse_datestring(  # dal primo del mese scorso
            request.GET.get("data_start"),
            default=(
                tamdates.ita_today().replace(day=1) - datetime.timedelta(days=1)).replace(
                day=1)
        )
        data_end = parse_datestring(  # all'ultimo del mese scorso
            request.GET.get("data_end"),
            default=tamdates.ita_today()
        )

    prenotazioni = Prenotazione.objects.filter(had_attachment=True, data_corsa__gte=data_start,
                                               data_corsa__lt=data_end + datetime.timedelta(days=1))
    gruppo_prenotazioni = OrderedDict()
    for prenotazione in prenotazioni:
        if prenotazione.cliente not in gruppo_prenotazioni:
            gruppo_prenotazioni[prenotazione.cliente] = []
        gruppo_prenotazioni[prenotazione.cliente].append(prenotazione)

    return render(request,
                  'attachments_list.html',
                  {
                      "data_start": data_start.date(),
                      "data_end": data_end.date(),
                      "quick_month_names": quick_month_names,
                      "dontHilightFirst": True,
                      "mediabundleJS": ('tamUI',),
                      "mediabundleCSS": ('tamUI',),
                      "gruppo_prenotazioni": gruppo_prenotazioni,
                  },
                  )
