
# --- Start of provided code (do not modify data_store or test_cases) ---

data_store = {
    "users": {
        "user_alice": {"name": "Alice", "org_id": "org_a", "role_ids": ["role_member"], "public_profile": False},
        "user_bob": {"name": "Bob", "org_id": "org_b", "role_ids": ["role_member"], "public_profile": True},
        "user_charlie": {"name": "Charlie", "org_id": "org_a", "role_ids": ["role_admin"], "public_profile": False},
        "user_diana": {"name": "Diana", "org_id": "org_a", "role_ids": ["role_guest"], "public_profile": False},
        "user_eve": {"name": "Eve", "org_id": "org_c", "role_ids": ["role_member"], "public_profile": False},
        "user_frank": {"name": "Frank", "org_id": "org_a", "role_ids": ["role_guest", "role_member"], "public_profile": False}, # Guest and Member - Guest rules apply first
    },
    "roles": {
        "role_member": {"name": "Member", "permission_ids": ["perm_read_doc", "perm_write_doc", "perm_read_report"]},
        "role_admin": {"name": "Admin", "permission_ids": []},
        "role_guest": {"name": "Guest", "permission_ids": []}, # Guest logic is hardcoded, no explicit permissions needed
    },
    "permissions": {
        "perm_read_doc": {"action": "read", "resource_type": "document"},
        "perm_write_doc": {"action": "write", "resource_type": "document"},
        "perm_read_report": {"action": "read", "resource_type": "report"},
        "perm_delete_doc": {"action": "delete", "resource_type": "document"},
    },
    "resources": {
        "res_doc_1_a": {"name": "Org A Private Doc 1", "type": "document", "org_id": "org_a", "visibility": "private", "owner_user_id": "user_alice"},
        "res_doc_2_a_pub": {"name": "Org A Public Doc 2", "type": "document", "org_id": "org_a", "visibility": "public", "owner_user_id": "user_alice"},
        "res_report_1_a": {"name": "Org A Private Report 1", "type": "report", "org_id": "org_a", "visibility": "private", "owner_user_id": "user_alice"},
        "res_doc_1_b": {"name": "Org B Private Doc 1", "type": "document", "org_id": "org_b", "visibility": "private", "owner_user_id": "user_bob"},
        "res_doc_2_b_pub_owner": {"name": "Org B Private Doc (Public Owner)", "type": "document", "org_id": "org_b", "visibility": "private", "owner_user_id": "user_bob"}, # Bob has public_profile=True
        "res_doc_1_c": {"name": "Org C Private Doc 1", "type": "document", "org_id": "org_c", "visibility": "private", "owner_user_id": "user_eve"},
        "res_report_2_b": {"name": "Org B Private Report", "type": "report", "org_id": "org_b", "visibility": "private", "owner_user_id": "user_bob"},
    },
}

test_cases = [
    # Admin checks (Charlie from org_a)
    ("user_charlie", "read", "res_doc_1_a", True),  # Admin reads own org private
    ("user_charlie", "write", "res_doc_1_b", True), # Admin writes other org private
    ("user_charlie", "delete", "res_doc_2_a_pub", True), # Admin deletes public resource

    # Guest checks (Diana from org_a)
    ("user_diana", "read", "res_doc_2_a_pub", True),  # Guest reads own org public
    ("user_diana", "read", "res_doc_2_b_pub_owner", True), # Guest reads other org public (by owner)
    ("user_diana", "read", "res_doc_1_a", False), # Guest reads own org private
    ("user_diana", "write", "res_doc_2_a_pub", False), # Guest writes public resource
    ("user_diana", "read", "res_doc_1_b", False), # Guest reads other org private

    # Guest with other roles (Frank from org_a) - Guest rules apply first
    ("user_frank", "read", "res_doc_2_a_pub", True), # Frank (Guest+Member) reads public
    ("user_frank", "read", "res_doc_1_a", False), # Frank (Guest+Member) cannot read private
    ("user_frank", "write", "res_doc_1_a", False), # Frank (Guest+Member) cannot write private

    # Regular User checks (Alice from org_a)
    ("user_alice", "read", "res_doc_1_a", True),  # Alice reads own org private doc
    ("user_alice", "write", "res_doc_1_a", True), # Alice writes own org private doc
    ("user_alice", "delete", "res_doc_1_a", False), # Alice tries to delete own org private doc (no delete perm)
    ("user_alice", "read", "res_report_1_a", True), # Alice reads own org private report
    ("user_alice", "write", "res_report_1_a", False), # Alice tries to write own org private report (no write report perm)
    ("user_alice", "read", "res_doc_2_a_pub", True), # Alice reads own org public doc
    ("user_alice", "read", "res_doc_2_b_pub_owner", True), # Alice reads other org public (by owner)
    ("user_alice", "read", "res_doc_1_b", False), # Alice reads other org private doc
    ("user_alice", "write", "res_doc_1_b", False), # Alice writes other org private doc

    # Regular User checks (Bob from org_b)
    ("user_bob", "read", "res_doc_1_b", True),  # Bob reads own org private doc
    ("user_bob", "read", "res_doc_1_a", False), # Bob reads other org private doc
    ("user_bob", "read", "res_doc_2_a_pub", True), # Bob reads other org public doc

    # Regular User checks (Eve from org_c)
    ("user_eve", "read", "res_doc_1_c", True), # Eve reads own org private doc
    ("user_eve", "read", "res_doc_1_a", False), # Eve reads other org private doc
]

