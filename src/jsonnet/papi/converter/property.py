from .ruleformatentity import RuleFormatEntityConverter
from .hostnames import HostnamesConverter
from .ruletree import RuleTreeConverter
from ....utils import get_valid_filename

class PropertyConverter(RuleFormatEntityConverter):
  def __init__(self, ruleFormat, property):
    super(PropertyConverter, self).__init__(ruleFormat)
    self.property = property

  @property
  def normalizedName(self):
    return get_valid_filename(self.property.name)

  @property
  def filename(self):
    return "{}.jsonnet".format(self.normalizedName)

  @property
  def path(self):
    """
    Path to this property's jsonnet file.
    """
    return self.filename

  @property
  def pathPrefix(self):
    """
    Path to the directory containing this rules children jsonnet files.
    """
    return self.normalizedName

  def convert(self):
    RuleTreeConverter(self.ruleFormat, self.property.ruleTree).convert()
    HostnamesConverter(self.ruleFormat, self.property.hostnames).convert()
