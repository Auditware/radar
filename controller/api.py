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
                print("[e] Failed to parse response from API")
                sys.exit(0)
        else:
            print(f"[e] Unexpectedly errored out with {response.status_code} response from API")
            print(e)
        sys.exit(0)


def detect_language_from_path(path: Path) -> tuple[str, str]:
    """Detect language and framework from file extension or folder contents.
    
    Returns: (language, framework) tuple
    """
    if path.is_file():
        if path.suffix == ".sol":
            return ("solidity", "standalone")
        elif path.suffix == ".rs":
            return ("rust", "unknown")
    elif path.is_dir():
        # Check for .sol files
        try:
            next(path.glob("**/*.sol"))
            # Check if it's a Foundry project
            if (path / "foundry.toml").exists():
                return ("solidity", "foundry")
            else:
                return ("solidity", "standalone")
        except StopIteration:
            pass
        
        # Check for Rust project (Cargo.toml, recursive)
        try:
            cargo_files = list(path.glob("**/Cargo.toml"))
            if not cargo_files:
                raise StopIteration
            
            # Detect Rust framework - check Cargo.toml dependencies first
            framework_detected = None
            for cargo_file in cargo_files:
                try:
                    content = cargo_file.read_text()
                    if "anchor-lang" in content or "anchor-spl" in content:
                        framework_detected = "anchor"
                        break
                    elif "stylus-sdk" in content:
                        framework_detected = "stylus"
                        break
                except:
                    pass
            
            # If detected from dependencies, return that
            if framework_detected:
                return ("rust", framework_detected)
            
            # Otherwise check for config files
            if (path / "Anchor.toml").exists():
                return ("rust", "anchor")
            elif (path / "Xargo.toml").exists():
                return ("rust", "stylus")
            else:
                return ("rust", "unknown")
        except StopIteration:
            pass
    return ("unknown", "unknown")


def generate_ast_for_file_or_folder(path: Path, path_type: str):
    # Detect and show language before AST generation
    language, framework = detect_language_from_path(path)
    if language != "unknown":
        print(f"[i] Language detected: {language}")
        if framework != "unknown":
            framework_label = {
                "anchor": "Anchor (Solana)",
                "stylus": "Stylus (Arbitrum)",
                "foundry": "Foundry",
                "standalone": "Standalone"
            }.get(framework, framework)
            print(f"[i] Framework/Toolchain: {framework_label}")
    
    try:
        response = requests.post(
            f"{api_uri}/generate_rust_ast/",
            json={"source_type": path_type, f"{path_type}_path": str(path), "framework": framework},
        )
        result = handle_response(response)
        if result is not None:
            print(f"[i] AST successfully generated for {path_type}")
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
            print(f"[i] Scan initiated for {path_type}")
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
    max_retries: int = 20,
    delay: int = 3,
):
    req_params = {"source_type": path_type, f"{path_type}_path": str(path)}
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(f"{api_uri}/poll_results/", params=req_params)
            if response.status_code == 200:
                response_data = response.json()
                results = response_data.get("results")
                template_count = response_data.get("template_count", 0)
                
                # Print template count
                if template_count:
                    print(f"[i] Ran {template_count} template{'s' if template_count != 1 else ''}")
                
                if local_path is not None:
                    results = localize_results(results, local_path)
                return results
            elif response.status_code == 202:
                retries += 1
                time.sleep(delay)
            else:
                handle_response(response)

        except requests.exceptions.RequestException as e:
            print(f"[e] Request failed: {e}")
            sys.exit(0)
    print("[w] Exceeded maximum retries. Tasks did not complete in time.")
    sys.exit(0)
