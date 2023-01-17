# coding=utf-8
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from board.models import BoardMessage


@permission_required("board.view", "/")
def main(request, template_name="board/bacheca.html"):
    if request.method == "POST":
        # invio senza socket
        if "deleteMessage" in request.POST:
            messageId = request.POST.get("deleteMessage", None)
            if messageId:
                message = BoardMessage.objects.get(id=messageId)
                if message.author != request.user:
                    messages.error(request, "Non puoi cancellare un messaggio non tuo.")
                else:
                    print("cancello il messaggio", message)
                    message.delete()
                    messages.success(request, "Messaggio cancellato.")
                    # TODO: Warn via socket of the deleted message
        else:
            messageText = request.POST.get("m", None)
            attachment = request.FILES.get("attach", None)
            if messageText or attachment:
                newMessage = BoardMessage(
                    author=request.user,
                    message=messageText,
                    date=timezone.now(),
                    attachment=attachment,
                )
                newMessage.save()
                # TODO: Warn via socket of the new message
        return HttpResponseRedirect(reverse("board-home"))

    board_messages = BoardMessage.objects.filter(active=True)

    return render(
        request,
        template_name,
        {"board_messages": board_messages},
    )
