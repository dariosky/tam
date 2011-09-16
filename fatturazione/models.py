from django.db import models
from tam.models import Viaggio

# Create your models here.
class Fattura(models.Model):
	emessa_da = models.TextField()	# anagrafica emittente
	emessa_a = models.TextField()	# anagrafica cliente
	note = models.TextField()
	
	tipo = models.CharField(max_length=1) # tipo fattura: 1.Consorzio (a cliente), 2.Conducente (a consorzio), 3.Ricevuta (a cliente)
	
	data = models.DateField()
	anno = models.IntegerField()
	progressivo = models.IntegerField()
	

class RigaFattura(models.Model):
	fattura = models.ForeignKey(Fattura, related_name="righe")
	descrizione = models.TextField()
	note = models.TextField()
	
	qta = models.IntegerField()
	prezzo = models.DecimalField( max_digits=9, decimal_places=2)	#fissa in euro
	iva = models.IntegerField()	# iva in percentuale
	
	viaggio = models.ForeignKey(Viaggio, null=True, related_name="fattura")
	