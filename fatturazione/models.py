# coding: utf-8
from django.db import models
from tam.models import Viaggio, Conducente, Cliente, Passeggero
from decimal import Decimal, ROUND_HALF_UP
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.conf import settings

nomi_fatture = {'1': "Fattura consorzio", '2': "Fattura conducente", '3': "Ricevuta taxi",
                '4': "Fattura consorzio esente IVA", '5': "Fattura conducente esente IVA"}
nomi_plurale = {'1': "fatture consorzio", '2': "fatture conducente", '3': "ricevute taxi",
                '4': "fatture consorzio esente IVA", '5': "fatture conducente esente IVA"}

DATA_RICEVUTE_SDOPPIATE = getattr(settings, 'DATA_RICEVUTE_SDOPPIATE', None)
INVOICES_FOOTERS = getattr(settings, "INVOICES_FOOTERS", {})


class Fattura(models.Model):
    emessa_da = models.TextField()  # anagrafica emittente
    emessa_a = models.TextField()  # anagrafica cliente
    # cliente e passeggero sono prepopolati in automatico (uno dei 2) ma non sono obbligatori.
    # servono solo per avere un'associazione, emessa_a fa fede
    cliente = models.ForeignKey(Cliente, null=True, blank=True, related_name="fatture",
                                on_delete=models.SET_NULL)
    passeggero = models.ForeignKey(Passeggero, null=True, blank=True, related_name="fatture",
                                   on_delete=models.SET_NULL)

    note = models.TextField(blank=True)  # note in testata

    tipo = models.CharField(max_length=1,
                            db_index=True)  # tipo fattura: 1.Consorzio (a cliente), 2.Conducente (a consorzio), 3.Ricevuta (a cliente)

    data = models.DateField(db_index=True)
    anno = models.IntegerField(db_index=True, null=True)
    progressivo = models.IntegerField(db_index=True, null=True)

    archiviata = models.BooleanField(default=False)  # se true la fattura non è più modificabile

    class Meta:
        verbose_name_plural = "Fatture"
        ordering = ("anno", "progressivo")
        permissions = (('generate', 'Genera le fatture'),
                       ('smalledit', 'Smalledit: alle fat.conducente'),
                       ('view', 'Visualizzazione fatture'))

    def __unicode__(self):
        anno = self.anno or "-"
        progressivo = self.progressivo or "-"
        if not self.data: return "fattura-senza-data"
        return u"%s %s/%s del %s emessa a %s. %d righe" % (
        nomi_fatture[self.tipo], anno, progressivo,
        self.data.strftime("%d/%m/%Y %H:%M"),
        self.destinatario(),
        self.righe.count()
        )

    def mittente(self):
        return self.emessa_da.replace('\r', '').split('\n')[0]

    def destinatario(self):
        return self.emessa_a.replace('\r', '').split('\n')[0]

    def val_imponibile(self):
        return Decimal(sum([riga.val_imponibile() for riga in self.righe.all()]))

    def val_iva(self):
        return Decimal(sum([riga.val_iva() for riga in self.righe.all()]))

    def val_totale(self):
        return Decimal(sum([riga.val_totale() for riga in self.righe.all()]))

    def nome_fattura(self):
        """ Nome fattura (singolare) """
        return nomi_fatture[self.tipo]

    def url(self):
        return reverse("tamFatturaId",
                       kwargs={'id_fattura': self.id})

    def emessa_da_html(self):
        result = self.emessa_da \
            .replace("www.artetaxi.com",
                     "<a target='_blank' href='http://www.artetaxi.com'>www.artetaxi.com</a>") \
            .replace("info@artetaxi.com",
                     "<a target='_blank' href='mailto:info@artetaxi.com'>info@artetaxi.com</a>")
        return mark_safe(result)

    def descrittore(self):
        prefissiFattura = {"1": "FC", "4": "FE"}  # Fattura consorzio, fattura consorzio esente IVA
        if self.anno and self.progressivo:
            return "%s%s/%s" % (prefissiFattura.get(self.tipo, ""), self.anno, self.progressivo)
        return "%s%s" % (self.anno or "", self.progressivo or "")

    def is_ricevuta_sdoppiata(self):
        return (self.tipo == "3") and DATA_RICEVUTE_SDOPPIATE and (
        self.data >= DATA_RICEVUTE_SDOPPIATE)

    def note_fisse(self):
        if self.tipo == '3':
            testo_fisso = "Servizio trasporto emodializzato da Sua abitazione al centro emodialisi assistito e viceversa come da distinta."
            if self.is_ricevuta_sdoppiata():
                testo_fisso = testo_fisso.replace("Servizio trasporto emodializzato",
                                                  "Servizio di trasporto di tipo collettivo per emodializzato")
            return testo_fisso

    def footer(self):
        # ritorna una lista di righe che vanno nel footer di questa fattura
        return INVOICES_FOOTERS.get(self.tipo, [])

    def log_url(self):
        # <a href="{% url "actionLog" %}?type=fattura&amp;id={{ viaggio.id }}">log</a>
        return mark_safe(reverse('actionLog') + "?type=fattura&amp;id=%d" % self.id)


class RigaFattura(models.Model):
    fattura = models.ForeignKey(Fattura, related_name="righe")
    riga = models.IntegerField()

    descrizione = models.TextField()
    note = models.TextField()

    qta = models.IntegerField()
    prezzo = models.DecimalField(max_digits=9, decimal_places=2, default=0,
                                 null=True)  # fissa in euro
    iva = models.IntegerField()  # iva in percentuale

    viaggio = models.OneToOneField(Viaggio, null=True, related_name="riga_fattura",
                                   on_delete=models.SET_NULL)
    conducente = models.ForeignKey(Conducente, null=True, related_name="fatture",
                                   on_delete=models.SET_NULL)
    riga_fattura_consorzio = models.OneToOneField("RigaFattura", null=True,
                                                  related_name="fattura_conducente_collegata",
                                                  on_delete=models.SET_NULL)

    def val_imponibile(self):
        result = (self.prezzo or Decimal(0)) * self.qta
        return result.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

    def val_iva(self):
        result = self.val_imponibile() * self.iva / Decimal(100)
        return result.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)

    def val_totale(self):
        return self.val_imponibile() + self.val_iva()

    class Meta:
        verbose_name_plural = "Righe Fattura"
        # ordino per fattura.tipo in modo da copiare prima le fatture
        # referenziate (che hanno tipo minore di quelle che referenziano)
        ordering = ("fattura__tipo", "fattura", "riga")

    def __unicode__(self):
        return u"Fattura %d. Riga %d. %.2f." % (self.fattura.id, self.riga, self.prezzo or 0)
