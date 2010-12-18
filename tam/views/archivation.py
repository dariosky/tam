from django.shortcuts import render_to_response, HttpResponse, get_object_or_404
from django.http import HttpResponseRedirect	#use the redirects
from django.contrib.auth.decorators import login_required #, permission_required   # used to force a view to logged users
from django import forms
from django.template.context import RequestContext	 # Context with steroid
from django.utils.translation import ugettext as _

import datetime

@login_required
def archivation(request, template_name="utils/archive/menu.html"):
	dontHilightFirst=True
	if not request.user.is_superuser:
		request.user.message_set.create(message=u"Devi avere i superpoteri per accedere all'archiviazione.")
		return HttpResponseRedirect(reverse("tamUtil"))

	class ArchiveForm(forms.Form):
		""" Form che chiede una data non successiva a 30 giorni fa """
		class Media:
			css = {
				'all': ('js/jquery.ui/themes/ui-lightness/ui.all.css', )
			}
			js = ('js/jquery.min.js', 'js/jquery.ui/jquery-ui.custom-min.js', 'js/calendarPreferences.js')

		end_date=forms.DateField(
					label="Data finale",
					input_formats=[_('%d/%m/%Y')],
					initial=datetime.date.today().replace(month=1, day=1).strftime('%d/%m/%Y')
			)

	form = ArchiveForm()
	
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@login_required
def action(request, template_name="utils/archive/action.html"):
	""" Archivia le corse, mantenendo le classifiche inalterate """
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@login_required
def archive(request, template_name="utils/archive/list.html"):
	""" Visualizza le corse archiviate """
	
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

@login_required
def flat(request, template_name="utils/archive/flat.html"):
	""" Livella le classifiche, in modo che gli ultimi abbiano zero """
	return render_to_response(template_name, locals(), context_instance=RequestContext(request))
