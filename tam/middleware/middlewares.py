from django.core.mail import EmailMessage	# to send mail easily

class ConsoleExceptionMiddleware(object):
    def process_exception(self, request, exception):
        import traceback
        import sys
        exc_info = sys.exc_info()
        mailMessage='\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))
        host= request.get_host()
        if "127.0.0.1" in host:
#        	print "*skip mail exception"
			pass
        else:
#        	print host
        	EmailMessage(subject="TAM Exception", body=mailMessage, to=["dariosky@gmail.com"]).send()#fail_silently=True)
