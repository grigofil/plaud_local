#!/usr/bin/env python3
"""
Тестирование через curl
"""

import subprocess
import json

def test_with_curl():
    """Тестирует endpoint через curl"""
    print("=== Тестирование через curl ===")
    
    # Сначала получаем токен
    login_cmd = [
        'curl', '-X', 'POST', 
        'http://localhost:8000/auth/login',
        '-d', 'username=qq',
        '-d', 'password=qq123'
    ]
    
    try:
        result = subprocess.run(login_cmd, capture_output=True, text=True)
        print(f"Login status: {result.returncode}")
        print(f"Login output: {result.stdout}")
        
        if result.returncode == 0:
            login_data = json.loads(result.stdout)
            token = login_data.get('access_token')
            print(f"Token: {token[:20]}...")
            
            # Теперь тестируем /users
            users_cmd = [
                'curl', '-X', 'GET',
                'http://localhost:8000/users',
                '-H', f'Authorization: Bearer {token}'
            ]
            
            result2 = subprocess.run(users_cmd, capture_output=True, text=True)
            print(f"Users status: {result2.returncode}")
            print(f"Users output: {result2.stdout}")
            print(f"Users error: {result2.stderr}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_with_curl()
