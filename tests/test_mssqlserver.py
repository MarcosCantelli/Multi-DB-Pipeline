from multidb.adapters.mssqlserver import escape_value, split_batches


def test_escape_value_wraps_in_braces():
    assert escape_value("abc;123") == "{abc;123}"


def test_escape_value_doubles_closing_brace():
    assert escape_value("abc}123") == "{abc}}123}"


def test_split_batches_splits_on_go():
    sql = "CREATE TABLE a (id INT);\nGO\nCREATE PROCEDURE p AS SELECT 1;"

    batches = split_batches(sql)

    assert batches == [
        "CREATE TABLE a (id INT);",
        "CREATE PROCEDURE p AS SELECT 1;"
    ]


def test_split_batches_ignores_go_inside_words():
    sql = "SELECT 1 AS GOAL;"

    batches = split_batches(sql)

    assert batches == [
        "SELECT 1 AS GOAL;"]

def test_split_batches_accepts_lowercase_go():
    sql = "CREATE TABLE a (id INT);\ngo\nCREATE PROCEDURE p AS SELECT 1;"

    batches = split_batches(sql)

    assert batches == [
        "CREATE TABLE a (id INT);", "CREATE PROCEDURE p AS SELECT 1;"]