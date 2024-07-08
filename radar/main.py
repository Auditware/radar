from pathlib import Path
from helpers import check_path, copy_to_docker_mount, parse_arguments
from api import generate_ast_for_file_or_folder, run_scan


def main():
    args = parse_arguments()
    path = Path(args.path)
    path_type = check_path(path)
    print(f"[i] Loading {path_type} '{path}'")
    copy_to_docker_mount(path, path_type)

    templates_path = None
    if args.templates:
        templates_path = Path(args.templates)
        if not templates_path.exists():
            print(
                f"[e] Error: Provided custom templates folder path {templates_path} is invalid"
            )
            raise FileNotFoundError
        copy_to_docker_mount(templates_path, "folder")
        print(f"Using custom templates from: {templates_path}")

    generate_ast_for_file_or_folder(path, path_type)
    run_scan(path, path_type, templates_path)


if __name__ == "__main__":
    main()
