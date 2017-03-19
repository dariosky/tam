# coding: utf-8
import datetime
import itertools
import logging
import re
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse  # to resolve named urls
from django.db import connections, models
from django.db.models.deletion import SET_NULL, PROTECT
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from future.utils import python_2_unicode_compatible

import tam.tamdates as tamdates
from tam.disturbi import fasce_semilineari, trovaDisturbi, fasce_uno_due

Calendar = None
if 'calendariopresenze' in settings.INSTALLED_APPS:
    try:
        from calendariopresenze.models import Calendar
    except ImportError:
        Calendar = None

TIPICLIENTE = (("H", "Hotel"), ("A", "Agenzia"),
               ("D", "Ditta"))  # se null nelle corse è un privato
TIPICOMMISSIONE = [("F", "€"), ("P", "%")]
TIPISERVIZIO = [("T", "Taxi"), ("C", "Collettivo")]


def get_classifiche():
    """	Restituisco le classifiche globali (per le corse confermate)
        Restituisce una lista di dizionari, ognuna con i valori del conducente.
        Utilizzo una query fuori dall'ORM di Django per migliorare le prestazioni.
    """
    # logging.debug("Ottengo le classifiche globali.")
    cursor = connections['default'].cursor()
    query = """
        SELECT
            c.id AS conducente_id, c.nick AS conducente_nick, c.max_persone AS max_persone,
            coalesce(sum("punti_diurni"),0)+classifica_iniziale_diurni AS "puntiDiurni",
            coalesce(sum(punti_notturni),0)+classifica_iniziale_notturni AS "puntiNotturni",
            coalesce(sum("prezzoVenezia"),0) + classifica_iniziale_long AS "prezzoVenezia",
            coalesce(sum("prezzoPadova"),0) + classifica_iniziale_medium AS "prezzoPadova",
            coalesce(sum("prezzoDoppioPadova"),0) + "classifica_iniziale_doppiPadova" AS "prezzoDoppioPadova",
            coalesce(sum("punti_abbinata"),0) + "classifica_iniziale_puntiDoppiVenezia" AS punti_abbinata
        FROM tam_conducente c
            LEFT JOIN tam_viaggio v ON c.id=v.conducente_id AND v.conducente_confermato
        WHERE c.attivo --and c.nick='2'
            AND CASE WHEN NOT v.annullato OR v.annullato IS NULL THEN 0 END = 0
        GROUP BY c.id, c.nick
        ORDER BY conducente_nick
    """
    cursor.execute(query, ())
    results = cursor.fetchall()

    classifiche = []
    fieldNames = [field[0] for field in cursor.description]
    for classifica in results:
        classDict = {}
        for name, value in zip(fieldNames, classifica):
            classDict[name] = value
        classifiche.append(classDict)
    return classifiche


def reallySpaceless(s):
    """ Given a string, removes all double spaces and tab """
    s = re.sub('[\s\t][\s\t]+', " ", s, flags=re.DOTALL).strip()
    return s


@python_2_unicode_compatible
class Luogo(models.Model):
    """ Indica un luogo, una destinazione conosciuta.
        Ogni luogo appartiene ad un bacino all'interno del quale
         verrano cercati gli accoppiamenti.
        Al luogo afferiranno i listini, le corse e tutto il resto.
    """
    nome = models.CharField("Località ", max_length=25, unique=True)
    bacino = models.ForeignKey("Bacino", verbose_name="Bacino di appartenenza",
                               null=True, blank=True)
    speciale = models.CharField("Luogo particolare", max_length=1,
                                default="",
                                choices=(("-", "-"), ("A", "Aeroporto"),
                                         ("S", "Stazione")))

    # una delle località sarà  la predefinita... tra le proprietà  dell'utente

    class Meta:
        verbose_name_plural = _("Luoghi")
        ordering = ["nome"]

    def __str__(self):
        if self.nome[0] == ".":
            return self.nome[1:]
        return self.nome

    def delete_url(self):
        return reverse("tamLuogoIdDel", kwargs={"id": self.id})

    def save(self, *args, **kwargs):
        if 'updateViaggi' in kwargs:
            updateViaggi = kwargs['updateViaggi']
            del (kwargs['updateViaggi'])
        else:
            updateViaggi = True
        super(Luogo, self).save(*args, **kwargs)
        if not updateViaggi: return
        # aggiorno tutte le corse precalcolate con quel luogo
        viaggiCoinvolti = Viaggio.objects.filter(
            tratta_start__da=self) | Viaggio.objects.filter(
            tratta_start__a=self) | \
                          Viaggio.objects.filter(
                              tratta__da=self) | Viaggio.objects.filter(
            tratta__a=self) | \
                          Viaggio.objects.filter(
                              tratta_end__da=self) | Viaggio.objects.filter(
            tratta_end__a=self)
        viaggiCoinvolti = viaggiCoinvolti.filter(
            conducente_confermato=False)  # ricalcolo tutti i non confermati
        for viaggio in viaggiCoinvolti:
            viaggio.updatePrecomp()


@python_2_unicode_compatible
class Bacino(models.Model):
    """ I bacini sono dei gruppi di luoghi da cercare
        di accorpare nelle corse abbinate """
    nome = models.CharField(max_length=20, unique=True)

    class Meta:
        verbose_name_plural = _("Bacini")
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def delete_url(self):
        return reverse("tamBacinoIdDel", kwargs={"id": self.id})


@python_2_unicode_compatible
class Tratta(models.Model):
    """ Indica un tragitto, con indicati i default
        di tempo, spazio e spese di autostrada """
    da = models.ForeignKey(Luogo, related_name="tempo_da")
    a = models.ForeignKey(Luogo, related_name="tempo_a")
    minuti = models.IntegerField(
        default=0)  # tempo di viaggio espresso in minuti
    km = models.IntegerField(default=0)
    costo_autostrada = models.DecimalField(max_digits=9, decimal_places=2,
                                           default=0)  # fino a 9.999.999,99

    class Meta:
        verbose_name_plural = _("Tratte")
        unique_together = (("da", "a"),)
        ordering = ["da", "a"]

    def __str__(self):
        return u"%s - %s: %dm., %dkm" % (self.da, self.a, self.minuti, self.km)

    def is_valid(self):
        """ Return true if the path have all it's information completed """
        return self.minuti and self.km

    def delete_url(self):
        return reverse("tamTrattaIdDel", kwargs={"id": self.id})

    def save(self, *args, **kwargs):
        """ Salvo la tratta """
        if 'updateViaggi' in kwargs:
            updateViaggi = kwargs['updateViaggi']
            del (kwargs['updateViaggi'])
        else:
            updateViaggi = True
        super(Tratta, self).save(*args, **kwargs)
        # invalida la cache
        keyword = ("tratta%s-%s" % (self.da.id, self.a.id)).replace(" ", "")
        cache.delete(keyword)

        if updateViaggi:
            # aggiorno tutte le corse precalcolate con questa tratta
            viaggiCoinvolti = Viaggio.objects.filter(tratta_start=self) | \
                              Viaggio.objects.filter(tratta=self) | \
                              Viaggio.objects.filter(tratta_end=self)
            viaggiCoinvolti = viaggiCoinvolti.filter(
                conducente_confermato=False)  # ricalcolo tutti i non confermati
            for viaggio in viaggiCoinvolti:
                viaggio.updatePrecomp()


