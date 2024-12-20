from __future__ import annotations

DOCUMENTATION = """
options:
  ipam_client:
    description: The URL, including the API client, to the API endpoint
    required: False
    type: string
    version_added: 2.10
  ipam_token:
    description: The API token to access the endpoint
    required: False
    type: string
    version_added: 2.10
  with_mac_address:
    description: Return only items with a MAC address
    required: False
    type: boolean
    default: False
    version_added: 2.10
  with_hostname:
    description: Return only items with a hostname
    required: False
    type: boolean
    default: False
    version_added: 2.10
  all_child_subnets:
    description: Descend into child subnets
    required: False
    type: boolean
    default: True
    version_added: 2.10
"""

EXAMPLES = """
"""

RETURN = """
"""

from urllib.error import HTTPError, URLError

import json
from ansible.errors import AnsibleError
from ansible.module_utils.common.text.converters import to_text, to_native
from ansible.module_utils.urls import open_url, ConnectionError, SSLValidationError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()

def get_ipam_connection_params(variables, option_ipam_client = None, option_ipam_token = None):
    ipam_client = variables.get('ipam_client', None)
    ipam_token  = variables.get('ipam_token',  None)

    if option_ipam_client:
        ipam_client = option_ipam_client

    if option_ipam_token:
        ipam_token = option_ipam_token

    if not ipam_client or not ipam_token:
        raise AnsibleError("Connection values are not complete. Requires at least ipam_client and ipam_token to be set.")

    return ipam_client, ipam_token

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        for id in terms:
            self.set_options(var_options=variables, direct=kwargs)

            ipam_client, ipam_token = get_ipam_connection_params(variables, self.get_option('ipam_client'), self.get_option('ipam_token'))
            headers={"token": ipam_token}

            ret = []

            subnets=[id]

            if self.get_option('all_child_subnets'):
                api=f"{ipam_client}/subnets/{id}/slaves_recursive/"
                try:
                    display.vvvv(f'Accessing api: {api}')
                    response = open_url(
                        api,
                        headers=headers,
                    )
                    data = json.loads(to_text(response.read()))
                    display.vvvvv(to_text(data))
                    for item in data.get('data', []):
                        subnet_id = item.get('id')
                        if subnet_id not in subnets:
                            subnets.append(subnet_id)
                except HTTPError as e:
                    raise AnsibleError("Received HTTP error for %s : %s" % (api, to_native(e)))
                except URLError as e:
                    raise AnsibleError("Failed lookup url for %s : %s" % (api, to_native(e)))
                except SSLValidationError as e:
                    raise AnsibleError("Error validating the server's certificate for %s: %s" % (api, to_native(e)))
                except ConnectionError as e:
                    raise AnsibleError("Error connecting to %s: %s" % (api, to_native(e)))

            display.vvvv(f'Subnets to process: {subnets}')

            for subnet in subnets:
                api=f"{ipam_client}/subnets/{subnet}/addresses/"
                display.vvvv(f'Accessing api: {api}')

                try:
                    response = open_url(
                        api,
                        headers=headers,
                    )
                    data = json.loads(to_text(response.read()))
                    display.vvvvv(to_text(data))
                    for item in data.get('data', []):
                        if (
                            not self.get_option('with_mac_address') or item.get('mac', None) is not None
                        ) and (
                            not self.get_option('with_hostname') or item.get('hostname', None) is not None
                        ):
                            ret.append(
                                to_text(
                                    {
                                        'hostname': item.get('hostname', f'ip-{item.get("ip").replace(".", "-")}'),
                                        'ip': item.get('ip', 'undefined'),
                                        'mac': item.get('mac', 'undefined'),
                                        'subnet_id': subnet,
                                    }
                                )
                            )

                except HTTPError as e:
                    display.vvvv(f'HTTP Error received: {to_text(e)}')
                except URLError as e:
                    raise AnsibleError("Failed lookup url for %s : %s" % (api, to_native(e)))
                except SSLValidationError as e:
                    raise AnsibleError("Error validating the server's certificate for %s: %s" % (api, to_native(e)))
                except ConnectionError as e:
                    raise AnsibleError("Error connecting to %s: %s" % (api, to_native(e)))

        return ret