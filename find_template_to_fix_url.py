import os
import re

has_url_pattern = re.compile(r'\{%\s*url')
# {% load url from future %}
future_url_pattern = re.compile(r'\{%\s*load\s+url\s+from\s+future')
url_comma_parameters = re.compile(r'\{%\s*url\s*(.*?)%\}', re.DOTALL)
param_tokenizer = re.compile(r'[,\s]+')

errors = url_files_count = warnings = 0
for dirpath, dirnames, filenames in os.walk('.'):
	if 'environment' in dirpath:
		continue
	for filename in filenames:
		name, ext = os.path.splitext(filename)
		if ext in ('.html', '.htm', 'djhtml'):
			#if not "base" in name: continue
			path = os.path.join(dirpath, filename)
			with file(path, 'r') as f:
				content = f.read()
				has_url = re.search(has_url_pattern, content)
				if has_url:
					url_files_count += 1
					error = []
					warning = []
					future_url = re.search(future_url_pattern, content)
					if not future_url:
						error.append("Future URL missing: {% load url from future %}")
					parameters = re.findall(url_comma_parameters, content)
					for parameter in parameters:
						#print parameter
						if "," in parameter:
							error.append("Comma in url parameters")
						if parameter[0] not in ("\'", "\""):
							parameter_tokens = re.split(param_tokenizer, parameter)
							warning.append("URL name without commas (this can be valid if %s is a template variable)" % parameter_tokens[0])

					if error or warning:
						print path
						if error:
							print "  ERROR: %s" % ", ".join(error)
							errors += len(error)
						if warning:
							print "  WARNING: %s" % ", ".join(warning)
							warnings += len(warning)
						
print
print "%d files with url. %d errors, %d warnings" % (url_files_count, errors, warnings)
# errato: {% url "orderImage" order.tipo_doc, order.anno_doc, order.numero_doc, order.progressivo_riga %}">




