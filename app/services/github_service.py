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


def branch_exists(branch_name: str) -> bool:

    result = subprocess.run(
        ["git", "branch", "--list", branch_name],
        capture_output=True,
        text=True
    )

    return branch_name in result.stdout

def remote_branch_exists(branch_name: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch_name],
        capture_output=True,
        text=True
    )

    return bool(result.stdout.strip())

def current_branch():

    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True
    )

    return result.stdout.strip()

def has_changes():

    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    return bool(result.stdout.strip())



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

    previous_branch = current_branch()

    try:

        # Switch to branch or create it
        if branch_exists(branch_name):

            run_command(
                ["git", "checkout", branch_name]
            )

        else:

            run_command(
                ["git", "checkout", "-b", branch_name]
            )

        # Pull only if the remote branch already exists
        if remote_branch_exists(branch_name):

            run_command(
                [
                    "git",
                    "pull",
                    "--rebase",
                    "origin",
                    branch_name
                ]
            )

        else:

            print(f"Remote branch '{branch_name}' does not exist. Skipping pull.")

        # Stage all changes
        run_command(
            ["git", "add", "."]
        )

        # Commit only if there are changes
        if has_changes():

            run_command(
                [
                    "git",
                    "commit",
                    "-m",
                    commit_message
                ]
            )

        # Push the branch
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

    except Exception as e:

        try:
            run_command(
                ["git", "reset", "--hard", "HEAD"]
            )
        except:
            pass

        try:
            run_command(
                ["git", "checkout", previous_branch]
            )
        except:
            pass

        return {
            "status": "failed",
            "error": str(e)
        }