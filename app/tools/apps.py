import re
import subprocess


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):
    text = text.lower().strip()

    text = re.sub(r"[-_.]", " ", text)

    return " ".join(text.split())


# ============================================================
# WINDOWS APPLICATION DISCOVERY
# ============================================================

def get_installed_apps():

    powershell_command = r"""
    Get-StartApps |
    ForEach-Object {
        "$($_.Name)|$($_.AppID)"
    }
    """

    try:

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_command
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        if result.returncode != 0:
            return []

        apps = []

        for line in result.stdout.splitlines():

            if "|" not in line:
                continue

            name, app_id = line.split("|", 1)

            name = name.strip()
            app_id = app_id.strip()

            if name and app_id:

                apps.append(
                    {
                        "name": name,
                        "app_id": app_id
                    }
                )

        return apps

    except Exception:
        return []


# ============================================================
# WORD HELPERS
# ============================================================

def get_words(text):
    return normalize_text(text).split()


def word_similarity(query_word, app_word):
    """
    Conservative generic word matching.

    No application-specific knowledge.
    """

    if query_word == app_word:
        return 1.0

    # Prefix:
    # "calcul" -> "calculator"
    if len(query_word) >= 3:
        if app_word.startswith(query_word):
            return 0.90

    return 0.0


# ============================================================
# GENERIC INITIAL / ABBREVIATION MATCHING
# ============================================================

def abbreviation_matches(query_word, app_words):
    """
    Determines whether a short query such as:

        vs

    can represent consecutive application words such as:

        visual studio

    This is completely generic.
    """

    if len(query_word) < 2:
        return False

    initials = "".join(
        word[0]
        for word in app_words
        if word
    )

    # Direct initials match
    if query_word == initials:
        return True

    # Search consecutive words.
    for start in range(len(app_words)):

        current = ""

        for end in range(start, len(app_words)):

            current += app_words[end][0]

            if current == query_word:
                return True

            if len(current) >= len(query_word):
                break

    return False


# ============================================================
# MATCH ONE QUERY WORD
# ============================================================

def match_query_word(query_word, app_words):
    """
    Returns the strongest match for one user word.
    """

    # Exact word
    for app_word in app_words:

        if query_word == app_word:
            return 1.0

    # Prefix
    for app_word in app_words:

        score = word_similarity(
            query_word,
            app_word
        )

        if score > 0:
            return score

    # Generic abbreviation
    if abbreviation_matches(
        query_word,
        app_words
    ):
        return 0.85

    return 0.0


# ============================================================
# APPLICATION SCORE
# ============================================================

def application_score(query, app_name):

    query_words = get_words(query)
    app_words = get_words(app_name)

    if not query_words or not app_words:
        return 0.0

    # Exact application name
    if normalize_text(query) == normalize_text(app_name):
        return 1.0

    scores = []

    for query_word in query_words:

        score = match_query_word(
            query_word,
            app_words
        )

        scores.append(score)

    # CRITICAL:
    #
    # Every query word must match.
    #
    # This prevents:
    #
    # "vs code"
    #
    # from matching:
    #
    # "Developer Command Prompt for VS 2022"
    #
    # because "code" has no valid match there.

    if any(score == 0 for score in scores):
        return 0.0

    # Average match quality
    average_score = sum(scores) / len(scores)

    return average_score


# ============================================================
# FIND BEST APPLICATION
# ============================================================

def find_application(query):

    applications = get_installed_apps()

    if not applications:
        return None

    candidates = []

    for app in applications:

        score = application_score(
            query,
            app["name"]
        )

        if score > 0:

            candidates.append(
                (
                    score,
                    app
                )
            )

    if not candidates:
        return None

    # Highest score first
    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    best_score, best_app = candidates[0]

    # Require a strong match
    if best_score < 0.80:
        return None

    return best_app


# ============================================================
# OPEN APPLICATION
# ============================================================

def open_application(application):
    application = application.strip()

    if not application:
        return "Please tell me which application you want me to open."

    app = find_application(application)

    if not app:
        return (
            f"I couldn't find an application matching "
            f"'{application}'."
        )

    app_name = app["name"]
    app_id = app["app_id"]

    try:
        powershell_command = (
            "Start-Process "
            f'"shell:AppsFolder\\{app_id}"'
        )

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_command,
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:
            return f"Opening {app_name}."

        return (
            f"I found {app_name}, but Windows "
            f"could not launch it."
        )

    except Exception as error:
        return (
            f"I couldn't open {app_name}.\n"
            f"Error: {error}"
        )


# ============================================================
# FIND RUNNING APPLICATION
# ============================================================

def find_running_application(name):

    app = find_application(name)

    if not app:
        return None

    app_name = app["name"]

    # Escape single quotes for PowerShell.
    safe_name = app_name.replace(
        "'",
        "''"
    )

    powershell_command = f"""
    Get-Process |
    Where-Object {{
        $_.MainWindowHandle -ne 0 -and
        $_.MainWindowTitle -and
        $_.MainWindowTitle -like '*{safe_name}*'
    }} |
    Select-Object -First 1 |
    Select-Object Id, ProcessName, MainWindowTitle
    """

    try:

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_command,
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode != 0:
            return None

        output = result.stdout.strip()

        if not output:
            return None

        # PowerShell's default table output is not ideal for
        # machine parsing, so perform a second query that
        # returns only the process ID.
        powershell_pid_command = f"""
        Get-Process |
        Where-Object {{
            $_.MainWindowHandle -ne 0 -and
            $_.MainWindowTitle -and
            $_.MainWindowTitle -like '*{safe_name}*'
        }} |
        Select-Object -First 1 -ExpandProperty Id
        """

        pid_result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                powershell_pid_command,
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        pid = pid_result.stdout.strip()

        if not pid:
            return None

        return {
            "app": app,
            "pid": pid,
        }

    except Exception:
        return None


# ============================================================
# CLOSE APPLICATION
# ============================================================

def close_application(application):

    application = application.strip()

    if not application:
        return (
            "Please tell me which application "
            "you want me to close."
        )

    running = find_running_application(
        application
    )

    if not running:

        app = find_application(
            application
        )

        if not app:
            return (
                f"I couldn't find an application "
                f"matching '{application}'."
            )

        return (
            f"{app['name']} is not currently running."
        )

    app_name = running["app"]["name"]
    pid = running["pid"]

    try:

        # First attempt a normal process close.
        #
        # taskkill without /F allows Windows to request
        # a normal shutdown rather than immediately
        # terminating the process.

        result = subprocess.run(
            [
                "taskkill",
                "/PID",
                pid,
            ],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        if result.returncode == 0:

            return f"Closed {app_name}."

        return (
            f"I found {app_name}, but Windows "
            f"couldn't close it normally."
        )

    except Exception as error:

        return (
            f"I couldn't close {app_name}.\n"
            f"Error: {error}"
        )