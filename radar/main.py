from pathlib import Path
from helpers import check_path, copy_to_docker_mount, parse_arguments
from api import scan_file


def main():
    args = parse_arguments()
    path = Path(args.path)
    path_type = check_path(path)
    print(f"[i] Loading {path_type} '{path}'")
    copy_to_docker_mount(path, path_type)

    if path_type == "file":
        scan_file(path)


if __name__ == "__main__":
    main()
