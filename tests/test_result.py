from src.utils.result import Ok, Err, Ok_of, Err_of, result_from


class TestResult:
    def test_ok(self):
        r = Ok(42)
        assert r.ok is True
        assert r.value == 42
        assert r.unwrap() == 42
        assert r.unwrap_or(0) == 42

    def test_err(self):
        r = Err("fail")
        assert r.ok is False
        assert r.error == "fail"
        assert r.unwrap_or(0) == 0

    def test_err_unwrap_raises(self):
        r = Err("fail")
        try:
            r.unwrap()
            assert False, "should have raised"
        except ValueError:
            pass

    def test_ok_map(self):
        r = Ok(2).map(lambda x: x * 3)
        assert r.unwrap() == 6

    def test_err_map(self):
        r = Err("fail").map(lambda x: x * 3)
        assert r.ok is False

    def test_ok_of(self):
        r = Ok_of("hello")
        assert r.ok is True

    def test_err_of(self):
        r = Err_of("error")
        assert r.ok is False

    def test_result_from_success(self):
        r = result_from(lambda x: x + 1, 5)
        assert r.ok is True
        assert r.unwrap() == 6

    def test_result_from_failure(self):
        r = result_from(lambda: 1 / 0)
        assert r.ok is False
        assert "division" in r.error
