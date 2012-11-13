#coding: utf-8
from django.db import models
from django.contrib.auth.models import User
from tam.models import Cliente, Luogo, Viaggio

"""
	Regole da rispettare:
		non mostro i prezzi
		creo/modifico solo se >=24h da ora
		non posso modificare se il viaggio è già confermato
"""


TIPI_PAGAMENTO = (
					('D', 'Diretto'),
					('H', 'Hotel'), 	# diventa "conto finemese"
					('F', 'Fattura'), 	# fattura richiesta
				)

# Create your models here.
class UtentePrenotazioni(models.Model):
	user = models.OneToOneField(User, related_name='prenotazioni')
	cliente = models.ForeignKey(Cliente)
	luogo = models.ForeignKey(Luogo)
	nome_operatore = models.CharField(max_length=40, null=True)
	email = models.EmailField(null=True)

	class Meta:
		verbose_name_plural = "Utenti prenotazioni"
		ordering = ("cliente", "user")
		permissions = (('manage_permissions', 'Gestisci utenti prenotazioni'),)

	def __unicode__(self):
		return "%(user)s - %(cliente)s da '%(luogo)s' - %(email)s" % {
											"user": self.user.username,
											"cliente": self.cliente.nome,
											"luogo": self.luogo.nome,
											"email": self.email,
										}


class Prenotazione(models.Model):
	owner = models.ForeignKey(UtentePrenotazioni, editable=False)
	data_registrazione = models.DateTimeField(auto_now_add=True)

	data_corsa = models.DateTimeField()

	pax = models.IntegerField(default=1)
	is_collettivo = models.BooleanField(
									"Individuale o collettivo?",
									choices=((False, 'Individuale'), (True, 'Collettivo')),
									default=False
									)

	is_arrivo = models.BooleanField("Arrivo o partenza?",
									choices=((True, 'Arrivo'), (False, 'Partenza')),
									default=True)
	luogo = models.ForeignKey(Luogo)

	pagamento = models.CharField(max_length=1,
								 choices=TIPI_PAGAMENTO,
								 default="D")

	note_camera = models.CharField("Numero di camera", max_length=20, blank=True)
	note_cliente = models.CharField("Nome del cliente", max_length=40, blank=True)
	note = models.TextField(blank=True)

	viaggio = models.OneToOneField(Viaggio,
								   null=True,
								   editable=False)

	class Meta:
		verbose_name_plural = "Prenotazioni"
		ordering = ("data_registrazione", "owner")

	def __unicode__(self):
		return "Prenotazione del %(data_registrazione)s" % self.__dict__
