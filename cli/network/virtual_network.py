import requests
from bs4 import BeautifulSoup

import cli.utils.common as common
import cli.utils.string_util as util

from cli.network.network_exception import NetworkError

logger = common.get_logger("virtual-network")

CONTENT_TYPE = "application/vnd.ibm.powervm.uom+xml; Type=ClientNetworkAdapter"
DEFAULT_NW_SLOT = 3

# Note: The VirtualSlotNumber tag is set to 3, which corresponds to the value in the 99_custom_network.cfg file.
#       Any changes to this value must also be updated in the configuration file.
def populate_payload(vlanid, vswitchid, vswitchname):
    return f'''
<ClientNetworkAdapter:ClientNetworkAdapter xmlns:ClientNetworkAdapter="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2" schemaVersion="V1_0">
    <Metadata>
        <Atom>
        </Atom>
    </Metadata>
    <VirtualSlotNumber kxe="false" kb="COD">{DEFAULT_NW_SLOT}</VirtualSlotNumber>
    <PortVLANID kb="CUR" kxe="false">{vlanid}</PortVLANID>
    <VirtualSwitchID kxe="false" kb="ROR">{vswitchid}</VirtualSwitchID>
    <VirtualSwitchName ksv="V1_12_0" kb="ROR" kxe="false">{vswitchname}</VirtualSwitchName>
</ClientNetworkAdapter:ClientNetworkAdapter>
'''

def get_network_uuid(config, cookies, system_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualNetwork/quick/All"
    url = "https://" +  util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml, type=VirtualNetwork"}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise NetworkError(f"failed to list VLAN, error: {response.text}")
    uuid = ""
    network_name = util.get_vnetwork_name(config)
    for nw in response.json():
        if nw["NetworkName"] == network_name:
            uuid = nw["UUID"]
            break

    if "" == uuid:
        raise NetworkError(f"no virtual network available with name '{network_name}'")
    else:
        logger.debug(f"Network UUID for the virtual network {network_name}: {uuid}")
    return uuid

def get_vlan_details(config, cookies, system_uuid):
    nw_uuid = get_network_uuid(config, cookies, system_uuid)
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/VirtualNetwork/{nw_uuid}"
    url = "https://" +  util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml, type=VirtualNetwork"}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise NetworkError(f"failed to get VLAN details, error: {response.text}")
    
    soup = BeautifulSoup(response.text, 'xml')
    vlan_id = soup.find("NetworkVLANID")
    vswitch_id = soup.find("VswitchID")

    return vlan_id.text, vswitch_id.text

def check_network_adapter(config, cookies, partition_uuid, vlan_id, vswitch_id):
    uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}/ClientNetworkAdapter"
    url =  "https://" +  util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": CONTENT_TYPE}
    slot_num = -1
    try:
        response = requests.get(url, headers=headers, cookies=cookies, verify=False)
        if response.status_code == 204:
            logger.debug(f"No network is attached to lpar '{partition_uuid}' yet")
            return False, slot_num
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'xml')
            if soup.find("PortVLANID").text == vlan_id and soup.find("VirtualSwitchID").text == vswitch_id :
                logger.debug(f"Found network with VLAN '{vlan_id}' and Switch '{vswitch_id}' attached to lpar.")
                slot_num = soup.find("VirtualSlotNumber").text
                return True, slot_num
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"failed to check if virtual network is attached to the partition while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise NetworkError(f"failed to check if virtual network is attached to the partition, error: {e}")
    return False, slot_num

def attach_network(config, cookies, system_uuid, partition_uuid):
    try:
        # Get VLAN ID and VSWITCH ID
        vlan_id, vswitch_id = get_vlan_details(config, cookies, system_uuid)

        # Check if network adapter is already attached to lpar. If not, do attach
        attached, slot_num = check_network_adapter(config, cookies, partition_uuid, vlan_id, vswitch_id)
        if attached:
            logger.debug(f"Network '{util.get_vnetwork_name(config)}' is already attached to lpar")
            return slot_num

        payload = populate_payload(vlan_id, vswitch_id, util.get_vswitch_name(config))

        uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}/ClientNetworkAdapter"
        url =  "https://" +  util.get_host_address(config) + uri
        headers = {"x-api-key": util.get_session_key(config), "Content-Type": CONTENT_TYPE}
        response = requests.put(url, headers=headers, cookies=cookies, data=payload, verify=False)
        response.raise_for_status()
        logger.debug(f"Network '{util.get_vnetwork_name(config)}' attached to lpar")
    except requests.exceptions.RequestException as e:
        raise NetworkError(f"failed to attach virtual network to the partition while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise NetworkError(f"failed to attach virtual network to the partition, error: {e}")
    return DEFAULT_NW_SLOT
