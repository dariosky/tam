from django.contrib.auth.decorators import permission_required
from django.shortcuts import render
from board.models import BoardMessage


@permission_required('board.view', '/')
def main(request, template_name='board/bacheca.html'):
	board_messages = BoardMessage.objects.filter(active=True)

	return render(
		request,
		template_name,
		{'board_messages': board_messages},
	)
