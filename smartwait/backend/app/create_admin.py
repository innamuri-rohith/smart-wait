"""Create the first administrator from the command line.

Usage (run from the backend folder):
    python -m app.create_admin --email admin@smartwait.dev --name "Admin"
You will be prompted for the password, so it does not appear in shell history.
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.database import SessionLocal, init_db
from app.db.models import Role, User


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a SmartWait administrator")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    password = getpass.getpass("Password (min 8 chars, letters and digits): ")
    if len(password) < 8 or not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        print("Password does not meet the policy.")
        sys.exit(1)

    init_db()
    email = args.email.lower()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            print("An account with this email already exists.")
            sys.exit(1)
        db.add(
            User(
                email=email,
                password_hash=hash_password(password),
                full_name=args.name.strip(),
                role=Role.admin,
            )
        )
        db.commit()
    print(f"Administrator created: {email}")


if __name__ == "__main__":
    main()
