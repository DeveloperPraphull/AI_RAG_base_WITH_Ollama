import subprocess



def run_command(cmd):

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    print("COMMAND:", cmd)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("RETURN CODE:", result.returncode)

    if result.returncode != 0:
        raise Exception(
            f"""
            Command: {cmd}

            STDOUT:
            {result.stdout}

            STDERR:
            {result.stderr}
            """
        )

    return result.stdout.strip()

def create_branch(branch_name: str):

    run_command(
        ["git", "checkout", "-b", branch_name]
    )

    return f"Branch {branch_name} created"

def switch_branch(branch_name: str):

    run_command(
        ["git", "checkout", branch_name]
    )

    return f"Switched to {branch_name}"


def commit_changes(message: str):

    run_command(["git", "add", "."])

    run_command(
        ["git", "commit", "-m", message]
    )

    return "Committed successfully"

def push_branch(branch_name: str):

    run_command(
        ["git", "push", "origin", branch_name]
    )

    return f"Pushed {branch_name}"

def create_and_push_branch(
    branch_name: str,
    commit_message: str
):

    run_command(
        ["git", "checkout", "-b", branch_name]
    )

    run_command(["git", "add", "."])

    run_command(
        ["git", "commit", "-m", commit_message]
    )

    run_command(
        [
            "git",
            "push",
            "-u",
            "origin",
            branch_name
        ]
    )

    return {
        "status": "success",
        "branch": branch_name
    }
def push_code(
    branch_name: str,
    commit_message: str
):

    # Check if branch exists
    result = subprocess.run(
        ["git", "branch", "--list", branch_name],
        capture_output=True,
        text=True
    )

    if branch_name not in result.stdout:
        run_command(
            ["git", "checkout", "-b", branch_name]
        )
    else:
        run_command(
            ["git", "checkout", branch_name]
        )

    run_command(["git", "add", "."])

    run_command(
        ["git", "commit", "-m", commit_message]
    )

    run_command(
        [
            "git",
            "push",
            "-u",
            "origin",
            branch_name
        ]
    )

    return {
        "status": "success",
        "branch": branch_name
    }