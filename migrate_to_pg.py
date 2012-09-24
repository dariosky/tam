# coding: utf-8
from django.core.management import setup_environ
import settings
from tam.models import stopAllLog
setup_environ(settings)

from tam.models import User, Bacino, Luogo #@UnusedWildImport

objects = [
			User,
			Bacino,
			Luogo,
#			Tratta,
#			Conducente,
#			Listino,
#			PrezzoListino,
		 ]#Conducente, Luogo]

def move_all_objects_of_model(Model, db_from='sqlite', db_to='postgre'):
	totale = Model.objects.using(db_from).count()
	print "Copio %d oggetti di tipo %s da %s a %s" % (totale,
													  Model.__name__,
													  db_from,
													  db_to)
	kwargs = {}
	if Model.__name__ in ('Luogo', 'Tratta'):
		kwargs['updateViaggi'] = False
	for obj in Model.objects.all():
		obj.save(using=db_to, **kwargs)
		print "  copio", obj

def delete_all_objects_of_model(Model, db_name='postgre'):
	totale = Model.objects.using(db_name).count()
	print "Cancello %d records da %s in postgre" % (totale, Object.__name__)
	Model.objects.using(db_name).all().delete()

stopAllLog()
for Object in objects:
	delete_all_objects_of_model(Object)

for Object in objects:
	move_all_objects_of_model(Object)
