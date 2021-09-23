from abc import ABC, abstractmethod
from ...writer import JsonnetWriter
import os, sys

class BaseConverter(ABC):
  @abstractmethod
  def convert(self, writer):
    pass
