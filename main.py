import re
from typing import Tuple
from common import DayOfTheWeek
from course_off_api import CourseOffAPI
from google_calendar_api.google_calendar_api import GoogleCalendarAPIWrapper


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
        semester_start_date, semester_end_date = cf_api.get_term_bounds()
        courses = cf_api.get_courses()

    g_cal = GoogleCalendarAPIWrapper()
    for course in courses:
        for time_slot in course.time_slots:
            g_cal.add_weekly_event(name=course.name, repeats_on=time_slot.day_of_week,
                                   start_time=time_slot.start_time, end_time=time_slot.end_time,
                                   start_date=semester_start_date, end_date=semester_end_date,
                                   location=f'{time_slot.building} - Rm {time_slot.room}')


if __name__ == '__main__':
    main()
