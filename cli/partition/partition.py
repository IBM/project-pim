import requests

from bs4 import BeautifulSoup

import cli.utils.common as common
import cli.utils.string_util as util

from cli.partition.partition_exception import PartitionError


logger = common.get_logger("partition")
CONTENT_TYPE = "application/vnd.ibm.powervm.uom+xml; Type=LogicalPartition"


def populate_payload(config):
    lpar_name_hash = common.string_hash(
        util.get_partition_name(config).lower())
    partition_name = util.get_partition_name(
        config).lower() + "-" + lpar_name_hash[:16]
    return f'''
<LogicalPartition:LogicalPartition xmlns:LogicalPartition="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/" xmlns="http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/" xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2" schemaVersion="V1_8_0">
    <CurrentProfileSync>On</CurrentProfileSync>
    <PartitionMemoryConfiguration kb="CUD" kxe="false" schemaVersion="V1_8_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <DesiredMemory kb="CUD" kxe="false">{convert_gb_to_mb(util.get_desired_memory(config))}</DesiredMemory>
        <MaximumMemory kb="CUD" kxe="false">{convert_gb_to_mb(util.get_max_memory(config))}</MaximumMemory>
        <MinimumMemory kb="CUD" kxe="false">{convert_gb_to_mb(util.get_min_memory(config))}</MinimumMemory>
    </PartitionMemoryConfiguration>
    <PartitionName kxe="false" kb="CUR">{partition_name}</PartitionName>
    {get_processor_config(config)}
    <PartitionType kxe="false" kb="COD">{util.get_partition_type(config)}</PartitionType>
</LogicalPartition:LogicalPartition>
'''


def get_processor_config(config):
    if util.has_dedicated_proc(config) == "true":
        return f'''<PartitionProcessorConfiguration kb="CUD" kxe="false" schemaVersion="V1_8_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <DedicatedProcessorConfiguration kb="CUD" kxe="false" schemaVersion="V1_8_0">
                <Metadata>
                    <Atom/>
                </Metadata>
                <DesiredProcessors kb="CUD" kxe="false">{util.get_desired_proc(config)}</DesiredProcessors>
                <MaximumProcessors kxe="false" kb="CUD">{util.get_max_proc(config)}</MaximumProcessors>
                <MinimumProcessors kb="CUD" kxe="false">{util.get_min_proc(config)}</MinimumProcessors>
            </DedicatedProcessorConfiguration>
            <HasDedicatedProcessors kxe="false" kb="CUD">{util.has_dedicated_proc(config)}</HasDedicatedProcessors>
            <SharingMode kxe="false" kb="CUD">{util.get_sharing_mode(config)}</SharingMode>
        </PartitionProcessorConfiguration>
        '''

    return f'''<PartitionProcessorConfiguration kb="CUD" kxe="false" schemaVersion="V1_8_0">
            <Metadata>
                <Atom/>
            </Metadata>
            <HasDedicatedProcessors kxe="false" kb="CUD">{util.has_dedicated_proc(config)}</HasDedicatedProcessors>
            <SharedProcessorConfiguration kb="CUD" kxe="false" schemaVersion="V1_0">
                <Metadata>
                    <Atom />
                </Metadata>
                <DesiredProcessingUnits kb="CUD" kxe="false">{util.get_shared_desired_proc(config)}</DesiredProcessingUnits>
                <DesiredVirtualProcessors kb="CUD" kxe="false">{util.get_shared_desired_virt_proc(config)}</DesiredVirtualProcessors>
                <MaximumProcessingUnits kb="CUD" kxe="false">{util.get_shared_max_proc(config)}</MaximumProcessingUnits>
                <MaximumVirtualProcessors kb="CUD" kxe="false">{util.get_shared_max_virt_proc(config)}</MaximumVirtualProcessors>
                <MinimumProcessingUnits kb="CUD" kxe="false">{util.get_shared_min_proc(config)}</MinimumProcessingUnits>
                <MinimumVirtualProcessors kb="CUD" kxe="false">{util.get_shared_min_virt_proc(config)}</MinimumVirtualProcessors>
            </SharedProcessorConfiguration>
            <SharingMode kxe="false" kb="CUD">{util.get_sharing_mode(config)}</SharingMode>
        </PartitionProcessorConfiguration>
        '''


def get_lpar_update_payload(config, curr_lpar_payload):
    lpar_payload = None
    try:
        curr_lpar = BeautifulSoup(curr_lpar_payload, 'xml')
        lpar_mem_config = curr_lpar.find("PartitionMemoryConfiguration")
        min_memory = lpar_mem_config.find("MinimumMemory")
        max_memory = lpar_mem_config.find("MaximumMemory")
        desired_memory = lpar_mem_config.find("DesiredMemory")
        if min_memory is None or max_memory is None or desired_memory is None:
            raise PartitionError(
                "xml parsing error: unable to find memory configs from partition payload")
        min_memory.string.replace_with(
            str(convert_gb_to_mb(util.get_min_memory(config))))
        max_memory.string.replace_with(
            str(convert_gb_to_mb(util.get_max_memory(config))))
        desired_memory.string.replace_with(
            str(convert_gb_to_mb(util.get_desired_memory(config))))

        lpar_cpu_config = curr_lpar.find("PartitionProcessorConfiguration")
        partition_name = curr_lpar.find("PartitionName")
        if util.has_dedicated_proc(config) == "true":
            desired_proc = lpar_cpu_config.find("DesiredProcessors")
            min_proc = lpar_cpu_config.find("MinimumProcessors")
            max_proc = lpar_cpu_config.find("MaximumProcessors")
            if desired_proc is None or min_proc is None or max_proc is None:
                raise PartitionError(
                    "xml parsing error: unable to find processor configs from partition payload")
            desired_proc.string.replace_with(util.get_desired_proc(config))
            min_proc.string.replace_with(util.get_min_proc(config))
            max_proc.string.replace_with(util.get_max_proc(config))
        else:
            # Switch from dedicated to shared processor config
            if lpar_cpu_config is None:
                raise PartitionError(
                    "xml parsing error: unable to find processor configs from partition payload")
            lpar_cpu_config.decompose()
            new_proc_config = BeautifulSoup(
                get_processor_config(config), 'xml')
            partition_name.insert_after(new_proc_config)
        lpar_payload = curr_lpar
    except Exception as e:
        raise PartitionError(f"failed to get partition's compute(cpu & memory) configurations, error: {e}")
    return lpar_payload


