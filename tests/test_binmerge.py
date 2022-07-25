import os
import pytest
import re

from re_helpers import binmerge


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


def result_match(output, handled=0, equal=0, differences=0, ambiguous=0, worst=0):
    return re.search(
        "^"
        + re.escape(
            binmerge.RESULT_STRING.format(
                handled=handled,
                equal=equal,
                differences=differences,
                ambiguous=ambiguous,
                worst=worst,
            )
        )
        + "$",
        output.decode("utf-8"),
        re.MULTILINE,
    )


@pytest.fixture
def files():
    return [
        os.path.join(FIXTURE_DIR, "helloworld.txt"),
        os.path.join(FIXTURE_DIR, "hello.txt"),
    ]


def test_noargs():
    """Test that the program exits with an error if no arguments are provided."""
    with pytest.raises(SystemExit) as e:
        binmerge.main([])
    assert e.value.code is not None and e.value.code != 0


def test_args():
    """Program exits without an error if valid arguments are provided."""
    with pytest.raises(SystemExit) as e:
        binmerge.main(["--help"])
    assert e.value.code is None or e.value.code == 0


def test_similar(capsysbinary, files):
    """Merging similar files works."""
    with open(files[0], "rb") as f:
        data = f.read()
    binmerge.main([files[0], files[0], files[0]])
    out, err = capsysbinary.readouterr()
    assert result_match(err, handled=12, equal=12, worst=3)
    assert out == data


def test_dissimilar(capsysbinary, files):
    """Merging dissimilar files works."""
    with open(files[0], "rb") as f:
        data = f.read()
    binmerge.main([files[0], files[1], files[0]])
    out, err = capsysbinary.readouterr()
    assert result_match(err, handled=12, equal=5, differences=7, worst=2)
    assert out == data


def test_minimum(files):
    """Minimum option works."""
    with pytest.raises(SystemExit) as e:
        binmerge.main(["--minimum", "3", files[0], files[1], files[0]])
    assert e.value.code == "minimum_not_met"
