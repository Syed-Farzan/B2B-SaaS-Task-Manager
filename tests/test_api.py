import uuid

import pytest


async def register_org_admin(client, org_name: str, email: str, password: str = "secret123"):
    resp = await client.post(
        "/api/v1/register",
        json={
            "organization_name": org_name,
            "email": email,
            "password": password,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login_user(client, email: str, password: str = "secret123") -> str:
    resp = await client.post(
        "/api/v1/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_register_login_and_me(client):
    reg = await register_org_admin(client, "Acme Corp", "admin@acme.com")
    assert reg["role"] == "Admin"
    assert reg["organization"] == "Acme Corp"

    token = await login_user(client, "admin@acme.com")
    me_resp = await client.get("/api/v1/me", headers=auth_headers(token))
    assert me_resp.status_code == 200
    me = me_resp.json()
    assert me["user"] == "admin@acme.com"
    assert me["role"] == "Admin"
    assert "organization_id" in me


@pytest.mark.asyncio
async def test_invite_member_and_login_shares_tenant(client):
    await register_org_admin(client, "Acme Corp", "admin@acme.com")
    admin_token = await login_user(client, "admin@acme.com")
    admin_me = (await client.get("/api/v1/me", headers=auth_headers(admin_token))).json()

    invite_resp = await client.post(
        "/api/v1/users/invite",
        json={"email": "dev@acme.com", "password": "memberpass123"},
        headers=auth_headers(admin_token),
    )
    assert invite_resp.status_code == 201, invite_resp.text
    invited = invite_resp.json()
    assert invited["email"] == "dev@acme.com"
    assert invited["role"] == "Member"
    assert invited["organization_id"] == admin_me["organization_id"]

    member_token = await login_user(client, "dev@acme.com", "memberpass123")
    member_me = (await client.get("/api/v1/me", headers=auth_headers(member_token))).json()
    assert member_me["role"] == "Member"
    assert member_me["organization_id"] == admin_me["organization_id"]


@pytest.mark.asyncio
async def test_member_rbac_enforcement(client):
    await register_org_admin(client, "Acme Corp", "admin@acme.com")
    admin_token = await login_user(client, "admin@acme.com")

    proj_resp = await client.post(
        "/api/v1/projects",
        json={"title": "Core API", "description": "Backend work"},
        headers=auth_headers(admin_token),
    )
    assert proj_resp.status_code == 200
    project_id = proj_resp.json()["id"]

    task_resp = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Build auth", "status": "To Do", "priority": "High"},
        headers=auth_headers(admin_token),
    )
    assert task_resp.status_code == 200
    task_id = task_resp.json()["id"]

    await client.post(
        "/api/v1/users/invite",
        json={"email": "member@acme.com", "password": "memberpass123"},
        headers=auth_headers(admin_token),
    )
    member_token = await login_user(client, "member@acme.com", "memberpass123")

    # Member is forbidden (403) from creating projects, tasks, or inviting users
    assert (
        await client.post(
            "/api/v1/projects",
            json={"title": "Unauthorized Project"},
            headers=auth_headers(member_token),
        )
    ).status_code == 403
    assert (
        await client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json={"title": "Unauthorized Task"},
            headers=auth_headers(member_token),
        )
    ).status_code == 403
    assert (
        await client.post(
            "/api/v1/users/invite",
            json={"email": "other@acme.com", "password": "pass"},
            headers=auth_headers(member_token),
        )
    ).status_code == 403

    # Member can read projects/tasks, update status, and read/write comments in their org
    assert (await client.get("/api/v1/projects", headers=auth_headers(member_token))).status_code == 200
    assert (
        await client.get(f"/api/v1/projects/{project_id}/tasks", headers=auth_headers(member_token))
    ).status_code == 200
    status_resp = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "In Progress"},
        headers=auth_headers(member_token),
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "In Progress"

    comment_resp = await client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "Working on this now"},
        headers=auth_headers(member_token),
    )
    assert comment_resp.status_code == 200
    comments = (
        await client.get(f"/api/v1/tasks/{task_id}/comments", headers=auth_headers(member_token))
    ).json()
    assert len(comments) == 1
    assert comments[0]["content"] == "Working on this now"