def convert_gb_to_mb(value):
    return int(value) * 1024


def get_all_partitions(config, cookies, system_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition/quick/All"
    url = "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config)}
    response = requests.get(url, headers=headers,
                            cookies=cookies, verify=False)
    if response.status_code != 200:
        raise PartitionError(
            f"failed to get partition list, error: {response.text}")
    return response.json()


# Checks if partition exists, returns exists and if partition is created by PIM
def check_partition_exists(config, cookies, system_uuid):
    uuid = ""
    created_by_pim = False
    try:
        partitions = get_all_partitions(config, cookies, system_uuid)
        lpar_name = util.get_partition_name(config).lower()
        lpar_name_hash = common.string_hash(lpar_name)
        pim_lpar_name = lpar_name + "-" + lpar_name_hash[:16]
        for partition in partitions:
            # Check if either partition name with pim suffix(created by PIM) or just partition name(not created by PIM)
            if partition["PartitionName"] == lpar_name or partition["PartitionName"] == pim_lpar_name:
                uuid = partition["UUID"]
                if partition["PartitionName"] == pim_lpar_name:
                    created_by_pim = True
                break

        if len(uuid) > 0:
            logger.debug(f"UUID of partition '{lpar_name}': {uuid}")
            return True, created_by_pim, uuid
        else:
            logger.debug(f"no partition available with name '{lpar_name}'")
    except Exception as e:
        raise e
    return False, created_by_pim, uuid


def create_partition(config, cookies, system_uuid):
    logger.debug(
        f"Creating partition with name '{util.get_partition_name(config)}'")
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition"
    url = "https://" + util.get_host_address(config) + uri
    payload = populate_payload(config)
    headers = {"x-api-key": util.get_session_key(config),
               "Content-Type": CONTENT_TYPE}
    response = requests.put(url, headers=headers,
                            data=payload, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise PartitionError(
            f"failed to create partition, error: {response.text}")

    soup = BeautifulSoup(response.text, 'xml')
    partition_uuid = soup.find("PartitionUUID")
    return partition_uuid.text


def get_partition_details(config, cookies, system_uuid, partition_uuid):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition/{partition_uuid}"
    url = "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config),
               "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=LogicalPartition"}
    response = requests.get(url, headers=headers,
                            cookies=cookies, verify=False)
    if response.status_code != 200:
       raise PartitionError(
            f"failed to get partition details, error: {response.text}")
    soup = BeautifulSoup(response.text, 'xml')
    lpar = str(soup.find('LogicalPartition'))
    return lpar


def edit_lpar_compute(config, cookies, system_uuid, partition_uuid):
    try:
        partition_payload = get_partition_details(
            config, cookies, system_uuid, partition_uuid)
        updated_lpar_payload = get_lpar_update_payload(
            config, partition_payload)
        if updated_lpar_payload is None:
            raise PartitionError(
                f"failed to get updated lpar compute payload, error: {response.text}")

        logger.debug(
            f"New compute flavor: {util.get_partition_flavor(config)}")
        uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}"
        url = "https://" + util.get_host_address(config) + uri
        headers = {"x-api-key": util.get_session_key(config),
                   "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=LogicalPartition"}
        response = requests.post(url, headers=headers, cookies=cookies, data=str(
            updated_lpar_payload), verify=False)
        if response.status_code != 200:
            raise PartitionError(
                f"failed to edit lpar compute, error: {response.text}")
    except Exception as e:
        raise e
    logger.debug(
        f"Compute for partition: {partition_uuid} is updated successfully")
    return


def set_partition_boot_string(config, cookies, system_uuid, partition_uuid, partition_payload, boot_string):
    uri = f"/rest/api/uom/ManagedSystem/{system_uuid}/LogicalPartition/{partition_uuid}"
    url = "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config),
               "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=LogicalPartition"}
    payload = BeautifulSoup(partition_payload, 'xml')
    pending_boot = payload.find("PendingBootString")
    pending_boot.append(boot_string)

    response = requests.post(url, headers=headers,
                             cookies=cookies, data=str(payload), verify=False)
    if response.status_code != 200:
        raise PartitionError(
            f"failed to update boot order for the partition: '{partition_uuid}', error: {response.text}")
    logger.debug(
        f"Updated the boot order for the partition: '{partition_uuid}'")
    return


def remove_partition(config, cookies, partition_uuid):
    uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}"
    url = "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config),
               "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=LogicalPartition"}
    response = requests.delete(
        url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 204:
        logger.error(f"failed to delete partition, error: '{response.text}'")
        return
    logger.debug("Partition deleted successfully")
