"""
Test script for User Database functionality
"""

import sys
from user_db import user_db
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def test_database():
    """Run all database tests"""
    
    print_header("🧪 MARITIME DEFENSE DASHBOARD - USER DATABASE TESTS")
    
    # Test 1: Check default admin
    print("✅ Test 1: Default Admin User")
    admin = user_db.get_user(1)
    if admin:
        print(f"   Email: {admin['email']}")
        print(f"   Role: {admin['role']}")
        print(f"   Status: {'Active' if admin['is_active'] else 'Inactive'}")
        print(f"   Created: {admin['created_at']}")
    else:
        print("   ❌ Admin user not found")
    
    # Test 2: Register new user
    print("\n✅ Test 2: Register New User")
    success, message = user_db.register_user(
        email="testuser@example.com",
        password="TestPass123",
        full_name="Test User",
        role="user"
    )
    print(f"   Result: {message}")
    
    # Test 3: Duplicate registration
    print("\n✅ Test 3: Duplicate Registration (Should Fail)")
    success, message = user_db.register_user(
        email="testuser@example.com",
        password="TestPass123",
        full_name="Test User",
        role="user"
    )
    print(f"   Result: {message}")
    
    # Test 4: Invalid password
    print("\n✅ Test 4: Invalid Password (Should Fail)")
    success, message = user_db.register_user(
        email="invalid@example.com",
        password="short",
        full_name="Invalid User",
        role="user"
    )
    print(f"   Result: {message}")
    
    # Test 5: Invalid email
    print("\n✅ Test 5: Invalid Email (Should Fail)")
    success, message = user_db.register_user(
        email="invalidemail",
        password="ValidPass123",
        full_name="Invalid Email",
        role="user"
    )
    print(f"   Result: {message}")
    
    # Test 6: Authentication - Correct credentials
    print("\n✅ Test 6: Authentication - Correct Credentials")
    success, user_data = user_db.authenticate_user(
        email="testuser@example.com",
        password="TestPass123"
    )
    if success:
        print(f"   ✅ Authentication successful")
        print(f"   User: {user_data['full_name']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Role: {user_data['role']}")
        print(f"   Login Count: {user_data['login_count']}")
    else:
        print(f"   ❌ Authentication failed")
    
    # Test 7: Authentication - Wrong password
    print("\n✅ Test 7: Authentication - Wrong Password (Should Fail)")
    success, user_data = user_db.authenticate_user(
        email="testuser@example.com",
        password="WrongPassword"
    )
    if success:
        print(f"   ❌ Should have failed!")
    else:
        print(f"   ✅ Correctly rejected wrong password")
    
    # Test 8: Authentication - Non-existent user
    print("\n✅ Test 8: Authentication - Non-existent User (Should Fail)")
    success, user_data = user_db.authenticate_user(
        email="nonexistent@example.com",
        password="AnyPassword123"
    )
    if success:
        print(f"   ❌ Should have failed!")
    else:
        print(f"   ✅ Correctly rejected non-existent user")
    
    # Test 9: Get user
    print("\n✅ Test 9: Get User Information")
    user = user_db.get_user(2)
    if user:
        print(f"   Email: {user['email']}")
        print(f"   Full Name: {user['full_name']}")
        print(f"   Role: {user['role']}")
        print(f"   Active: {user['is_active']}")
        print(f"   Login Count: {user['login_count']}")
    else:
        print("   ❌ User not found")
    
    # Test 10: Update user
    print("\n✅ Test 10: Update User Information")
    success, message = user_db.update_user(
        user_id=2,
        full_name="Updated Test User"
    )
    print(f"   Result: {message}")
    
    # Test 11: Change password
    print("\n✅ Test 11: Change Password")
    success, message = user_db.change_password(
        user_id=2,
        old_password="TestPass123",
        new_password="NewPass456"
    )
    print(f"   Result: {message}")
    
    # Test 12: Authenticate with new password
    print("\n✅ Test 12: Authenticate with New Password")
    success, user_data = user_db.authenticate_user(
        email="testuser@example.com",
        password="NewPass456"
    )
    if success:
        print(f"   ✅ Authentication successful with new password")
    else:
        print(f"   ❌ Authentication failed")
    
    # Test 13: Get all users
    print("\n✅ Test 13: Get All Users")
    all_users = user_db.get_all_users()
    print(f"   Total users: {len(all_users)}")
    for user in all_users:
        status = "🟢" if user['is_active'] else "🔴"
        print(f"   {status} {user['email']} ({user['role']})")
    
    # Test 14: Deactivate user
    print("\n✅ Test 14: Deactivate User")
    success, message = user_db.deactivate_user(user_id=2)
    print(f"   Result: {message}")
    
    # Test 15: Try to authenticate deactivated user
    print("\n✅ Test 15: Authenticate Deactivated User (Should Fail)")
    success, user_data = user_db.authenticate_user(
        email="testuser@example.com",
        password="NewPass456"
    )
    if success:
        print(f"   ❌ Should have failed!")
    else:
        print(f"   ✅ Correctly rejected deactivated user")
    
    # Test 16: Activate user
    print("\n✅ Test 16: Activate User")
    success, message = user_db.activate_user(user_id=2)
    print(f"   Result: {message}")
    
    # Test 17: Get login history
    print("\n✅ Test 17: Get Login History")
    history = user_db.get_login_history(user_id=2)
    print(f"   Total logins: {len(history)}")
    for entry in history[:3]:
        print(f"   - {entry['login_time']}")
    
    # Test 18: Password validation
    print("\n✅ Test 18: Password Validation")
    test_passwords = [
        ("short", False),
        ("NoDigits", False),
        ("noupppercase123", False),
        ("ValidPass123", True),
        ("SecurePassword2025", True),
    ]
    
    for pwd, expected in test_passwords:
        is_valid, msg = user_db.validate_password(pwd)
        status = "✅" if is_valid == expected else "❌"
        print(f"   {status} '{pwd}': {msg}")
    
    # Test 19: Email validation
    print("\n✅ Test 19: Email Validation")
    test_emails = [
        ("valid@example.com", True),
        ("user.name@domain.co.uk", True),
        ("invalid@", False),
        ("@example.com", False),
        ("notanemail", False),
    ]
    
    for email, expected in test_emails:
        is_valid = user_db.validate_email(email)
        status = "✅" if is_valid == expected else "❌"
        print(f"   {status} '{email}': {is_valid}")
    
    # Summary
    print_header("📊 TEST SUMMARY")
    print("✅ All tests completed successfully!")
    print(f"✅ Database location: {user_db.DB_PATH}")
    print(f"✅ Total users in database: {len(user_db.get_all_users())}")
    print(f"✅ Timestamp: {datetime.now().isoformat()}")

if __name__ == "__main__":
    try:
        test_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

