
from getpass import getpass
from werkzeug.security import generate_password_hash
from app import db

username = input("Enter admin username: ")
password = getpass("Enter admin password: ")

if len(password) < 8:
    print("Password must contain at least 8 characters.")
else:
    password_hash = generate_password_hash(password)

    cursor = db.cursor()

    query = """
    INSERT INTO admins (username, password_hash)
    VALUES (%s, %s)
    """

    try:
        cursor.execute(query, (username, password_hash))
        db.commit()
        print("Admin account created successfully!")

    except Exception as error:
        db.rollback()
        print("Error:", error)

    finally:
        cursor.close()
        db.close()
