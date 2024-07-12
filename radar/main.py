from pathlib import Path
from helpers import check_path, copy_to_docker_mount, parse_arguments, print_write_outputs
from api import generate_ast_for_file_or_folder, run_scan, poll_results


def main():
    args = parse_arguments()
    contaner_path = Path(args.container_path)
    path_type = check_path(contaner_path)
    print(f"[i] Loading {path_type} '{contaner_path}'")
    copy_to_docker_mount(contaner_path, path_type)

    container_output_path = Path("/radar_data/output.json")

    templates_path = None
    if args.templates:
        templates_path = Path(args.templates)
        if not templates_path.exists():
            print(
                f"[e] Provided custom templates folder path {templates_path} is invalid"
            )
            raise FileNotFoundError
        copy_to_docker_mount(templates_path, "folder")
        print(f"[i] Using custom provided templates folder.")
    
    local_path = None
    if args.path:
        local_path = Path(args.path)

    generate_ast_for_file_or_folder(contaner_path, path_type)
    run_scan(contaner_path, path_type, templates_path)
    results = poll_results(contaner_path, path_type, local_path)
    print_write_outputs(results, container_output_path)


if __name__ == "__main__":
    main()
