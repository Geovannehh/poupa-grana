from datetime import timedelta

from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import LoginAttempt


class LimitedLoginView(LoginView):
    def post(self, request, *args, **kwargs):
        before = timezone.now() - timedelta(minutes=15)
        LoginAttempt.objects.filter(created_at__lt=before).delete()
        identity = (
            request.META.get("REMOTE_ADDR", "")
            + "|"
            + request.POST.get("username", "").casefold()[:150]
        )
        self.attempt_key = salted_hmac("login-rate", identity, algorithm="sha256").hexdigest()
        if LoginAttempt.objects.filter(key=self.attempt_key, created_at__gte=before).count() >= 10:
            response = HttpResponse("Muitas tentativas. Aguarde 15 minutos.", status=429)
            response["Retry-After"] = "900"
            return response
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        LoginAttempt.objects.create(key=self.attempt_key)
        return super().form_invalid(form)

    def form_valid(self, form):
        LoginAttempt.objects.filter(key=self.attempt_key).delete()
        return super().form_valid(form)