def get_tratta(da, a):
    """ Ritorna una data DA-A, se non esiste, A-DA, se non esiste la crea """
    if not da or not a: return
    keyword = ("tratta%s-%s" % (da.id, a.id)).replace(" ", "")
    trattacache = cache.get(keyword)
    if trattacache:
        return trattacache
        # logging.debug("Cerco la tratta %s - %s" % (da, a))
    tratta = Tratta.objects.filter(da=da, a=a)
    if tratta.count():
        result = tratta[0]  # trovata la tratta esatta
    else:
        tratta = Tratta.objects.filter(da=a, a=da)
        if tratta.count():
            result = tratta[0]  # trovata la tratta inversa
        else:
            tratta = Tratta(da=da, a=a)
            tratta.save()
            result = tratta
    cache.set(keyword, result)  # keep in cache
    return result


@python_2_unicode_compatible
class Viaggio(models.Model):
    """ Questa è una corsa, vecchia o nuova che sia.
        Tabella chiave di tutto. """
    # nell'inserimento chiedo inizialmente le basi
    data = models.DateTimeField("Data e ora", db_index=True)
    da = models.ForeignKey(Luogo, related_name="da")
    a = models.ForeignKey(Luogo, related_name="a")
    numero_passeggeri = models.IntegerField(default=1)
    # se non è consentito il raggruppamento contemporaneo
    esclusivo = models.BooleanField("Servizio taxi", default=True)

    cliente = models.ForeignKey("Cliente", null=True, blank=True,
                                db_index=True,
                                on_delete=PROTECT)  # se null è un privato

    # eventuale passeggero se cliente 'Privato'
    passeggero = models.ForeignKey("Passeggero", null=True, blank=True,
                                   on_delete=SET_NULL)

    prezzo = models.DecimalField(max_digits=9, decimal_places=2,
                                 default=0)  # fino a 9999.99
    costo_autostrada = models.DecimalField(max_digits=9, decimal_places=2,
                                           default=0)  # fino a 9999.99

    costo_sosta = models.DecimalField(
        # This is the total price of the stop (when the driver should wait before another
        # ride (with a constante rate per hour)
        max_digits=9, decimal_places=2,
        default=0)  # fino a 9999.99

    abbuono_fisso = models.DecimalField(max_digits=9, decimal_places=2,
                                        default=0)  # fino a 9999.99
    abbuono_percentuale = models.IntegerField(default=0)  # abbuono percentuale

    prezzo_sosta = models.DecimalField(
        # an additional fixed price that is added to the price (for the stop)
        # there's some automatic-thing that add it on stations/airports
        _('Prezzo sosta addizionale'),
        max_digits=9, decimal_places=2,
        default=0)
    additional_stop = models.IntegerField(
        # this will be manually added to tell that the ride will last something more
        # ... no prices are involved (they should be added to prezzo_sosta)
        _("Sosta addizionale (minuti)"),
        default=0,
    )

    # flag per indicare se la corsa è incassata dall'albergo
    #  (sarà utile per reportistica)
    incassato_albergo = models.BooleanField("Conto fine mese",
                                            default=False)

    fatturazione = models.BooleanField("Fatturazione richiesta", default=False)
    pagamento_differito = models.BooleanField("Fatturazione esente IVA",
                                              default=False)
    cartaDiCredito = models.BooleanField("Pagamento con carta di credito",
                                         default=False)
    commissione = models.DecimalField("Quota consorzio", max_digits=9,
                                      decimal_places=2,
                                      default=0)  # in euro o percentuale, a seconda del tipo
    tipo_commissione = models.CharField("Tipo di quota", max_length=1,
                                        choices=TIPICOMMISSIONE, default="F")
    numero_pratica = models.CharField(max_length=20, null=True, blank=True)

    # l'eventuale viaggio padre nei raggruppamenti
    padre = models.ForeignKey("Viaggio", null=True, blank=True)

    data_padre = models.DateTimeField("Data e ora padre", db_index=True,
                                      null=True, editable=False)
    id_padre = models.PositiveIntegerField("ID Gruppo", db_index=True,
                                           null=True, editable=False)

    # True quando il conducente è fissato
    conducente_richiesto = models.BooleanField("Escluso dai supplementari",
                                               default=False)

    # conducente (proposto o fissato)
    conducente = models.ForeignKey("Conducente", null=True, blank=True,
                                   db_index=True)

    # True quando il conducente è fissato
    conducente_confermato = models.BooleanField("Conducente confermato",
                                                default=False)

    note = models.TextField(blank=True)
    pagato = models.BooleanField(default=False)

    # Luogo to calculate stats, in instance, should be populated on creation
    luogoDiRiferimento = models.ForeignKey(Luogo, related_name="riferimento",
                                           null=True)

    # per i padri della abbinate conta quanti km di abbinata
    # sono già  stati conguagliati
    km_conguagliati = models.IntegerField("Km conguagliati", null=True,
                                          blank=True, default=0,
                                          editable=False)

    html_tragitto = models.TextField(blank=True, editable=False)
    tratta = models.ForeignKey(Tratta, null=True, blank=True, default=None,
                               editable=False)
    tratta_start = models.ForeignKey(Tratta, null=True, blank=True,
                                     related_name='viaggio_start_set',
                                     editable=False)
    tratta_end = models.ForeignKey(Tratta, null=True, blank=True,
                                   related_name='viaggio_end_set',
                                   editable=False)

    # tipo (null: non è abbinata, P: partenza, successiva altrimenti)
    is_abbinata = models.CharField(max_length=1, null=True, blank=True, editable=False)

    punti_notturni = models.DecimalField(max_digits=6, decimal_places=2, default=0, editable=False)
    punti_diurni = models.DecimalField(max_digits=6, decimal_places=2, default=0, editable=False)

    # numero di chilometri per la riga (le 3 tratte)
    km = models.IntegerField(default=0, editable=False)

    # tipo di viaggio True se è un arrivo
    arrivo = models.BooleanField(default=True, editable=False)

    # True se il viaggio ha tutte le tratte definite
    is_valid = models.BooleanField(default=True, editable=False)

    punti_abbinata = models.IntegerField(default=0, editable=False)
    prezzoPunti = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)

    prezzoVenezia = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
    prezzoPadova = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
    prezzoDoppioPadova = models.DecimalField(max_digits=9, decimal_places=2,
                                             editable=False, default=0)
    prezzo_finale = models.DecimalField(max_digits=9, decimal_places=2, editable=False, default=0)
    date_start = models.DateTimeField(editable=False,
                                      default=tamdates.date_enforce(
                                          datetime.datetime(2009, 1, 1, 0, 0, 0)),
                                      db_index=True)
    # la data finale, di tutto il gruppo di corse, per trovare intersezioni
    date_end = models.DateTimeField(editable=False, null=True, db_index=True)
    annullato = models.BooleanField('Corsa annullata', default=False,
                                    editable=True, db_index=True)

    # per non dover fare query quando visualizzo il viaggio,
    #  mi imposto che deriva da una prenotazione
    is_prenotazione = models.BooleanField('Derivato da prenotazione',
                                          default=False, editable=False)

    """ Nel listare i viaggi, mostro solo quelli padre,
        con sottolistati i loro eventuali viaggi figli """

    class Meta:
        verbose_name_plural = _("Viaggi")
        permissions = (('change_oldviaggio', 'Cambia vecchio viaggio'),
                       ('change_doppi', 'Cambia il numero di casette'))
        ordering = ("data_padre", "id_padre", "data", 'id')

    def url(self):
        return reverse("tamNuovaCorsaId", kwargs={"id": self.id})

    def __str__(self):
        result = u"%s da %s a %s." % (
            self.data.astimezone(tamdates.tz_italy).strftime("%d/%m/%Y %H:%M"),
            self.da, self.a)
        if self.cliente:
            result += u" Per %s:" % self.cliente
        else:
            result += u" Per privato:"
        result += u" %spax %s." % (
            self.numero_passeggeri,
            self.esclusivo and u"taxi" or u"collettivo")
        if self.conducente:
            result += u" Assegnato a %s." % self.conducente
        return result

    def descrizioneDivisioneClassifiche(self):
        """ Restituisco come il viaggio si divide nelle classifiche """
        return descrizioneDivisioneClassifiche(self)

    def classifiche(self):
        """
        A dictionary with the classifiche of this Viaggio
        @return: dict(str:Decimal)
        """
        return dict(
            sosta=self.prezzo_sosta,
            prezzoVenezia=self.prezzoVenezia,
            prezzoPadova=self.prezzoPadova,
            prezzoDoppioPadova=self.prezzoDoppioPadova,
            puntiAbbinata=self.punti_abbinata,
            puntiDiurni=self.punti_diurni,
            puntiNotturni=self.punti_notturni,
            prezzoPunti=self.prezzoPunti,
        )

    def updatePrecomp(self, doitOnFather=True, force_save=False,
                      forceDontSave=False, numDoppi=None):
        """ Aggiorna tutti i campi precalcolati del viaggio.
            Se il tragitto è cambiato e il viaggio era già salvato lo aggiorna
            Se il viaggio ha un padre ricorre sul padre.
            Se il viaggio ha figli ricorre sui figli.
            numDoppi se è diverso da None forza al numero di doppi indicato
            con forceDontSave indico l'id che sto già salvando, e che non c'è bisogno di risalvare anche se cambia
        """
        # print "updateprecomp:", self.id
        if doitOnFather and self.padre_id:
            # logging.debug("Ricorro al padre di %s: %s" % (self.pk, self.padre.pk))
            if force_save:
                self.save()
            self.padre.updatePrecomp(
                forceDontSave=forceDontSave)  # run update on father instead
            return
        changed = False

        # lista dei campi che vengono ricalcolati
        fields = [
            "html_tragitto",
            "prezzo_finale", "km",
            "prezzoVenezia", "prezzoPadova",
            "prezzoDoppioPadova",
            "punti_abbinata",
            "arrivo",
            "is_valid",
            "date_start",
            "date_end",
        ]

        oldValues = {}
        for field in fields:
            oldValues[field] = getattr(self, field)

        # le tratte come prima cosa, sono richieste da tutti
        self.tratta = self._tratta()
        self.tratta_start = self._tratta_start()
        self.tratta_end = self._tratta_end()
        self.date_start = self._date_start()  # richiede tratta_start
        self.date_end = self.get_date_end(recurse=True)  # date_end finale

        self.arrivo = self.is_arrivo()

        self.km = self.get_kmrow()  # richiede le tratte

        # costo della sosta 12€/h, richiede tratte, usa _isabbinata e nexbro
        self.costo_sosta = Decimal(self.sostaFinaleMinuti()) * 12 / 60

        self.is_abbinata = self._is_abbinata()
        self.is_valid = self._is_valid()  # richiede le tratte

        forzaSingolo = (numDoppi is 0)
        # richiede le tratte
        self.prezzo_finale = self.get_value(forzaSingolo=forzaSingolo)

        # Precalcolo i punti disturbo della corsa
        self.punti_diurni = self.punti_notturni = Decimal(0)
        self.prezzoPadova = self.prezzoVenezia = self.prezzoDoppioPadova = 0
        self.punti_abbinata = self.prezzoPunti = 0

        if self.id:  # itero sui figli
            for figlio in self.viaggio_set.all():
                figlio.updatePrecomp(doitOnFather=False, numDoppi=numDoppi,
                                     forceDontSave=forceDontSave)

        process_classifiche(viaggio=self, force_numDoppi=numDoppi)

        self.html_tragitto = self.get_html_tragitto()

        for field in fields:
            if oldValues[field] != getattr(self, field):
                changed = True
                break

        if (changed and self.id and not forceDontSave) or force_save:
            self.save()

    def get_classifica(self, classifiche=None, conducentiPerCapienza=None):
        # le tre liste con (conducente, stato)
        #  (conducenti sono ordinate per chiave generata dalla corsa)
        conducenti = []
        occupati = []
        fondo_classifica = []
        # print "getclassifica", self

        if classifiche is None:
            classifiche = get_classifiche()
        classid = {}
        for classifica in classifiche:  # metto le classifiche in un dizionario
            # id = classifica["conducente_id"]
            classid[classifica["conducente_id"]] = classifica

        # cache conducenti per capienza *************
        if self.numero_passeggeri in conducentiPerCapienza:
            conducentiConCapienza = conducentiPerCapienza[self.numero_passeggeri]
        else:
            # Metto in cache la lista dei clienti
            #  che possono portare almeno X persone
            conducentiConCapienza = Conducente.objects.filter(
                max_persone__gte=self.numero_passeggeri)
            conducentiPerCapienza[self.numero_passeggeri] = conducentiConCapienza
        # ***************************************************

        # {conducente.id: [list of caltoken (name, available, tags)]}
        c_byid = {}
        if 'calendariopresenze' in settings.INSTALLED_APPS:
            if self.date_end is None:
                print("date_end non dovrebbe essere mai null per il calcolo delle classifiche")
            else:
                calendarizzati = Calendar.objects.filter(
                    date_start__lt=self.date_end,
                    # I use the date-interval cross detection
                    date_end__gt=self.date_start,
                    # available=False,  # I'll consider calendar event even if the conducente is available
                )
                # creo un array che associa all'id del conducente,
                #  quello che sta facendo eventualmente durante questa corsa

                for calendario in calendarizzati:
                    cid = calendario.conducente.id
                    c_byid[cid] = c_byid.get(cid, []) + [(calendario.name,
                                                          calendario.available,
                                                          calendario.tags)]
                viaggi_contemporanei = Viaggio.objects.filter(
                    padre_id=None,  # I figli non hanno date_end
                    date_start__lt=self.date_end,
                    # I use the date-interval cross detection
                    date_end__gt=self.date_start,
                    conducente_confermato=True,
                )
                for viaggio in viaggi_contemporanei:
                    cid = viaggio.conducente.id
                    # name, available, tags
                    c_byid[cid] = c_byid.get(cid, []) + [('in viaggio', False,
                                                          "cal_travel")]

        # listo i conducenti attivi che parteciperanno
        for conducente in conducentiConCapienza:
            if conducente.attivo is False:
                fondo_classifica.append(
                    (conducente, '*inattivo*', False, 'cal_inactive'))
                continue
            if conducente.id in c_byid:
                cal = c_byid[conducente.id]
                # disponibile solo se tutti gli appuntamenti sono disponibili
                available = all([c[1] for c in
                                 cal])
                if not available:
                    occupati.append((conducente,
                                     ", ".join(c[0] for c in cal),  # names
                                     available,
                                     " ".join(c[2] for c in cal))  # tags
                                    )
                    continue
                    # se ho appuntamenti ma sono disponibile continuo
                    # (e inserisco in classifica conducenti)
            else:
                # un conducente disponibile non ha impegni
                available = True
                cal = []
            # if conducente.assente

            chiave = []

            keys = []  # da priorità alle classifiche così come nei settings
            for desc_classifica in settings.CLASSIFICHE:
                punti_viaggio = getattr(self, desc_classifica['viaggio_field'])
                if punti_viaggio:
                    ignore_if_field = desc_classifica.get('ignore_if_field',
                                                          None)
                    if ignore_if_field is not None and getattr(self,
                                                               ignore_if_field):
                        # print "ho punti in %s, salto %s" %
                        #  (ignore_if_field, desc_classifica['mapping_field'])
                        continue
                    chiave.append(classid[conducente.id][
                                      desc_classifica['mapping_field']])
                    keys.append(desc_classifica['mapping_field'])

            chiave.append(
                conducente.nick)  # nei pari-meriti metto i nick in ordine

            conducenti.append((chiave, conducente,
                               ", ".join(c[0] for c in cal),  # names
                               available,
                               " ".join(c[2] for c in cal))  # tags
                              )
        conducenti.sort()
        return itertools.chain([c[1:] for c in conducenti], occupati,
                               fondo_classifica)

    def get_html_tragitto(self):
        """ Ritorna il tragitto da template togliendogli tutti gli spazi """
        tragitto = render_to_string('corse/dettagli_viaggio.inc.html',
                                    {"viaggio": self,
                                     "STATIC_URL": settings.STATIC_URL})
        tragitto = reallySpaceless(tragitto)
        return tragitto

    def save(self, *args, **kwargs):
        """Ridefinisco il salvataggio dei VIAGGI
            per popolarmi i campi calcolati"""
        assert self.luogoDiRiferimento is not None, "Missing reference place"
        if 'updateViaggi' in kwargs:
            updateViaggi = kwargs['updateViaggi']
            del (kwargs['updateViaggi'])
        else:
            updateViaggi = True
        if not updateViaggi:
            return super(Viaggio, self).save(*args, **kwargs)

        # quando confermo o richiedo un conducente DEVO avere un conducente
        if not self.conducente:
            self.conducente_confermato = False
            self.conducente_richiesto = False
        # il conducente richiesto rende automaticamente il viaggio confermato
        if self.conducente_richiesto:
            self.conducente_confermato = True
        if not self.conducente_confermato:
            self.conducente = None
        if self.cliente:
            self.passeggero = None

        # inserisco data e ID del gruppo per gli ordinamenti
        self.id_padre = self.padre_id if self.padre_id is not None else self.id
        self.data_padre = self.padre.data if self.padre_id is not None else self.data

        logging.debug("Update di *%s*." % self.pk)
        # invalidate_template_cache("viaggio", self.id)
        super(Viaggio, self).save(*args, **kwargs)
        for figlio in self.viaggio_set.all():  # i figli ereditano dal padre
            changed = False
            # tutti i figli hanno un solo padre, nessuna ricorsione
            if self.padre_id:
                figlio.padre = self.padre
                changed = True
            # il conducente è sempre quello del padre...
            if figlio.conducente != self.conducente:
                figlio.conducente = self.conducente
                changed = True
            # ... e così la conferma
            if figlio.conducente_confermato != self.conducente_confermato:
                figlio.conducente_confermato = self.conducente_confermato
                changed = True
            if changed:
                logging.debug("Update -> *%s*." % figlio.pk)
                figlio.save(*args, **kwargs)

    def delete_url(self):
        return reverse("tamCorsaIdDel", kwargs={"id": self.id})

    def is_arrivo(self):
        """ Return True if travel is an ARRIVO referring to luogo """
        # logging.debug("is_arrivo")
        luogo = self.luogoDiRiferimento
        if not luogo:
            return False  # non ho un riferimento
        # aggiungo un tag ad ogni viaggio a seconda se è un arrivo o meno
        bacinoPredefinito = luogo.bacino

        if bacinoPredefinito:  # vengo da una zona
            # mi muovo solo se sono fuori dalla zona
            return bacinoPredefinito != self.da.bacino
        else:  # vengo da un posto (non da una zona)
            # mi muovo se il posto è diverso
            return luogo != self.da

    def _get_prefratello(self):
        """ Per i figli restituisco il fratello precedente (o il padre) """
        # logging.debug("Trovo il pre fratello per %s"%self.id)
        if self.padre_id is None:
            return
        lastbro = self.padre
        for fratello in self.padre.viaggio_set.all():
            if fratello == self:
                break
            lastbro = fratello
        return lastbro

    prefratello = property(_get_prefratello)

    def nextfratello(self):
        """ Per le abbinate restituisco il prossimo fratello
            (Niente se è l'ultimo) """
        # print "Trovo il next fratello per %d" % self.id
        if self.padre_id is None:
            if not self._is_abbinata(simpleOne=True):
                # self.nextfratello = None
                return  # per i singoli ritorno None
            else:
                padre = self
        else:
            padre = self.padre
        lastbro = padre
        for fratello in padre.viaggio_set.all():
            if lastbro == self:
                return fratello
            lastbro = fratello

    def lastfratello(self):
        """ Restituisco l'ultimo viaggio del gruppo """
        logging.debug("Trovo l'ultimo fratello per %s" % self.id)
        lastone = self
        if self.padre_id:  # vado al padre
            lastone = self.padre
        if lastone.viaggio_set.count() > 0:  # e scendo all'ultimo figlio
            lastone = list(lastone.viaggio_set.all())[-1]
        return lastone

    def _tratta_start(self):
        """ Restituisce la tratta dal luogo di riferimento
            all'inizio della corsa """
        # logging.debug("Trovo la tratta start %s" % self.id)
        # per singoli o padri parto dal luogo di riferimento
        if self.padre_id is None:
            luogoDa = self.luogoDiRiferimento
            if luogoDa != self.da:
                return get_tratta(luogoDa, self.da)

    def _tratta(self):
        """ Normalmente è la tratta vera e propria, ma per le associazioni
            potrebbe essere una tratta intermedia, o addirittura essere nulla
        """
        # logging.debug("Trovo la tratta middle %s" % self.id)
        if self._is_abbinata() == "P":
            return None
        else:
            return get_tratta(self.da, self.a)

    def _tratta_end(self):
        """ Restituisce la tratta dalla fine della corsa
            al luogo di riferimento
        """
        # logging.debug("Trovo la tratta end %s" % self.id)
        nextbro = self.nextfratello()
        if not nextbro:  # non ho successivi, riporto al luogoDiRiferimento
            da = self.a
            a = self.luogoDiRiferimento
        else:
            if self._is_abbinata() == "P":
                # sono un collettivo partenza:
                #  la tratta=None quindi vado dal mio iniziale
                #  all'iniziale prossimo
                da = self.da
                a = nextbro.da
            else:
                da = self.a
                a = nextbro.da
        if da != a:
            return get_tratta(da, a)

    def sostaFinale(self):
        """ Return a timedelta with the time between the time of the end of the ride
        and the beginning of the return or the next brother
        """
        result = datetime.timedelta()
        nextbro = self.nextfratello()
        this_end = self.get_date_end()

        # if self.additional_stop:
        #     manual_stop = datetime.timedelta(minutes=self.additional_stop)
        #     result += manual_stop
        #     this_end += manual_stop
        if nextbro:
            if nextbro.data > this_end:
                result += (nextbro.data - this_end)
        return result

    def sostaFinaleMinuti(self):
        sosta = self.sostaFinale()
        minutes = 0
        if sosta and sosta.seconds > 60:
            minutes += int(sosta.seconds / 60)
        return minutes

    def _date_start(self):
        """ Return the time to start to be there in time, looking Tratte
            if the start place is the same time is the time of the travel
        """
        tratta_start = self.tratta_start
        anticipo = 0
        if tratta_start and tratta_start.is_valid():  # tratta iniziale
            anticipo += tratta_start.minuti
        if anticipo:
            return self.data - datetime.timedelta(minutes=anticipo)
        else:
            return self.data

    def get_date_end(self, recurse=False):
        """ Ritorno il tempo finale di tutta la corsa
            (compresi eventuali figli se recurse) """
        # logging.debug("Data finale di %s. Recurse:%s"%(self.id, recurse))
        # se devo ancora salvare non cerco figli
        if not recurse or not self.id:
            ultimaCorsa = self  # trovo il tempo finale solo di me stesso
        else:
            # trovo il tempo finale dell'ULTIMA corsa
            ultimaCorsa = self.lastfratello()

        tratta = ultimaCorsa.tratta
        tratta_end = ultimaCorsa.tratta_end
        end_time = ultimaCorsa.data

        # logging.debug("Partiamo da %s"%end_time)

        # quando parto da un aeroporto la corsa dura 30 minuti di più
        # non quando sono in sosta, arrivato in un aereoporto,
        # in modo che i 30 minuti in più siano alla ripartenza
        if ultimaCorsa.da.speciale == 'A' and tratta:
            end_time += datetime.timedelta(minutes=30)

        if self.additional_stop:
            end_time += datetime.timedelta(minutes=self.additional_stop)

        if tratta and tratta.is_valid():  # add the runtime of this tratta
            # logging.debug("Aggiungo %s per la tratta %s" %(tratta.minuti, tratta))
            end_time += datetime.timedelta(minutes=tratta.minuti)
        if tratta_end and tratta_end.is_valid():
            # logging.debug("Aggiungo %s per la tratta %s" %(tratta_end.minuti, tratta_end))
            end_time += datetime.timedelta(minutes=tratta_end.minuti)
            # logging.debug("Tempo finale: %s "%end_time)
        return end_time

    def trattaInNotturna(self):
        """ Restituisce True se la sola tratta considerata (non i figli e non le pre_tratte post_tratte
         sono in fascia [22-6) """
        start = self.data
        tratta = self._tratta()
        if tratta:
            end = self.data + datetime.timedelta(minutes=tratta.minuti)
        else:
            end = self.data
        inizioNotte = start.replace(hour=22, minute=0)
        if start.hour < 6: inizioNotte -= datetime.timedelta(days=1)
        fineNotte = end.replace(hour=6, minute=0)
        if fineNotte < inizioNotte: fineNotte += datetime.timedelta(days=1)
        result = False
        if start <= inizioNotte and end >= inizioNotte: result = True
        if start < fineNotte and end >= fineNotte: result = True
        if start >= inizioNotte and end <= fineNotte: result = True
        return result

    def disturbi(self, date_start=None, date_end=None):
        """ Restituisce un dizionario di "codiceFascia":punti con le fasce e i punti disturbo relativi.
            Ho due fasce mattutine 4-6, 6-7:45 di due e un punto
            due fasce serali 20-22:30, 22:30-4
            a due a due hanno lo stesso codice prefissato con la data in cui la fascia comincia
            Il disturbo finale per una fascia è il massimo del valore di tutte le se sottofascie componenti
        """
        if self.conducente_richiesto:
            return {}
        if self.date_start < tamdates.date_enforce(
            datetime.datetime(2012, 3, 1)):
            metodo = fasce_uno_due
        else:
            metodo = getattr(settings, "METODO_FASCE", fasce_semilineari)
        return trovaDisturbi(self.date_start, self.get_date_end(recurse=True),
                             metodo=metodo)

    def get_kmrow(self):
        """ Restituisce il N° di KM totali di corsa con andata, corsa e ritorno """
        tratta_start = self._tratta_start()
        tratta = self._tratta()
        tratta_end = self._tratta_end()
        result = 0
        if tratta_start: result += tratta_start.km
        if tratta: result += tratta.km
        if tratta_end: result += tratta_end.km
        return result

    def get_kmtot(self):
        """ Restituisce il N° di KM totali di corsa con andata, corsa, figli e ritorno """
        result = self.get_kmrow()
        if self.id is None: return result
        for figlio in self.viaggio_set.all():
            result += figlio.get_kmrow()
        return result

    def _is_collettivoInPartenza(self):
        """	Vero se questo viaggio va dalla partenza alla partenza del fratello successivo.
            Assieme si andrà  ad una destinazione comune
        """
        # logging.debug("Is collettivo in partenza %s" %self.id)
        nextbro = self.nextfratello()
        if nextbro and nextbro.da == self.a:
            # se il successivo parte da dove arrivo è sicuramente un collettivo in successione
            return False
        if nextbro and nextbro.data < \
                self.data + datetime.timedelta(
                minutes=get_tratta(self.da, self.a).minuti + (
                    30 if self.da.speciale == "A" else 0)):
            # tengo conto che questa corsa dura 30 minuti in più se parte da un aereoporto
            # logging.debug("%s e' prima delle %s" % (nextbro.id, self.data+datetime.timedelta(minutes=get_tratta(self.da, self.a).minuti*0.5)) )
            return True
        else:
            return False

    def _is_abbinata(self, simpleOne=False):
        """ True se la corsa un'abbinata (padre o figlio)
            se simpleOne==False controllo anche le differenze
            tra abbinata in Successione e abbinata in Partenza
        """
        # print("Abbinata? %s" % self.id)
        if self.id is None:
            # prima di salvare non sono un'abbinata (viaggio_set.count() mi darebbe tutte le corse
            return False if simpleOne else None
        if self.padre_id or self.viaggio_set.count() > 0:
            if simpleOne: return True
            if self._is_collettivoInPartenza():
                return "P"  # collettivo in partenza
            else:
                return "S"  # abbinata
        else:
            return ""  # non abbinata

    def is_long(self):
        """ Ritorna vero se la tratta, andando e tornando è lunga """
        return self.km >= getattr(settings, 'KM_PER_LUNGHE', 50)

    def is_medium(self):
        """ Ritorna vero se la tratta è media """
        return 25 <= self.km < getattr(settings, 'KM_PER_LUNGHE', 50) or (
            self.km < 25 and self.prezzo > 16)

    def _is_valid(self):
        """Controlla che il viaggio abbia tutte le tratte definite"""
        tratta_start = self.tratta_start
        tratta = self.tratta
        tratta_end = self.tratta_end
        if (tratta_start is None or tratta_start.is_valid()) and (
                    tratta is None or tratta.is_valid()) and (
                    tratta_end is None or tratta_end.is_valid()):
            return True
        else:
            return False

    def vecchioConfermato(self):
        return self.conducente_confermato and self.date_start < tamdates.ita_now().replace(
            hour=0, minute=0)

    def prezzo_commissione(self):
        """ Restituisce il valore in euro della commissione """
        if not self.commissione:
            return 0
        else:
            if self.tipo_commissione == "P":
                return self.prezzo * (
                    self.commissione / Decimal(
                        100))  # commissione in percentuale
            else:
                return self.commissione

    def get_value(self, **kwargs):
        """ Return the value of this trip on the scoreboard """
        return process_value(self, **kwargs)

    def get_valuetot(self, **kwargs):
        result = self.get_value(**kwargs)
        for figlio in self.viaggio_set.all():
            result += figlio.get_value(**kwargs)
        return result

    def lordo(self):
        """ Il lordo vero e proprio """
        result = self.prezzo
        for figlio in self.viaggio_set.all():
            result += figlio.prezzo
        return result

    def get_lordotot(self):
        """ Restituisce il lordo, tolto di autostrada e commissione """
        result = self.prezzo - self.costo_autostrada - self.prezzo_commissione()
        # logging.debug("Corsa padre: %s" % result )
        for figlio in self.viaggio_set.all():
            # logging.debug("	 figlio: %s" % (figlio.prezzo - figlio.costo_autostrada - figlio.prezzo_commissione()))
            result += figlio.prezzo - figlio.costo_autostrada - figlio.prezzo_commissione()
        return result

    def costo_autostrada_default(self):
        """ Restituisce il costo totale dell'autostrada, in modo da suggerirlo """
        # print "Ricalcolo autostrada per %d" % self.pk    #TMP:
        tratta_start = self._tratta_start()
        tratta = self._tratta()
        tratta_end = self._tratta_end()
        result = 0
        if tratta_start:
            # print tratta_start.da, tratta_start.a
            result += tratta_start.costo_autostrada
        if tratta:
            # print tratta.da, tratta.a
            result += tratta.costo_autostrada
        if tratta_end:
            # print tratta_end.da, tratta_end.a
            result += tratta_end.costo_autostrada
        return result

    def confirmed(self):
        """ True se il conducente è confermato... nel qual caso poi lo conto in classifica """
        return self.conducente_confermato

    def warning(self):
        """ True se la corsa va evidenziata perché non ancora confermata se manca poco alla partenza """
        return (not self.conducente_confermato
                and (self.date_start - datetime.timedelta(
            hours=2) < tamdates.ita_now())
                )

    def punti_notturni_interi_list(self):
        return range(int(self.punti_notturni))

    def punti_notturni_quarti(self):
        """ Restituisce la parte frazionaria dei notturni """
        return self.punti_notturni % 1

    def punti_diurni_interi_list(self):
        return range(int(self.punti_diurni))

    def punti_diurni_quarti(self):
        """ Restituisce la parte frazionaria dei notturni """
        return self.punti_diurni % 1

    def incidenza_prezzo_sosta(self):
        """ Stringa che aggiungo alla descrizione dei prezzi per indicare che la sosta viene scontata """
        if settings.SCONTO_SOSTA:
            return "al %d%%" % (100 - settings.SCONTO_SOSTA)
        else:
            return ""

    def incidenza_differto(self):
        """ Stringa che aggiungo alla descrizione dei prezzi per indicare che il prezzo viene scontato perché differto """
        if settings.SCONTO_FATTURATE:
            return "- p%d%%" % settings.SCONTO_FATTURATE
        else:
            return ""

    def prezzo_netto(self, iva=10):
        if PREZZO_VIAGGIO_NETTO:
            return self.prezzo
        else:
            return self.prezzo * 100 / (100 + iva)


