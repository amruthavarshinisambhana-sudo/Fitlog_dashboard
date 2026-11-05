import pytest

from fitlog_store import (
    create_user,
    get_user_role,
    list_users_for_admin,
    reset_first_admin_password,
    set_user_role,
    authenticate_user,
)


@pytest.fixture
def accounts_db(tmp_path):
    return tmp_path / "fitlog_test.db"


def make_user(accounts_db, username):
    return create_user(
        username,
        "secure-pass-123",
        accounts_db,
        accounts_db.parent / "missing_workouts.csv",
    )


def test_first_signup_is_admin_and_later_signup_is_user(accounts_db):
    first = make_user(accounts_db, "first_user")
    second = make_user(accounts_db, "second_user")

    assert first["role"] == "admin"
    assert second["role"] == "user"
    assert get_user_role(first["id"], accounts_db) == "admin"


def test_admin_can_view_account_metadata_and_change_another_role(accounts_db):
    admin = make_user(accounts_db, "fitlog_admin")
    member = make_user(accounts_db, "fitlog_member")

    users = list_users_for_admin(admin["id"], accounts_db)
    assert [user["username"] for user in users] == ["fitlog_admin", "fitlog_member"]
    assert users[1]["workout_count"] == 0

    set_user_role(admin["id"], member["id"], "admin", accounts_db)
    assert get_user_role(member["id"], accounts_db) == "admin"

    set_user_role(admin["id"], member["id"], "user", accounts_db)
    assert get_user_role(member["id"], accounts_db) == "user"


def test_regular_user_cannot_view_or_change_roles(accounts_db):
    admin = make_user(accounts_db, "owner_admin")
    member = make_user(accounts_db, "regular_member")

    with pytest.raises(PermissionError, match="Administrator access"):
        list_users_for_admin(member["id"], accounts_db)
    with pytest.raises(PermissionError, match="Administrator access"):
        set_user_role(member["id"], admin["id"], "user", accounts_db)


def test_admin_cannot_change_own_role(accounts_db):
    admin = make_user(accounts_db, "only_admin")

    with pytest.raises(ValueError, match="own role"):
        set_user_role(admin["id"], admin["id"], "user", accounts_db)


def test_recovery_code_resets_only_the_first_admin_password(accounts_db):
    admin = make_user(accounts_db, "recovery_admin")
    member = make_user(accounts_db, "recovery_member")
    code = "c" * 43

    assert reset_first_admin_password("incorrect", "new-secure-pass", code, accounts_db) is None
    assert authenticate_user("recovery_admin", "secure-pass-123", accounts_db)

    result = reset_first_admin_password(code, "new-secure-pass", code, accounts_db)

    assert result == {"username": "recovery_admin"}
    assert authenticate_user("recovery_admin", "new-secure-pass", accounts_db)
    assert authenticate_user("recovery_admin", "secure-pass-123", accounts_db) is None
    assert authenticate_user("recovery_member", "secure-pass-123", accounts_db)
    assert get_user_role(admin["id"], accounts_db) == "admin"
    assert get_user_role(member["id"], accounts_db) == "user"


def test_recovery_requires_a_long_configured_code(accounts_db):
    make_user(accounts_db, "recovery_admin")

    assert reset_first_admin_password("short", "new-secure-pass", "short", accounts_db) is None
    with pytest.raises(ValueError, match="8 characters"):
        reset_first_admin_password("x" * 32, "tiny", "x" * 32, accounts_db)
