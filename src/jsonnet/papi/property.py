from ..writer import JsonnetWriter
import sys
from ...edgegrid import Session

class Property:
  @staticmethod
  def getHostnames(edgerc, section, name, version="latest", accountSwitchKey=None):
    session = Session(edgerc, section, accountSwitchKey)

    print("*** searching for property...", name, file=sys.stderr)
    response = session.post("/papi/v1/search/find-by-value", json={"propertyName": name})
    if not response.ok:
      raise RuntimeError(
        (
          "Endpoint /papi/v1/search/find-by-value said:\n"
          "%s %s\n"
          "%s\n"
        ) % (response.status_code, response.reason, response.text)
      )

    versions = response.json().get("versions").get("items")
    if len(versions) == 0:
      raise RuntimeError("not found")

    pid = next(version.get("propertyId") for version in versions)
    if version == "latest":
      version = max(v.get("propertyVersion") for v in versions)
      print("*** Latest is v%s" % version, file=sys.stderr)

    print("*** retrieving property hostnames for", name, version, file=sys.stderr)
    url = "/papi/v1/properties/{}/versions/{}/hostnames".format(pid, version)
    response = session.get(url)
    if not response.ok:
      raise RuntimeError(
        (
          "Endpoint %s said:\n"
          "%s %s\n"
          "%s\n"
        ) % (url, response.status_code, response.reason, response.text)
      )
    hostnames = response.json().get('hostnames').get('items')
    return hostnames

  @staticmethod
  def get(edgerc, section, name, version="latest", ruleFormat=None, accountSwitchKey=None):
    session = Session(edgerc, section, accountSwitchKey)

    print("*** searching for property...", name, file=sys.stderr)
    response = session.post("/papi/v1/search/find-by-value", json={"propertyName": name})
    if not response.ok:
      raise RuntimeError(
        (
          "Endpoint /papi/v1/search/find-by-value said:\n"
          "%s %s\n"
          "%s\n"
        ) % (response.status_code, response.reason, response.text)
      )

    versions = response.json().get("versions").get("items")
    if len(versions) == 0:
      raise RuntimeError("not found")

    pid = next(version.get("propertyId") for version in versions)
    if version == "latest":
      version = max(v.get("propertyVersion") for v in versions)
      print("*** Latest is v%s" % version, file=sys.stderr)

    print("*** retrieving property rule tree for", name, pid, version, file=sys.stderr)
    headers = {}
    if ruleFormat is not None:
      accept = "application/vnd.akamai.papirules.{}+json".format(ruleFormat.ruleFormat)
      headers["Accept"] = accept
    url = "/papi/v1/properties/{}/versions/{}/rules".format(pid, version)
    response = session.get(url, headers=headers, params=dict(validateRules=False, validateMode="fast"))
    if not response.ok:
      raise RuntimeError(
        (
          "Endpoint %s said:\n"
          "%s %s\n"
          "%s\n"
        ) % (url, response.status_code, response.reason, response.text)
      )
    ruleTree = response.json()

    print("*** retrieving property hostnames for", name, version, file=sys.stderr)
    url = "/papi/v1/properties/{}/versions/{}/hostnames".format(pid, version)
    response = session.get(url)
    if not response.ok:
      raise RuntimeError(
        (
          "Endpoint %s said:\n"
          "%s %s\n"
          "%s\n"
        ) % (url, response.status_code, response.reason, response.text)
      )
    hostnames = response.json().get('hostnames').get('items')
    return Property(name, ruleTree, hostnames)

  def __init__(self, name, ruleTree, hostnames):
    self.name = name
    self.ruleTree = ruleTree
    self.hostnames = hostnames