@python_2_unicode_compatible
class Conducente(models.Model):
    """ I conducuenti, ogni conducente avrà la propria classifica, ed una propria vettura.
        Ogni conducente può essere in servizio o meno.
    """
    nome = models.CharField("Nome", max_length=40, unique=True)
    dati = models.TextField(null=True, blank=True,
                            help_text='Stampati nelle fattura conducente')
    nick = models.CharField("Sigla", max_length=5, blank=True, null=True)
    max_persone = models.IntegerField(default=4)
    attivo = models.BooleanField(default=True, db_index=True)
    emette_ricevute = models.BooleanField("Emette senza IVA?",
                                          help_text="Il conducente può emettere fatture senza IVA?",
                                          default=True)
    has_bus = models.BooleanField("Ha un bus?",
                                  editable=False,
                                  default=False)
    assente = models.BooleanField(default=False)

    classifica_iniziale_diurni = models.DecimalField("Supplementari diurni",
                                                     max_digits=12,
                                                     decimal_places=2,
                                                     default=0)
    classifica_iniziale_notturni = models.DecimalField(
        "Supplementari notturni", max_digits=12, decimal_places=2,
        default=0)

    classifica_iniziale_puntiDoppiVenezia = models.IntegerField(
        "Punti Doppi Venezia", default=0)
    classifica_iniziale_prezzoDoppiVenezia = models.DecimalField(
        "Valore Doppi Venezia", max_digits=12,
        decimal_places=2, default=0)  # fino a 9999.99
    classifica_iniziale_doppiPadova = models.DecimalField("Doppi Padova",
                                                          max_digits=12,
                                                          decimal_places=2,
                                                          default=0)  # fino a 9999.99

    classifica_iniziale_long = models.DecimalField("Venezia", max_digits=12,
                                                   decimal_places=2,
                                                   default=0)  # fino a 9999.99
    classifica_iniziale_medium = models.DecimalField("Padova", max_digits=12,
                                                     decimal_places=2,
                                                     default=0)  # fino a 9999.99

    class Meta:
        verbose_name_plural = _("Conducenti")
        ordering = ["-attivo", "nick", "nome"]
        permissions = (
            ('change_classifiche_iniziali', 'Cambia classifiche iniziali'),)

    def save(self, *args, **kwargs):
        # global cache_conducentiPerPersona
        # cache_conducentiPerPersona = {}	# cancello la cache dei conducenti con capienza
        cache.delete('conducentiPerPersona')
        super(Conducente, self).save(*args, **kwargs)

    def __str__(self):
        if self.nick:
            return self.nick
        else:
            return self.nome

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        if self.nick and other.nick:
            return self.nick < other.nick
        else:
            return self.nome < other.nome

    def delete_url(self):
        return reverse("tamConducenteIdDel", kwargs={"id": self.id})

    def url(self):
        return reverse("tamConducenteId", kwargs={"id": self.id})

    def ricevute(self):
        """ Ritorno le ricevute emesse da questo conducente """
        from fatturazione.models import Fattura

        ricevute = Fattura.objects.filter(tipo='3', righe__conducente=self)
        return ricevute.distinct()


