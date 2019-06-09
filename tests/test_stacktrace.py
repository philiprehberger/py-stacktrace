from philiprehberger_stacktrace import format_exception, ExceptionReport, FrameInfo


def _make_exception():
    try:
        raise ValueError("test error")
    except ValueError as e:
        return e


def test_format_exception():
    exc = _make_exception()
    report = format_exception(exc)
    assert isinstance(report, ExceptionReport)
    assert report.exc_type == "ValueError"
    assert report.message == "test error"


def test_frames():
    exc = _make_exception()
    report = format_exception(exc)
    assert len(report.frames) > 0
    assert isinstance(report.frames[0], FrameInfo)


def test_frame_info():
    exc = _make_exception()
    report = format_exception(exc)
    frame = report.frames[-1]
    assert frame.function == "_make_exception"
    assert frame.lineno > 0
    assert "test_stacktrace" in frame.filename


def test_short_output():
    exc = _make_exception()
    report = format_exception(exc)
    short = report.short()
    assert "ValueError" in short
    assert "test error" in short


def test_detailed_output():
    exc = _make_exception()
    report = format_exception(exc)
    detailed = report.detailed(color=False)
    assert "ValueError" in detailed
    assert "test error" in detailed


def test_detailed_with_color():
    exc = _make_exception()
    report = format_exception(exc)
    detailed = report.detailed(color=True)
    assert "\033[" in detailed  # ANSI codes


def test_chained_exception():
    try:
        try:
            raise ValueError("original")
        except ValueError as e:
            raise RuntimeError("wrapped") from e
    except RuntimeError as e:
        report = format_exception(e)
        assert report.cause is not None
        assert report.cause.exc_type == "ValueError"
        assert report.exc_type == "RuntimeError"


def test_short_filename():
    frame = FrameInfo(filename="/usr/lib/python3.12/json/__init__.py", lineno=1, function="test", line="")
    assert isinstance(frame.short_filename, str)


def test_is_stdlib():
    exc = _make_exception()
    report = format_exception(exc)
    # Our test frames should not be stdlib
    for frame in report.frames:
        if "test_stacktrace" in frame.filename:
            assert frame.is_stdlib is False
