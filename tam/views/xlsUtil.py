#!/usr/bin/env python
#-- coding: iso8859-15 --
import xlwt as pyExcelerator
import datetime
from decimal import Decimal

knownStyles={}	# list of already cached prepared Styles
knownPattern={}

def sty(propList=[], num_format=None, background_color=None, foreground_color=None):
	""" Given a list of properties, create an Excel style """
	if isinstance(propList, str): propList=[propList]
	propList.sort()	#sort so order is ininfluent
	stylename="-".join(propList)
	if num_format:
		stylename+="-"+unicode(num_format)
	if	background_color or foreground_color:
		patternName="%s/%s" % (foreground_color, background_color)
		stylename+="-"+patternName
	else:
		patternName=None
		
	if stylename in knownStyles.keys():
		return knownStyles[stylename]
	
	style=pyExcelerator.XFStyle()
	align = pyExcelerator.Alignment()
	align.vert=pyExcelerator.Alignment.VERT_CENTER	# VERT_TOP, VERT_BOTTOM
	font=pyExcelerator.Font()
	borders=pyExcelerator.Borders()

	if num_format is not None:
		style.num_format_str=num_format	#numeric format
	else:
		style.num_format_str="general"
	
	if patternName:
		if patternName in knownPattern:
			pattern=knownPattern[patternName]
		else:
			pattern=pyExcelerator.Pattern()
			pattern.pattern_fore_colour=background_color
			pattern.pattern=style.pattern.SOLID_PATTERN
			knownPattern[patternName]=pattern
			
		style.pattern=pattern
		
		
	for prop in propList:
		if prop in ("b", "bold"):
			font.bold=True
		elif prop=="center":
			align.horz = pyExcelerator.Alignment.HORZ_CENTER
			align.vert = pyExcelerator.Alignment.VERT_CENTER
		elif prop=="right":
			align.horz = pyExcelerator.Alignment.HORZ_RIGHT
			align.vert = pyExcelerator.Alignment.VERT_CENTER
		elif prop=="wrap":
			align.wrap=pyExcelerator.Alignment.WRAP_AT_RIGHT
		elif prop.startswith("border"):
			if prop[-1]!="r":	#"border2" give borderswidth 2
				weight=int(prop[-1])
			else:				#"border" gives width 1
				weight=1
			borders.left=weight
			borders.right=weight
			borders.top=weight
			borders.bottom=weight
		elif prop.startswith("size"):
			if prop[4:]:	#"size2" give size 2
				size=int(prop[4:])
			else:				#"border" gives width 1
				size=10
			font.height=size
		else:
			font.name=prop
			
	style.borders=borders
	style.alignment=align
	style.font=font
	
	knownStyles[stylename]=style
	return style
	
font_normal=pyExcelerator.Font()
font_normal.name='Times New Roman'

font_bold=pyExcelerator.Font()
font_bold.bold=True
font_bold.name='Times New Roman'

alignCenter = pyExcelerator.Alignment()
alignCenter.horz = pyExcelerator.Alignment.HORZ_CENTER
alignCenter.vert = pyExcelerator.Alignment.VERT_CENTER

style_normal = pyExcelerator.XFStyle()
style_normal.font=font_normal

style_normalCenter = pyExcelerator.XFStyle()
style_normalCenter.alignment=alignCenter

style_bold = pyExcelerator.XFStyle()
style_bold.font=font_bold

style_boldCenter=pyExcelerator.XFStyle()
style_boldCenter.font=font_bold

style_boldCenter.alignment=alignCenter

style_boldDate=pyExcelerator.XFStyle()
style_boldDate.font=font_bold
style_boldDate.num_format_str='M/D/YYYY'

style_boldpercent=pyExcelerator.XFStyle()
style_boldpercent.font=font_bold
style_boldpercent.num_format_str='0%'

style_twoDec = pyExcelerator.XFStyle()
style_twoDec.font=font_normal
style_twoDec.num_format_str='0.00'

class XlsColors:
	yellow=51
	purple=37
	violet=0x24
xlsColWidth={}

def resetSizes():
	""" Reset sheet sizes """
	global xlsColWidth
	xlsColWidth={}
	
