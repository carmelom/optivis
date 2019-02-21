from __future__ import unicode_literals, division
from __future__ import absolute_import

from builtins import object
import abc
import weakref

from . import labels
from future.utils import with_metaclass

class AbstractBenchItem(with_metaclass(abc.ABCMeta, object)):
    """
    Abstract class for any bench item (e.g. component, link) to subclass. This does not include labels.
    """

    def __init__(self, labels=None, paramList=None, pykatObject=None, *args, **kwargs):
        self.labels = labels
        self.paramList = paramList
        self.pykatObject = pykatObject

    @abc.abstractmethod
    def getLabelOrigin(self):
        pass

    @abc.abstractmethod
    def getLabelAzimuth(self):
        pass

    @abc.abstractmethod
    def getSize(self):
        pass

    @property
    def labels(self):
        return self.__labels

    @labels.setter
    def labels(self, theseLabels):
        processedLabels = []

        if theseLabels is not None:
            for label in theseLabels:
                if not isinstance(label, labels.Label):
                    raise Exception('Specified label is not of type Label')

                # tell label what its attached item is
                label.item = self

                processedLabels.append(label)

        self.__labels = processedLabels

    @property
    def pykatObject(self):
        # references to external items should be made using weakref, so if they are deleted after the reference is made, the reference will be None
        if self.__pykatObject is None:
            raise Exception('External item is deleted')

        # handle weak references
        if isinstance(self.__pykatObject, weakref.ReferenceType):
            return self.__pykatObject()
        else:
            return self.__pykatObject

    @pykatObject.setter
    def pykatObject(self, pykatObject):
        self.__pykatObject = pykatObject
