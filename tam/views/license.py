#coding: utf-8
import datetime
from tam.models import TamLicense
from django.http import HttpResponseRedirect	#use the redirects
from django.core.urlresolvers import reverse	#to resolve named urls
from django import forms
import random
import base64
from hashlib import md5
from django.conf import settings
from Crypto.Cipher import Blowfish

def get_license_detail(encodedString=None):
	""" Trova i dettagli sulla licenza.
		Prende la licenza da stringa se gli viene passata, altrimenti la prende da DB
	"""
	from django.conf import settings
	r = {	"tam_version": settings.TAM_VERSION,
			"tam_licensed": False,
			"tam_valid_license": True
		}
	try:
		if not encodedString:
			licenzadb=TamLicense.objects.get()
			encodedString=licenzadb.license
		clearText=decode(encodedString)
		tokens=clearText.split("|")
		if len(tokens)!=2:
			r["tam_valid_license"]=False
		else:
			r["tam_registred_user"], r["tam_expiration_date"] = tokens
			if r["tam_expiration_date"]=="unlimited":
				r["tam_expiration_date"]=None
				r["tam_licensed"] = True
			else:
				try:
					import time
					tup=time.strptime(r["tam_expiration_date"], "%Y-%m-%d")
					r["tam_expiration_date"]=datetime.date(*tup[:3])
					r["tam_licensed"] = datetime.date.today() <= r["tam_expiration_date"]
				except:
					r["tam_expiration_date"]=datetime.date.today()-datetime.timedelta(days=1) #scade ieri
	except TamLicense.DoesNotExist:
		pass
	return r

def license_context(request):
	result=get_license_detail()
	return result

class LicForm(forms.ModelForm):
	def clean(self):
		encodedLicense=self.cleaned_data.get("license", "")
		encodedLicense=encodedLicense.replace(" ","").replace("\n","").replace("\r","")
		detail=get_license_detail(encodedLicense)
		if not detail["tam_valid_license"]:
			raise forms.ValidationError(u"Il codice della licenza non è valido.")
		self.cleaned_data["license"]=encodedLicense
		return self.cleaned_data
	class Meta:
		model=TamLicense

def decode(coded):
	from django.conf import settings
	from Crypto.Cipher import Blowfish
	obj=Blowfish.new(settings.SECRET_KEY, Blowfish.MODE_ECB)
	try:
		try:
			ciph = base64.b32decode(coded)
		except NameError:
			ciph = base64.decodestring(coded)
		
		plaintext = obj.decrypt(ciph)
		try:
			(c1, plain, c2) = plaintext.split(":ok:")
		except ValueError:
			return ""
	except:
		return ""	#if something goes wrong
	return plain

def encode(plain):
	obj=Blowfish.new(settings.SECRET_KEY, Blowfish.MODE_ECB)
	
	randcode=str(random.randint(0, 9999999999999))
	randstring=md5(randcode).hexdigest()
	split = random.randrange(10)+1
	s = randstring[:split] +  ':ok:' + plain +':ok:'+ randstring[split:]
	length = len(s)

	l = length + 8 - (length % 8)
	padded = s +  " " * (8 - length % 8)

	ciph=obj.encrypt(padded[:l])
	try:
		return base64.b32encode(ciph)
	except NameError:
		return base64.encodestring(ciph)



def licensed(func):
	def wrapCheckLicense(request, *args, **kwargs):
		r=get_license_detail()
		if not r["tam_licensed"]:
			return HttpResponseRedirect(reverse("tamLicense"))
		else:
			return func(request, *args, **kwargs)
	return wrapCheckLicense

