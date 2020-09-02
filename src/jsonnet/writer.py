import sys
# pylint: disable=import-error
py3 = sys.version_info[0] >= 3
if py3:
  from io import StringIO
else:
  from StringIO import StringIO

class JsonnetWriter(StringIO):
  def __init__(self):
    super(JsonnetWriter, self).__init__()

  def writeln(self, s = ""):
    self.write(s + "\n")
