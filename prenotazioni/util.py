#coding:utf-8
from tam.models import Viaggio, ProfiloUtente
from tam.views.tamUtils import getDefault

preavviso_ore = 48

def prenotaCorsa(prenotazione):
	" Crea il viaggio e lo associa alla corsa "

	utentePrenotazioni = prenotazione.owner
	profilo = ProfiloUtente.objects.get(user=utentePrenotazioni.user)

	if prenotazione.is_arrivo:
		# arrivo dal luogo indicato a cliente
		partenza = prenotazione.luogo
		arrivo = utentePrenotazioni.luogo
	else:
		# partenza dal cliente al luogo indicato
		partenza = utentePrenotazioni.luogo
		arrivo = prenotazione.luogo
	note_complete = prenotazione.note
	if prenotazione.note_camera:
		note_complete = ("Camera: %s\n" % prenotazione.note_camera) + note_complete
	if prenotazione.note_cliente:
		note_complete = ("Cliente: %s\n" % prenotazione.note_cliente) + note_complete
	cliente = utentePrenotazioni.cliente
	viaggio = Viaggio(
					data=prenotazione.data_corsa,

					da=partenza,
					a=arrivo,
					luogoDiRiferimento=profilo.luogo, # è il riferimento di chi ha creato l'utente

					numero_passeggeri=prenotazione.pax,
					esclusivo=not prenotazione.is_collettivo,
					cliente=cliente,
					prezzo=0,

					note=note_complete,

					incassato_albergo=cliente.incassato_albergo,
					fatturazione=cliente.fatturazione,
					pagamento_differito=cliente.pagamento_differito,
					tipo_commissione=cliente.tipo_commissione if cliente.commissione > 0 else 'F',
					commissione=cliente.commissione,

					)
	default = getDefault(viaggio)
	for attribute_name in default:
		setattr(viaggio, attribute_name, default[attribute_name])

	viaggio.is_prenotazione = True

	#TODO:
	# imposto il flag di fatturazione, incassato hotel o differito in base
	# alla prenotazione

	viaggio.save()
	viaggio.updatePrecomp()
	return viaggio

if __name__ == '__main__':
	import datetime
	from prenotazioni.models import Prenotazione
	viaggi = Viaggio.objects.filter(
									data__gt=datetime.datetime(2012, 11, 14, 0, 0),
									data__lt=datetime.datetime(2012, 11, 14, 22, 0)
									)
	viaggi = viaggi.exclude(note__icontains="Creato a mano")
	viaggi.delete()

	Prenotazione.objects.all().delete()
	print "Cancellato tutto"
