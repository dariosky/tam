# coding: utf-8
#===============================================================================
# Migrate all indicated models from a DB to another using the Django ORM
# this is useful to get some object manipulation in the while
#
# Steps for the migration
# define in the setting.DATABASES the source and target database definition
# (default 'sqlite' => 'postgre')
# run syncdb and migrations on the empty db
# in Tam we have:
# 	manage.py syncdb
# 	manage.py migrate tam
# 	manage.py migrate fatturazione
# 	manage.py migrate prenotazioni
# 	manage.py migrate djangotasks
#
# run this script and wait
#===============================================================================


from django.conf import settings

# HACK: Force settings cause in sqlite all dates are referred to CET
# all dates in DB are referred to this default timezone
settings.USE_TZ = False
settings.TIME_ZONE = 'Europe/Rome'	

from tam.models import stopAllLog
from django.db import transaction

#setup_environ(settings)

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from tam.models import *  # @UnusedWildImport
from fatturazione.models import Fattura, RigaFattura
from prenotazioni.models import UtentePrenotazioni, Prenotazione
objects = [
			ContentType,
			Permission,
			Group,
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

			UtentePrenotazioni,
			Prenotazione
		 ]

manyToManyToSave = {
					'Group':['permissions'],
					'User':['groups', 'user_permissions'],
					'UtentePrenotazioni':['clienti'],
				}
@transaction.commit_manually
def move_all_objects_of_model(Model, db_from='sqlite', db_to='postgre'):
	totale = Model.objects.using(db_from).count()
	name = Model.__name__
	print "Copio %d oggetti di tipo %s da %s a %s" % (totale,
													  name,
													  db_from,
													  db_to)
	kwargs = {}
	if name in ('Luogo', 'Tratta', 'Viaggio', 'Prenotazione'):
		kwargs['updateViaggi'] = False
	tutti = Model.objects.using(db_from).all()
#	if name == 'Viaggio': # per testare solo su alcuni viaggi
#		tutti = tutti.filter(id__in=(8143, 8264))
	for field in Model._meta.local_fields:
		if hasattr(field, 'auto_now_add') and field.auto_now_add == True:
			print "\tDisabilito l'autoadd nel campo %s" % field.name
			field.auto_now_add = False
	try:
		for obj in tutti:
			# print obj.id, "\n ", obj
			if name in manyToManyToSave:
				oldRelations = {}
				for manyFieldName in manyToManyToSave[name]:
					# keep the id list of all related objects
					oldRelations[manyFieldName] = [e[0] for e in getattr(obj, manyFieldName).all().values_list('id')]
					# print "copio le %d correlazioni %s con %s" % (len(oldRelations[manyFieldName]), manyFieldName, name),
				obj.save(using=db_to, **kwargs)
				for manyFieldName in manyToManyToSave[name]:
					for oldRelatedID in oldRelations[manyFieldName]:
						newRelated = getattr(obj, manyFieldName).model.objects.using(db_to).get(id=oldRelatedID)
						getattr(obj, manyFieldName).add(newRelated)  # add with the save DB
					# print "ne ritrovo %d" % len(getattr(obj, manyFieldName).all()),
				# print
			else:
				if name == 'Permission' and len(obj.name) > 50:
					print "Truncate permission name from %s to %s" % (obj.name, obj.name[:50])
					obj.name = obj.name[:50]
				obj.save(using=db_to, **kwargs)
	except Exception, e:
		print "\nErrore nella copia: ******************"

		transaction.rollback()
		print "Error on object id:", obj.id
		print obj
		# rieseguo l'operazione per sollevare l'eccezione...
		# fuori dalla gestione della transazione

		obj.save(using=db_to, **kwargs)
		print e

		raise Exception('Annullo la copia di %s e mi fermo' % name)

	else:
		transaction.commit()
		pass

	transaction.commit()


def delete_all_objects_of_model(Model, db_name='postgre'):
	totale = Model.objects.using(db_name).count()
	print "Cancello %d records da %s in postgre" % (totale, Object.__name__)
	Model.objects.using(db_name).all().delete()


def setAllSequencesToMax(db_name='postgre'):
	from django.db import connections
	con = connections[db_name]
	cursor = con.cursor()
	# get sequence and table name I'll get the field name from the sequence name
	cursor.execute("""
		WITH fq_objects AS (SELECT c.oid,c.relname AS fqname , 
		                           c.relkind, c.relname AS relation 
		                    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace ),
		
		     sequences AS (SELECT oid,fqname FROM fq_objects WHERE relkind = 'S'),  
		     tables    AS (SELECT oid, fqname FROM fq_objects WHERE relkind = 'r' )  
		SELECT
		       s.fqname AS sequence, 
		       t.fqname AS table
		FROM 
		     pg_depend d JOIN sequences s ON s.oid = d.objid  
		                 JOIN tables t ON t.oid = d.refobjid  
		WHERE 
		     d.deptype = 'a' ;
	""")
	sequences = cursor.fetchall()
	for r in sequences:
		sequence_name, table_name = r
		field_name = sequence_name[len(table_name) + 1:-4]

		maximizeSequenceCommand = """
			select setval(
					'%(sequence_name)s',
					(select coalesce(max(%(field_name)s),0)+1 from %(table_name)s)
			); 
		""" % {	"sequence_name":sequence_name,
				"table_name":table_name,
				"field_name":field_name}
		#print maximizeSequenceCommand.strip()
		cursor.execute(maximizeSequenceCommand)

	transaction.rollback_unless_managed(using=db_name)	# eventually commit
	print "Sequences set"

if __name__ == '__main__':
	stopAllLog()
	for Object in objects:
		delete_all_objects_of_model(Object)
	print
	for Object in objects:
		move_all_objects_of_model(Object)

	print "Now everything is copied, we should reset all sequences to their max+1"

	startAllLog()

	setAllSequencesToMax()
	print "Fine."

"""
Final notes:
	per avere l'ordinamento per byte dei luoghi:
	alter table tam_luogo alter column nome TYPE character varying(25) COLLATE pg_catalog."C";
"""