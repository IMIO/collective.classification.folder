# -*- coding: utf-8 -*-
"""Module where all interfaces, events and exceptions live."""

from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class ICollectiveClassificationFolderLayer(IDefaultBrowserLayer):
    """Marker interface that defines a browser layer."""


class IServiceInCharge(Interface):
    """Marker interface of service in copy adapter"""


class IServiceInCopy(Interface):
    """Marker interface of service in copy adapter"""
