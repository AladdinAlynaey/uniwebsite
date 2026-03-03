#!/usr/bin/env python3
"""
Comprehensive Access Control Test — Tests every user against every endpoint.
Generates a full test report.
"""

import requests
import json
import time

BASE = "http://localhost:5006"

# All users organized by role
USERS = {
    "super_admin": [
        {"name": "Super Admin", "email": "admin@university.edu", "password": "admin123", "faculty": "ALL"},
    ],
    "faculty_head": [
        {"name": "Prof. Mohammed Al-Qadhi", "email": "dean.aiit@university.edu", "password": "dean1234", "faculty": "AIIT"},
        {"name": "Prof. Khalid Al-Amin", "email": "dean.eng@university.edu", "password": "dean1234", "faculty": "ENG"},
    ],
    "teacher": [
        {"name": "Dr. Amin Shayea", "email": "amin.shayea@university.edu", "password": "teacher1234", "faculty": "AIIT"},
        {"name": "Mr. Mohammed Alqumasi", "email": "mohammed.alqumasi@university.edu", "password": "teacher1234", "faculty": "AIIT"},
        {"name": "Mr. Mohaned Al-Mashriqi", "email": "mohaned.almashriqi@university.edu", "password": "teacher1234", "faculty": "AIIT"},
        {"name": "Mr. Omeir Albadani", "email": "omeir.albadani@university.edu", "password": "teacher1234", "faculty": "AIIT"},
        {"name": "Prof. Ahmed Sultan", "email": "ahmed.sultan@university.edu", "password": "teacher1234", "faculty": "AIIT"},
        {"name": "Mr. Hamdan Talib", "email": "hamdan.talib@university.edu", "password": "teacher1234", "faculty": "AIIT"},
        {"name": "Dr. Nabil Saleh", "email": "nabil.saleh@university.edu", "password": "teacher1234", "faculty": "ENG"},
        {"name": "Dr. Layla Hassan", "email": "layla.hassan@university.edu", "password": "teacher1234", "faculty": "ENG"},
    ],
    "batch_rep": [
        {"name": "Alaadin", "email": "rep.alaadin@university.edu", "password": "rep1234", "faculty": "AIIT", "batch": "Alaadin's Batch"},
        {"name": "Ahmed Test", "email": "rep.test@university.edu", "password": "rep1234", "faculty": "AIIT", "batch": "Test Batch 2025"},
        {"name": "Ali Mohammed", "email": "rep.ce@university.edu", "password": "rep1234", "faculty": "ENG", "batch": "CE Batch 2025"},
    ],
    "student": [
        {"name": "Yusuf Ali Hassan", "email": "yusuf.ali@student.university.edu", "password": "student1234", "faculty": "AIIT", "batch": "Test 2025"},
        {"name": "Fatima Mohammed Said", "email": "fatima.mohammed@student.university.edu", "password": "student1234", "faculty": "AIIT", "batch": "Test 2025"},
        {"name": "Omar Khalid Nasser", "email": "omar.khalid@student.university.edu", "password": "student1234", "faculty": "AIIT", "batch": "Test 2025"},
        {"name": "Maryam Saleh Ahmed", "email": "maryam.saleh@student.university.edu", "password": "student1234", "faculty": "AIIT", "batch": "Test 2025"},
        {"name": "Hassan Ibrahim Taher", "email": "hassan.ibrahim@student.university.edu", "password": "student1234", "faculty": "AIIT", "batch": "Test 2025"},
        {"name": "Tariq Omar Saleh", "email": "tariq.omar@student.university.edu", "password": "student1234", "faculty": "ENG", "batch": "CE 2025"},
        {"name": "Nada Khalid Ali", "email": "nada.khalid@student.university.edu", "password": "student1234", "faculty": "ENG", "batch": "CE 2025"},
        {"name": "Majid Yusuf Hassan", "email": "majid.yusuf@student.university.edu", "password": "student1234", "faculty": "ENG", "batch": "CE 2025"},
    ],
}

