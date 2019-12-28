import re
from typing import Tuple

from course_off_api import CourseOffAPI


def verify_email(email: str) -> bool:
    email_regex = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'
    return bool(re.match(pattern=email_regex, string=email))


def read_login_info() -> Tuple[str, str]:
    login_file = 'login.txt'
    with open(login_file, 'r') as login_file_obj:
        try:
            email, password = login_file_obj.read().split('\n')
        except (EOFError, ValueError):
            raise ValueError('Incorrectly formatted login file. Please format the file as follows:\n'
                              'email@example.com\n'
                              'password123')
        if not verify_email(email):
            raise ValueError(f'Invalid email: {email}')

        return email, password


def main():
    email, password = read_login_info()
    with CourseOffAPI(email, password) as cf_api:
        cf_api.select_term('Spring 2020')
        courses = cf_api.get_courses()




if __name__ == '__main__':
    main()