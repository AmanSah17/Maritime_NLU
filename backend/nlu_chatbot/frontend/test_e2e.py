"""
End-to-End Test for Maritime Defense Dashboard
Tests: Database, Authentication, JWT, Session Management
"""

import sys
from user_db import user_db
from auth_manager import AuthManager
from datetime import datetime

def print_section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_database():
    """Test database functionality"""
    print_section("🗄️  DATABASE TESTS")
    
    # Test 1: Check admin user
    print("✅ Test 1: Admin User Exists")
    admin = user_db.get_user(2)
    assert admin is not None, "Admin user not found"
    assert admin['email'] == 'amansah1717@gmail.com', "Admin email mismatch"
    assert admin['role'] == 'admin', "Admin role mismatch"
    print(f"   ✅ Admin: {admin['email']} ({admin['role']})")
    
    # Test 2: Get all users
    print("\n✅ Test 2: Get All Users")
    all_users = user_db.get_all_users()
    assert len(all_users) > 0, "No users found"
    print(f"   ✅ Total users: {len(all_users)}")
    for user in all_users:
        print(f"      - {user['email']} ({user['role']})")
    
    # Test 3: Email validation
    print("\n✅ Test 3: Email Validation")
    valid_emails = [
        'admin@example.com',
        'user.name@domain.co.uk',
        'test+tag@example.com'
    ]
    invalid_emails = [
        'invalid@',
        '@example.com',
        'notanemail'
    ]
    
    for email in valid_emails:
        assert user_db.validate_email(email), f"Valid email rejected: {email}"
    print(f"   ✅ Valid emails: {len(valid_emails)} passed")
    
    for email in invalid_emails:
        assert not user_db.validate_email(email), f"Invalid email accepted: {email}"
    print(f"   ✅ Invalid emails: {len(invalid_emails)} rejected")
    
    # Test 4: Password validation
    print("\n✅ Test 4: Password Validation")
    valid_passwords = [
        'ValidPass123',
        'SecurePassword2025',
        'Admin@2025'
    ]
    invalid_passwords = [
        'short',
        'NoDigits',
        'noupppercase123'
    ]
    
    for pwd in valid_passwords:
        is_valid, msg = user_db.validate_password(pwd)
        assert is_valid, f"Valid password rejected: {pwd} - {msg}"
    print(f"   ✅ Valid passwords: {len(valid_passwords)} passed")
    
    for pwd in invalid_passwords:
        is_valid, msg = user_db.validate_password(pwd)
        assert not is_valid, f"Invalid password accepted: {pwd}"
    print(f"   ✅ Invalid passwords: {len(invalid_passwords)} rejected")

def test_authentication():
    """Test authentication functionality"""
    print_section("🔐 AUTHENTICATION TESTS")
    
    # Test 1: Authenticate admin
    print("✅ Test 1: Authenticate Admin User")
    success, user_data = user_db.authenticate_user(
        'amansah1717@gmail.com',
        'maritime_defense_2025'
    )
    assert success, "Admin authentication failed"
    assert user_data['email'] == 'amansah1717@gmail.com', "Email mismatch"
    assert user_data['role'] == 'admin', "Role mismatch"
    print(f"   ✅ Authenticated: {user_data['full_name']}")
    print(f"   ✅ Role: {user_data['role']}")
    print(f"   ✅ Login count: {user_data['login_count']}")
    
    # Test 2: Wrong password
    print("\n✅ Test 2: Reject Wrong Password")
    success, _ = user_db.authenticate_user(
        'amansah1717@gmail.com',
        'WrongPassword123'
    )
    assert not success, "Wrong password was accepted"
    print(f"   ✅ Wrong password correctly rejected")
    
    # Test 3: Non-existent user
    print("\n✅ Test 3: Reject Non-existent User")
    success, _ = user_db.authenticate_user(
        'nonexistent@example.com',
        'AnyPassword123'
    )
    assert not success, "Non-existent user was accepted"
    print(f"   ✅ Non-existent user correctly rejected")
    
    # Test 4: Deactivated user
    print("\n✅ Test 4: Reject Deactivated User")
    # Create test user
    user_db.register_user(
        email='deactivated@example.com',
        password='TestPass123',
        full_name='Deactivated User',
        role='user'
    )
    # Deactivate
    user_db.deactivate_user(user_id=3)
    # Try to authenticate
    success, _ = user_db.authenticate_user(
        'deactivated@example.com',
        'TestPass123'
    )
    assert not success, "Deactivated user was accepted"
    print(f"   ✅ Deactivated user correctly rejected")

