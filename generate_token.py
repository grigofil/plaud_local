#!/usr/bin/env python3
"""
Скрипт для генерации безопасных API токенов для Plaud Local
"""

import secrets
import string
import argparse

def generate_token(length=32):
    """Генерирует безопасный токен заданной длины"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    parser = argparse.ArgumentParser(description='Генератор API токенов для Plaud Local')
    parser.add_argument('-l', '--length', type=int, default=32, 
                       help='Длина токена (по умолчанию: 32)')
    parser.add_argument('-n', '--count', type=int, default=1,
                       help='Количество токенов (по умолчанию: 1)')
    
    args = parser.parse_args()
    
    print(f"Генерирую {args.count} токен(ов) длиной {args.length} символов:")
    print("-" * 50)
    
    tokens = []
    for i in range(args.count):
        token = generate_token(args.length)
        tokens.append(token)
        print(f"{i+1:2d}. {token}")
    
    print("-" * 50)
    print("Для использования добавьте в .env файл:")
    print(f"API_AUTH_TOKEN={','.join(tokens)}")
    
    if args.count > 1:
        print("\nИли по отдельности:")
        for i, token in enumerate(tokens, 1):
            print(f"API_AUTH_TOKEN_{i}={token}")

if __name__ == "__main__":
    main()

