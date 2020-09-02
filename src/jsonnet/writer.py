import sys
# pylint: disable=import-error
py3 = sys.version_info[0] >= 3
if py3:
  from io import StringIO
else:
  from StringIO import StringIO

from subprocess import Popen, PIPE

class JsonnetWriter(StringIO):
  def __init__(self):
    super(JsonnetWriter, self).__init__()

  def writeln(self, s = ""):
    self.write(s + "\n")

  def getvalue(self):
    val = super(JsonnetWriter, self).getvalue()
    try:
      val = Popen(["jsonnetfmt", "-"], stdout=PIPE, stdin=PIPE).communicate(input=val.encode())[0]
      val = val.decode("utf-8")
    except:
      pass
    return val
