# coding: utf-8
import datetime
# from tam.models import TamLicense
# from django.http import HttpResponseRedirect	#use the redirects
# from django.core.urlresolvers import reverse	#to resolve named urls
# from django import forms
# import random
# import base64
# from hashlib import md5
from django.conf import settings
# from Crypto.Cipher import Blowfish

# def get_license_detail(encodedString=None):
#	""" Trova i dettagli sulla licenza.
#		Prende la licenza da stringa se gli viene passata, altrimenti la prende da DB
#	"""
#	r = {	"tam_version": settings.TAM_VERSION,
#			"tam_licensed": False,
#			"tam_valid_license": True
#		}
#	try:
#		if not encodedString:
#			licenzadb=TamLicense.objects.get()
#			encodedString=licenzadb.license
#		clearText=decode(encodedString)
#		tokens=clearText.split("|")
#		if len(tokens)!=2:
#			r["tam_valid_license"]=False
#		else:
#			r["tam_registred_user"], r["tam_expiration_date"] = tokens
#			if r["tam_expiration_date"]=="unlimited":
#				r["tam_expiration_date"]=None
#				r["tam_licensed"] = True
#			else:
#				try:
#					import time
#					tup=time.strptime(r["tam_expiration_date"], "%Y-%m-%d")
#					r["tam_expiration_date"]=datetime.date(*tup[:3])
#					r["tam_licensed"] = datetime.date.today() <= r["tam_expiration_date"]
#				except:
#					r["tam_expiration_date"]=datetime.date.today()-datetime.timedelta(days=1) #scade ieri
#	except TamLicense.DoesNotExist:
#		pass
#	return r

# class LicForm(forms.ModelForm):
#	def clean(self):
#		encodedLicense=self.cleaned_data.get("license", "")
#		encodedLicense=encodedLicense.replace(" ","").replace("\n","").replace("\r","")
#		detail=get_license_detail(encodedLicense)
#		if not detail["tam_valid_license"]:
#			raise forms.ValidationError(u"Il codice della licenza non è valido.")
#		self.cleaned_data["license"]=encodedLicense
#		return self.cleaned_data
#	class Meta:
#		model=TamLicense

# def decode(coded):
#	from Crypto.Cipher import Blowfish
#	obj=Blowfish.new(settings.SECRET_KEY, Blowfish.MODE_ECB)
#	try:
#		try:
#			ciph = base64.b32decode(coded)
#		except NameError:
#			ciph = base64.decodestring(coded)
#
#		plaintext = obj.decrypt(ciph)
#		try:
#			(c1, plain, c2) = plaintext.split(":ok:")
#		except ValueError:
#			return ""
#	except:
#		return ""	#if something goes wrong
#	return plain
#
# def encode(plain):
#	obj=Blowfish.new(settings.SECRET_KEY, Blowfish.MODE_ECB)
#
#	randcode=str(random.randint(0, 9999999999999))
#	randstring=md5(randcode).hexdigest()
#	split = random.randrange(10)+1
#	s = randstring[:split] +  ':ok:' + plain +':ok:'+ randstring[split:]
#	length = len(s)
#
#	l = length + 8 - (length % 8)
#	padded = s +  " " * (8 - length % 8)
#
#	ciph=obj.encrypt(padded[:l])
#	try:
#		return base64.b32encode(ciph)
#	except NameError:
#		return base64.encodestring(ciph)



# def licensed(func):
#	def wrapCheckLicense(request, *args, **kwargs):
#		tam_registered_user = settings.TAM_LICENSE_USER
#		tam_expirtazion_date = settings.TAM_LICENSE_EXPIRATION
##		r=get_license_detail()
#		if not tam_registered_user:
#			return HttpResponseRedirect(reverse("tamLicense"))
#		else:
#			return func(request, *args, **kwargs)
#	return wrapCheckLicense

from markViews import public
from django.shortcuts import render


@public
def notLicensed(request, template_name="registration/license.html"):
    #	if request.method=="POST":
    #		if not request.user.has_perm('tam.change_tamlicense'):
    #			messages.error(request, "Devi avere i superpoteri per cambiare la licenza.")
    #			return HttpResponseRedirect("/")
    #		for license in TamLicense.objects.all():
    #			license.delete()
    #
    #	form=LicForm(request.POST or None)
    #
    #	if form.is_valid():
    #		form.save()
    #		return HttpResponseRedirect(reverse("tamCorse"))

    return render(request, template_name, locals())


# def activation(request, template_name="registration/activation.html"):
#	user=request.user
#	if not user.is_superuser:
#		messages.error(request, "Devi essere il superuser per accedere all'attivazione.")
#		return HttpResponseRedirect("/")
#	lic=get_license_detail()
#	ininame=lic.get("tam_registred_user","")
#	expiration=lic.get("tam_expiration_date", None)
#	if lic["tam_licensed"] and not expiration:
#		initype="unlimited"
#	elif lic["tam_licensed"]:
#		initype="trial"
#	else:
#		initype="no"
#
#	actualLicenseType="no"
#	if lic and lic["tam_licensed"]:
#		if lic["tam_expiration_date"]:
#			actualLicenseType="trial"
#		else:
#			actualLicenseType="unlimited"
#
#	class ActivationForm(forms.Form):
#		name=forms.CharField(max_length=50, label="Registrata a", initial=ininame)
#		type=forms.ChoiceField(
#								[("no","Non registrata"), ("trial","Licenza di prova"), ("unlimited","Illimitata")],
#								label="Tipo", initial=actualLicenseType
#							)
#		data=forms.DateField(initial=expiration or (datetime.date.today()+datetime.timedelta(days=31)), required=False )
#		def clean(self):
#			cleaned=self.cleaned_data
#			if self.cleaned_data["type"]=="unlimited":
#				cleaned["data"]="unlimited"
#			elif self.cleaned_data["type"]=="no":
#				cleaned["data"]=datetime.date.today()-datetime.timedelta(days=1) #scade ieri
#			return cleaned
#	form=ActivationForm(request.POST or None)
#	if form.is_valid():
#		for license in TamLicense.objects.all():
#			license.delete()
##		expireDate=datetime.date(year=2008, month=10, day=15)
#		clearText="%s|%s"%(form.cleaned_data["name"], form.cleaned_data["data"])
#		licForm=LicForm({"license":encode( clearText )})
#		licForm.save()
#		return HttpResponseRedirect(reverse("tamUtil"))
#	return render_to_response(template_name, locals(), context_instance=RequestContext(request))

def get_license_detail():
    license_owner = getattr(settings, 'LICENSE_OWNER', None)
    license_expiration = getattr(settings, 'LICENSE_EXPIRATION', None)
    license_valid = not license_expiration or (datetime.date.today() <= license_expiration)
    return locals()
