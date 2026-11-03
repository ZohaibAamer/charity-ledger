"""Stub of the dbt_utils package namespace so sqlfluff can parse models.

Only the macros this project uses need stubbing; output just has to be
valid SQL, not correct SQL.
"""


def generate_surrogate_key(fields):
    joined = " || ".join(str(f) for f in fields)
    return f"md5({joined})"
