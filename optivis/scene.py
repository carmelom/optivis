from __future__ import unicode_literals, division
from __future__ import absolute_import

from past.builtins import basestring
from builtins import object
import datetime

from . import geometry
from .bench import components
from .bench import links
from .layout import constraints


class Scene(object):
    links = []
    constraints = []

    def __init__(self, title=None, reference=None):
        if title is None:
            title = datetime.datetime.now().strftime('%Y-%M-%d %H:%M')

        self.title = title
        self.reference = reference

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, title):
        if not isinstance(title, basestring):
            raise Exception('Specified title is not of type basestring')

        self.__title = title

    @property
    def reference(self):
        """
        Reference component for layout. The azimuth of this component
        is used as the absolute reference when laying out scenes.
        """

        return self.__reference

    @reference.setter
    def reference(self, component):
        if component is not None:
            # check component is valid object
            if not isinstance(component, components.AbstractComponent):
                raise Exception(
                    'Specified component is not of type AbstractComponent')

        self.__reference = component

    def link(self, *args, **kwargs):
        link = links.Link(*args, **kwargs)

        self.addLink(link)

    def addLink(self, link):
        if not isinstance(link, links.AbstractLink):
            raise Exception('Specified link is not of type AbstractLink')

        self.links.append(link)

    def addConstraint(self, constraint):
        if not isinstance(constraint, layout.constraints.AbstractConstraint):
            raise Exception(
                'Specified constraint is not of type AbstractConstraint')

        self.constraints.append(constraint)

    def getComponents(self):
        components = []

        for link in self.links:
            if link.inputNode.component not in components:
                components.append(link.inputNode.component)

            if link.outputNode.component not in components:
                components.append(link.outputNode.component)

        return components

    def getBoundingBox(self):
        # set initial bounds to infinity
        lowerBound = geometry.Coordinates(float('inf'), float('inf'))
        upperBound = geometry.Coordinates(float('-inf'), float('-inf'))

        # loop over components to find actual bounds
        for component in self.getComponents():
            (thisLowerBound, thisUpperBound) = component.getBoundingBox()

            if thisLowerBound.x < lowerBound.x:
                lowerBound.x = thisLowerBound.x
            if thisLowerBound.y < lowerBound.y:
                lowerBound.y = thisLowerBound.y
            if thisUpperBound.x > upperBound.x:
                upperBound.x = thisUpperBound.x
            if thisUpperBound.y > upperBound.y:
                upperBound.y = thisUpperBound.y

        return (lowerBound, upperBound)

    def getSize(self):
        (lowerBound, upperBound) = self.getBoundingBox()

        return upperBound.translate(lowerBound.flip())
