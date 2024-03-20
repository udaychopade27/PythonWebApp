from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Function to initialize the SQLite database
def initialize_database():
    conn = sqlite3.connect('bmi_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bmi_results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, weight REAL, height REAL, bmi REAL)''')
    conn.commit()
    conn.close()

initialize_database()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    weight = float(request.form['weight'])
    height = float(request.form['height'])

    bmi = calculate_bmi(weight, height)

    # Store BMI result in the database
    store_bmi(weight, height, bmi)

    return render_template('result.html', bmi=bmi)

def calculate_bmi(weight, height):
    return weight / (height ** 2)

def store_bmi(weight, height, bmi):
    conn = sqlite3.connect('bmi_database.db')
    c = conn.cursor()
    c.execute('INSERT INTO bmi_results (weight, height, bmi) VALUES (?, ?, ?)', (weight, height, bmi))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    app.run(debug=True)

