from django.http import JsonResponse
from django.shortcuts import render
from django.utils.timezone import now
from django.views.decorators.csrf import ensure_csrf_cookie


def status_api(request):
    return JsonResponse(
        {
            'status': 'ok',
            'servico': 'triagem-medica',
            'timestamp': now().isoformat(),
        }
    )


@ensure_csrf_cookie
def home(request):
    return render(request, 'home.html')


@ensure_csrf_cookie
def cadastro(request):
    return render(request, 'cadastro.html')


@ensure_csrf_cookie
def chat_teste(request):
    return render(request, 'chat_teste.html')
