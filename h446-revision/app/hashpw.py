"""Print a password hash for APP_PASSWORD_HASH.

    python -m app.hashpw
    docker compose run --rm app python -m app.hashpw
"""

import getpass
import sys

from app.auth import hash_password


def main() -> None:
    first = getpass.getpass("New password: ")
    if len(first) < 10:
        sys.exit("Use at least 10 characters.")
    if getpass.getpass("Repeat password: ") != first:
        sys.exit("Passwords didn't match.")
    print(hash_password(first))


if __name__ == "__main__":
    main()
