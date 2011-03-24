#!/usr/bin/env python
#-- coding: iso8859-15 --
import xlwt
from xlwt import Workbook #@UnusedImport
import datetime
from decimal import Decimal
import logging
logging.basicConfig(
				level=logging.DEBUG,
				format='%(message)s'
			)

knownStyles = {}	# list of already cached prepared Styles
knownPattern = {}

def styleCopy(style=None, **kwargs):
	" Restituisce uno stile copia di quello passato con le proprietà  indicate "
	# dallo stile passato ricreo propList, num_format, background_color e foreground_color
	proplist = []
	newParameters = {}
	if style:
		if style.font.bold:
			proplist.append("b")
		if (style.alignment.horz, style.alignment.vert) == (xlwt.Alignment.HORZ_CENTER, xlwt.Alignment.VERT_CENTER):
			proplist.append("center")
		elif (style.alignment.horz, style.alignment.vert) == (xlwt.Alignment.HORZ_RIGHT, xlwt.Alignment.VERT_CENTER):
			proplist.append("right")
		if style.alignment.wrap == xlwt.Alignment.WRAP_AT_RIGHT:
			proplist.append("wrap")
		if style.borders.left > 0:
			proplist.append("border%s" % style.borders.left)	# tutti i bordi hanno lo stesso spessore
		if style.font.name <> 'Arial':
			proplist.append(style.font.name)	# il nome del font
		if style.font.height <> 200:
			proplist.append('size%s' % style.font.height)	# dimensione
		if style.pattern.pattern_fore_colour <> 64:
			newParameters['background_color'] = style.pattern.pattern_fore_colour
	newParameters.update(kwargs)
	return sty(proplist, **newParameters)


def sty(propList=[], num_format="general", background_color=None, foreground_color=None):
	""" Given a list of properties, create an Excel style """
	if isinstance(propList, str): propList = [propList]
	propList.sort()	#sort so order is ininfluent
	stylename = "-".join(propList)
	if num_format:
		stylename += "-" + unicode(num_format)
	if	background_color or foreground_color:
		patternName = "%s/%s" % (foreground_color, background_color)
		stylename += "-" + patternName
	else:
		patternName = None

	if stylename in knownStyles.keys():
		return knownStyles[stylename]

	style = xlwt.XFStyle()
	align = xlwt.Alignment()
	align.vert = xlwt.Alignment.VERT_CENTER	# VERT_TOP, VERT_BOTTOM
	font = xlwt.Font()
	borders = xlwt.Borders()

	style.num_format_str = num_format or 'general'	#numeric format

	if patternName:
		if patternName in knownPattern:
			pattern = knownPattern[patternName]
		else:
			pattern = xlwt.Pattern()
			pattern.pattern_fore_colour = background_color
			pattern.pattern = style.pattern.SOLID_PATTERN
			knownPattern[patternName] = pattern

		style.pattern = pattern


	for prop in propList:
		if prop in ("b", "bold"):
			font.bold = True
		elif prop == "center":
			align.horz = xlwt.Alignment.HORZ_CENTER
			align.vert = xlwt.Alignment.VERT_CENTER
		elif prop == "right":
			align.horz = xlwt.Alignment.HORZ_RIGHT
			align.vert = xlwt.Alignment.VERT_CENTER
		elif prop == "wrap":
			align.wrap = xlwt.Alignment.WRAP_AT_RIGHT
		elif prop.startswith("border"):
			if prop[-1] != "r":	#"border2" give borderswidth 2
				weight = int(prop[-1])
			else:				#"border" gives width 1
				weight = 1
			borders.left = weight
			borders.right = weight
			borders.top = weight
			borders.bottom = weight
		elif prop.startswith("size"):
			if prop[4:]:	#"size2" give size 2
				size = int(prop[4:])
			else:				#"size" gives size 10
				size = 10
			font.height = size
		else:
			font.name = prop

	style.borders = borders
	style.alignment = align
	style.font = font

	knownStyles[stylename] = style
	return style


class XlsColors:
	yellow = 51
	purple = 37
	violet = 0x24
xlsColWidth = {}

def resetSizes():
	""" Reset sheet sizes """
	global xlsColWidth
	xlsColWidth = {}

