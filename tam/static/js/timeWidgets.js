$(".time-widget").on('keyup',function () {
		if ((this.value.length > 2) && (this.value.indexOf(":") == -1)) {
			this.value = this.value.slice(0, 2) + ':' + this.value.slice(2);
		}
	}
).on('focusout', function () {
		/* append chat to time string to make it 5-char-long complete time*/
		var newvalue = this.value;
		if (newvalue == "") return;	// no string, keep it empty
		if (newvalue.length < 2 || newvalue.indexOf(":") == 1) {
			newvalue = "0" + newvalue;
		}
		if (newvalue.length < 3) newvalue += ":";
		if (newvalue.length < 5) newvalue += new Array(5 - newvalue.length + 1).join('0');
		if (this.value != newvalue) this.value = newvalue;
	});
