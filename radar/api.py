import requests

from helpers import get_env_variable


# @note Use case is mostly container, leaving a basic resolver as groundwork for the future
def resolve_django() -> str:
    port = get_env_variable("DJANGO_PORT")
    local = f'http://{get_env_variable("DJANGO_HOST_LOCAL")}:{port}'
    container = f'http://{get_env_variable("DJANGO_HOST")}:{port}'

    try:
        response = requests.get(local, timeout=10)
        if response.status_code == 200:
            return local
        else:
            raise Exception("Service unavailable")
    except:
        return container


api_uri = resolve_django()
print(f"[i] Found API URL at {api_uri}")


def scan_file(path):
    try:
        response = requests.post(
            f"{api_uri}/generate_ast/",
            json={"source_type": "file", "file_path": str(path)},
        )

        if response.status_code == 201:
            # @todo implement success state handling
            print(f"[i] AST successfully generated for {path}")
        else:
            try:
                error_response = response.json()
            except requests.exceptions.JSONDecodeError:
                error_response = response.text
            print(f"[e] Error parsing file: {response.status_code} - {error_response}")
    except requests.exceptions.RequestException as e:
        print(f"[e] Request failed: {e}")
