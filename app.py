from flask import Flask, request, render_template
import sqlite3
import os

app = Flask(__name__)

# Function to initialize the SQLite database
def init_db():
    if os.path.exists('bmi.db'):
        os.remove('bmi.db')
    conn = sqlite3.connect('bmi.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bmi (
            id INTEGER PRIMARY KEY,
            weight REAL NOT NULL,
            height REAL NOT NULL,
            bmi REAL NOT NULL,
            min_ideal_weight REAL NOT NULL,
            max_ideal_weight REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

def calculate_bmi(weight, height):
    height_meters = height / 100
    bmi = weight / (height_meters ** 2)
    return bmi

def calculate_ideal_weight(height):
    min_bmi = 18.5
    max_bmi = 24.9
    height_meters = height / 100
    min_ideal_weight = min_bmi * (height_meters ** 2)
    max_ideal_weight = max_bmi * (height_meters ** 2)
    return (min_ideal_weight, max_ideal_weight)

def save_data(weight, height, bmi):
    min_ideal_weight, max_ideal_weight = calculate_ideal_weight(height)
    conn = sqlite3.connect('bmi.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bmi (weight, height, bmi, min_ideal_weight, max_ideal_weight) 
        VALUES (?, ?, ?, ?, ?)
    ''', (weight, height, bmi, min_ideal_weight, max_ideal_weight))
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        bmi = calculate_bmi(weight, height)
        save_data(weight, height, bmi)
        ideal_weight_range = calculate_ideal_weight(height)
        return render_template('result.html', bmi=bmi, ideal_weight_range=ideal_weight_range)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

