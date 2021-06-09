# -*- coding: utf-8 -*-

from ZPublisher.HTTPRequest import HTTPRequest
from plone.restapi.deserializer import json_body
from plone.restapi.services.content import update
from plone import api

import json


def create_request(base_request, body):
    request = HTTPRequest(
        base_request.stdin, base_request._orig_env, base_request.response
    )
    for attr in base_request.__dict__.keys():
        setattr(request, attr, getattr(base_request, attr))
    request.set("BODY", body)
    return request


class BasePatch(update.ContentPatch):
    def reply(self):
        data = json_body(self.request)
        children = []
        identifier = data.pop("internal_reference_no", None)
        if not identifier:
            raise ValueError(u"Missing identifier {0}".format(identifier))
        elements = api.content.find(
            context=self.context, internal_reference_no=identifier
        )
        if not elements:
            raise ValueError(u"There is no value for identifier {0}".format(identifier))
        self.context = self.context[elements[0].id]
        if "__children__" in data:
            children = data.pop("__children__")
            self.request.set("BODY", json.dumps(data))
        super(BasePatch, self).reply()
        if children:
            for child in children:
                request = create_request(self.request, json.dumps(child))
                child_request = BasePatch()
                child_request.context = self.context
                child_request.request = request
                child_request.reply()


class ImportPatch(BasePatch):
    def reply(self):
        data = json_body(self.request)
        for element in data["data"]:
            self.request.set("BODY", json.dumps(element))
            super(ImportPatch, self).reply()
