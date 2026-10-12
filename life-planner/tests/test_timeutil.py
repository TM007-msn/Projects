from datetime import timezone

from app.timeutil import iso_local, parse_local


def test_naive_time_in_summer_is_read_as_bst():
    assert parse_local("2026-10-12T17:00") == parse_local("2026-10-12T16:00:00+00:00")


def test_naive_time_in_winter_is_read_as_gmt():
    assert parse_local("2026-12-01T17:00").hour == 17


def test_explicit_offset_is_respected():
    assert parse_local("2026-12-01T17:00+02:00").hour == 15


def test_output_is_uk_local():
    utc = parse_local("2026-10-12T16:00+00:00")
    assert utc.tzinfo == timezone.utc
    assert iso_local(utc) == "2026-10-12T17:00+01:00"


def test_clocks_going_back_is_handled():
    # Sunday 25/10/2026 the UK goes from BST to GMT at 02:00.
    assert iso_local(parse_local("2026-10-24T09:00")) == "2026-10-24T09:00+01:00"
    assert iso_local(parse_local("2026-10-26T09:00")) == "2026-10-26T09:00+00:00"
