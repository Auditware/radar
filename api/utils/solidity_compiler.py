import json
import subprocess
import re
import os
from pathlib import Path
from semantic_version import Version
from typing import List

SOLC_CMD_TIMEOUT = 30


def parse_gitmodules(gitmodules_path: Path) -> List[str]:
    """Parse .gitmodules and extract GitHub package identifiers (owner/repo)."""
    packages = []
    try:
        with open(gitmodules_path, 'r') as f:
            content = f.read()
        
        # Match github URLs: https://github.com/owner/repo or git@github.com:owner/repo
        pattern = r'url\s*=\s*(?:https://github\.com/|git@github\.com:)([^/\s]+/[^/\s]+?)(?:\.git)?(?:\s|$)'
        matches = re.findall(pattern, content)
        packages = [match.strip() for match in matches if match.strip()]
    except Exception:
        pass
    return packages


def prepare_foundry_project(project_dir: Path, force: bool = False) -> bool:
    """
    Prepare a Foundry project by ensuring dependencies are installed and built.
    Runs automatically when lib/ directory is missing or empty.
    Returns True if preparation was successful, False otherwise.
    """
    if not (project_dir / "foundry.toml").exists():
        return False
    
    lib_dir = project_dir / "lib"
    needs_prep = force or not lib_dir.exists() or not any(lib_dir.iterdir()) if lib_dir.exists() else True
    
    # In CI, always run to ensure clean builds even if lib/ exists
    is_ci = os.getenv("CI") or os.getenv("GITHUB_ACTIONS") or os.getenv("GITLAB_CI")
    if is_ci:
        needs_prep = True
    
    if not needs_prep:
        return False
    
    print("[i] Preparing Foundry project...")
    
    # Fix permissions first (may be running as non-root with root-owned mounted dir)
    try:
        subprocess.run(
            ["chmod", "-R", "777", str(project_dir)],
            capture_output=True,
            timeout=10
        )
    except Exception:
        pass
    
    try:
        # First, ensure the project directory is writable
        # In Docker, mounted volumes may be owned by root, so fix permissions
        try:
            os.makedirs(lib_dir, exist_ok=True)
        except PermissionError:
            print("[w] Cannot create lib directory (permission denied)")
            return False
        
        # Initialize git repo if .git doesn't exist (needed for forge install with git submodules)
        git_dir = project_dir / ".git"
        if not git_dir.exists():
            print("[i] Initializing git repository for Foundry...")
            result = subprocess.run(
                ["git", "init"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                print(f"[w] git init failed: {result.stderr[:100]}")
                return False
            
            subprocess.run(
                ["git", "config", "user.email", "radar@auditware.io"],
                cwd=str(project_dir),
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Radar"],
                cwd=str(project_dir),
                capture_output=True
            )
            # Add all files and commit (required for forge install to work)
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(project_dir),
                capture_output=True
            )
            result = subprocess.run(
                ["git", "commit", "-m", "Initial commit for Foundry setup", "--no-gpg-sign"],
                cwd=str(project_dir),
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"[w] git commit failed: {result.stderr[:100]}")
            print("[i] Git repository initialized successfully")
        
        # Parse .gitmodules to get dependency package names
        gitmodules_path = project_dir / ".gitmodules"
        packages = parse_gitmodules(gitmodules_path) if gitmodules_path.exists() else []
        
        if packages:
            # Install dependencies with explicit package names
            install_cmd = ["forge", "install"] + packages
            result = subprocess.run(
                install_cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"[i] Foundry dependencies installed ({len(packages)} packages)")
            else:
                print(f"[w] forge install failed (code {result.returncode}): {result.stderr[:200]}")
                if "Permission denied" in result.stderr:
                    return False
        else:
            # No .gitmodules or no packages found, try plain forge install
            result = subprocess.run(
                ["forge", "install"],
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print("[i] Foundry dependencies installed")
            else:
                print(f"[w] forge install failed (code {result.returncode}): {result.stderr[:200]}")
                if "Permission denied" in result.stderr:
                    return False
        
        result = subprocess.run(
            ["forge", "build", "--force"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            print("[i] Foundry project built successfully")
            return True
        else:
            print(f"[w] Foundry build had issues: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[w] Foundry preparation timed out")
        return False
    except FileNotFoundError:
        print("[w] forge command not found")
        return False


def detect_solidity_version(file_content: str) -> str:
    pragma_match = re.search(r'pragma\s+solidity\s+([^;]+);', file_content)
    if pragma_match:
        version_spec = pragma_match.group(1).strip()
        version_spec = version_spec.replace('^', '').replace('>=', '').replace('>', '')
        version_match = re.search(r'(\d+\.\d+\.\d+)', version_spec)
        if version_match:
            detected = version_match.group(1)
            if Version(detected) >= Version('0.8.0'):
                return detected
    return '0.8.20'


def get_foundry_remappings(project_dir: Path) -> List[str]:
    """Get remappings from Foundry project using 'forge remappings' command."""
    try:
        result = subprocess.run(
            ["forge", "remappings"],
            cwd=str(project_dir),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            remappings = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            print(f"[i] Found {len(remappings)} remappings from Foundry project")
            return remappings
        return []
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return []


def compile_solidity_files(file_paths: list[Path], remappings: List[str] = None, base_path: Path = None) -> dict:
    """Compile multiple Solidity files together in a single compilation unit."""
    
    # Detect highest required version from all files
    max_version = "0.8.0"
    sources = {}
    
    for file_path in file_paths:
        file_content = file_path.read_text()
        detected_version = detect_solidity_version(file_content)
        if Version(detected_version) > Version(max_version):
            max_version = detected_version
        
        # Use relative path if base_path is provided
        if base_path:
            try:
                source_key = str(file_path.relative_to(base_path))
            except ValueError:
                source_key = str(file_path)
        else:
            source_key = str(file_path)
        
        sources[source_key] = {"content": file_content}
    
    if Version(max_version) < Version('0.8.0'):
        raise ValueError(f"Solidity version {max_version} < 0.8.0 is not supported. Only Solidity 0.8+ is supported.")
    
    print(f"[i] Compiling {len(file_paths)} files with solc {max_version}")
    
    # Install and select compiler version
    try:
        result = subprocess.run(
            ["solc-select", "use", max_version],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
    except subprocess.CalledProcessError as e:
        if "must be installed" in str(e.stderr):
            print(f"[i] Installing solc {max_version}...")
            subprocess.run(
                ["solc-select", "install", max_version],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            subprocess.run(
                ["solc-select", "use", max_version],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
        else:
            raise RuntimeError(f"Failed to set solc version to {max_version}: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("solc-select not found. Please install it: pip install solc-select")
    
    solc_input = {
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi"],
                    "": ["ast"]
                }
            }
        }
    }
    
    if remappings:
        solc_input["settings"]["remappings"] = remappings
    
    cwd = base_path if base_path else None
    
    # Build solc command
    solc_cmd = ["solc", "--standard-json"]
    if base_path:
        solc_cmd.extend(["--allow-paths", str(base_path)])
    
    try:
        result = subprocess.run(
            solc_cmd,
            input=json.dumps(solc_input),
            capture_output=True,
            text=True,
            timeout=SOLC_CMD_TIMEOUT,
            cwd=str(cwd) if cwd else None
        )
        
        ast_output = json.loads(result.stdout)
        
        if "errors" in ast_output:
            errors = [e for e in ast_output["errors"] if e.get("severity") == "error"]
            if errors:
                error_msgs = "\n".join([e.get("message", str(e)) for e in errors])
                raise ValueError(f"Solidity compilation errors:\n{error_msgs}")
        
        if not ast_output.get("sources"):
            raise ValueError("Compilation failed - no sources generated")
        
        return ast_output
        
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Solidity compilation timed out after {SOLC_CMD_TIMEOUT} seconds")
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse solc output: {result.stdout}")


def compile_solidity_file(file_path: Path, remappings: List[str] = None, base_path: Path = None) -> dict:
    file_content = file_path.read_text()
    
    solc_version = detect_solidity_version(file_content)
    
    if Version(solc_version) < Version('0.8.0'):
        raise ValueError(f"Solidity version {solc_version} < 0.8.0 is not supported. Only Solidity 0.8+ is supported.")
    
    print(f"[i] Compiling {file_path} with solc {solc_version}")
    
    try:
        result = subprocess.run(
            ["solc-select", "use", solc_version],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
    except subprocess.CalledProcessError as e:
        if "must be installed" in str(e.stderr):
            print(f"[i] Installing solc {solc_version}...")
            subprocess.run(
                ["solc-select", "install", solc_version],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            subprocess.run(
                ["solc-select", "use", solc_version],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
        else:
            raise RuntimeError(f"Failed to set solc version to {solc_version}: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("solc-select not found. Please install it: pip install solc-select")
    
    # Use relative path if base_path is provided (for Foundry projects)
    if base_path:
        try:
            source_key = str(file_path.relative_to(base_path))
        except ValueError:
            source_key = str(file_path)
    else:
        source_key = str(file_path)
    
    solc_input = {
        "language": "Solidity",
        "sources": {source_key: {"content": file_content}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi"],
                    "": ["ast"]
                }
            }
        }
    }
    
    if remappings:
        solc_input["settings"]["remappings"] = remappings
    
    cwd = base_path if base_path else None
    
    if cwd:
        print(f"[i] Running solc from directory: {cwd}")
        print(f"[i] Source key: {source_key}")
    
    # Build solc command - add --allow-paths for Foundry projects
    solc_cmd = ["solc", "--standard-json"]
    if base_path:
        # Allow access to the entire project directory
        solc_cmd.extend(["--allow-paths", str(base_path)])
    
    try:
        result = subprocess.run(
            solc_cmd,
            input=json.dumps(solc_input),
            capture_output=True,
            text=True,
            timeout=SOLC_CMD_TIMEOUT,
            cwd=str(cwd) if cwd else None
        )
        
        ast_output = json.loads(result.stdout)
        
        if "errors" in ast_output:
            errors = [e for e in ast_output["errors"] if e.get("severity") == "error"]
            if errors:
                error_msgs = "\n".join([e.get("message", str(e)) for e in errors])
                raise ValueError(f"Solidity compilation errors:\n{error_msgs}")
        
        if not ast_output.get("sources"):
            raise ValueError("Compilation failed - no sources generated")
        
        return ast_output
        
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Solidity compilation timed out after {SOLC_CMD_TIMEOUT} seconds")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse solc output: {e}")