def test_jwt():
    """Test JWT token functionality"""
    print_section("🔑 JWT TOKEN TESTS")
    
    # Test 1: Create token
    print("✅ Test 1: Create JWT Token")
    token = AuthManager.create_jwt_token('amansah1717@gmail.com')
    assert token is not None, "Token creation failed"
    assert len(token) > 0, "Token is empty"
    print(f"   ✅ Token created: {token[:50]}...")
    
    # Test 2: Verify token
    print("\n✅ Test 2: Verify JWT Token")
    payload = AuthManager.verify_jwt_token(token)
    assert payload is not None, "Token verification failed"
    assert payload['username'] == 'amansah1717@gmail.com', "Username mismatch"
    assert payload['role'] == 'admin', "Role mismatch"
    print(f"   ✅ Token verified")
    print(f"   ✅ Username: {payload['username']}")
    print(f"   ✅ Role: {payload['role']}")
    print(f"   ✅ Expiry: {payload['exp']}")
    
    # Test 3: Invalid token
    print("\n✅ Test 3: Reject Invalid Token")
    payload = AuthManager.verify_jwt_token('invalid.token.here')
    assert payload is None, "Invalid token was accepted"
    print(f"   ✅ Invalid token correctly rejected")

def test_session():
    """Test session management"""
    print_section("💾 SESSION MANAGEMENT TESTS")
    
    # Test 1: Initialize session
    print("✅ Test 1: Initialize Session State")
    AuthManager.init_session_state()
    print(f"   ✅ Session state initialized")
    
    # Test 2: Session storage
    print("\n✅ Test 2: Session Storage")
    # This would require Streamlit context, so we'll just verify the methods exist
    assert hasattr(AuthManager, 'save_session_to_storage'), "save_session_to_storage method missing"
    assert hasattr(AuthManager, 'load_session_from_storage'), "load_session_from_storage method missing"
    print(f"   ✅ Session storage methods available")

def test_user_management():
    """Test user management functionality"""
    print_section("👥 USER MANAGEMENT TESTS")
    
    # Test 1: Register new user
    print("✅ Test 1: Register New User")
    success, message = user_db.register_user(
        email='newuser@example.com',
        password='NewPass123',
        full_name='New User',
        role='user'
    )
    assert success, f"Registration failed: {message}"
    print(f"   ✅ User registered: newuser@example.com")
    
    # Test 2: Get user
    print("\n✅ Test 2: Get User Information")
    user = user_db.get_user(4)
    assert user is not None, "User not found"
    assert user['email'] == 'newuser@example.com', "Email mismatch"
    print(f"   ✅ User found: {user['full_name']}")
    
    # Test 3: Update user
    print("\n✅ Test 3: Update User")
    success, message = user_db.update_user(
        user_id=4,
        full_name='Updated User'
    )
    assert success, f"Update failed: {message}"
    user = user_db.get_user(4)
    assert user['full_name'] == 'Updated User', "Update failed"
    print(f"   ✅ User updated: {user['full_name']}")
    
    # Test 4: Change password
    print("\n✅ Test 4: Change Password")
    success, message = user_db.change_password(
        user_id=4,
        old_password='NewPass123',
        new_password='UpdatedPass456'
    )
    assert success, f"Password change failed: {message}"
    print(f"   ✅ Password changed successfully")
    
    # Test 5: Deactivate user
    print("\n✅ Test 5: Deactivate User")
    success, message = user_db.deactivate_user(user_id=4)
    assert success, f"Deactivation failed: {message}"
    user = user_db.get_user(4)
    assert user['is_active'] == 0, "User still active"
    print(f"   ✅ User deactivated")
    
    # Test 6: Activate user
    print("\n✅ Test 6: Activate User")
    success, message = user_db.activate_user(user_id=4)
    assert success, f"Activation failed: {message}"
    user = user_db.get_user(4)
    assert user['is_active'] == 1, "User still inactive"
    print(f"   ✅ User activated")

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  🧪 MARITIME DEFENSE DASHBOARD - END-TO-END TESTS")
    print("="*70)
    
    try:
        test_database()
        test_authentication()
        test_jwt()
        test_session()
        test_user_management()
        
        print_section("✅ ALL TESTS PASSED!")
        print("🚀 System is ready for production use")
        print(f"📊 Timestamp: {datetime.now().isoformat()}")
        print("="*70 + "\n")
        
        return 0
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