@pytest.mark.asyncio
async def test_cross_tenant_projects_and_tasks_return_404(client):
    await register_org_admin(client, "Tenant A", "a@tenanta.com")
    token_a = await login_user(client, "a@tenanta.com")
    proj_a = (
        await client.post(
            "/api/v1/projects",
            json={"title": "Secret A Project"},
            headers=auth_headers(token_a),
        )
    ).json()

    await register_org_admin(client, "Tenant B", "b@tenantb.com")
    token_b = await login_user(client, "b@tenantb.com")

    # Tenant B listing projects cannot see Tenant A's project
    list_b = (await client.get("/api/v1/projects", headers=auth_headers(token_b))).json()
    assert list_b == []

    # Tenant B trying to list or create tasks in Tenant A's project gets 404
    assert (
        await client.get(
            f"/api/v1/projects/{proj_a['id']}/tasks",
            headers=auth_headers(token_b),
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/projects/{proj_a['id']}/tasks",
            json={"title": "Cross-tenant injection"},
            headers=auth_headers(token_b),
        )
    ).status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_task_status_returns_404(client):
    await register_org_admin(client, "Tenant A", "a@tenanta.com")
    token_a = await login_user(client, "a@tenanta.com")
    proj_a = (
        await client.post(
            "/api/v1/projects",
            json={"title": "Project A"},
            headers=auth_headers(token_a),
        )
    ).json()
    task_a = (
        await client.post(
            f"/api/v1/projects/{proj_a['id']}/tasks",
            json={"title": "Task A"},
            headers=auth_headers(token_a),
        )
    ).json()

    await register_org_admin(client, "Tenant B", "b@tenantb.com")
    token_b = await login_user(client, "b@tenantb.com")

    resp = await client.patch(
        f"/api/v1/tasks/{task_a['id']}/status",
        json={"status": "Done"},
        headers=auth_headers(token_b),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_comments_return_404(client):
    await register_org_admin(client, "Tenant A", "a@tenanta.com")
    token_a = await login_user(client, "a@tenanta.com")
    proj_a = (
        await client.post(
            "/api/v1/projects",
            json={"title": "Project A"},
            headers=auth_headers(token_a),
        )
    ).json()
    task_a = (
        await client.post(
            f"/api/v1/projects/{proj_a['id']}/tasks",
            json={"title": "Confidential Task"},
            headers=auth_headers(token_a),
        )
    ).json()
    await client.post(
        f"/api/v1/tasks/{task_a['id']}/comments",
        json={"content": "Confidential comment"},
        headers=auth_headers(token_a),
    )

    await register_org_admin(client, "Tenant B", "b@tenantb.com")
    token_b = await login_user(client, "b@tenantb.com")

    # Both GET and POST comments across tenants must return 404
    get_resp = await client.get(
        f"/api/v1/tasks/{task_a['id']}/comments",
        headers=auth_headers(token_b),
    )
    assert get_resp.status_code == 404

    post_resp = await client.post(
        f"/api/v1/tasks/{task_a['id']}/comments",
        json={"content": "Sneaky comment"},
        headers=auth_headers(token_b),
    )
    assert post_resp.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_email_rejected_on_register_and_invite(client):
    await register_org_admin(client, "Acme Corp", "admin@acme.com")
    admin_token = await login_user(client, "admin@acme.com")

    dup_reg = await client.post(
        "/api/v1/register",
        json={
            "organization_name": "Other Corp",
            "email": "admin@acme.com",
            "password": "password123",
        },
    )
    assert dup_reg.status_code == 400

    dup_invite = await client.post(
        "/api/v1/users/invite",
        json={"email": "admin@acme.com", "password": "password123"},
        headers=auth_headers(admin_token),
    )
    assert dup_invite.status_code == 400


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected(client):
    fake_id = uuid.uuid4()
    assert (await client.get("/api/v1/me")).status_code == 401
    assert (await client.get("/api/v1/projects")).status_code == 401
    assert (
        await client.post(
            "/api/v1/users/invite",
            json={"email": "x@y.com", "password": "pass"},
        )
    ).status_code == 401
    assert (
        await client.get(f"/api/v1/tasks/{fake_id}/comments")
    ).status_code == 401
