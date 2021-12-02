import os
import textwrap
import sys
import json
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
    if len(s) < 80:
      self.write(json.dumps(s))
    else:
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

  def dump(self, path):
    data = self.getvalue()
    dirname = os.path.dirname(path)
    if len(dirname):
      os.makedirs(dirname, exist_ok=True)
    with open(path, "w", newline='\n') as fd:
      fd.write(data)
    print(os.path.realpath(path), file=sys.stderr)