# Endpoints to test per role
# Format: (path, expected_for_role: "ALLOW"|"DENY")
ENDPOINTS = {
    "public": [
        ("/", "ALLOW"),
        ("/news", "ALLOW"),
        ("/subjects", "ALLOW"),
        ("/chatbot", "ALLOW"),
    ],
    "super_admin_only": [
        ("/superadmin/dashboard", None),  # Only super_admin should get ALLOW
    ],
    "faculty_head_only": [
        ("/faculty/dashboard", None),
    ],
    "teacher_only": [
        ("/teacher/dashboard", None),
    ],
    "batch_rep_only": [
        ("/admin/dashboard", None),
        ("/admin/students", None),
        ("/admin/lectures", None),
        ("/admin/news", None),
        ("/admin/my-grades", None),      # NEW: batch rep student capability
        ("/admin/my-attendance", None),   # NEW: batch rep student capability
    ],
    "student_only": [
        ("/student/dashboard", None),
        ("/student/grades", None),
        ("/student/attendance", None),
    ],
    "common_auth": [
        ("/profile", None),  # Any logged-in user
    ],
}

def login(session, email, password):
    """Login and return True/False."""
    try:
        resp = session.post(f"{BASE}/login", data={"email": email, "password": password}, allow_redirects=False)
        # Follow redirect to check where we end up
        if resp.status_code in [302, 303]:
            location = resp.headers.get("Location", "")
            # If redirected to login again, login failed
            if "/login" in location:
                return False
            return True
        return False
    except Exception as e:
        return False

def logout(session):
    """Logout."""
    try:
        session.get(f"{BASE}/logout", allow_redirects=True)
    except:
        pass

def test_endpoint(session, path):
    """Test if endpoint is accessible. Returns (status_code, accessible, final_url_hint)."""
    try:
        resp = session.get(f"{BASE}{path}", allow_redirects=True, timeout=10)
        status = resp.status_code
        
        # Check if we were redirected to login (denied)
        final_url = resp.url
        if "/login" in final_url and path != "/login":
            return status, "DENIED", "→ login"
        if "/student_login" in final_url:
            return status, "DENIED", "→ student_login"
        
        # Check for flash messages about permissions
        text = resp.text[:2000].lower()
        if "permission" in text and "do not have" in text:
            return status, "DENIED", "→ permission denied"
        if "admin access required" in text:
            return status, "DENIED", "→ admin required"
        if "please log in" in text:
            return status, "DENIED", "→ login required"
        
        if status == 200:
            return status, "ALLOWED", "OK"
        if status == 404:
            return status, "NOT_FOUND", "404"
        return status, "OTHER", f"status={status}"
    except Exception as e:
        return 0, "ERROR", str(e)[:50]


