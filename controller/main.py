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
    output_type = "json"

    if args.output:
        if args.output.endswith(".sarif"):
            output_type = "sarif"
        elif args.output.endswith(".md"):
            output_type = "md"

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
        
        # Determine if templates is a file or folder
        templates_type = check_path(Path("/templates"))
        
        if templates_type == "file":
            # For a single file, create templates directory and copy the file into it
            templates_dir = Path("/radar_data/templates")
            
            # Ensure the templates directory exists and is clean
            if templates_dir.exists():
                if templates_dir.is_dir():
                    import shutil
                    shutil.rmtree(templates_dir)
                else:
                    templates_dir.unlink()
            
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy the single file into the templates directory
            original_filename = args.templates_filename if args.templates_filename else "template.yaml"
            copy_to_docker_mount(
                Path("/templates"),
                templates_dir / original_filename,
                "file",
            )
            templates_path = Path("templates")
            print(f"[i] Using custom provided template file: {original_filename}")
        else:
            copy_to_docker_mount(
                Path("/templates"),
                Path("/radar_data/templates"),
                "folder",
            )
            templates_path = Path("templates")
            print(f"[i] Using custom provided templates folder.")

    local_path = None
    if args.path:
        local_path = Path(args.path)

    ast = generate_ast_for_file_or_folder(container_path, path_type)
    run_scan(container_path, path_type, templates_path)
    results = poll_results(container_path, path_type, local_path)
    
    print_write_outputs(
        results, ast["ast"], args.ast, local_path, output_type, args.ignore, args.debug if hasattr(args, 'debug') else False
    )

if __name__ == "__main__":
    main()