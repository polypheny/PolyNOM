import docker
import logging

logger = logging.getLogger(__name__)

class Finalizer():
    def run(self, container_name="polypheny", remove = False):
        try:
            client = docker.from_env()
            client.ping()
        except docker.errors.DockerException as e:
            logger.error("Docker is not running or not accessible.")
            raise RuntimeError("Docker is not running or not accessible.") from e

        try:
            container = client.containers.get(container_name)
            if container.status == 'running':
                container.stop()
            logger.info(f"Container '{container_name}' stopped.")
            if remove:
                container.remove()
            logger.info(f"Container '{container_name}' removed.")
        except docker.errors.NotFound:
            logger.warning(f"No container named '{container_name}' found.")
        except docker.errors.APIError as e:
            logger.error(f"Failed to stop the container '{container_name}'")
            raise RuntimeError(f"Failed to stop the container '{container_name}'") from e

