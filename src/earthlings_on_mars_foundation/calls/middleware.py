"""HTTP request logging middleware."""

from __future__ import annotations

import contextlib
import json
import logging
import traceback

from django.http import Http404, HttpRequest, HttpResponse
from django.http.request import RawPostDataException
from django.utils.deprecation import MiddlewareMixin

request_logger = logging.getLogger("django.customRequestLogger")


class SessionLogMiddleware(MiddlewareMixin):
    """Log requests."""

    # def __init__(self, get_response):
    #    self.get_response = get_response

    # def __call__(self, request):
    #    start_time = time.monotonic()
    #    log_data = {
    #        "remote_address": request.META["REMOTE_ADDR"],
    #        "server_hostname": socket.gethostname(),
    #        "request_method": request.method,
    #        "request_path": request.get_full_path(),
    #    }

    #    req_body = json.loads(request.body.decode("utf-8")) if request.body else {}
    #    log_data["request_body"] = req_body

    #    # request passes on to controller
    #    response = self.get_response(request)

    #    # add runtime to our log_data
    #    if response and response["content-type"] == "application/json":
    #        response_body = json.loads(response.content.decode("utf-8"))
    #        log_data["response_body"] = response_body
    #    log_data["run_time"] = time.time() - start_time

    #    request_logger.info(msg=log_data)

    #    return response

    def save(self, request: HttpRequest, response: HttpResponse | None = None, exception: Exception | None = None, status_code: int | None = None) -> None:
        """Save data about a request and response pair."""
        headers = request.headers
        response_data = None
        request_data = None

        try:
            request_data = json.loads(self.clean_text(request.body))
        except RawPostDataException:
            response_data = "RawPostDataException: You cannot access body after reading from request's data stream"
        except Exception:  # noqa: BLE001
            with contextlib.suppress(Exception):
                request_data = self.clean_text(request.body)

        if "CONTENT_TYPE" not in headers or headers["CONTENT_TYPE"] != "application/x-www-form-urlencoded":
            try:
                response_data = json.loads(self.clean_text(response.content))
            except RawPostDataException:
                response_data = "RawPostDataException: You cannot access body after reading from request's data stream"
            except Exception:  # noqa: BLE001
                with contextlib.suppress(Exception):
                    response_data = self.clean_text(response.content)

        log_data = {
            #'HEADERS': headers,
            "METHOD": request.method,
            #'USER': {
            #    'ip_address': self.get_client_ip(request)
            # },
            "URL": request.build_absolute_uri(),
            "REQUEST_DATA": request_data,
            "RESPONSE_DATA": response_data,
            "ERROR_MESSAGE": exception,
            "STATUS_CODE": status_code,
        }

        request_logger.error(log_data) if exception else request_logger.info(log_data)

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Log exception."""
        status_code = 404 if isinstance(exception, Http404) else 500

        try:
            self.save(request, exception=exception, status_code=status_code)
        except Exception:
            error = traceback.format_exc()
            request_logger.exception(error)

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response."""
        try:
            response_data = {
                "request": request,
                "response": response,
                "status_code": response.status_code,
            }

            if "/admin" not in request.path and "/static" not in request.path:
                self.save(**response_data)
        except Exception:
            error = traceback.format_exc()
            request_logger.exception(error)
        return response

    def clean_text(self, text: str | bytes) -> str:
        """Ensure text is loggable."""
        if isinstance(text, bytes):
            try:
                return text.decode("utf-8").replace("\\n", "").replace("\\t", "").replace("\\r", "")
            except Exception:
                request_logger.exception()
        return str(text)

    def get_client_ip(self, request: HttpResponse) -> str:
        """Get a client's IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

        return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")