# --- End of provided code ---

# You must implement the following functions:

def is_public_resource(resource_id: str, data_store: dict) -> bool:
    """
    Determines if a resource is public based on its visibility or owner's public_profile.
    """
    resource = data_store["resources"].get(resource_id)
    if not resource:
        return False

    if resource["visibility"] == "public":
        return True

    owner_user = data_store["users"].get(resource.get("owner_user_id"))
    if owner_user and owner_user.get("public_profile"):
        return True

    return False

def get_effective_permissions(user_id: str, data_store: dict) -> set[tuple[str, str]]:
    """
    Gathers a user's combined permissions (action, resource_type) from all their roles.
    Returns a set of (action, resource_type) tuples.
    """
    user = data_store["users"].get(user_id)
    if not user:
        return set()

    effective_permissions = set()
    for role_id in user["role_ids"]:
        role = data_store["roles"].get(role_id)
        if role:
            for perm_id in role["permission_ids"]:
                permission = data_store["permissions"].get(perm_id)
                if permission:
                    effective_permissions.add((permission["action"], permission["resource_type"]))
    return effective_permissions

def access_check(user_id: str, action: str, resource_id: str, data_store: dict) -> bool:
    """
    Checks if a user has permission to perform an action on a resource based on the rules.
    """
    user = data_store["users"].get(user_id)
    resource = data_store["resources"].get(resource_id)

    if not user or not resource:
        return False # User or resource not found

    user_roles = [data_store["roles"][rid]["name"] for rid in user["role_ids"] if rid in data_store["roles"]]
    is_admin = "Admin" in user_roles
    is_guest = "Guest" in user_roles
    
    # Rule 1: Admins bypass all checks
    if is_admin:
        return True

    # Rule 2: Guests
    if is_guest:
        if action != "read":
            return False # Guests can only read
        return is_public_resource(resource_id, data_store) # Guests can only read public resources

    # For Regular Users (Non-Admin, Non-Guest)
    resource_is_public = is_public_resource(resource_id, data_store)
    resource_type = resource["type"]

    # Rule 4.1: Can read any public resource
    if action == "read" and resource_is_public:
        return True

    # For private resources or non-read actions on public resources
    # Rule 4.2: For private resources, they can only access resources belonging to their own organization
    if not resource_is_public and resource["org_id"] != user["org_id"]:
        return False

    # Rule 4.3: For private resources within their organization, access is granted if their combined role permissions include the requested `action` for the `resource_type` of the target resource.
    effective_permissions = get_effective_permissions(user_id, data_store)
    return (action, resource_type) in effective_permissions


if __name__ == "__main__":
    results = []
    for user_id, action, resource_id, expected in test_cases:
        result = access_check(user_id, action, resource_id, data_store)
        results.append(f"{user_id} {action} {resource_id}: {result}")

    with open("access_log.txt", "w") as f:
        for line in results:
            f.write(line + "\n")

    print("Access check results written to access_log.txt")
