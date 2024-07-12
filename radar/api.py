import json
import sys
import time
import requests
from pathlib import Path
from helpers import get_env_variable, localize_results


# Use case is mostly container, leaving a basic resolver as groundwork for the future
def resolve_django() -> str:
    port = get_env_variable("DJANGO_PORT")
    local = f'http://{get_env_variable("DJANGO_HOST_LOCAL")}:{port}'
    container = f'http://{get_env_variable("DJANGO_HOST")}:{port}'

    try:
        response = requests.get(local, timeout=10)
        if response.status_code == 200:
            return local
        else:
            raise Exception("Django service unavailable")
    except:
        return container


api_uri = resolve_django()

def handle_response(response):
    try:
        response.raise_for_status()
        return response.json()
    except (requests.HTTPError, requests.exceptions.RequestException, ValueError) as e:
        if str(response.status_code).startswith("4"):
            print(f"[e] {e}")
            try:
                res_json = response.json()
                print(json.dumps(res_json, indent=4))
            except:
                sys.exit(0)
        else:
            print(f"[e] {response.status_code} error response from API")
        sys.exit(0)


def generate_ast_for_file_or_folder(path: Path, path_type: str):
    try:
        response = requests.post(
            f"{api_uri}/generate_ast/",
            json={"source_type": path_type, f"{path_type}_path": str(path)},
        )
        result = handle_response(response)
        if result is not None:
            print(f"[i] AST successfully generated for {path}")
            return result
        else:
            print(f"[e] Failed to generate AST for {path}")
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f"[e] Request failed: {e}")
        sys.exit(0)


def run_scan(path: Path, path_type: str, templates_path: Path = None):
    try:
        req_body = {"source_type": path_type, f"{path_type}_path": str(path)}
        if templates_path is not None:
            req_body["templates_path"] = str(templates_path)

        response = requests.post(
            f"{api_uri}/run_scan/",
            json=req_body,
        )
        result = handle_response(response)
        if result is not None:
            print(f"[i] Scan initiated for {path}")
            return result
        else:
            print(f"[e] Scan execution failed for {path}")
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f"[e] Request failed: {e}")
        sys.exit(0)


def poll_results(
    path: Path,
    path_type: str,
    local_path: Path = None,
    max_retries: int = 10,
    delay: int = 1,
):
    req_params = {"source_type": path_type, f"{path_type}_path": str(path)}
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(f"{api_uri}/poll_results/", params=req_params)
            if response.status_code == 200:
                results = response.json().get("results")
                if local_path is not None:
                    results = localize_results(results, local_path)
                return results
            elif response.status_code == 202:
                if retries > 0:
                    print(
                        f"[i] Polling for scan results. (Retry {retries + 1}/{max_retries})"
                    )
                else:
                    print("[i] Polling for scan results.")
                retries += 1
                time.sleep(delay)
            else:
                handle_response(response)

        except requests.exceptions.RequestException as e:
            print(f"[e] Request failed: {e}")
            sys.exit(0)
    print("[w] Exceeded maximum retries. Tasks did not complete in time.")
    sys.exit(0)
