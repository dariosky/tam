# coding: utf-8
from django.core.management import setup_environ
import settings
from tam.models import stopAllLog
from django.db import transaction
setup_environ(settings)

from tam.models import * #@UnusedWildImport
from fatturazione.models import Fattura, RigaFattura

objects = [
			User,
			Bacino,
			Luogo,
			Tratta,
			Conducente,
			Listino,
			PrezzoListino,
			Cliente,
			Passeggero,
			ProfiloUtente,
			Conguaglio,
			Viaggio,
			Fattura,
			RigaFattura,
		 ]

@transaction.commit_manually
def move_all_objects_of_model(Model, db_from='sqlite', db_to='postgre'):
	totale = Model.objects.using(db_from).count()
	name = Model.__name__
	print "Copio %d oggetti di tipo %s da %s a %s" % (totale,
													  name,
													  db_from,
													  db_to)
	kwargs = {}
	if name in ('Luogo', 'Tratta', 'Viaggio'):
		kwargs['updateViaggi'] = False
	tutti = Model.objects.using(db_from).all()
	#if name == 'Viaggio':
	#	tutti = tutti.filter(id__in=(52489, 52479))
	try:
		for obj in tutti:
			#print obj.id, "\n ", obj
			obj.save(using=db_to, **kwargs)
	except:
		print "errore nella copia:"

		transaction.rollback()
		print obj.id
		# rieseguo l'operazione per sollevare l'eccezione...
		# fuori dalla gestione della transazione
		obj.save(using=db_to, **kwargs)
		#raise Exception('Annullo la copia di %s e mi fermo' % name)

	else:
		transaction.commit()
		pass

	transaction.commit()

def delete_all_objects_of_model(Model, db_name='postgre'):
	totale = Model.objects.using(db_name).count()
	print "Cancello %d records da %s in postgre" % (totale, Object.__name__)
	Model.objects.using(db_name).all().delete()

stopAllLog()
for Object in objects:
	delete_all_objects_of_model(Object)
print
for Object in objects:
	move_all_objects_of_model(Object)

print "Fine."
startAllLog()
