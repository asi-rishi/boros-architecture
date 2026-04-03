
# -- Start of Data Definitions --
users_data = {
    1: {'name': 'Alice', 'organization_id': 101, 'is_admin': False, 'public_profile': True},
    2: {'name': 'Bob', 'organization_id': 101, 'is_admin': False, 'public_profile': False},
    3: {'name': 'Charlie', 'organization_id': 102, 'is_admin': True, 'public_profile': False},
    4: {'name': 'Diana', 'organization_id': 102, 'is_admin': False, 'public_profile': False},
    5: {'name': 'Eve_Guest', 'organization_id': 103, 'is_admin': False, 'public_profile': False},
    6: {'name': 'Frank', 'organization_id': 101, 'is_admin': False, 'public_profile': False},
}

organizations_data = {
    101: {'name': 'OrgA'},
    102: {'name': 'OrgB'},
    103: {'name': 'OrgC'},
}

permissions_map = {
    'read': 1001, 'write': 1002, 'delete': 1003, 'manage_users': 1004,
}
permissions_id_to_name = {v: k for k, v in permissions_map.items()}

roles_map = {
    'viewer': 201, 'editor': 202, 'admin_role': 203, 'guest_role': 204,
}
roles_id_to_name = {v: k for k, v in roles_map.items()}

user_roles_data = { # user_id -> [role_id, ...]
    1: [roles_map['editor']],
    2: [roles_map['viewer']],
    3: [roles_map['admin_role']], # This role is for Charlie, but his 'is_admin' flag overrides standard role checks.
    4: [roles_map['viewer']],
    5: [roles_map['guest_role']],
    6: [roles_map['viewer']],
}

role_permissions_data = { # role_id -> [permission_id, ...]
    roles_map['viewer']: [permissions_map['read']],
    roles_map['editor']: [permissions_map['read'], permissions_map['write']],
    roles_map['admin_role']: [permissions_map['read'], permissions_map['write'], permissions_map['delete'], permissions_map['manage_users']],
    roles_map['guest_role']: [permissions_map['read']], # Guests have internal 'read' but are further restricted by resource type.
}

resources_data = {
    10001: {'name': 'Report A', 'organization_id': 101, 'owner_user_id': 1, 'visibility': 'private'}, # Owner Alice has public_profile=True
    10002: {'name': 'Doc B', 'organization_id': 101, 'owner_user_id': 2, 'visibility': 'public'},
    10003: {'name': 'Project Plan C', 'organization_id': 101, 'owner_user_id': 1, 'visibility': 'private'}, # Owner Alice has public_profile=True
    10004: {'name': 'Server Log D', 'organization_id': 102, 'owner_user_id': 3, 'visibility': 'private'},
    10005: {'name': 'Public Notice E', 'organization_id': 103, 'owner_user_id': 5, 'visibility': 'public'},
    10006: {'name': 'Confidential F', 'organization_id': 101, 'owner_user_id': 6, 'visibility': 'private'}, # Owner Frank has public_profile=False
    10007: {'name': 'Cross-Org G', 'organization_id': 102, 'owner_user_id': 4, 'visibility': 'private'},
}
# -- End of Data Definitions --

def access_check(user_id: int, permission_name: str, resource_id: int) -> bool:
    """
    Checks if a user has the specified permission on a resource based on a set of rules.
    """
    user = users_data.get(user_id)
    resource = resources_data.get(resource_id)

    if not user or not resource:
        return False # User or resource not found

    # Rule 1: Admin Bypass
    if user['is_admin']:
        return True

    # Rule 2: Guest Access
    user_roles = user_roles_data.get(user_id, [])
    if roles_map['guest_role'] in user_roles:
        if permission_name != 'read':
            return False

        # Check if resource is public for guest read access
        is_resource_public = resource['visibility'] == 'public'
        resource_owner_id = resource['owner_user_id']
        resource_owner = users_data.get(resource_owner_id)

        if resource_owner and resource_owner['public_profile']:
            is_resource_public = True
        
        if is_resource_public:
            return True
        else:
            return False

    # Rule 3: Organization Scope
    if user['organization_id'] != resource['organization_id']:
        return False

    # Rule 4: Role-Based Permissions
    required_permission_id = permissions_map.get(permission_name)
    if required_permission_id is None:
        return False # Invalid permission name

    aggregated_permissions = set()
    for role_id in user_roles:
        permissions_for_role = role_permissions_data.get(role_id, [])
        aggregated_permissions.update(permissions_for_role)
    
    return required_permission_id in aggregated_permissions

# Test Cases
test_cases = [
    (1, 'read', 10001),
    (1, 'write', 10001),
    (2, 'write', 10001),
    (3, 'delete', 10004),
    (3, 'manage_users', 10001),
    (2, 'read', 10004),
    (5, 'read', 10002),
    (5, 'write', 10002),
    (5, 'read', 10006),
    (4, 'read', 10003),
    (6, 'read', 10003),
]

results = []
for user_id, permission_name, resource_id in test_cases:
    result = access_check(user_id, permission_name, resource_id)
    results.append(str(result))

# Write results to file
with open('access_results.txt', 'w') as f:
    for res in results:
        f.write(res + '\n')

print("Access check results written to access_results.txt")
