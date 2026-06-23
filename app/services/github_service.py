import subprocess


def run_command(cmd):

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(result.stderr)

    return result.stdout


def push_code(
    branch_name: str,
    commit_message: str
):

    run_command([
        "git",
        "checkout",
        "-b",
        branch_name
    ])

    run_command([
        "git",
        "add",
        "."
    ])

    run_command([
        "git",
        "commit",
        "-m",
        commit_message
    ])

    run_command([
        "git",
        "push",
        "-u",
        "origin",
        branch_name
    ])

    return {
        "status": "success",
        "branch": branch_name
    }