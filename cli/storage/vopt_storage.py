import requests
from bs4 import BeautifulSoup

import cli.utils.common as common
import cli.utils.string_util as util

from cli.storage.storage_exception import StorageError

logger = common.get_logger("vopt_storage")

CONTENT_TYPE = "application/vnd.ibm.powervm.uom+xml; Type=VirtualIOServer"

def get_vopt_scsi_mapping(hmc_host, partition_uuid, system_uuid, vopt_name):
    scsi_mapping = f'''
    <VirtualSCSIMapping schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <AssociatedLogicalPartition kb="CUR" kxe="false" href="https://{hmc_host}/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition/{partition_uuid}" rel="related"/>
        <Storage kxe="false" kb="CUR">
            <VirtualOpticalMedia schemaVersion="V1_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <MediaName kxe="false" kb="CUR">{vopt_name}</MediaName>
                <MountType kxe="false" kb="CUD">r</MountType>
            </VirtualOpticalMedia>
        </Storage>
    </VirtualSCSIMapping>
    '''
    return BeautifulSoup(scsi_mapping, 'xml')

def populate_payload(config, vios_payload, hmc_host, partition_uuid, system_uuid, vopt_name):
    vios_bs = BeautifulSoup(vios_payload, 'xml')
    scsi_mappings = vios_bs.find('VirtualSCSIMappings')

    if vopt_name:
        bc_scsi = get_vopt_scsi_mapping(hmc_host, partition_uuid, system_uuid, vopt_name)
        scsi_mappings.append(bc_scsi)
    else:
        bootstrap_scsi = get_vopt_scsi_mapping(hmc_host, partition_uuid, system_uuid, util.get_bootstrap_iso(config))
        cloudinit_scsi = get_vopt_scsi_mapping(hmc_host, partition_uuid, system_uuid, util.get_cloud_init_iso(config))
        scsi_mappings.append(bootstrap_scsi)
        scsi_mappings.append(cloudinit_scsi)

    return str(vios_bs)

def check_if_scsi_mapping_exist(partition_uuid, vios, media_dev_name):
    found = False
    try:
        soup = BeautifulSoup(vios, 'xml')
        scsi_mappings = soup.find_all('VirtualSCSIMapping')
        # Iterate over all SCSI mappings and look for Storage followed by PhysicalVolume XML tags
        for scsi in scsi_mappings:
            lpar_link = scsi.find("AssociatedLogicalPartition")
            if lpar_link is not None and partition_uuid in lpar_link.attrs["href"]:
                b_dev = scsi.find("BackingDeviceName")
                if b_dev is not None and b_dev.text == media_dev_name:
                    found = True
                    break
    except Exception as e:
        raise StorageError(f"failed to check if storage SCSI mapping is present in VIOS, error: {e}")
    return found

def attach_vopt(vios_payload, config, cookies, partition_uuid, sys_uuid, vios_uuid, vopt_name):
    try:
        uri = f"/rest/api/uom/ManagedSystem/{sys_uuid}/VirtualIOServer/{vios_uuid}"
        hmc_host = util.get_host_address(config)
        url =  "https://" +  hmc_host + uri
        headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=VirtualIOServer"}
        payload = populate_payload(config, vios_payload, hmc_host, partition_uuid, sys_uuid, vopt_name)
        response = requests.post(url, headers=headers, cookies=cookies, data=payload, verify=False)

        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise StorageError(f"failed to attach vOPT device to the partition while making http request, error: {e}, response: {e.response.text}")
    except Exception as e:
        raise StorageError(f"failed to attach vOPT device to the partition, error: {e}")
    return
