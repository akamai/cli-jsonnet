import contextlib
import os
import re

def get_valid_filename(filename):
  """
  Return the given string converted to a string that can be used for a clean
  filename. Remove leading and trailing spaces; convert other spaces to
  underscores; and remove anything that is not an alphanumeric, dash,
  underscore, or dot.
  >>> get_valid_filename("john's portrait in 2004.jpg")
  'johns_portrait_in_2004.jpg'

  (stolen from: https://github.com/django/django/blob/master/django/utils/text.py)
  """
  s = filename.strip().replace(' ', '_')
  return re.sub(r'(?u)[^-\w.]', '', s)

@contextlib.contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.makedirs(new_dir, exist_ok=True)
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)