import os
from collections import namedtuple

# Define the data model using namedtuples for immutability and clarity
User = namedtuple('User', ['id', 'organization_id', 'role_ids', 'is_admin', 'public_profile'])
Role = namedtuple('Role', ['id', 'permission_ids'])
Permission = namedtuple('Permission', ['id', 'action']) # e.g., 'read', 'write', 'delete'
Resource = namedtuple('Resource', ['id', 'organization_id', 'owner_user_id', 'visibility']) # e.g., 'private', 'public', 'internal'

# Pre-populate data stores. These dictionaries simulate a database.
USERS_DB = {
    0: User(id=0, organization_id=None, role_ids=[], is_admin=False, public_profile=False), # Special 'Guest' user
    1: User(id=1, organization_id=101, role_ids=[], is_admin=True, public_profile=False), # Admin user for Org 101
    2: User(id=2, organization_id=101, role_ids=['r_dev'], is_admin=False, public_profile=False), # Developer in Org 101
    3: User(id=3, organization_id=102, role_ids=['r_viewer'], is_admin=False, public_profile=True), # Viewer in Org 102, public profile
    4: User(id=4, organization_id=102, role_ids=['r_dev'], is_admin=False, public_profile=False), # Developer in Org 102
    5: User(id=5, organization_id=101, role_ids=[], is_admin=False, public_profile=False), # User with no roles in Org 101
}

ROLES_DB = {
    'r_dev': Role(id='r_dev', permission_ids=['p_read', 'p_write']),
    'r_viewer': Role(id='r_viewer', permission_ids=['p_read']),
}

PERMISSIONS_DB = {
    'p_read': Permission(id='p_read', action='read'),
    'p_write': Permission(id='p_write', action='write'),
    'p_delete': Permission(id='p_delete', action='delete'),
}

RESOURCES_DB = {
    'res1': Resource(id='res1', organization_id=101, owner_user_id=2, visibility='private'),
    'res2': Resource(id='res2', organization_id=101, owner_user_id=2, visibility='public'),
    'res3': Resource(id='res3', organization_id=102, owner_user_id=3, visibility='private'),
    'res4': Resource(id='res4', organization_id=102, owner_user_id=3, visibility='internal'),
    'res5': Resource(id='res5', organization_id=101, owner_user_id=3, visibility='private'), # Owner u3 has public_profile=True, making this resource public
    'res6': Resource(id='res6', organization_id=102, owner_user_id=None, visibility='public'),
}

def access_check(user: User, resource: Resource, requested_action: str) -> bool:
    """
    Determines if a user has permission to perform a requested action on a resource.

    Args:
        user: The User object attempting the action.
        resource: The Resource object being accessed.
        requested_action: The action requested (e.g., 'read', 'write', 'delete').

    Returns:
        True if the user has access, False otherwise.
    """
    # Helper function to determine if a resource is public (Rule 3)
    def _is_resource_public(res: Resource) -> bool:
        is_owner_profile_public = False
        if res.owner_user_id is not None and res.owner_user_id in USERS_DB:
            is_owner_profile_public = USERS_DB[res.owner_user_id].public_profile
        return res.visibility == 'public' or is_owner_profile_public

    # --- IMPLEMENT YOUR LOGIC BELOW THIS LINE ---
    # Follow the Access Rules provided in the problem description.
    # Rule 1: Admins bypass all permission checks
    if user.is_admin:
        return True

    is_public = _is_resource_public(resource)

    # Rule 2: Guests can only read public resources
    if user.id == 0:
        return requested_action == 'read' and is_public

    # Rule 4a: Cross-organizational public resource reads
    if requested_action == 'read' and is_public:
        return True

    # Rule 4b: Organization check
    if user.organization_id != resource.organization_id:
        return False

    # Rule 4c: Role-based permission check within the same organization
    user_permissions = set()
    for role_id in user.role_ids:
        if role_id in ROLES_DB:
            for perm_id in ROLES_DB[role_id].permission_ids:
                if perm_id in PERMISSIONS_DB:
                    user_permissions.add(PERMISSIONS_DB[perm_id].action)

    return requested_action in user_permissions

# --- Test Harness (DO NOT MODIFY BELOW THIS LINE) ---
test_cases = [
    # (User object, Resource object, requested_action_string)
    (USERS_DB[1], RESOURCES_DB['res3'], 'write'), # Admin bypass
    (USERS_DB[0], RESOURCES_DB['res2'], 'read'), # Guest read public
    (USERS_DB[0], RESOURCES_DB['res2'], 'write'), # Guest write public
    (USERS_DB[0], RESOURCES_DB['res1'], 'read'), # Guest read private
    (USERS_DB[2], RESOURCES_DB['res1'], 'read'), # Dev role, same org, read permission
    (USERS_DB[2], RESOURCES_DB['res1'], 'write'), # Dev role, same org, write permission
    (USERS_DB[2], RESOURCES_DB['res1'], 'delete'), # Dev role, same org, no delete permission
    (USERS_DB[2], RESOURCES_DB['res3'], 'read'), # Dev role, different org, private resource
    (USERS_DB[2], RESOURCES_DB['res2'], 'read'), # Regular user read public from same org
    (USERS_DB[2], RESOURCES_DB['res2'], 'write'), # Regular user write public from same org
    (USERS_DB[3], RESOURCES_DB['res2'], 'read'), # Viewer role, different org, public resource read
    (USERS_DB[3], RESOURCES_DB['res2'], 'write'), # Viewer role, different org, public resource write (no role permission)
    (USERS_DB[3], RESOURCES_DB['res4'], 'read'), # Viewer role, same org, read permission
    (USERS_DB[3], RESOURCES_DB['res4'], 'write'), # Viewer role, same org, no write permission
    (USERS_DB[5], RESOURCES_DB['res1'], 'read'), # No roles, same org, private resource
    (USERS_DB[5], RESOURCES_DB['res2'], 'read'), # No roles, same org, public resource read
    (USERS_DB[5], RESOURCES_DB['res2'], 'write'), # No roles, same org, public resource write (no role permission)
    (USERS_DB[2], RESOURCES_DB['res5'], 'read'), # u2 (org 101) reads res5 (org 101, public via u3 owner)
    (USERS_DB[4], RESOURCES_DB['res5'], 'read'), # u4 (org 102) reads res5 (org 101, public via u3 owner)
    (USERS_DB[4], RESOURCES_DB['res6'], 'write'), # u4 (org 102) writes res6 (org 102, public by visibility)
]

output_filename = "access_results.txt"

with open(output_filename, 'w') as f:
    for i, (user, resource, action) in enumerate(test_cases):
        result = access_check(user, resource, action)
        f.write(f"{result}\n")

print(f"Access check results written to {output_filename}")
