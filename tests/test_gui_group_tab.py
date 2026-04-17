from gui_group_tab import is_valid_email


def test_valid_email():
    assert is_valid_email("name@example.com") is True


def test_valid_email_subdomain():
    assert is_valid_email("name@mail.example.co.jp") is True


def test_invalid_no_dot_in_domain():
    assert is_valid_email("name@gmailcom") is False


def test_invalid_no_at():
    assert is_valid_email("namegmail.com") is False


def test_invalid_space():
    assert is_valid_email("name @gmail.com") is False


def test_invalid_empty():
    assert is_valid_email("") is False
