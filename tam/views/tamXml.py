#coding:utf8
import xlsUtil
from django.http import HttpResponse, HttpResponseRedirect
import logging
import StringIO
from django.utils.datastructures import SortedDict
from django.contrib import messages

corseField = SortedDict()
corseField['data'] = 'Data'
corseField['da.nome'] = 'Da'
corseField['a.nome'] = 'A'
corseField['cliente.nome'] = 'Cliente'
corseField['numero_passeggeri'] = 'pax'
corseField['prezzo'] = 'Lordo'
corseField['prezzo_commissione'] = 'Quota cons.'
corseField['abbuono_fisso'] = 'Abbuono [€]'
corseField['abbuono_percentuale'] = 'Abbuono [%]'
corseField['prezzo_sosta'] = 'Sosta'
corseField['fatturazione'] = 'Fattura?'
corseField['incassato_albergo'] = 'Inc.albergo?'
corseField['pagamento_differito'] = 'Posticipato?'
corseField['cartaDiCredito'] = 'Carta?'
corseField['conducente.nick'] = 'Conducente'
corseField['note'] = 'note'

def djangoManagerToTable(self, fields):
	""" Should return a list of tables
		Take a list of django object managers and a list of fields to return as input
	"""
	# trasformo il manager viaggi in una lista di righe

	self.queryDescriptor = fields.values()
	manager = self.manager
	table = []
	for record in manager:
		row = []
		for field in fields.keys():
			if "." in field:
				related = record
				for token in field.split('.'):	# iterate sub object with .
					if related:
						related = related.__getattribute__(token)
					else:
						break
			else:
				related = record.__getattribute__(field)

			if callable(related): related = related()	# if it's a method call it
			row.append(related)
		table.append(row)
	return (table,)	# only one result sheet with our table

def xlsResponse(request, querySet):
	doc = xlsUtil.Workbook()

	numViaggi = querySet.count()
	logging.debug("Export to EXCEL %d viaggi." % numViaggi)
	maxViaggi = 1500
	if numViaggi > maxViaggi:
		messages.error(request, "Non puoi esportare in Excel più di %d viaggi contemporaneamente." % maxViaggi)
		return HttpResponseRedirect("/")	# back home

	querySet = querySet.select_related("da", "a", "cliente", "conducente", "passeggero")
	generatore = xlsUtil.Sql2xls(doc, manager=querySet)

	tamEnumerateTables = lambda x: djangoManagerToTable(x, fields=corseField)
	generatore.enumerateTables = tamEnumerateTables
	generatore.run()
	if generatore.sheetCount:
		output = StringIO.StringIO()

#			filename=os.path.join( os.path.dirname(__file__), 'tempExcel.xls')
#			doc.save(filename)
#			responseFile=file(filename,"rb")
#			response = HttpResponse(responseFile.read(), mimetype='application/excel')
#			responseFile.close()

		doc.save(output)	# save the excel
		output.seek(0)
		response = HttpResponse(output.getvalue(), mimetype='application/excel')

		response['Content-Disposition'] = 'attachment; filename="%s"' % 'tamExport.xls'
		return response
	else:
		messages.error(request, "Non ho alcun viaggio da mettere in Excel, cambia i filtri per selezionarne qualcuno.")
		del generatore
		return HttpResponseRedirect("/")	# back home
