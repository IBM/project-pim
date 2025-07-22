import paramiko

from cli.app.ai_app_exception import AIAppError
from cli.auth.auth_exception import AuthError
from cli.network.network_exception import NetworkError
import cli.network.virtual_network as virtual_network
from cli.partition.partition_exception import PartitionError
import cli.partition.activation as activation
import cli.partition.partition as partition
from cli.storage.storage_exception import StorageError
import cli.storage.storage as storage
import storage.virtual_storage as vstorage
import cli.storage.vopt_storage as vopt
import cli.utils.command_util as command_util
import cli.utils.common as common
import cli.utils.iso_util as iso_util
import cli.utils.monitor_util as monitor_util
import cli.utils.string_util as util
from cli.vios.vios_exception import VIOSError
import cli.vios.vios as vios_operation

logger = common.get_logger("pim-launch")

def launch(config_file_path):
    cookies = None
    try:
        logger.info("Launching PIM partition")
        config = common.initialize_config(config_file_path)
        # Invoking initialize_command to perform common actions like validation, authentication etc.
        is_config_valid, cookies, sys_uuid, vios_uuid_list = command_util.initialize_command(config)
        if is_config_valid:
            _launch(config, cookies, sys_uuid, vios_uuid_list)
            logger.info("PIM partition successfully launched")
    except Exception as e:
        logger.error(f"encountered an error: {e}")
    finally:
        if cookies:
            command_util.cleanup(config, cookies)

def _launch(config, cookies, sys_uuid, vios_uuids):
    try:
        # Check if SSH key pair is configured, if empty generate key pair
        if not util.get_ssh_priv_key(config) or not util.get_ssh_pub_key(config):
            logger.debug("Generate & load SSH keys into config from local")
            config = common.load_ssh_keys(config)

        # Populate configobj with public key content to get populated in cloud-init config
        config["ssh"]["pub-key"] = common.readfile(
            util.get_ssh_pub_key(config))

        active_vios_servers = vios_operation.get_active_vios(
            config, cookies, sys_uuid, vios_uuids)
        if len(active_vios_servers) == 0:
            logger.error("failed to find active VIOS server")
            raise VIOSError("failed to find active VIOS server")
        logger.debug(
            f"List of active VIOS '{list(active_vios_servers.keys())}'")

        vios_media_uuid_list = vios_operation.get_vios_with_mediarepo_tag(active_vios_servers)
        if len(vios_media_uuid_list) == 0:
            logger.error("failed to find VIOS server for the partition")
            raise StorageError("failed to find VIOS server for the partition")

        logger.info("Setting up partition")
        exists, created_by_pim, partition_uuid = partition.check_partition_exists(config, cookies, sys_uuid)
        if exists:
            logger.info(f"Partition already exists, partition UUID: {partition_uuid}")
            if not created_by_pim:
                # Existing partition case: Shutdown the partition if its in active state
                logger.info("Shutting down user provided partition to attach network and installation medias")
                activation.shutdown_partition(config, cookies, partition_uuid)
        elif not exists:
            partition_uuid = partition.create_partition(config, cookies, sys_uuid)
            logger.info(f"New partition created, partition UUID: {partition_uuid}")

        logger.info("Setting up network")
        slot_num = virtual_network.attach_network(
            config, cookies, sys_uuid, partition_uuid)
        logger.info("Network setup completed")

        logger.info(
            "Downloading(bootstrap) & building(cloud-init) installation ISOs")
        iso_util.build_and_download_iso(config, slot_num, common.iso_dir, common.cloud_init_config_dir)
        logger.info("Downloaded & built installation ISOs")

        logger.info("Loading installation ISOs to VIOS media repository")
        vios_bootstrap_media_uuid = iso_util.upload_iso_to_media_repository(
            config, cookies, common.iso_dir, util.get_bootstrap_iso(config), sys_uuid, vios_media_uuid_list)
        logger.debug(
            f"a. Selecting '{vios_bootstrap_media_uuid}' VIOS to mount bootstrap vOPT")
        vios_cloudinit_media_uuid = iso_util.upload_iso_to_media_repository(
            config, cookies, common.iso_dir, util.get_cloud_init_iso(config), sys_uuid, vios_media_uuid_list)
        logger.debug(
            f"b. Selecting '{vios_cloudinit_media_uuid}' VIOS to mount cloudinit vOPT")
        logger.info("Installation ISOs loaded to VIOS media repository")

        logger.info("Attaching installation ISOs to the partition")
        vios_payload = vios_operation.get_vios_details(
            config, cookies, sys_uuid, vios_bootstrap_media_uuid)

        # Attach bootstrap vOPT
        vopt_bootstrap = util.get_bootstrap_iso(config)
        vopt_cloud_init = util.get_cloud_init_iso(config)

        cloud_init_attached = False
        b_scsi_exists, _, _ = command_util.check_if_scsi_mapping_exist(
            partition_uuid, vios_payload, vopt_bootstrap)
        if not b_scsi_exists:
            if vios_cloudinit_media_uuid == vios_bootstrap_media_uuid:
                vopt.attach_vopt(vios_payload, config, cookies,
                                 partition_uuid, sys_uuid, vios_bootstrap_media_uuid, "")
                cloud_init_attached = True
            else:
                vopt.attach_vopt(vios_payload, config, cookies, partition_uuid,
                                 sys_uuid, vios_bootstrap_media_uuid, vopt_bootstrap)
        if not cloud_init_attached:
            vios_cloudinit_payload = vios_operation.get_vios_details(
                config, cookies, sys_uuid, vios_cloudinit_media_uuid)
            c_scsi_exists, _, _ = command_util.check_if_scsi_mapping_exist(
                partition_uuid, vios_cloudinit_payload, vopt_cloud_init)
            if not c_scsi_exists:
                vopt.attach_vopt(vios_cloudinit_payload, config, cookies, partition_uuid,
                                 sys_uuid, vios_cloudinit_media_uuid, vopt_cloud_init)

        logger.info("Installation ISOs attached to the partition")

        logger.info("Setting up storage")
        setup_storage(config, cookies, active_vios_servers, sys_uuid, partition_uuid)

        lpar_state = activation.check_lpar_status(config, cookies, partition_uuid)
        if lpar_state != "running":
            logger.debug("Setting partition bootstring as 'cd/dvd-all'")
            partition_payload = partition.get_partition_details(
                config, cookies, sys_uuid, partition_uuid)
            partition.set_partition_boot_string(
                config, cookies, sys_uuid, partition_uuid, partition_payload, "cd/dvd-all")

        logger.info("Activating the partition")
        activation.activate_partition(config, cookies, partition_uuid)
        logger.info("Partition activated")

        logger.info("Monitoring boot process, this will take a while")
        monitor_util.monitor_bootstrap_boot(config)
        monitor_util.monitor_pim(config)
    except (AIAppError, AuthError, NetworkError, PartitionError, StorageError, VIOSError, paramiko.SSHException, Exception) as e:
        raise e

