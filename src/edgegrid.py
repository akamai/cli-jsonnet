import sys, pathlib
import requests
from akamai.edgegrid import EdgeGridAuth, EdgeRc
from .logging import logger

py3 = sys.version_info[0] >= 3
if py3:
	from configparser import ConfigParser
	from urllib import parse
else:
	import ConfigParser
	# pylint: disable=import-error
	import urlparse as parse

class Session(requests.Session):
	def __init__(self, edgerc, section, accountSwitchKey=None, **kwargs):
		super(Session, self).__init__(**kwargs)
		self.edgerc = EdgeRc(str(pathlib.Path(edgerc).expanduser()))
		self.section = section

		self.accountSwitchKey = None
		if self.edgerc.has_option(section, "account_key"):
			self.accountSwitchKey = self.edgerc.get(section, "account_key")
		if accountSwitchKey != None:
			self.accountSwitchKey = accountSwitchKey

		self.auth = EdgeGridAuth(
			client_token=self.edgerc.get(section, "client_token"),
			client_secret=self.edgerc.get(section, "client_secret"),
			access_token=self.edgerc.get(section, "access_token"),
		)

	def request(self, method, url, params=None, **kwargs):
		baseUrl = "https://{host}".format(host=self.edgerc.get(self.section, "host"))
		url = parse.urljoin(baseUrl, url)
		if self.accountSwitchKey:
			params = params if params is not None else dict()
			params.update(accountSwitchKey=self.accountSwitchKey)
		return super(Session, self).request(method, url, params=params, **kwargs)
