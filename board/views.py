from django.shortcuts import  render
from board.models import BoardMessage


def main(request, template_name='board/main.html'):
	board_messages = BoardMessage.objects.filter(active=True)

	return render(
				request,
				template_name,
				{'board_messages':board_messages},
			)
