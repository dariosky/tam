# coding=utf-8
from decimal import Decimal
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


def moneyfmt(value, places=2, curr="", sep=".", dp=",", pos="", neg="-", trailneg=""):
    """Convert Decimal to a money formatted string.

    places:  required number of places after the decimal point
    curr:	optional currency symbol before the sign (may be blank)
    sep:	 optional grouping separator (comma, period, space, or blank)
    dp:	  decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:	 optional sign for positive numbers: '+', space or blank
    neg:	 optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places  # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else "0")
    build(dp)
    if not digits:
        build("0")
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return "".join(reversed(result))


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    # oldTemplate = None	# reset count at any template change

    def showPage(self):
        # pagina = getattr(self, 'pagina', 1)
        # print "pagina %d" % pagina
        # self.pagina = pagina + 1

        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def apply_page_numbers(self):
        num_pages = len(self._saved_page_states)

        for pagenum, state in enumerate(self._saved_page_states):
            self.__dict__.update(state)
            if num_pages > 1:
                self.draw_page_number(pagenum + 1, num_pages)
            canvas.Canvas.showPage(self)

        self._saved_page_states = []

    def save(self):
        """add page info to each page (page x of y) if y>1"""
        self.apply_page_numbers()

        canvas.Canvas.save(self)

    def draw_page_number(self, pagenum, page_count):
        self.setFont("Helvetica", 7)
        width = self._pagesize[0]
        self.drawRightString(
            width / 2, 1 * cm, "Pagina %d di %d" % (pagenum, page_count)
        )
