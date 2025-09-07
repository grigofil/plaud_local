#!/usr/bin/env python3
"""
Скрипт для удаления пользователей из системы Plaud
"""

import requests
import sys
import getpass

def get_auth_token(api_url, username, password):
    """Получает токен авторизации для административных операций"""
    try:
        response = requests.post(
            f"{api_url}/auth/login",
            data={
                "username": username,
                "password": password
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('access_token')
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка авторизации: {error_detail}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return None

def list_users(api_url, token):
    """Получает список всех пользователей"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{api_url}/users", headers=headers)
        
        if response.status_code == 200:
            return response.json().get('users', [])
        else:
            print(f"❌ Ошибка при получении списка пользователей: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return []

def delete_user_by_id(api_url, token, user_id):
    """Удаляет пользователя по ID"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{api_url}/users/{user_id}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Пользователь успешно удален!")
            print(f"   ID: {result['deleted_user']['id']}")
            print(f"   Username: {result['deleted_user']['username']}")
            print(f"   Email: {result['deleted_user']['email']}")
            return True
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка при удалении пользователя: {error_detail}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def delete_user_by_username(api_url, token, username):
    """Удаляет пользователя по имени пользователя"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{api_url}/users/by-username/{username}", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Пользователь успешно удален!")
            print(f"   ID: {result['deleted_user']['id']}")
            print(f"   Username: {result['deleted_user']['username']}")
            print(f"   Email: {result['deleted_user']['email']}")
            return True
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка при удалении пользователя: {error_detail}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def deactivate_user(api_url, token, user_id):
    """Деактивирует пользователя (мягкое удаление)"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.patch(f"{api_url}/users/{user_id}/deactivate", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Пользователь деактивирован!")
            print(f"   ID: {result['user']['id']}")
            print(f"   Username: {result['user']['username']}")
            print(f"   Email: {result['user']['email']}")
            return True
        else:
            error_detail = response.json().get('detail', 'Неизвестная ошибка')
            print(f"❌ Ошибка при деактивации пользователя: {error_detail}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False

def main():
    # Настройки API
    API_URL = "http://localhost:8000"  # Измените на ваш URL API
    
    print("=== Удаление пользователя из Plaud ===\n")
    
    # Авторизация администратора
    print("Для удаления пользователей необходимо авторизоваться как администратор:")
    admin_username = input("Введите имя администратора: ").strip()
    if not admin_username:
        print("❌ Имя администратора не может быть пустым")
        return
    
    admin_password = getpass.getpass("Введите пароль администратора: ")
    if not admin_password:
        print("❌ Пароль не может быть пустым")
        return
    
    print(f"\nАвторизуюсь как {admin_username}...")
    token = get_auth_token(API_URL, admin_username, admin_password)
    
    if not token:
        print("❌ Не удалось авторизоваться")
        return
    
    print("✅ Авторизация успешна!")
    
    # Получаем список пользователей
    print("\nПолучаю список пользователей...")
    users = list_users(API_URL, token)
    
    if not users:
        print("❌ Не удалось получить список пользователей или пользователи не найдены")
        return
    
    print(f"\nНайдено пользователей: {len(users)}")
    print("\nСписок пользователей:")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Status':<10}")
    print("-" * 80)
    
    for user in users:
        status = "Активен" if user['is_active'] else "Заблокирован"
        print(f"{user['id']:<5} {user['username']:<20} {user['email']:<30} {status:<10}")
    
    print("-" * 80)
    
    # Выбор действия
    print("\nВыберите действие:")
    print("1. Удалить пользователя по ID")
    print("2. Удалить пользователя по имени")
    print("3. Деактивировать пользователя (мягкое удаление)")
    print("4. Выход")
    
    choice = input("\nВведите номер действия (1-4): ").strip()
    
    if choice == "1":
        try:
            user_id = int(input("Введите ID пользователя для удаления: ").strip())
            user = next((u for u in users if u['id'] == user_id), None)
            if not user:
                print("❌ Пользователь с таким ID не найден")
                return
            
            print(f"\nВы собираетесь удалить пользователя:")
            print(f"   ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            
            confirm = input("\nВы уверены? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y', 'да', 'д']:
                success = delete_user_by_id(API_URL, token, user_id)
                if success:
                    print("\n🎉 Пользователь успешно удален!")
                else:
                    print("\n💥 Не удалось удалить пользователя")
            else:
                print("❌ Операция отменена")
                
        except ValueError:
            print("❌ Неверный формат ID")
    
    elif choice == "2":
        username = input("Введите имя пользователя для удаления: ").strip()
        if not username:
            print("❌ Имя пользователя не может быть пустым")
            return
        
        user = next((u for u in users if u['username'] == username), None)
        if not user:
            print("❌ Пользователь с таким именем не найден")
            return
        
        print(f"\nВы собираетесь удалить пользователя:")
        print(f"   ID: {user['id']}")
        print(f"   Username: {user['username']}")
        print(f"   Email: {user['email']}")
        
        confirm = input("\nВы уверены? (yes/no): ").strip().lower()
        if confirm in ['yes', 'y', 'да', 'д']:
            success = delete_user_by_username(API_URL, token, username)
            if success:
                print("\n🎉 Пользователь успешно удален!")
            else:
                print("\n💥 Не удалось удалить пользователя")
        else:
            print("❌ Операция отменена")
    
    elif choice == "3":
        try:
            user_id = int(input("Введите ID пользователя для деактивации: ").strip())
            user = next((u for u in users if u['id'] == user_id), None)
            if not user:
                print("❌ Пользователь с таким ID не найден")
                return
            
            if not user['is_active']:
                print("❌ Пользователь уже деактивирован")
                return
            
            print(f"\nВы собираетесь деактивировать пользователя:")
            print(f"   ID: {user['id']}")
            print(f"   Username: {user['username']}")
            print(f"   Email: {user['email']}")
            
            confirm = input("\nВы уверены? (yes/no): ").strip().lower()
            if confirm in ['yes', 'y', 'да', 'д']:
                success = deactivate_user(API_URL, token, user_id)
                if success:
                    print("\n🎉 Пользователь успешно деактивирован!")
                else:
                    print("\n💥 Не удалось деактивировать пользователя")
            else:
                print("❌ Операция отменена")
                
        except ValueError:
            print("❌ Неверный формат ID")
    
    elif choice == "4":
        print("👋 До свидания!")
    
    else:
        print("❌ Неверный выбор")

if __name__ == "__main__":
    main()
