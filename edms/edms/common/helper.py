import json
from django.utils import timezone
from django.conf import settings

from edms.users.models import ForgotPasswordRequest


def custom_error(model_name, err):
    dict_err = json.loads(json.dumps(err))
    list_error = []
    if isinstance(dict_err, list):
        dict_err = dict_err[0]
    for x, y in dict_err.items():
        if isinstance(y, list):
            for error in range(len(y)):
                if "format" in y[error]:
                    y[error] = "format_invalid"
            err = f"{model_name}__{x}__{'_'.join([str(elem).replace(' ', '_') for elem in y])}"
            list_error.append(err.upper())
        if isinstance(y, dict):
            err = f"{model_name}__{list(y.keys())[0]}__invalid"
            list_error.append(err.upper())
    return list_error


def get_client_ip(request):
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def check_spam_forgot_password(ip_address):
    max_verify_time = timezone.now() - timezone.timedelta(
        hours=settings.PERIOD_MAX_TIMES_REQUEST_FORGET_PASSWORD
    )
    num_request = ForgotPasswordRequest.objects.filter(
        ip_address=ip_address,
        request_at__gte=max_verify_time
    ).count()
    if num_request >= settings.MAX_TIMES_REQUEST_FORGET_PASSWORD:
        return True
    return False
