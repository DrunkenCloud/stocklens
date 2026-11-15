from pipeline.breeze_client import check_response, is_session_error
from pipeline.run import status_for


def test_recognizes_expired_session_errors():
    assert is_session_error(Exception("Unexpected error: Session key is expired."))
    assert is_session_error(RuntimeError("SESSION KEY IS EXPIRED"))
    assert is_session_error(Exception("Invalid Session"))
    assert is_session_error(Exception("Unexpected error: Could not authenticate credentials. Please check session key."))


def test_other_errors_are_not_session_errors():
    assert not is_session_error(Exception("Connection reset by peer"))
    assert not is_session_error(KeyError("Success"))
    assert not is_session_error(Exception("Unable to retrieve customer details at the moment. Please try again later."))
    assert not is_session_error(Exception("Could not authenticate credentials. Please check api key."))


def test_exit_code_to_status():
    assert (status_for(0), status_for(1), status_for(75), status_for(-9)) == ("done", "failed", "skipped", "failed")


def test_check_response_unwraps_success_and_raises_on_error():
    assert check_response({"Success": [{"a": 1}], "Status": 200, "Error": None}) == [{"a": 1}]
    assert check_response({"Success": None, "Status": 200, "Error": None}) == []
    try:
        check_response({"Success": None, "Status": 500, "Error": "Rate limit exceeded"})
    except RuntimeError as e:
        assert "Rate limit exceeded" in str(e)
    else:
        raise AssertionError("expected RuntimeError")


if __name__ == "__main__":
    for t in (test_check_response_unwraps_success_and_raises_on_error, test_recognizes_expired_session_errors, test_other_errors_are_not_session_errors, test_exit_code_to_status):
        t()
        print(f"ok  {t.__name__}")
