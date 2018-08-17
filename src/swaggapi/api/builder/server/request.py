import os
import json
import httplib

import requests
from django.http import JsonResponse
from django.views.generic import View

from swaggapi.api.builder.common.model import AbstractAPIModel
from swaggapi.api.builder.server.exceptions import ServerError, BadRequest


class Request(object):
    URI = None
    DEFAULT_MODEL = None
    DEFAULT_RESPONSES = {}
    PARAMS_MODELS = {
        "get": None,
        "post": None,
        "delete": None,
        "put": None,
        "head": None,
        "patch": None,
        "trace": None,
    }
    RESPONSES_MODELS = {
        "get": None,
        "post": None,
        "delete": None,
        "put": None,
        "head": None,
        "patch": None,
        "trace": None,
    }
    TAGS = {
        "get": [],
        "post": [],
        "delete": [],
        "put": [],
        "head": [],
        "patch": [],
        "trace": [],
    }
    valid_methods = ["get", "post", "delete", "put", "head", "patch", "trace"]

    @classmethod
    def execute(cls, base_url, method, data, logger=None):
        url = os.path.join(base_url, cls.URI)
        if logger:
            logger.debug("request: %s - %s - %s", url, method, data)

        response = requests.request(method, url, json=data)

        if logger:
            logger.debug("response: %s(%s) - %s",
                         httplib.responses[response.status_code],
                         response.status_code,
                         response.content)

        return response


class DjangoRequestView(View, Request):
    def dispatch(self, request, *args, **kwargs):
        try:
            method = request.method.lower()
            model = self.PARAMS_MODELS[method] \
                if self.PARAMS_MODELS[method] is not None else \
                        self.DEFAULT_MODEL

            if not (model is None or issubclass(model, AbstractAPIModel)):
                raise ServerError(
                    details="Method params model should be subclass of"
                            "{}".format(AbstractAPIModel),
                    model=model,
                    response=request
                )

            if model is not None and issubclass(model, AbstractAPIModel):
                try:
                    request_params = json.loads(request.body)

                except Exception as e:
                    raise ServerError(
                        details=e.message,
                        model=model,
                        response=request.body
                    )
                try:
                    model = model(request_params)

                except Exception as e:
                    raise ServerError(
                        details=e.message,
                        model=model,
                        response=request_params
                    )


            request.model = model
            return super(DjangoRequestView, self).dispatch(
                request, *args, **kwargs)

        except BadRequest as e:
            return JsonResponse(e.message,
                                status=httplib.BAD_REQUEST)

        except ServerError as e:
            return JsonResponse(e.encode(),
                                status=httplib.INTERNAL_SERVER_ERROR)

        except Exception as e:
            raise JsonResponse(e.message,
                                status=httplib.INTERNAL_SERVER_ERROR)

    @classmethod
    def implemented_methods(cls):
        return [m.lower() for m in cls.valid_methods if hasattr(cls, m)]