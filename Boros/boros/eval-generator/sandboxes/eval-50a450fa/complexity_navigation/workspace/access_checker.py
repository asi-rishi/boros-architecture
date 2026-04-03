
USERS_DB = {
    'alice': {'organization_id': 'org_a', 'is_admin': False, 'is_guest': False, 'public_profile': False, 'roles': ['reader_role']},
    'bob': {'organization_id': 'org_a', 'is_admin': False, 'is_guest': False, 'public_profile': True, 'roles': ['writer_role']},
    'charlie': {'organization_id': 'org_b', 'is_admin': False, 'is_guest': False, 'public_profile': False, 'roles': ['reader_role', 'writer_role']},
    'admin_diana': {'organization_id': 'org_a', 'is_admin': True, 'is_guest': False, 'public_profile': False, 'roles': []},
    'guest_eve': {'organization_id': 'org_a', 'is_admin': False, 'is_guest': True, 'public_profile': False, 'roles': []},
    'owner_frank': {'organization_id': 'org_a', 'is_admin': False, 'is_guest': False, 'public_profile': True, 'roles': ['writer_role']}, # Owner with public profile
}

ROLES_DB = {
    'reader_role': {'permissions': ['read']},
    'writer_role': {'permissions': ['read', 'write']},
    'deleter_role': {'permissions': ['read', 'write', 'delete']},
}

RESOURCES_DB = {
    'doc_a_private': {'organization_id': 'org_a', 'visibility': 'private', 'owner_user_id': 'alice'},
    'doc_a_public': {'organization_id': 'org_a', 'visibility': 'public', 'owner_user_id': 'alice'},
    'doc_a_owned_by_public_profile': {'organization_id': 'org_a', 'visibility': 'private', 'owner_user_id': 'owner_frank'},
    'doc_b_private': {'organization_id': 'org_b', 'visibility': 'private', 'owner_user_id': 'charlie'},
    'doc_c_cross_org_public': {'organization_id': 'org_c', 'visibility': 'public', 'owner_user_id': None},
    'doc_d_nonexistent_owner': {'organization_id': 'org_a', 'visibility': 'private', 'owner_user_id': 'unknown_user'},
}

def can_access(user_id: str, resource_id: str, action: str) -> bool:
    if user_id not in USERS_DB or resource_id not in RESOURCES_DB:
        return False

    user_info = USERS_DB[user_id]
    resource_info = RESOURCES_DB[resource_id]

    # Rule 1: Admins
    if user_info['is_admin']:
        return True

    # Rule 2: Guests
    if user_info['is_guest']:
        if action != 'read':
            return False
        
        is_resource_public = resource_info['visibility'] == 'public'
        
        owner_id = resource_info.get('owner_user_id')
        if owner_id and owner_id in USERS_DB and USERS_DB[owner_id]['public_profile']:
            is_resource_public = True
        
        return is_resource_public

    # Rule 3: Regular Users (non-admin, non-guest)
    if user_info['organization_id'] != resource_info['organization_id']:
        return False

    effective_permissions = set()
    for role_id in user_info['roles']:
        if role_id in ROLES_DB:
            effective_permissions.update(ROLES_DB[role_id]['permissions'])
    
    return action in effective_permissions

TEST_CASES = [
    ('admin_diana', 'doc_a_private', 'read'),
    ('admin_diana', 'doc_b_private', 'delete'),
    ('guest_eve', 'doc_a_public', 'read'),
    ('guest_eve', 'doc_a_private', 'read'), # Should be denied (private resource)
    ('guest_eve', 'doc_a_owned_by_public_profile', 'read'), # Should be allowed (owned by public_profile user)
    ('guest_eve', 'doc_a_public', 'write'), # Should be denied (guests can't write)
    ('alice', 'doc_a_private', 'read'),
    ('alice', 'doc_a_private', 'write'), # Should be denied (alice is only reader)
    ('bob', 'doc_a_private', 'write'),
    ('charlie', 'doc_b_private', 'read'),
    ('charlie', 'doc_a_private', 'read'), # Should be denied (cross-organization)
    ('bob', 'doc_c_cross_org_public', 'read'), # Should be denied (cross-organization for regular user)
    ('unknown_user', 'doc_a_private', 'read'), # Non-existent user
    ('alice', 'unknown_doc', 'read'), # Non-existent resource
]

if __name__ == '__main__':
    with open('access_log.txt', 'w') as f:
        for user, resource, action in TEST_CASES:
            result = can_access(user, resource, action)
            f.write(f"{user},{resource},{action},{result}\n")