def updateSizes(sheet):
	""" Apply suggested width to all columns """
	for x, col in xlsColWidth.items():	# trovo le larghezze di colonna
#		print "setting col(%d) to %d" % (x, col)
		sheet.col(x).width=col

def myWrite(sheet, y, x, field, num_format="general" ):
	field_length=0
	if isinstance(field, Decimal):
		field=float(field)
	elif field is None:
		field=""
	try:
		if hasattr(field, "decode") and not isinstance(field, unicode):
			field=field.decode('utf-8')
	except:
		if hasattr(field, "decode") and not isinstance(field, unicode):
			field=field.decode('iso8859-15')
	
	if isinstance(num_format, pyExcelerator.XFStyle):
		stile=num_format
	else:	
#	print "prestile: %10s" %  num_format,
		if num_format=="general":
			if isinstance(field, datetime.date):
				num_format="DD/MM/YYYY"
				field_length=10
			if isinstance(field, datetime.datetime):
				num_format="DD/MM/YYYY HH:MM"
				field_length=16
#			 or isinstance(field, datetime.datetime)
		stile=sty(num_format=num_format)
#	print "%40s %s"% (field, num_format)
	sheet.write(y, x, field, stile)
#	print x, field
	if field_length==0: field_length=len(unicode(field))
	xlsColWidth[x]=max(xlsColWidth.get(x,3000), 310*field_length)	# default width and computed column width

def row2dict( row, desc ):
	""" Trasforma una tupla estratta con fetchrow in un dizionario usando un cursore"""
	result={}
	for i, field in enumerate( desc ):
		if i>=len(row): break
		if hasattr(row[i], "strip") and not isinstance(row[i], unicode):
			result[field]=unicode(row[i].strip(), errors='ignore')
		else:
			result[field]=row[i]
	return result

def splitImageFormat(format):
	""" return a tuple with: fieldOfImage, maxX, maxY given a format """
	tokens=format.split(",")
	numTokens=len(tokens)
	imageField=None
	maxX=None
	maxY=None
	if numTokens==0:
		pass
	elif numTokens==1:
		(imageField,) = tokens
	elif numTokens==2:
		(imageField,maxX) = tokens
	elif numTokens==3:
		(imageField,maxX,maxY) = tokens
	if maxX: maxX=int(maxX)
	if maxY: maxY=int(maxY)
	return imageField, maxX, maxY

def boxFit(dimensions, maxX, maxY=None):
	""" Return scaled box of dimesion with maxsize=max mantaining aspect """
	x, y = dimensions
	if maxY==None: maxY=maxX
	if maxX==None: maxX=maxY
	if not (maxX or maxY): return dimensions
	if x<=maxX and y<=maxY: return (x, y)	# lesser or equal, no need to resize
	aspect=float(x)/y
	rx, ry= x, y
	if rx>maxX:
		rx=maxX
		ry=int(round(rx/aspect))
	if ry>maxY:
		ry=maxY
		rx=int(round(aspect*ry))
#	print "Ridimensiono x,y (%d,%d) a (%d,%d)," % (x,y, maxX, maxY), " = (%d,%d)" % (int(rx), int(ry))
	return (int(rx), int(ry))

def xlsRowHeight(foglio, y, height):
	rowstyle=sty(['size%s'%height])
	foglio.row(y).set_style(rowstyle)
	foglio.row(y).height_mismatch=0