@python_2_unicode_compatible
class Cliente(models.Model):
    """ Ogni cliente ha le sue caratteristiche, ed eventualmente un suo listino """
    nome = models.CharField("Nome cliente", max_length=40, unique=True)
    dati = models.TextField(null=True, blank=True,
                            help_text='Stampati nelle fattura conducente')
    tipo = models.CharField("Tipo cliente", max_length=1, choices=TIPICLIENTE)
    fatturazione = models.BooleanField("Fatturazione richiesta", default=False)
    pagamento_differito = models.BooleanField("Fatturazione esente IVA",
                                              default=False)
    incassato_albergo = models.BooleanField("Conto fine mese", default=False)
    listino = models.ForeignKey("Listino", verbose_name="Listino cliente",
                                null=True, blank=True)
    commissione = models.DecimalField("Quota consorzio", max_digits=9,
                                      decimal_places=2,
                                      default=0)  # in euro o percentuale, a seconda del tipo
    tipo_commissione = models.CharField("Tipo di quota", max_length=1,
                                        choices=TIPICOMMISSIONE, default="F")
    attivo = models.BooleanField(default=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = _("Clienti")
        ordering = ["nome"]

    def __str__(self):
        if self.nome.strip():
            result = self.nome
        else:
            result = "(nessun nome)"
        if not self.attivo:
            result += "(inattivo)"
        return result

    def url(self):
        return reverse("tamClienteId", kwargs={"id_cliente": self.id})

    def save(self, *args, **kwargs):
        if self.nome.lower() == "privato":
            raise Exception(
                "Scusa ma non puoi chiamarlo PRIVATO... è un nome riservato")
        super(Cliente, self).save(*args, **kwargs)


@python_2_unicode_compatible
class Passeggero(models.Model):
    """ I passeggeri sono clienti particolari con meno caratteristiche """
    nome = models.CharField(max_length=40, unique=True)
    dati = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = _("Passeggeri")
        ordering = ["nome"]
        permissions = (
            ('fastinsert_passenger', 'Inserimento passeggero veloce'),)

    def __str__(self):
        return self.nome

    def delete_url(self):
        return reverse("tamPrivatoIdDel", kwargs={"id": self.id})

    def url(self):
        return reverse("tamPrivatoId", kwargs={"id": self.id})


@python_2_unicode_compatible
class Listino(models.Model):
    """ Ogni listino ha un suo nome ed una serie di tratte collegate.
        È indipendente dal cliente.
    """
    nome = models.CharField(max_length=30, unique=True)

    class Meta:
        verbose_name_plural = _("Listini")
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    def get_prezzo(self, da, a, tipo_servizio="T", pax=3, tryReverse=True):
        """ Cerca il prezzo del listino DA-A o A-DA, e restituisce None se non esiste """
        prezziDiretti = self.prezzolistino_set.filter(tratta__da=da,
                                                      tratta__a=a,
                                                      max_pax__gte=pax,
                                                      tipo_servizio=tipo_servizio)
        choosenResult = None  # scelgo il prezzo adeguato con meno passeggeri max
        for prezzoPossibile in prezziDiretti:
            if choosenResult:
                if prezzoPossibile.max_pax < choosenResult.max_pax: choosenResult = prezzoPossibile
            else:
                choosenResult = prezzoPossibile
        if choosenResult: return choosenResult
        if tryReverse:
            return self.get_prezzo(a, da, tipo_servizio, pax,
                                   tryReverse=False)  # provo a tornare il prezzo inverso


@python_2_unicode_compatible
class PrezzoListino(models.Model):
    """ Ogni tratta del listino ha due prezzi, una per la fascia diurna e una per la fascia notturna """
    listino = models.ForeignKey(Listino)
    tratta = models.ForeignKey(Tratta)
    prezzo_diurno = models.DecimalField(max_digits=9, decimal_places=2,
                                        default=10)  # fino a 9999.99
    prezzo_notturno = models.DecimalField(max_digits=9, decimal_places=2,
                                          default=10)  # fino a 9999.99

    commissione = models.DecimalField("Quota consorzio", max_digits=9,
                                      decimal_places=2, null=True,
                                      default=0)  # in euro o percentuale, a seconda del tipo
    tipo_commissione = models.CharField("Tipo di quota", max_length=1,
                                        choices=TIPICOMMISSIONE, default="F")
    ultima_modifica = models.DateField(auto_now=True)

    tipo_servizio = models.CharField(choices=TIPISERVIZIO, max_length=1,
                                     default="T")  # Collettivo o Taxi
    max_pax = models.IntegerField("Pax Massimi", default=4)

    flag_fatturazione = models.CharField("Fatturazione forzata",
                                         max_length=1,
                                         choices=[
                                             ('S', 'Fatturazione richiesta'),
                                             ('N',
                                              'Fatturazione non richiesta'),
                                             ('-',
                                              'Usa impostazioni del cliente'),
                                         ],
                                         default='-',
                                         blank=False, null=False,
                                         )

    class Meta:
        verbose_name_plural = _("Prezzi Listino")
        unique_together = (("listino", "tratta", "tipo_servizio", "max_pax"),)
        ordering = ["tipo_servizio", "max_pax"]

        # order_with_respect_to="tratta"

    def stringa_dettaglio(self):
        if self.tipo_servizio == "C":
            return "collettivo fino a %d pax" % self.max_pax
        else:
            return "taxi fino a %d pax" % self.max_pax

    def __str__(self):
        result = u"%s. Da %s a %s. %s [%s] " % (
            self.listino, self.tratta.da, self.tratta.a, self.prezzo_diurno,
            self.prezzo_notturno)
        if self.commissione:
            if self.tipo_commissione == "P":
                result += u"con quota del %d%% " % self.commissione
            else:
                result += u"con quota di %d€ " % self.commissione
        result += self.stringa_dettaglio()
        return result


@python_2_unicode_compatible
class ProfiloUtente(models.Model):
    user = models.OneToOneField(User, unique=True, editable=False)
    luogo = models.ForeignKey(Luogo, verbose_name="Luogo di partenza", null=True, blank=True)

    class Meta:
        permissions = (('can_backup', 'Richiede un backup'),
                       ('get_backup', 'Scarica un backup'),
                       ('reset_sessions', _('Can reset session')),
                       )
        verbose_name_plural = _("Profili utente")

    def __str__(self):
        return "%s" % self.user


@python_2_unicode_compatible
class Conguaglio(models.Model):
    """ Memorizza tutti i conguagli effettuati tra i conducenti """
    data = models.DateTimeField(auto_now=True)
    conducente = models.ForeignKey(Conducente)
    dare = models.DecimalField(max_digits=9, decimal_places=2,
                               default=10)  # fino a 9999.99

    class Meta:
        verbose_name_plural = _("Conguagli")

    def __str__(self):
        return "%s, %s: %s" % (self.data, self.conducente, self.dare)


# Comincia a loggare i cambiamenti a questi Modelli
from modellog.actions import startLog, stopLog

models_to_log = (Viaggio, Cliente, Passeggero,
                 Conducente, Tratta, PrezzoListino)


def startAllLog():
    for Model in models_to_log:
        startLog(Model)


def stopAllLog():
    for Model in models_to_log:
        stopLog(Model)


startAllLog()

# l'import di classifiche deve stare in fondo per evitare loop di importazione
from tam.views.classifiche import descrizioneDivisioneClassifiche

process_classifiche = settings.PROCESS_CLASSIFICHE_FUNCTION
process_value = settings.GET_VALUE_FUNCTION

PREZZO_VIAGGIO_NETTO = getattr(settings, 'PREZZO_VIAGGIO_NETTO', True)


# load models required for the tasks
# from tam.tasks import TaskBackup, TaskArchive  # @UnusedImport


class UnSerializableFileSystemStorage(FileSystemStorage):
    def deconstruct(self):
        return ("tam.models.UnSerializableFileSystemStorage", [], {})
