import requests
import time

from bs4 import BeautifulSoup

import cli.utils.common as common
import cli.utils.string_util as util

from cli.partition.partition_exception import PartitionError

logger = common.get_logger("activation")

CONTENT_TYPE = "application/vnd.ibm.powervm.web+xml; Type=JobRequest"

def populated_payload(lpar_profile_id):
    return f'''
<JobRequest xmlns="http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/"  xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2" schemaVersion="V1_0">
    <Metadata>
        <Atom/>
    </Metadata>
    <RequestedOperation kxe="false" kb="CUR" schemaVersion="V1_0">
    <Metadata>
    <Atom/>
    </Metadata>
    <OperationName kxe="false" kb="ROR">PowerOn</OperationName>
    <GroupName kxe="false" kb="ROR">LogicalPartition</GroupName>
    </RequestedOperation>
    <JobParameters kb="CUR" kxe="false" schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
	<JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kxe="false" kb="ROR">force</ParameterName>
       <ParameterValue kxe="false" kb="CUR">false</ParameterValue>
    </JobParameter>
    <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kxe="false" kb="ROR">LogicalPartitionProfile</ParameterName>
        <ParameterValue kxe="false" kb="CUR">{lpar_profile_id}</ParameterValue>
    </JobParameter>
    <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kxe="false" kb="ROR">novsi</ParameterName>
        <ParameterValue kxe="false" kb="CUR">true</ParameterValue>
    </JobParameter>
    <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kxe="false" kb="ROR">bootmode</ParameterName>
        <ParameterValue kxe="false" kb="CUR">norm</ParameterValue>
    </JobParameter>
    <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kxe="false" kb="ROR">keylock</ParameterName>
        <ParameterValue kxe="false" kb="CUR">manual</ParameterValue>
    </JobParameter>
   </JobParameters>
</JobRequest>
'''

def shutdown_payload():
    return f"""
    <JobRequest xmlns="http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/"  xmlns:ns2="http://www.w3.org/XML/1998/namespace/k2" schemaVersion="V1_0">
        <Metadata>
        <Atom/>
        </Metadata>
    <RequestedOperation kxe="false" kb="CUR" schemaVersion="V1_0">
        <Metadata>
        <Atom/>
        </Metadata>
        <OperationName kxe="false" kb="ROR">PowerOff</OperationName>
        <GroupName kxe="false" kb="ROR">LogicalPartition</GroupName>
    </RequestedOperation>
    <JobParameters kxe="false" kb="CUR" schemaVersion="V1_0">
        <Metadata>
        <Atom/>
        </Metadata>
        <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kb="ROR" kxe="false">immediate</ParameterName>
        <ParameterValue kxe="false" kb="CUR">true</ParameterValue>
    </JobParameter>
    <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kb="ROR" kxe="false">restart</ParameterName>
        <ParameterValue kxe="false" kb="CUR">false</ParameterValue>
    </JobParameter>
    <JobParameter schemaVersion="V1_0">
        <Metadata>
            <Atom/>
        </Metadata>
        <ParameterName kb="ROR" kxe="false">operation</ParameterName>
        <ParameterValue kxe="false" kb="CUR">shutdown</ParameterValue>
        </JobParameter>
    </JobParameters>
</JobRequest>
"""

def get_lpar_profile_id(config, cookies, partition_uuid):
    uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}/LogicalPartitionProfile"
    url =  "https://" +  util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.uom+xml; Type=LogicalPartitionProfile"}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise PartitionError(f"failed to get LPAR profile ID, error: {response.text}")
    soup = BeautifulSoup(response.text, 'xml')
    entry_node = soup.find('entry')
    lpar_profile_id = entry_node.find('id')
    return lpar_profile_id.text

def poll_job_status(config, cookies, job_id):
    uri = f"/rest/api/uom/jobs/{job_id}"
    url =  "https://" +  util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": "application/vnd.ibm.powervm.web+xml; type=JobRequest"}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise PartitionError(f"failed to get job completion, error: {response.text}")
    soup = BeautifulSoup(response.text, 'xml')
    status = soup.find("Status").text
    if status == "COMPLETED_OK":
        return True
    else:
        logger.debug(f"Job '{job_id}' status: {status}")
        return False

def check_job_status(config, cookies, response):
    # check job status for COMPLETED_OK
    soup = BeautifulSoup(response, 'xml')
    job_id = soup.find("JobID").text
    if soup.find("Status").text == "COMPLETED_OK":
        logger.debug("Partition activated successfully.")
        return
    else:
        # poll for job status to be COMPLETRED_OK 3 times.
        for i in range(10):
            status = poll_job_status(config, cookies, job_id)
            if status:
                return True
            else:
                time.sleep(10)
                continue
    return False

def activate_partition(config, cookies, partition_uuid):
    # Check partition state,don't activate if its in 'running' state
    lpar_state = check_lpar_status(config, cookies, partition_uuid)
    if lpar_state == "running":
        logger.debug("Partition already in 'running' state, skipping activation")
        return

    uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}/do/PowerOn"
    url =  "https://" +  util.get_host_address(config) + uri
    lpar_profile_id = get_lpar_profile_id(config, cookies, partition_uuid)
    payload = populated_payload(lpar_profile_id)

    headers = {"x-api-key": util.get_session_key(config), "Content-Type": CONTENT_TYPE}
    response = requests.put(url, headers=headers, cookies=cookies, data=payload, verify=False)
    if response.status_code != 200:
        raise PartitionError(f"failed to activate partition, error: {response.text}")
    # check job status for COMPLETED_OK
    status = check_job_status(config, cookies, response.text)
    if not status:
        raise PartitionError(f"failed to activate partition, activate job returned false")
    logger.debug("Partition activated successfully.")
    return

def check_lpar_status(config, cookies, partition_uuid):
    uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}"
    url =  "https://" + util.get_host_address(config) + uri
    headers = {"x-api-key": util.get_session_key(config)}
    response = requests.get(url, headers=headers, cookies=cookies, verify=False)
    if response.status_code != 200:
        raise PartitionError(f'failed to get LPAR details for {partition_uuid}, error: {response.text}')
    soup = BeautifulSoup(response.text, 'xml')
    state = soup.find("PartitionState")
    if state == None:
        raise PartitionError(f"partition state of LPAR '{partition_uuid}' found to be None")
    return state.text

def shutdown_partition(config, cookies, partition_uuid):
    lpar_state = check_lpar_status(config, cookies, partition_uuid)
    if lpar_state == "not activated":
        logger.debug("Partition already in 'not activated' state, skipping shutdown")
        return True

    uri = f"/rest/api/uom/LogicalPartition/{partition_uuid}/do/PowerOff"
    url =  "https://" + util.get_host_address(config) + uri
    payload = shutdown_payload()
    headers = {"x-api-key": util.get_session_key(config), "Content-Type": CONTENT_TYPE}
    response = requests.put(url, headers=headers, cookies=cookies, data=payload, verify=False)
    if response.status_code != 200:
        logger.error(f"failed to shutdown partition, error: {response.text}")
        return False
    # check job status for COMPLETED_OK
    status = check_job_status(config, cookies, response.text)
    if not status:
        logger.error(f"failed to shutdown partition, shutdown job returned false")
        return False
    return True
