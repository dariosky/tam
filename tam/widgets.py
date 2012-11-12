from django import forms

class MySplitDateTimeField(forms.fields.SplitDateTimeField):
	""" SplitDateTimeField with input format support """
	def __init__(self, date_input_formats=None, time_input_formats=None, *args, **kwargs):
		fields = (forms.fields.DateField(input_formats=date_input_formats),
				  forms.fields.TimeField(input_formats=time_input_formats))
		forms.fields.MultiValueField.__init__(self, fields, *args, **kwargs)


class MySplitDateWidget(forms.widgets.SplitDateTimeWidget):
	""" Ridefinisco il widget per mostrare data e ora con il formato che mi interessa """
#	class Media:
#		css = {
#			'all': ('/media/js/jquery.ui/themes/ui-lightness/ui.all.css', )
#		}
#		js= ('/media/js/jquery.ui/jquery-ui.custom-min.js', '/media/js/calendarPreferences.js')

	def __init__(self, *args, **kwargs):
		super(MySplitDateWidget, self).__init__(*args, **kwargs)
		self.widgets[0].attrs['class']="date-widget"
		self.widgets[1].attrs['class']="time-widget"
		self.widgets[1].attrs['maxlength'] = "5" # time max length

	def decompress(self, value):
		if value:
			return [value.date().strftime('%d/%m/%Y'), value.time().strftime('%H:%M')]
		return [None, None]
