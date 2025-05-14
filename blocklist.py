"""Defines the blocklist"""

# The blocklist is used to save tokens from users that logged out.
# If someone tries to use a token from a user that has logged out, it will be blocked.

BLOCKLIST = set()
