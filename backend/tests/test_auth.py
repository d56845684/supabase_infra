from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_register_employee_requires_employee_type(
    client,
    mock_supabase_service
):
    mock_supabase_service.sign_up = AsyncMock()

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "employee@example.com",
            "password": "password123",
            "name": "Employee User",
            "role": "employee"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "employee 角色必須提供 employee_type"
    mock_supabase_service.sign_up.assert_not_called()


@pytest.mark.asyncio
async def test_register_employee_creates_employee_entity(
    client,
    mock_supabase_service
):
    mock_user = Mock(id="employee-user-id", email="employee@example.com")
    signup_response = Mock(user=mock_user)
    mock_supabase_service.sign_up = AsyncMock(return_value=signup_response)
    mock_supabase_service.table_insert = AsyncMock(side_effect=[
        {"id": "employee-entity-id"},
        {"id": "profile-id"}
    ])
    mock_supabase_service.table_delete = AsyncMock()
    mock_supabase_service.admin_delete_user = AsyncMock()

    payload = {
        "email": "employee@example.com",
        "password": "password123",
        "name": "Employee User",
        "role": "employee",
        "employee_type": "full_time"
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "註冊成功，請檢查您的郵箱進行驗證"
    assert mock_supabase_service.table_insert.call_count == 2

    first_call = mock_supabase_service.table_insert.call_args_list[0]
    assert first_call.kwargs["table"] == "employees"
    assert first_call.kwargs["data"]["employee_type"] == "full_time"
    assert first_call.kwargs["use_service_key"] is True

    second_call = mock_supabase_service.table_insert.call_args_list[1]
    assert second_call.kwargs["table"] == "user_profiles"
    assert second_call.kwargs["data"]["employee_id"] == "employee-entity-id"
    assert second_call.kwargs["use_service_key"] is True


@pytest.mark.asyncio
async def test_register_teacher_creates_teacher_entity(
    client,
    mock_supabase_service
):
    mock_user = Mock(id="teacher-user-id", email="teacher@example.com")
    signup_response = Mock(user=mock_user)
    mock_supabase_service.sign_up = AsyncMock(return_value=signup_response)
    mock_supabase_service.table_insert = AsyncMock(side_effect=[
        {"id": "teacher-entity-id"},
        {"id": "profile-id"}
    ])
    mock_supabase_service.table_delete = AsyncMock()
    mock_supabase_service.admin_delete_user = AsyncMock()

    payload = {
        "email": "teacher@example.com",
        "password": "password123",
        "name": "Teacher User",
        "role": "teacher"
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "註冊成功，請檢查您的郵箱進行驗證"

    first_call = mock_supabase_service.table_insert.call_args_list[0]
    assert first_call.kwargs["table"] == "teachers"
    assert first_call.kwargs["data"]["teacher_no"].startswith("T")

    second_call = mock_supabase_service.table_insert.call_args_list[1]
    assert second_call.kwargs["table"] == "user_profiles"
    assert second_call.kwargs["data"]["teacher_id"] == "teacher-entity-id"


@pytest.mark.asyncio
async def test_register_student_creates_student_entity(
    client,
    mock_supabase_service
):
    mock_user = Mock(id="student-user-id", email="student@example.com")
    signup_response = Mock(user=mock_user)
    mock_supabase_service.sign_up = AsyncMock(return_value=signup_response)
    mock_supabase_service.table_insert = AsyncMock(side_effect=[
        {"id": "student-entity-id"},
        {"id": "profile-id"}
    ])
    mock_supabase_service.table_delete = AsyncMock()
    mock_supabase_service.admin_delete_user = AsyncMock()

    payload = {
        "email": "student@example.com",
        "password": "password123",
        "name": "Student User",
        "role": "student"
    }

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "註冊成功，請檢查您的郵箱進行驗證"

    first_call = mock_supabase_service.table_insert.call_args_list[0]
    assert first_call.kwargs["table"] == "students"
    assert first_call.kwargs["data"]["student_no"].startswith("S")

    second_call = mock_supabase_service.table_insert.call_args_list[1]
    assert second_call.kwargs["table"] == "user_profiles"
    assert second_call.kwargs["data"]["student_id"] == "student-entity-id"
