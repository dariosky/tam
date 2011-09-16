from django import forms

class MySplitDateTimeField(forms.fields.SplitDateTimeField):
	""" SplitDateTimeField with input format support """
	def __init__(self, date_input_formats=None, time_input_formats=None, *args, **kwargs):
		fields = (forms.fields.DateField(input_formats=date_input_formats),
				 forms.fields.TimeField(input_formats=time_input_formats))
		forms.fields.MultiValueField.__init__(self, fields, *args, **kwargs)


class MySplitDateWidget(forms.widgets.SplitDateTimeWidget):
	""" Ridefinisco il widget per mostrare data e ora con il formato che mi interessa """
	class Media:
		css = {
			'all': ('js/jquery.ui/themes/ui-lightness/ui.all.css', )
		}
		js= ('js/jquery.ui/jquery-ui.custom-min.js', 'js/calendarPreferences.js')

	def decompress(self, value):
		if value:
			return [value.date().strftime('%d/%m/%Y'), value.time().strftime('%H:%M')]
		return [None, None]
