# coding: utf-8
""" Definizione per classi dei vari tipi di fatturazione """

from django.db.models.query_utils import Q

from fatturazione.models import RigaFattura
from fatturazione.views.util import ultimoProgressivoFattura
from tam.models import Viaggio


class ModelloFattura(object):
    ask_progressivo = False
    generabile = True
    order_by = []
    codice = None

    @classmethod
    def urlname_generazione(cls):
        """Restituisce il nome dell'url che rimanda alla generazione di queste fatture"""
        return "tamFatGenerazione%s" % cls.codice

    @classmethod
    def urlname_manuale(cls):
        """Restituisce il nome dell'url che rimanda alla generazione manuale di una fattura"""
        return "tamFatManuale%s" % cls.codice

    @staticmethod
    def update_context(data_start, data_end):
        result = {}
        result["data_generazione"] = data_end
        return result

        # esente_iva può essere True o False o un callable con parametro l'oggetto origine


class FattureConsorzio(ModelloFattura):
    # Fatture consorzio: tutte le corse fatturabili, non fatturate con conducente confermato

    nome = "Fatture Consorzio"
    descrizione = """Le fatture che il consorzio fa ai clienti.
					 Dai viaggi confermati con il flag della fatturazione richiesta."""
    codice = "1"
    origine = Viaggio
    filtro = Q(fatturazione=True, conducente__isnull=False, riga_fattura=None) & ~(
        Q(conducente__nick__istartswith="ANNUL") | Q(annullato=True)
    )  # tolgo le corse assegnate al conducente annullato
    keys = ["cliente"]  # come dividere una fattura dall'altra
    order_by = ["cliente", "data"]  # ordinamento per generazione
    order_on_view = ["anno", "progressivo"]  # ordinamento in visualizzazione
    url_generazione = r"^genera/consorzio/$"  # ci si aggiunge $ per la generazione "manuale/" per la creazione
    ask_progressivo = True
    template_scelta = "1.perCliente.html"
    template_generazione = "2.perCliente.html"
    template_visualizzazione = "5.perCliente.html"
    codice_fattura = "FC"
    destinatario = "cliente"
    mittente = "consorzio"
    note = (
        "Segue fattura elettronica\nPagamento: Bonifico bancario 30 giorni data fattura"
    )
    esente_iva = False

    @staticmethod
    def update_context(data_start, data_end):
        result = ModelloFattura.update_context(data_start, data_end)
        result["anno_consorzio"] = data_end.year
        result["progressivo"] = (
            ultimoProgressivoFattura(result["anno_consorzio"], "1") + 1
        )  # ultimo progressivo '1'
        return result


class FattureNoIVA(ModelloFattura):
    # Fatture consorzio: tutte le corse fatturabili, non fatturate con conducente confermato
    #   con pagamento differito

    nome = "Fatture esenti IVA"
    descrizione = """Le fatture che i consorziati fanno ai clienti, ma esentate IVA (ex ricevute).
					 Per i soli viaggi con il flag "Fatturazione esente IVA"
				  """
    codice = "4"
    origine = Viaggio
    filtro = Q(
        pagamento_differito=True,
        fatturazione=False,
        conducente__isnull=False,
        riga_fattura=None,
    ) & ~(Q(conducente__nick__istartswith="ANNUL") | Q(annullato=True))
    keys = ["cliente", "passeggero"]  # come dividere una fattura dall'altra
    order_by = ["cliente", "data"]  # ordinamento per generazione
    order_on_view = ["anno", "progressivo"]  # ordinamento in visualizzazione
    url_generazione = r"^genera/esentiIVA/$"  # ci si aggiunge $ per la generazione "manuale/" per la creazione
    ask_progressivo = True
    template_scelta = "1.perCliente.html"
    template_generazione = "2.perCliente.html"
    template_visualizzazione = "5.perCliente.html"
    codice_fattura = "FE"
    destinatario = "cliente"
    mittente = "consorzio"
    note = (
        "Segue fattura elettronica\n"
        "Pagamento: Bonifico bancario 30 giorni data fattura"
        + "\nServizio trasporto emodializzato da Sua abitazione al centro emodialisi assistito e viceversa come da distinta."
    )
    esente_iva = True

    @staticmethod
    def update_context(data_start, data_end):
        result = ModelloFattura.update_context(data_start, data_end)
        result["anno_consorzio"] = data_end.year
        result["progressivo"] = (
            ultimoProgressivoFattura(result["anno_consorzio"], "4") + 1
        )  # ultimo progressivo '4'
        return result


class FattureConducente(ModelloFattura):
    # Fatture conducente: tutte le fatture consorzio senza una fattura_conducente_collegata

    nome = "Fatture Conducente"
    descrizione = """Le fatture che il conducente fa al consorzio.
					 Generate dalle fatture consorzio."""
    codice = "2"
    origine = RigaFattura
    filtro = Q(fattura__tipo="1", fattura_conducente_collegata=None) & ~Q(
        conducente__nick__istartswith="ANNUL"
    )
    keys = ["conducente"]  # come dividere una fattura dall'altra
    order_by = ["conducente", "viaggio__data", "viaggio__cliente"]  # ordinamento
    url_generazione = r"^genera/conducente/$"  # ci si aggiunge $ per la generazione "manuale/" per la creazione
    template_scelta = "1.perConducente.html"
    template_generazione = "2.perConducente.html"
    template_visualizzazione = "5.perConducente.html"
    destinatario = "consorzio"
    mittente = "conducente"
    esente_iva = False


class FattureConducenteNoIva(ModelloFattura):
    # Fatture conducente: tutte le fatture consorzio senza una fattura_conducente_collegata

    nome = "Fatture Conducente esenti IVA"
    descrizione = """Le fatture che il conducente fa al consorzio.
					 Generate dalle fatture consorzio esenti IVA."""
    codice = "5"
    origine = RigaFattura
    filtro = Q(fattura__tipo="4", fattura_conducente_collegata=None) & ~Q(
        conducente__nick__istartswith="ANNUL"
    )
    keys = ["conducente"]  # come dividere una fattura dall'altra
    order_by = [
        "conducente",
        "fattura__data",
        "viaggio__data",
        "viaggio__cliente",
    ]  # ordinamento
    url_generazione = r"^genera/conducenteNoIVA/$"  # ci si aggiunge $ per la generazione "manuale/" per la creazione
    template_scelta = "1.perConducente.html"
    template_generazione = "2.perConducente.html"
    template_visualizzazione = "5.perConducente.html"
    destinatario = "consorzio"
    mittente = "conducente"

    @staticmethod
    def esente_iva(source):
        if source.conducente.emette_ricevute:
            return True
        else:
            return False

    iva_forzata = 10  # quando non è esente_iva, imposto l'iva a 10


class FattureConducenteNoIvaSenzaFiltri(FattureConducenteNoIva):
    filtro = Q(fattura__tipo__in=("1", "4"), fattura_conducente_collegata=None)


class Ricevute(ModelloFattura):
    """Le ricevute, ora non più generabili
    producevano una ricevuta divisa a livello di PDF da consorzio a cliente, e da conducente a consorzio
    """

    nome = "Ricevute"
    descrizione = """Ricevute per emodializzati, divise in 2 a livello di stampa."""
    codice = "3"
    template_visualizzazione = "5.perConducenteCliente.html"

    mittente = "conducente"
    destinatario = "cliente"
    generabile = False
