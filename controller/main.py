from pathlib import Path
from helpers import (
    check_path,
    copy_to_docker_mount,
    parse_arguments,
    print_write_outputs,
)
from api import generate_ast_for_file_or_folder, run_scan, poll_results


def main():
    args = parse_arguments()
    container_path = Path(args.container_path)

    path_type = check_path(container_path)

    print(f"[i] Copying {path_type} from radar container to a shared docker volume")
    copy_to_docker_mount(
        Path("/contract"),
        Path("/radar_data" / container_path.relative_to("/")),
        path_type,
    )

    templates_path = None
    if args.templates:
        templates_path = Path(args.templates)
        if not templates_path.exists():
            print(
                f"[e] Provided custom templates folder path {templates_path} is invalid"
            )
            raise FileNotFoundError
        copy_to_docker_mount(
            Path("/templates"),
            Path("/radar_data" / templates_path.relative_to("/")),
            "folder",
        )
        print(f"[i] Using custom provided templates folder.")

    local_path = None
    if args.path:
        local_path = Path(args.path)

    ast = generate_ast_for_file_or_folder(container_path, path_type)
    run_scan(container_path, path_type, templates_path)
    results = poll_results(container_path, path_type, local_path)

    print_write_outputs(results, ast["ast"], args.ast)


if __name__ == "__main__":
    main()
