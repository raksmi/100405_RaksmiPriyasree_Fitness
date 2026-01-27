from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# Data files
USERS_FILE = "users_data.json"
MEDICINES_FILE = "medicines_data.json"

def load_data(filename, default):
    """Load data from JSON file"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except:
            return default
    return default

def save_data(filename, data):
    """Save data to JSON file"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def get_age_color(age):
    """Return color based on age"""
    if age < 13:
        return {"color": "#9B59B6", "name": "Purple", "light": "#E8DAEF"}
    elif 13 <= age <= 35:
        return {"color": "#27AE60", "name": "Green", "light": "#D5F5E3"}
    else:
        return {"color": "#F1C40F", "name": "Yellow", "light": "#FCF3CF"}

@app.route('/')
def index():
    """Home page"""
    users = load_data(USERS_FILE, {})
    medicines = load_data(MEDICINES_FILE, {})
    
    # Get current time for reminders
    current_time = datetime.now().strftime("%H:%M")
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Get reminders for today
    reminders = []
    for user_id, user_meds in medicines.items():
        if user_id in users:
            user = users[user_id]
            user_color = get_age_color(user['age'])
            
            for med_id, med_data in user_meds.items():
                for time_str in med_data['times']:
                    taken_key = f"{current_date}_{time_str}"
                    status = "taken" if taken_key in med_data['taken'] else "pending"
                    
                    # Calculate if reminder is due
                    try:
                        med_time = datetime.strptime(time_str, "%H:%M")
                        current_dt = datetime.strptime(current_time, "%H:%M")
                        time_diff = (current_dt - med_time).total_seconds() / 60
                        
                        if -5 <= time_diff <= 30:
                            reminders.append({
                                'user': user['name'],
                                'user_color': user_color,
                                'medicine': med_data['name'],
                                'dosage': med_data['dosage'],
                                'time': time_str,
                                'status': status,
                                'due': True
                            })
                    except:
                        reminders.append({
                            'user': user['name'],
                            'user_color': user_color,
                            'medicine': med_data['name'],
                            'dosage': med_data['dosage'],
                            'time': time_str,
                            'status': status,
                            'due': False
                        })
    
    return render_template('index.html', 
                         users=users, 
                         medicines=medicines, 
                         reminders=reminders,
                         current_time=current_time,
                         get_age_color=get_age_color)

@app.route('/add_user', methods=['POST'])
def add_user():
    """Add a new user"""
    data = request.json
    name = data.get('name', '').strip()
    age_str = data.get('age', '').strip()
    
    if not name or not age_str:
        return jsonify({'success': False, 'message': 'Please fill in all fields'})
    
    try:
        age = int(age_str)
        if age <= 0:
            return jsonify({'success': False, 'message': 'Age must be positive'})
    except ValueError:
        return jsonify({'success': False, 'message': 'Age must be a number'})
    
    users = load_data(USERS_FILE, {})
    user_id = str(len(users) + 1)
    users[user_id] = {
        'name': name,
        'age': age
    }
    
    save_data(USERS_FILE, users)
    
    return jsonify({
        'success': True, 
        'message': f'User {name} added successfully!',
        'user': {
            'id': user_id,
            'name': name,
            'age': age,
            'color': get_age_color(age)
        }
    })

@app.route('/register_medicine', methods=['POST'])
def register_medicine():
    """Register a new medicine"""
    data = request.json
    user_id = data.get('user_id', '').strip()
    med_name = data.get('med_name', '').strip()
    dosage = data.get('dosage', '').strip()
    frequency = data.get('frequency', '').strip()
    times = data.get('times', [])
    
    if not all([user_id, med_name, dosage, frequency]):
        return jsonify({'success': False, 'message': 'Please fill in all fields'})
    
    if not times:
        return jsonify({'success': False, 'message': 'Please specify at least one time'})
    
    # Validate times
    for time_str in times:
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            return jsonify({'success': False, 'message': f'Invalid time format: {time_str}'})
    
    # Sort times
    times.sort()
    
    medicines = load_data(MEDICINES_FILE, {})
    if user_id not in medicines:
        medicines[user_id] = {}
    
    med_id = str(len(medicines[user_id]) + 1)
    medicines[user_id][med_id] = {
        'name': med_name,
        'dosage': dosage,
        'frequency': frequency,
        'times': times,
        'taken': {}
    }
    
    save_data(MEDICINES_FILE, medicines)
    
    return jsonify({
        'success': True,
        'message': f'Medicine {med_name} registered successfully!'
    })

@app.route('/mark_taken', methods=['POST'])
def mark_taken():
    """Mark medicine as taken"""
    data = request.json
    user_id = data.get('user_id', '').strip()
    med_name = data.get('med_name', '').strip()
    time_str = data.get('time', '').strip()
    
    if not all([user_id, med_name, time_str]):
        return jsonify({'success': False, 'message': 'Missing required data'})
    
    medicines = load_data(MEDICINES_FILE, {})
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if user_id in medicines:
        for med_id, med_data in medicines[user_id].items():
            if med_data['name'] == med_name and time_str in med_data['times']:
                taken_key = f"{current_date}_{time_str}"
                med_data['taken'][taken_key] = True
                save_data(MEDICINES_FILE, medicines)
                return jsonify({
                    'success': True,
                    'message': f'Medicine {med_name} at {time_str} marked as taken!'
                })
    
    return jsonify({'success': False, 'message': 'Could not find medicine record'})

@app.route('/delete_user', methods=['POST'])
def delete_user():
    """Delete a user"""
    data = request.json
    user_id = data.get('user_id', '').strip()
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID required'})
    
    users = load_data(USERS_FILE, {})
    medicines = load_data(MEDICINES_FILE, {})
    
    if user_id in users:
        # Also delete user's medicines
        if user_id in medicines:
            del medicines[user_id]
            save_data(MEDICINES_FILE, medicines)
        
        del users[user_id]
        save_data(USERS_FILE, users)
        
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    
    return jsonify({'success': False, 'message': 'User not found'})

@app.route('/delete_medicine', methods=['POST'])
def delete_medicine():
    """Delete a medicine"""
    data = request.json
    user_id = data.get('user_id', '').strip()
    med_name = data.get('med_name', '').strip()
    
    if not all([user_id, med_name]):
        return jsonify({'success': False, 'message': 'Missing required data'})
    
    medicines = load_data(MEDICINES_FILE, {})
    
    if user_id in medicines:
        for med_id, med_data in list(medicines[user_id].items()):
            if med_data['name'] == med_name:
                del medicines[user_id][med_id]
                save_data(MEDICINES_FILE, medicines)
                return jsonify({'success': True, 'message': 'Medicine deleted successfully'})
    
    return jsonify({'success': False, 'message': 'Medicine not found'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
