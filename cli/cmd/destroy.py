import cli.partition.activation as activation
import cli.partition.partition as partition
import cli.utils.command_util as command_util
import cli.utils.common as common
import cli.utils.string_util as util
import cli.vios.vios as vios_operation

logger = common.get_logger("pim-destroy")


def destroy(config_file_path):
    cookies = None
    try:
        logger.info("Destroying PIM partition")
        config = common.initialize_config(config_file_path)
        # Invoking initialize_command to perform common actions like validation, authentication etc.
        is_config_valid, cookies, sys_uuid, vios_uuid_list = command_util.initialize_command(config)
        if is_config_valid:
            _destroy(config, cookies, sys_uuid, vios_uuid_list)
            logger.info("PIM partition successfully destroyed")
    except (Exception) as e:
        logger.error(f"encountered an error: {e}")
    finally:
        if cookies:
            command_util.cleanup(config, cookies)

def _destroy(config, cookies, sys_uuid, vios_uuid_list):
    try:
        exists, created_by_pim, partition_uuid = partition.check_partition_exists(
            config, cookies, sys_uuid)
        if exists:
            logger.info("Shutting down the partition")
            activation.shutdown_partition(config, cookies, partition_uuid)
            logger.info("Partition shut down")

        logger.info(
            "Detaching installation medias and physical disk from the partition")
        vios_operation.cleanup_vios(
            config, cookies, sys_uuid, partition_uuid, vios_uuid_list)
        logger.info(
            "Detached installation medias and physical disk from the partition")

        if created_by_pim and exists:
            logger.info("Destroying the partition")
            partition. remove_partition(config, cookies, partition_uuid)
            logger.info("Partition destroyed")
    except Exception as e:
        raise e
    return
