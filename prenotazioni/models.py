# coding: utf-8
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from future.utils import python_2_unicode_compatible

from board.models import fs, get_secure_attachment_subfolder
from prenotazioni.util import prenotaCorsa
from tam import tamdates
from tam.models import Cliente, Luogo, Viaggio

# Regole da rispettare:
# non mostro i prezzi
# creo/modifico solo se ad almeno TOT ore dalla data prenotazione
# non posso modificare se il viaggio è già confermato

TIPI_PAGAMENTO = (
    ("D", _("Diretto")),
    ("H", _("Hotel")),  # diventa "conto finemese"
    ("F", _("Fattura")),  # fattura richiesta
)


@python_2_unicode_compatible
class UtentePrenotazioni(models.Model):
    user = models.OneToOneField(User, related_name="prenotazioni")
    clienti = models.ManyToManyField(Cliente)
    luogo = models.ForeignKey(Luogo, on_delete=models.PROTECT)
    nome_operatore = models.CharField(max_length=40, null=True)
    email = models.EmailField(null=True)
    quick_book = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Utenti prenotazioni"
        ordering = ("user",)
        permissions = (("manage_permissions", "Gestisci utenti prenotazioni"),)

    def __str__(self):
        return "%(user)s - %(clienti)s da '%(luogo)s' - %(email)s" % {
            "user": self.user.username,
            "clienti": ", ".join([c.nome for c in self.clienti.all()]),
            "luogo": self.luogo.nome,
            "email": self.email,
        }


def prenotazioni_upload_to(instance, filename):
    return get_secure_attachment_subfolder(filename, fs, "prenotazioni/%Y/%m")


class Prenotazione(models.Model):
    owner = models.ForeignKey(
        UtentePrenotazioni, editable=False, on_delete=models.CASCADE
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    data_registrazione = models.DateTimeField(auto_now_add=True)

    data_corsa = models.DateTimeField(
        _("Data e ora"),
        help_text=_(
            "Nelle partenze indica l'ora della presa in hotel. Negli arrivi indica l'ora al luogo specificato."
        ),
    )

    pax = models.IntegerField(default=1)
    is_collettivo = models.BooleanField(
        _("Individuale o collettivo?"),
        choices=((False, _("Individuale")), (True, _("Collettivo"))),
        default=None,
    )

    is_arrivo = models.BooleanField(
        _("Arrivo o partenza?"),
        choices=((True, _("Arrivo da...")), (False, _("Partenza per..."))),
        default=None,
    )
    luogo = models.ForeignKey(Luogo, verbose_name=_("Luogo"), on_delete=models.PROTECT)

    pagamento = models.CharField(
        _("Pagamento"), max_length=1, choices=TIPI_PAGAMENTO, default="D"
    )

    note_camera = models.CharField(_("Numero di camera"), max_length=20, blank=True)
    note_cliente = models.CharField(_("Nome del cliente"), max_length=40, blank=True)
    note = models.TextField(_("Note"), blank=True)

    viaggio = models.OneToOneField(
        Viaggio,
        null=True,
        editable=False,
        # on_delete=models.SET_NULL,  # allow delete a viaggio, deleting the prenotazione
    )

    attachment = models.FileField(
        _("Allegato"),
        storage=fs,
        upload_to=prenotazioni_upload_to,
        null=True,
        blank=True,
        help_text=_("Allega un file alla richiesta (facoltativo)."),
    )
    had_attachment = models.BooleanField(
        "Allegato passato", editable=False, default=False
    )

    # had_attachment è vero quando in qualche momento ho ottenuto un allegato

    class Meta:
        verbose_name_plural = "Prenotazioni"
        ordering = ("-data_registrazione", "cliente", "owner")

    def __str__(self):
        result = "%s - %s" % (self.cliente, self.owner.user.username)
        result += " - " + ("arrivo" if self.is_arrivo else "partenza")
        result += " %s" % self.luogo
        result += " del %s" % self.data_corsa.astimezone(tamdates.tz_italy).strftime(
            "%d/%m/%Y %H:%M"
        )
        return result

    def is_editable(self):
        """True se la corsa è ancora modificabile"""
        ora = tamdates.ita_now()
        notice_func = settings.PRENOTAZIONI_PREAVVISO_NEEDED_FUNC
        notice_max = notice_func(self.data_corsa)
        inTempo = ora <= notice_max
        if not inTempo:
            return False
        if self.viaggio and self.viaggio.conducente_confermato:
            return False
        return True

    def save(self, **kwargs):
        # posso forzare updateViaggi a False se non voglio aggiornare i viaggi
        if "updateViaggi" in kwargs:
            updateViaggi = kwargs["updateViaggi"]
            del kwargs["updateViaggi"]
        else:
            updateViaggi = True

        if self.viaggio and updateViaggi:
            nuovoViaggio = prenotaCorsa(self, dontsave=True)
            chiavi_da_riportare = [
                "data",
                "da",
                "a",
                "numero_passeggeri",
                "esclusivo",
                "incassato_albergo",
                "fatturazione",
                "pagamento_differito",
                "cliente",
                "note",
            ]
            for chiave in chiavi_da_riportare:
                setattr(self.viaggio, chiave, getattr(nuovoViaggio, chiave))
            self.viaggio.save()
            self.viaggio.updatePrecomp()
        super(Prenotazione, self).save(**kwargs)

    def delete(self, *args, **kwargs):
        if self.viaggio:
            # annullo il viaggio
            self.viaggio.annullato = True
            self.viaggio.padre = None
            self.viaggio.save()
            self.viaggio.updatePrecomp()

        super(Prenotazione, self).delete(*args, **kwargs)
