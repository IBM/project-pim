import shutil

import cli.network.virtual_network as virtual_network
import cli.partition.activation as activation
import cli.partition.partition as partition
import cli.utils.monitor_util as monitor_util
import cli.storage.vopt_storage as vopt
import cli.utils.command_util as command_util
import cli.utils.common as common
import cli.utils.iso_util as iso_util
import cli.utils.string_util as util
import cli.vios.vios as vios


logger = common.get_logger("pim-update-config")

def update_config(config_file_path):
    cookies = None
    try:
        logger.info("Updating PIM partition's config")
        config = common.initialize_config(config_file_path)
        # Invoking initialize_command to perform common actions like validation, authentication etc.
        is_config_valid, cookies, sys_uuid, vios_uuid_list = command_util.initialize_command(
            config)
        if is_config_valid:
            _update_config(config, cookies, sys_uuid, vios_uuid_list)
            logger.info("PIM partition's config successfully updated")
    except Exception as e:
        logger.error(f"encountered an error: {e}")
    finally:
        if cookies:
            command_util.cleanup(config, cookies)

def _update_config(config, cookies, sys_uuid, vios_uuid_list):
    try:
        logger.debug("Checking partition exists")
        exists, _, partition_uuid = partition.check_partition_exists(config, cookies, sys_uuid)
        if not exists:
            logger.info(f"Partition named '{util.get_partition_name(config)}' not found, nothing to update")
            return

        if not util.get_ssh_priv_key(config) or not util.get_ssh_pub_key(config):
            logger.debug("Load SSH keys generated during launch to config")
            config = common.load_ssh_keys(config)

        config["ssh"]["pub-key"] = common.readfile(
            util.get_ssh_pub_key(config))
        
        logger.debug("Partition exists, generating cloud init config")

        # Get VLAN ID and VSWITCH ID
        vlan_id, vswitch_id = virtual_network.get_vlan_details(config, cookies, sys_uuid)

        # Check if network adapter is already attached to lpar. If not, do attach
        _, slot_num = virtual_network.check_network_adapter(config, cookies, partition_uuid, vlan_id, vswitch_id)

        iso_util.generate_cloud_init_iso_config(config, slot_num, common.cloud_init_update_config_dir)
        if not common.compare_dir(common.cloud_init_config_dir, common.cloud_init_update_config_dir):
            logger.info("No change in config, skipping the update")
            shutil.rmtree(common.cloud_init_update_config_dir)
            return
        logger.info("Detected config change, updating")
        iso_util.generate_cloud_init_iso_file(common.update_iso_dir, config, common.cloud_init_update_config_dir)

        logger.info("Shutting down the partition")
        activation.shutdown_partition(config, cookies, partition_uuid)
        logger.info("Partition shut down to attach the new config")

        cloud_init_iso = util.get_cloud_init_iso(config)
        logger.info("Uploading the new cloud init with the config changes")
        vios_cloudinit_media_uuid = iso_util.upload_iso_to_media_repository(config, cookies, common.update_iso_dir, cloud_init_iso, sys_uuid, vios_uuid_list)
        logger.debug("Cloud init uploaded")
        
        logger.info("Attaching the cloud init to the partition")
        vios_payload = vios.get_vios_details(config, cookies, sys_uuid, vios_cloudinit_media_uuid)
        vopt.attach_vopt(vios_payload, config, cookies, partition_uuid, sys_uuid, vios_cloudinit_media_uuid, cloud_init_iso)
        logger.info("New cloud init config attached to the partition.")

        logger.info("Activating the partition")
        activation.activate_partition(config, cookies, partition_uuid)
        logger.info("Partition activated")

        logger.info("Monitoring boot process, this will take a while")
        monitor_util.monitor_pim(config)

        # Move used cloud init iso to iso dir
        shutil.move(f"{common.update_iso_dir}/{cloud_init_iso}", f"{common.iso_dir}/{cloud_init_iso}")
        
        # Cleanup existing config and move updated config
        shutil.rmtree(common.cloud_init_config_dir)
        shutil.move(common.cloud_init_update_config_dir, common.cloud_init_config_dir)
    except Exception as e:
        raise e
