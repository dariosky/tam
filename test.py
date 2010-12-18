# coding: utf-8
import os
os.environ["DJANGO_SETTINGS_MODULE"]="settings"

from tam.models import *
from django.db import connection

def nuoveClassifiche():
	cursor=connection.cursor()
	query="""
		select
		 c.id as conducente_id, c.nick as conducente_nick,
		 sum(punti_diurni)+classifica_iniziale_diurni as num_disturbi_diurni,
		 sum(punti_notturni)+classifica_iniziale_notturni as num_disturbi_notturni,
		 sum(prezzoVenezia) + classifica_iniziale_long as priceLong,
		 sum(prezzoPadova) + classifica_iniziale_medium as priceMedium,
		 sum(prezzoDoppioPadova), --+ classifica_iniziale_medium as priceMedium
		 sum(punti_abbinata)
		from tam_viaggio v
		join tam_conducente c on v.conducente_id=c.id
		where conducente_confermato=1 --and c.nick='2'
		group by c.id, c.nick
	"""
	cursor.execute( query, () )
	results=cursor.fetchall()
	classifiche=[]
	fieldNames=[field[0] for field in cursor.description]
	for classifica in results:
		classDict={}
		for name, value in zip(fieldNames, classifica):
			classDict[name]=value
		classifiche.append(classDict)
	return classifiche

#print nuoveClassifiche()

#print "Fine."