class Sql2xls(object):
	"""
		Given a SQL query and a connection to a DB put sql results on a xls file
		If more table are returned they will be splitted over many worksheets.

		Query could have special comments to give some hint or description to generated worksheets
		--name: Titolo del foglio, scritto in alto
		--shortname: nome del foglio di lavoro
		--imageField: campoCheIndicaIlNomeDelFile[, maxX[, maxY]]
	"""
	def __init__(self, doc, con=None, query=None, processRowCallback=None, additionalHeaders=None, **kwargs):
		self.sheetCount=0
		self.query=query
		self.doc=doc
		self.con=con
		self.additionalHeaders=additionalHeaders
		self.processRowCallback=processRowCallback
		self.queryDescriptor=None
		self.enumerateTables=self.enumerateSQLTables
		self.sheetNames=[]
		self.shortNames=[]
		self.imageFields=[]
		self.__dict__.update(kwargs)	# create new attr on class based on kwargs

		for key, value in kwargs.items():
			pass

	@staticmethod
	def enumerateSQLTables(self):
		""" Enumerate tables starting from current condition (tipically connection and query)
			The table is a list of list, and the cursor descriptor (with fields name) is also returned in self.queryDescriptior
		"""
		if not self.con:
			return
		query=self.query
		import re	# used to parse special comment in query
		self.sheetNames=[g.strip() for g in re.findall(r"--name:(.*?)\n", query)]
		self.shortNames=[g.strip() for g in re.findall(r"--shortname:(.*?)\n", query)]
		self.imageFields=[g.strip() for g in re.findall(r"--imageField:(.*?)\n", query)]	# field name wich will go through mimagoFilename
		cur=self.con.cursor()
		cur.execute(self.query)
		while True:
			try:
				results=cur.fetchall()
				self.queryDescriptor=[desc[0] for desc in cur.description]
				yield results
			except:
				pass
			if not cur.nextset(): break

	def run(self):
		import os	# used to check file existance
		defaultTableNumber=1
		for results in self.enumerateTables(self):
			if self.sheetNames and self.sheetCount<len(self.sheetNames):
				title=self.sheetNames[self.sheetCount]
			else: title=None
			if self.shortNames and self.sheetCount<len(self.shortNames):
				shorttitle=self.shortNames[self.sheetCount]
			else: shorttitle=None

			if self.imageFields and self.sheetCount<len(self.imageFields):
				imageField, imageMaxX, imageMaxY = splitImageFormat(self.imageFields[self.sheetCount])
			else:
				imageField=None

			foglio=self.doc.add_sheet(shorttitle or "Results%s"%defaultTableNumber)
			resetSizes()
			if not shorttitle: defaultTableNumber+=1
			x=0
			y=0
			if title:	# print sheet title
#				print title,
				foglio.write(0,0, title,  sty(["b",'size300']))
				y=2

			headers=self.queryDescriptor
			if self.additionalHeaders:
				headers+=self.additionalHeaders
			for header in headers:	# print column description
				myWrite(foglio, y, x, header, sty(["b","center"]))
#				foglio.write(y,x, header, sty(["b","center"]) )
				x+=1

			y+=1
			x=0
			foglio.panes_frozen=True
			foglio.horz_split_pos=y
#			print len(results)

			tmpImgToRemove=False
			for row in results:
				self.drow=row2dict(row, self.queryDescriptor)
				self.fields=list(row)
				if imageField:
					self.imagePath=self.drow[imageField]
				else:
					self.imagePath=None
				if self.processRowCallback:
					self.processRowCallback(self)
				for field in self.fields:
#					if hasattr(field, "__len__"):
	#					print len(field)
#						columnSizes[x]=max(columnSizes.get(x,3000), 300*len(field))	# default width and computed column width
					myWrite(foglio, y, x, field)	# write fields
#					columnSizes[x]=max( columnSizes.get(x,3000),
#
#									)
					x+=1

				tmpImg='.tmp.bmp'
				if imageField:
#					print self.imagePath
					if os.path.isfile(self.imagePath):
						from PIL import Image as PILImage	# used to write and convert embedded images
						img=PILImage.open(file(self.imagePath, "rb"))
						img=img.convert('RGB')
						newsize=boxFit((img.size[0], img.size[1]), imageMaxX, imageMaxY) #make an Image a little bigger
						img=img.resize(newsize, PILImage.ANTIALIAS) #resize inplace
						try:
							tmpImage=file(tmpImg,'wb')
							tmpImgToRemove=True
							img.save( tmpImage, "BMP", quality=85)	# PNG is also valid
							tmpImage.close()
							xlsRowHeight(foglio, y, int(newsize[1]*13)) # l'altezza della riga è la dimensione dell'immagini in pixel * 13
							foglio.insert_bitmap(tmpImg, y, x)
						except:
							pass
					else:
						image=None
						myWrite(foglio, y, x, '***')

				x=0
				y+=1
				if y%1000==0:
#					print "Flushing to temp, we're at %s"%y
					foglio.flush_row_data()

			if tmpImgToRemove:
				os.unlink(tmpImg)

			updateSizes(foglio)

			self.sheetCount+=1