def updateSizes(sheet):
	""" Apply suggested width to all columns """
	for x, col in xlsColWidth.items():	# trovo le larghezze di colonna
		logging.debug( "setting col(%d) to %d" % (x, col))
		sheet.col(x).width = min(col, 65535)	# set a max column width

def styleFromField(field, stile=sty(), **kwargs):
	" Restituisco uno stile dato dal campo, basato sullo stile indicato "
	if stile.num_format_str == "general":
		if isinstance(field, datetime.datetime) and field.hour == field.min == field.second == field.microsecond == 0:
			field = field.date()
		if isinstance(field, datetime.datetime):
			return styleCopy(stile, num_format="DD/MM/YYYY HH:MM")
#			stile.num_format_str="DD/MM/YYYY HH:MM"
		elif isinstance(field, datetime.date):
			return styleCopy(stile, num_format="DD/MM/YYYY")
#			stile.num_format_str="DD/MM/YYYY"

	return stile

def myWrite(sheet, y, x, field, style=sty()):
	if isinstance(field, Decimal):
		field = float(field)
	elif field is None:
		field = ""
	try:
		if hasattr(field, "decode") and not isinstance(field, unicode):
			field = field.decode('utf-8')
	except:
		if hasattr(field, "decode") and not isinstance(field, unicode):
			field = field.decode('iso8859-15')

	stile = styleFromField(field, style)
	sheet.write(y, x, field, stile)
	if isinstance(field, datetime.datetime):
		field_length = 16
	elif isinstance(field, datetime.date):
		field_length = 10
	elif isinstance(field, xlwt.Formula):
		field_length = 10;
	else:
		field_length = len(unicode(field))
	xlsColWidth[x] = max(xlsColWidth.get(x, 3000), 310 * field_length)	# default width and computed column width

def row2dict(row, desc):
	""" Trasforma una tupla estratta con fetchrow in un dizionario usando un cursore"""
	result = {}
	for i, field in enumerate(desc):
		if i >= len(row): break
		if hasattr(row[i], "strip") and not isinstance(row[i], unicode):
			result[field] = unicode(row[i].strip(), errors='ignore')
		else:
			result[field] = row[i]
	return result

def splitImageFormat(format):
	""" return a tuple with: fieldOfImage, maxX, maxY given a format """
	tokens = format.split(",")
	numTokens = len(tokens)
	imageField = None
	maxX = None
	maxY = None
	if numTokens == 0:
		pass
	elif numTokens == 1:
		(imageField,) = tokens
	elif numTokens == 2:
		(imageField, maxX) = tokens
	elif numTokens == 3:
		(imageField, maxX, maxY) = tokens
	if maxX: maxX = int(maxX)
	if maxY: maxY = int(maxY)
	return imageField, maxX, maxY

def boxFit(dimensions, maxX, maxY=None):
	""" Return scaled box of dimesion with maxsize=max mantaining aspect """
	x, y = dimensions
	if maxY == None: maxY = maxX
	if maxX == None: maxX = maxY
	if not (maxX or maxY): return dimensions
	if x <= maxX and y <= maxY: return (x, y)	# lesser or equal, no need to resize
	aspect = float(x) / y
	rx, ry = x, y
	if rx > maxX:
		rx = maxX
		ry = int(round(rx / aspect))
	if ry > maxY:
		ry = maxY
		rx = int(round(aspect * ry))
	#	 "Ridimensiono x,y (%d,%d) a (%d,%d)," % (x,y, maxX, maxY), " = (%d,%d)" % (int(rx), int(ry))
	return (int(rx), int(ry))

