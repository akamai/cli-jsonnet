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

GITIGNORE_TERRAFORM = """
# Local .terraform directories
**/.terraform/*

# .tfstate files
*.tfstate
*.tfstate.*

# Crash log files
crash.log

# Exclude all .tfvars files, which are likely to contain sentitive data, such as
# password, private keys, and other secrets. These should not be part of version
# control as they are data points which are potentially sensitive and subject
# to change depending on the environment.
#
*.tfvars

# Ignore override files as they are usually used to override resources locally and so
# are not checked in
override.tf
override.tf.json
*_override.tf
*_override.tf.json

# Include override files you do wish to add to version control using negated pattern
#
# !example_override.tf

# Include tfplan files to ignore the plan output of command: terraform plan -out=tfplan
# example: *tfplan*

# Ignore CLI configuration files
.terraformrc
terraform.rc
"""