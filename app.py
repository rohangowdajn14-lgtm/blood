
import os

from flask import Flask, render_template, request, session, redirect, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
db = mysql.connector.connect(
    host=os.environ["MYSQL_HOST"],
    user=os.environ["MYSQL_USER"],
    password=os.environ["MYSQL_PASSWORD"],
    database=os.environ["MYSQL_DATABASE"]
)

print("MySQL Connected Successfully!")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':

        full_name = request.form['full_name']
        age = request.form['age']
        gender = request.form['gender']
        blood_group = request.form['blood_group']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        city = request.form['city']

        if len(password) < 8:
            return "Password must contain at least 8 characters."

        password_hash = generate_password_hash(password)

        cursor = db.cursor()

        query = """
        INSERT INTO donors
        (full_name, age, gender, blood_group, phone, email, city, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            full_name, age, gender, blood_group,
            phone, email, city, password_hash
        )

        cursor.execute(query, values)
        db.commit()
        cursor.close()

        return "Donor Registered Successfully!"

    return render_template('register.html')


@app.route('/search', methods=['GET', 'POST'])
def search():

    donors = []
    searched = False

    if request.method == 'POST':

        blood_group = request.form['blood_group']
        city = request.form['city']

        cursor = db.cursor()

        query = """
        SELECT * FROM donors
        WHERE blood_group = %s
        AND LOWER(city) = LOWER(%s)
        """

        cursor.execute(query, (blood_group, city.strip()))
        donors = cursor.fetchall()

        cursor.close()
        searched = True

    return render_template(
        'search.html',
        donors=donors,
        searched=searched
    )


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cursor = db.cursor()

        query = """
        SELECT donor_id, full_name, password_hash
        FROM donors
        WHERE email = %s
        """

        cursor.execute(query, (email,))
        donor = cursor.fetchone()
        cursor.close()

        if donor and donor[2] and check_password_hash(donor[2], password):

            session['donor_id'] = donor[0]
            session['donor_name'] = donor[1]

            return redirect(url_for('home'))

        return "Invalid email or password. Please try again."

    return render_template('login.html')

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('home'))
@app.route('/dashboard')
def dashboard():

    if 'donor_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()

    query = "SELECT * FROM donors WHERE donor_id = %s"
    cursor.execute(query, (session['donor_id'],))

    donor = cursor.fetchone()

    cursor.close()

    if donor is None:
        session.clear()
        return redirect(url_for('login'))

    return render_template('dashboard.html', donor=donor)
@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():

    if 'donor_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()

    if request.method == 'POST':

        full_name = request.form['full_name']
        age = request.form['age']
        gender = request.form['gender']
        blood_group = request.form['blood_group']
        phone = request.form['phone']
        email = request.form['email']
        city = request.form['city']

        query = """
        UPDATE donors
        SET full_name=%s, age=%s, gender=%s,
            blood_group=%s, phone=%s, email=%s, city=%s
        WHERE donor_id=%s
        """

        values = (
            full_name, age, gender, blood_group,
            phone, email, city, session['donor_id']
        )

        cursor.execute(query, values)
        db.commit()
        cursor.close()

        session['donor_name'] = full_name

        return redirect(url_for('dashboard'))

    cursor.execute(
        "SELECT * FROM donors WHERE donor_id = %s",
        (session['donor_id'],)
    )

    donor = cursor.fetchone()
    cursor.close()

    if donor is None:
        session.clear()
        return redirect(url_for('login'))

    return render_template('edit_profile.html', donor=donor)
@app.route('/delete-account', methods=['POST'])
def delete_account():

    if 'donor_id' not in session:
        return redirect(url_for('login'))

    cursor = db.cursor()

    query = "DELETE FROM donors WHERE donor_id = %s"

    cursor.execute(query, (session['donor_id'],))

    db.commit()
    cursor.close()

    session.clear()

    return redirect(url_for('home'))
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        cursor = db.cursor()

        query = """
        SELECT admin_id, username, password_hash
        FROM admins
        WHERE username = %s
        """

        cursor.execute(query, (username,))
        admin = cursor.fetchone()
        cursor.close()

        if admin and check_password_hash(admin[2], password):

            session['admin_id'] = admin[0]
            session['admin_username'] = admin[1]

            return redirect(url_for('admin_dashboard'))

        return "Invalid admin username or password."

    return render_template('admin_login.html')
@app.route('/admin-dashboard')
def admin_dashboard():

    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM donors")
    total_donors = cursor.fetchone()[0]

    query = """
    SELECT donor_id, full_name, age, gender,
           blood_group, phone, email, city
    FROM donors
    ORDER BY donor_id DESC
    """

    cursor.execute(query)
    donors = cursor.fetchall()

    cursor.close()

    return render_template(
        'admin_dashboard.html',
        donors=donors,
        total_donors=total_donors,
        admin_username=session['admin_username']
    )
@app.route('/admin-logout')
def admin_logout():

    session.pop('admin_id', None)
    session.pop('admin_username', None)

    return redirect(url_for('admin_login'))
if __name__ == '__main__':
    app.run(debug=True)