def xlsRowHeight(foglio, y, height):
	rowstyle = sty(['size%s' % height])
	foglio.row(y).set_style(rowstyle)
	foglio.row(y).height_mismatch = 0

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
		self.sheetCount = 0
		self.query = query
		self.doc = doc
		self.con = con
		self.additionalHeaders = additionalHeaders
		self.processRowCallback = processRowCallback
		self.queryDescriptor = None
		self.enumerateTables = self.enumerateSQLTables
		self.sheetNames = []
		self.shortNames = []
		self.imageFields = []
		self.__dict__.update(kwargs)	# create new attr on class based on kwargs

	@staticmethod
	def enumerateSQLTables(self):
		""" Enumerate tables starting from current condition (tipically connection and query)
			The table is a list of list, and the cursor descriptor (with fields name) is also returned in self.queryDescriptior
		"""
		if not self.con:
			return
		query = self.query
		import re	# used to parse special comment in query
		self.sheetNames = [g.strip() for g in re.findall(r"--name:(.*?)\n", query)]
		self.shortNames = [g.strip() for g in re.findall(r"--shortname:(.*?)\n", query)]
		self.imageFields = [g.strip() for g in re.findall(r"--imageField:(.*?)\n", query)]	# field name wich will go through mimagoFilename
		cur = self.con.cursor()
		cur.execute(self.query)
		while True:
			try:
				results = cur.fetchall()
				self.queryDescriptor = [desc[0] for desc in cur.description]
				yield results
			except:
				pass
			if not cur.nextset(): break

	def run(self):
		import os	# used to check file existance
		defaultTableNumber = 1
		for results in self.enumerateTables(self):
			if self.sheetNames and self.sheetCount < len(self.sheetNames):
				title = self.sheetNames[self.sheetCount]
			else: title = None
			if self.shortNames and self.sheetCount < len(self.shortNames):
				shorttitle = self.shortNames[self.sheetCount]
			else: shorttitle = None

			if self.imageFields and self.sheetCount < len(self.imageFields):
				imageField, imageMaxX, imageMaxY = splitImageFormat(self.imageFields[self.sheetCount])
				from PIL import Image as PILImage	# used to write and convert embedded images @UnresolvedImport
			else:
				imageField = None

			foglio = self.doc.add_sheet(shorttitle or "Results%s" % defaultTableNumber)
			resetSizes()
			if not shorttitle: defaultTableNumber += 1
			x = 0
			y = 0
			if title:
				foglio.write(0, 0, title, sty(["b", 'size300']))
				y = 2

			headers = self.queryDescriptor
			if self.additionalHeaders:
				headers += self.additionalHeaders
			for header in headers:
				myWrite(foglio, y, x, header, sty(["b", "center"]))
#				foglio.write(y,x, header, sty(["b","center"]) )
				x += 1

			y += 1
			x = 0
			foglio.panes_frozen = True
			foglio.horz_split_pos = y
			logging.debug("%s %d" % (title, len(results)))

			tmpImgToRemove = False
			for row in results:
				self.drow = row2dict(row, self.queryDescriptor)
				self.fields = list(row)
				if imageField:
					self.imagePath = self.drow[imageField]
				else:
					self.imagePath = None
				if self.processRowCallback:
					self.processRowCallback(self)
				for field in self.fields:
#					if hasattr(field, "__len__"):
#						columnSizes[x]=max(columnSizes.get(x,3000), 300*len(field))	# default width and computed column width
					myWrite(foglio, y, x, field)	# write fields
#					columnSizes[x]=max( columnSizes.get(x,3000),
#
#									)
					x += 1

				tmpImg = '.tmp.bmp'
				if imageField:
					if os.path.isfile(self.imagePath):
						img = PILImage.open(file(self.imagePath, "rb"))
						img = img.convert('RGB')
						newsize = boxFit((img.size[0], img.size[1]), imageMaxX, imageMaxY) #make an Image a little bigger
						img = img.resize(newsize, PILImage.ANTIALIAS) #resize inplace
						try:
							tmpImage = file(tmpImg, 'wb')
							tmpImgToRemove = True
							img.save(tmpImage, "BMP", quality=85)	# PNG is also valid
							tmpImage.close()
							xlsRowHeight(foglio, y, int(newsize[1] * 13)) # l'altezza della riga Ãš la dimensione dell'immagini in pixel * 13
							foglio.insert_bitmap(tmpImg, y, x)
						except:
							pass
					else:
						myWrite(foglio, y, x, '***')

				x = 0
				y += 1
				if y % 1000 == 0:
					logging.debug("Flushing to temp, we're at %s" % y)
					foglio.flush_row_data()

			if tmpImgToRemove:
				os.unlink(tmpImg)

			updateSizes(foglio)

			self.sheetCount += 1
