import docker

class Finalizer():
    def run(self, container_name="polypheny"):
        try:
            client = docker.from_env()
            client.ping()
        except docker.errors.DockerException as e:
            raise RuntimeError("Docker is not running or not accessible") from e

        try:
            container = client.containers.get(container_name)
            if container.status == 'running':
                container.stop()
            container.remove()
            print(f"Container '{container_name}' stopped and removed.")
        except docker.errors.NotFound:
            print(f"No container named '{container_name}' found.")
        except docker.errors.APIError as e:
            raise RuntimeError(f"Failed to stop or remove the container '{container_name}'") from e