def setup_storage(config, cookies, active_vios, sys_uuid, lpar_id):
    try:
        # Re-run scenario: Check if physical disk/virtualdisk/SAN storage(VFC) is already attached to partition
        storage_attached = False
        for a_vios_uuid, a_vios in active_vios.items():
            logger.debug(f"Checking for existing physical disk attachment in VIOS '{a_vios_uuid}'")
            physical_disk_found, _ = storage.check_if_storage_attached(
                a_vios, lpar_id)
            if physical_disk_found:
                logger.info(
                    f"Physical disk is already attached to lpar '{lpar_id}'")
                storage_attached = True
            if not storage_attached:
                vdisk_found, vdisk_name = vstorage.check_if_vdisk_attached(a_vios, lpar_id)
                if vdisk_found:
                    logger.info(f"Virtual disk '{vdisk_name}' is already attached to lpar '{lpar_id}'")
                    storage_attached = True
            if not storage_attached:
                vfc_disk_found, _ = storage.check_if_vfc_disk_attached(
                    a_vios, lpar_id)
                if vfc_disk_found:
                    logger.info(
                        f"SAN storage(VFC) disk is already attached to lpar '{lpar_id}'")
                    storage_attached = True

        vdisk_attached = False
        if util.use_logical_volume(config) and not storage_attached:
            handle_virtual_disk(config, cookies, active_vios, sys_uuid, lpar_id)
            vdisk_attached = True

        if not storage_attached and not vdisk_attached:
            vios_storage_list = vios_operation.get_vios_with_physical_storage(
                config, active_vios)
            if len(vios_storage_list) == 0:
                logger.error(
                    "failed to find physical volume for the partition")
                raise StorageError(
                    "failed to find physical volume for the partition")
            storage.attach_physical_storage(
                config, cookies, sys_uuid, lpar_id, vios_storage_list)
    except (StorageError, VIOSError, Exception) as e:
        raise e

def handle_virtual_disk(config, cookies, active_vios, sys_uuid, lpar_id):
    try:
        vios_storage_list = vios_operation.get_vios_with_physical_storage(
            config, active_vios)
        if len(vios_storage_list) == 0:
            logger.error("failed to find physical volume for the partition")
            raise StorageError("failed to find physical volume for the partition")
        vios_storage_uuid = vios_storage_list[0][0]
        updated_vios_payload = vios_operation.get_vios_details(config, cookies, sys_uuid, vios_storage_uuid)

        # Check if virtual storage already exists under the given volumegroup
        vg_id = vstorage.get_volume_group_id(config, cookies, vios_storage_uuid, util.get_volume_group_name(config))
        found, _, _ = vstorage.check_if_vdisk_exists(config, cookies, vios_storage_uuid, vg_id, util.get_virtual_disk_name(config))
        # Create virtualdisk only if it doesn't exist under volumegroup
        if not found:
            vstorage.create_virtualdisk(config, cookies, vios_storage_uuid, vg_id)
            updated_vios_payload = vios_operation.get_vios_details(config, cookies, sys_uuid, vios_storage_uuid)

        vstorage.attach_virtualdisk(updated_vios_payload, config, cookies, lpar_id, sys_uuid, vios_storage_uuid)
    except (StorageError, VIOSError, Exception) as e:
        raise e
    logger.info(f"virtualdisk is attached to partition '{lpar_id}' successfully")
    return
