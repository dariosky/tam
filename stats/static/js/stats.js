$(function () {
	$(".accordhead").click(function () {
		$(this).next().toggle('slow');
		return false;
	});

	$('.daterange').datepicker();
	dragula([document.getElementById("available"), document.getElementById("enabled")]);
	$('#statsform').submit(
		function () {
			var $this = $(this);
			if ($('input[name="qfilter"]:checked').length == 0) {
				$this.append(
					$("<input name='qfilter' type='hidden'/>").val("none")
				);
			}
			var groupers = [];
			$("#enabled").find('div').each(function () {
				groupers.push($(this).text().toLowerCase())
			});
			$this.append(
				$("<input name='qgrouper' type='hidden'/>").val(groupers.join(",") || "none")
			);
		}
	);
});

function setDateRange(month_delta) {
	function setDateValue($target, date) {
		$target.val(date.getDate() + "/" + (date.getMonth() + 1) + "/" + date.getFullYear());
	}

	var today = new Date(),
		start = new Date(today.getTime()), end;
	start.setDate(1);	// first day of the month
	start.setMonth(today.getMonth() + month_delta);	// this takes care also of changing years
	end = new Date(start);

	end.setMonth(start.getMonth() + 1);
	end.setDate(end.getDate() - 1);
	setDateValue($('#data_start'), start);
	setDateValue($('#data_end'), end);
}
