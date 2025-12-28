def validate_login(name, password, college, experience):
    if not all([name, password, college, experience]):
        return False
    return True
