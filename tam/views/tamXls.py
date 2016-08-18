# coding:utf-8
import logging
from collections import OrderedDict
from io import BytesIO

import xlwt
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect

from modellog.actions import logAction
from tam.views import xlsUtil

corseField = OrderedDict()
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
corseField['incassato_albergo'] = 'ContoFM?'
corseField['pagamento_differito'] = 'Fatturazione esente IVA?'
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
                for token in field.split('.'):  # iterate sub object with .
                    if related:
                        related = related.__getattribute__(token)
                    else:
                        break
            else:
                if field == "incassato_albergo" and getattr(settings,
                                                            'TAM_EXPORT_EXCEL_FINEMESE_LORDO',
                                                            False):
                    # a request to put contofinemese as lordo
                    related = record.__getattribute__(
                        "prezzo") if record.__getattribute__(field) else 0
                else:
                    related = record.__getattribute__(field)

            if callable(related):
                related = related()  # if it's a method call it
            row.append(related)
        table.append(row)
    return table,  # only one result sheet with our table


def xlsResponse(request, querySet):
    doc = xlwt.Workbook()

    numViaggi = querySet.count()
    logging.debug("Export to EXCEL %d viaggi." % numViaggi)
    if numViaggi > settings.MAX_XLS_ROWS:
        messages.error(request,
                       "Non puoi esportare in Excel più di %d viaggi contemporaneamente." % settings.MAX_XLS_ROWS)
        return HttpResponseRedirect("/")  # back home

    # from guppy import hpy
    # h = hpy()
    # h.setref()

    querySet = querySet.select_related("da", "a", "cliente", "conducente",
                                       "passeggero")
    generatore = xlsUtil.Sql2xls(doc, manager=querySet)

    tamEnumerateTables = lambda x: djangoManagerToTable(x, fields=corseField)
    generatore.enumerateTables = tamEnumerateTables
    generatore.run()
    if generatore.sheetCount:
        output = BytesIO()

        doc.save(output)  # save the excel
        output.seek(0)
        response = HttpResponse(output.getvalue(),
                                content_type='application/excel')

        response['Content-Disposition'] = \
            'attachment; filename="%s"' % 'tamExport.xls'
        logAction(action='X',
                  description="Export in Excel di %d corse." % numViaggi,
                  user=request.user, log_date=None)
        # print h.heap()
        return response
    else:
        messages.error(request,
                       "Non ho alcun viaggio da mettere in Excel," +
                       " cambia i filtri per selezionarne qualcuno.")
        del generatore
        return HttpResponseRedirect("/")  # back home
