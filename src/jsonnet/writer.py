import textwrap
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

  def writeMultilineString(self, s):
    wrapped = "\n".join(textwrap.wrap(s, width=80, initial_indent="    ", subsequent_indent="    "))
    self.write('|||\n{}\n|||'.format(wrapped))

  def getvalue(self):
    val = super(JsonnetWriter, self).getvalue()
    try:
      proc = Popen(["jsonnetfmt", "-"], stdout=PIPE, stdin=PIPE)
      out = proc.communicate(input=val.encode())[0]
      if proc.returncode == 0:
        val = out.decode("utf-8")
    except:
      pass
    return val
