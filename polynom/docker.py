import time
import logging
import polypheny
import docker
from docker.errors import DockerException, NotFound, ImageNotFound
import polynom.config as cfg

logger = logging.getLogger(__name__)

def _wait_for_prism(address, user, password, transport, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                conn = polypheny.connect(
                    address,
                    username=user,
                    password=password,
                    transport=transport
                )
                conn.close()
                return
            except EOFError:
                time.sleep(1)
            except Exception as e:
                raise RuntimeError(f"Unexpected error while connecting to Polypheny: {e}") from e
        raise TimeoutError("Timed out waiting for Polypheny to become available.")

def _deploy_polypheny(address, user: str, password: str, transport: str):
        logger.info("Establishing connection to Docker...")
        try:
            client = docker.from_env()
            client.ping()
        except DockerException as e:
            logger.error("Docker is not running or not accessible.")
            raise RuntimeError("Docker is not running or not accessible.") from e

        container_name = cfg.get(cfg.POLYPHENY_CONTAINER_NAME)
        image_name = cfg.get(cfg.POLYPHENY_IMAGE_NAME)
        ports = cfg.get(cfg.POLYPHENY_PORTS)

        try:
            logger.info(f"Checking for presence of Polypheny container '{container_name}'...")
            container = client.containers.get(container_name)
            container.start()
            logger.info(f"Container '{container_name}' found and started.")
        except NotFound:
            logger.info("Polypheny container not found. Deploying a new container. This may take a moment...")
            try:
                client.images.pull(image_name)
                container = client.containers.run(
                    image_name,
                    name=container_name,
                    ports=ports,
                    detach=True
                )
                logger.info(f"New Polypheny container '{container_name}' deployed and started.")
            except DockerException as e:
                logger.error(f"Failed to create or run the Polypheny container: {e}")
                raise RuntimeError("Failed to create or run the Polypheny container.") from e

        logger.info(f"Waiting for Polypheny Prism to become available at {address}...")
        try:
            _wait_for_prism(address, user, password, transport)
            logger.info("Polypheny Prism is now responsive.")
        except TimeoutError as e:
            logger.error(str(e))
            raise RuntimeError("Polypheny container did not become ready in time.") from e

def _stop_container_by_name(container_name):
        try:
            client = docker.from_env()
            client.ping()
            container = client.containers.get(container_name)
            if container.status == 'running':
                container.stop()
            logger.info(f"Container '{container_name}' stopped.")
        except NotFound:
            logger.warning(f"No container named '{container_name}' found.")
        except DockerException as e:
            logger.error(f"Failed to stop the container '{container_name}': {e}")
            raise RuntimeError(f"Failed to stop the container '{container_name}'") from e

def _remove_container_by_name(container_name):
        try:
            client = docker.from_env()
            client.ping()
            container = client.containers.get(container_name)
            container.remove()
            logger.info(f"Container '{container_name}' removed.")
        except NotFound:
            logger.warning(f"No container named '{container_name}' found.")
        except DockerException as e:
            logger.error(f"Failed to remove the container '{container_name}': {e}")
            raise RuntimeError(f"Failed to remove the container '{container_name}'") from e