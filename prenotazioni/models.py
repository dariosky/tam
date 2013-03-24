# coding: utf-8
from django.db import models
from django.contrib.auth.models import User
from tam.models import Cliente, Luogo, Viaggio
import datetime
from prenotazioni.util import preavviso_ore, prenotaCorsa
from tam import tamdates

# Regole da rispettare:
# 	non mostro i prezzi
# 	creo/modifico solo se ad almeno TOT ore dalla data prenotazione
# 	non posso modificare se il viaggio è già confermato



TIPI_PAGAMENTO = (
	('D', 'Diretto'),
	('H', 'Hotel'), # diventa "conto finemese"
	('F', 'Fattura'),  # fattura richiesta
)

# Create your models here.
class UtentePrenotazioni(models.Model):
	user = models.OneToOneField(User, related_name='prenotazioni')
	clienti = models.ManyToManyField(Cliente)
	luogo = models.ForeignKey(Luogo, on_delete=models.PROTECT)
	nome_operatore = models.CharField(max_length=40, null=True)
	email = models.EmailField(null=True)

	class Meta:
		verbose_name_plural = "Utenti prenotazioni"
		ordering = ("user",)
		permissions = (('manage_permissions', 'Gestisci utenti prenotazioni'),)

	def __unicode__(self):
		return "%(user)s - %(clienti)s da '%(luogo)s' - %(email)s" % {
		"user": self.user.username,
		"clienti": ", ".join([c.nome for c in self.clienti.all()]),
		"luogo": self.luogo.nome,
		"email": self.email,
		}


class Prenotazione(models.Model):
	owner = models.ForeignKey(UtentePrenotazioni, editable=False, on_delete=models.CASCADE)
	cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
	data_registrazione = models.DateTimeField(auto_now_add=True)

	data_corsa = models.DateTimeField("Data e ora",
	                                  help_text="Nelle partenze indica l'ora della presa in hotel. Negli arrivi è l'ora al luogo indicato.")

	pax = models.IntegerField(default=1)
	is_collettivo = models.BooleanField(
		"Individuale o collettivo?",
		choices=((False, 'Individuale'), (True, 'Collettivo')),
		default=None
	)

	is_arrivo = models.BooleanField("Arrivo o partenza?",
	                                choices=((True, 'Arrivo da...'), (False, 'Partenza per...')),
	                                default=None
	)
	luogo = models.ForeignKey(Luogo, on_delete=models.PROTECT)

	pagamento = models.CharField(max_length=1,
	                             choices=TIPI_PAGAMENTO,
	                             default="D")

	note_camera = models.CharField("Numero di camera", max_length=20, blank=True)
	note_cliente = models.CharField("Nome del cliente", max_length=40, blank=True)
	note = models.TextField(blank=True)

	viaggio = models.OneToOneField(Viaggio,
	                               null=True,
	                               editable=False,
	                               on_delete=models.PROTECT,
	)

	class Meta:
		verbose_name_plural = "Prenotazioni"
		ordering = ("cliente", "-data_corsa", "owner")

	def __unicode__(self):
		result = "%s - %s" % (self.cliente, self.owner.user.username)
		result += " - " + ("arrivo" if self.is_arrivo else "partenza")
		result += " %s" % self.luogo
		result += " del %s" % self.data_corsa.astimezone(tamdates.tz_italy).strftime('%d/%m/%Y %H:%M')
		return result

	def is_editable(self):
		" True se la corsa è ancora modificabile "
		ora = tamdates.ita_now()
		inTempo = ora < (self.data_corsa - datetime.timedelta(hours=preavviso_ore))
		if not inTempo: return False
		if self.viaggio and self.viaggio.conducente_confermato:
			return False
		return True

	def save(self, **kwargs):
		# posso forzare updateViaggi a False se non voglio aggiornare i viaggi
		if 'updateViaggi' in kwargs:
			updateViaggi = kwargs['updateViaggi']
			del (kwargs['updateViaggi'])
		else:
			updateViaggi = True

		if self.viaggio and updateViaggi:
			nuovoViaggio = prenotaCorsa(self, dontsave=True)
			chiavi_da_riportare = [
				'data', 'da', 'a', 'numero_passeggeri', 'esclusivo',
				'incassato_albergo', 'fatturazione', 'pagamento_differito',
				'cliente',
				'note'
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
