from __future__ import division

import datetime

from BenchObjects import Component, Link

class Bench(object):
  ###
  # Optivis canvas components

  components = []
  links = []
  
  def __init__(self, title=None):
    if title is None:
      title = datetime.datetime.now().strftime('%Y-%M-%d %H:%M')
    
    self.title = title
    
    return
    
  def addComponent(self, component):
    if not isinstance(component, Component):    
      raise Exception('Specified component is not of type Component')
    
    self.components.append(component)
  
  def addLink(self, link):
    if not isinstance(link, Link):
      raise Exception('Specified link is not of type Link')
    
    if not link.inputNode.component in self.components:
      raise Exception('Input node component has not been added to table')
    
    if not link.outputNode.component in self.components:
      raise Exception('Output node component has not been added to table')
    
    self.links.append(link)

  @property
  def title(self):
    return self.__title

  @title.setter
  def title(self, title):
    self.__title = title