def run_all_tests():
    """Run comprehensive tests for every user."""
    results = {}
    total_pass = 0
    total_fail = 0
    total_tests = 0
    
    # Define expected access per role
    role_access = {
        "super_admin": {
            "/superadmin/dashboard": "ALLOW",
            "/faculty/dashboard": "ALLOW",  # super admin can access faculty too
            "/teacher/dashboard": "DENY",
            "/admin/dashboard": "ALLOW",  # super admin can access admin
            "/admin/students": "ALLOW",
            "/admin/lectures": "ALLOW",
            "/admin/news": "ALLOW",
            "/admin/my-grades": "ALLOW",
            "/admin/my-attendance": "ALLOW",
            "/student/dashboard": "DENY",
            "/student/grades": "DENY",
            "/student/attendance": "DENY",
            "/profile": "ALLOW",
        },
        "faculty_head": {
            "/superadmin/dashboard": "DENY",
            "/faculty/dashboard": "ALLOW",
            "/teacher/dashboard": "DENY",
            "/admin/dashboard": "DENY",
            "/admin/students": "DENY",
            "/admin/lectures": "DENY",
            "/admin/news": "DENY",
            "/admin/my-grades": "DENY",
            "/admin/my-attendance": "DENY",
            "/student/dashboard": "DENY",
            "/student/grades": "DENY",
            "/student/attendance": "DENY",
            "/profile": "ALLOW",
        },
        "teacher": {
            "/superadmin/dashboard": "DENY",
            "/faculty/dashboard": "DENY",
            "/teacher/dashboard": "ALLOW",
            "/admin/dashboard": "DENY",
            "/admin/students": "DENY",
            "/admin/lectures": "DENY",
            "/admin/news": "DENY",
            "/admin/my-grades": "DENY",
            "/admin/my-attendance": "DENY",
            "/student/dashboard": "DENY",
            "/student/grades": "DENY",
            "/student/attendance": "DENY",
            "/profile": "ALLOW",
        },
        "batch_rep": {
            "/superadmin/dashboard": "DENY",
            "/faculty/dashboard": "DENY",
            "/teacher/dashboard": "DENY",
            "/admin/dashboard": "ALLOW",
            "/admin/students": "ALLOW",
            "/admin/lectures": "ALLOW",
            "/admin/news": "ALLOW",
            "/admin/my-grades": "ALLOW",
            "/admin/my-attendance": "ALLOW",
            "/student/dashboard": "DENY",
            "/student/grades": "DENY",
            "/student/attendance": "DENY",
            "/profile": "ALLOW",
        },
        "student": {
            "/superadmin/dashboard": "DENY",
            "/faculty/dashboard": "DENY",
            "/teacher/dashboard": "DENY",
            "/admin/dashboard": "DENY",
            "/admin/students": "DENY",
            "/admin/lectures": "DENY",
            "/admin/news": "DENY",
            "/admin/my-grades": "DENY",
            "/admin/my-attendance": "DENY",
            "/student/dashboard": "ALLOW",
            "/student/grades": "ALLOW",
            "/student/attendance": "ALLOW",
            "/profile": "ALLOW",
        },
    }
    
    # Public pages (no login needed)
    print("=" * 70)
    print("TESTING PUBLIC PAGES (no login)")
    print("=" * 70)
    s = requests.Session()
    public_results = []
    for path, _ in ENDPOINTS["public"]:
        status, access, hint = test_endpoint(s, path)
        passed = access == "ALLOWED"
        total_tests += 1
        if passed:
            total_pass += 1
        else:
            total_fail += 1
        public_results.append({"path": path, "status": status, "access": access, "passed": passed})
        print(f"  {'✅' if passed else '❌'} {path}: {access} ({hint})")
    results["public"] = public_results
    
    # Test chatbot page publicly
    status, access, hint = test_endpoint(s, "/chatbot")
    total_tests += 1
    passed = access == "ALLOWED"
    if passed:
        total_pass += 1
    else:
        total_fail += 1
    print(f"  {'✅' if passed else '❌'} /chatbot: {access} ({hint})")
    
    # Test news page publicly
    status, access, hint = test_endpoint(s, "/news")
    total_tests += 1
    passed = access == "ALLOWED"
    if passed:
        total_pass += 1
    else:
        total_fail += 1
    print(f"  {'✅' if passed else '❌'} /news: {access} ({hint})")
    
    # Test each user role
    all_paths = list(role_access["super_admin"].keys())
    
    for role, users in USERS.items():
        print(f"\n{'=' * 70}")
        print(f"TESTING ROLE: {role.upper()} ({len(users)} users)")
        print(f"{'=' * 70}")
        
        expected = role_access[role]
        results[role] = []
        
        for user in users:
            print(f"\n  👤 {user['name']} ({user['email']}) — Faculty: {user['faculty']}")
            s = requests.Session()
            
            # Test login
            login_ok = login(s, user["email"], user["password"])
            total_tests += 1
            if login_ok:
                total_pass += 1
                print(f"    ✅ LOGIN: Success")
            else:
                total_fail += 1
                print(f"    ❌ LOGIN: Failed")
                results[role].append({
                    "user": user["name"],
                    "email": user["email"],
                    "login": False,
                    "tests": []
                })
                continue
            
            user_tests = []
            for path in all_paths:
                status, access, hint = test_endpoint(s, path)
                exp = expected[path]
                
                # Normalize: ALLOWED matches ALLOW, DENIED matches DENY
                actual = "ALLOW" if access == "ALLOWED" else "DENY"
                passed = actual == exp
                
                total_tests += 1
                if passed:
                    total_pass += 1
                else:
                    total_fail += 1
                
                icon = "✅" if passed else "❌"
                print(f"    {icon} {path}: {actual} (expected: {exp})")
                user_tests.append({
                    "path": path,
                    "expected": exp,
                    "actual": actual,
                    "passed": passed,
                    "status": status,
                })
            
            results[role].append({
                "user": user["name"],
                "email": user["email"],
                "faculty": user["faculty"],
                "login": True,
                "tests": user_tests,
            })
            
            logout(s)
    
    # Summary
    print(f"\n{'=' * 70}")
    print(f"FINAL RESULTS: {total_pass}/{total_tests} PASSED")
    pct = round(total_pass / total_tests * 100, 1) if total_tests > 0 else 0
    print(f"PASS RATE: {pct}%")
    if total_fail > 0:
        print(f"FAILURES: {total_fail}")
    print(f"{'=' * 70}")
    
    # Save results to JSON
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_tests": total_tests,
        "total_pass": total_pass,
        "total_fail": total_fail,
        "pass_rate": pct,
        "results": results,
    }
    with open("test_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults saved to test_results.json")
    return summary

if __name__ == "__main__":
    run_all_tests()
