import datetime
import re
import requests
from typing import List
from common import DayOfTheWeek


class CourseTimeSlot:
    def __init__(self, building: str, room: str, day_of_week: DayOfTheWeek,
                 start_time: datetime.time, end_time: datetime.time):
        self.building = building
        self.room = room
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self) -> str:
        str_start_time = str(self.start_time)
        str_end_time = str(self.end_time)
        return f'{self.day_of_week.name}: {str_start_time}-{str_end_time} at {self.building}'

    __str__ = __repr__


class Course:
    def __init__(self, name: str, major: str, class_id: int, crn: int, instructor: str,
                 num_credits: int, time_slots: List[CourseTimeSlot]):
        self.name = name
        self.major = major
        self.class_id = class_id
        self.crn = crn
        self.credits = num_credits
        self.instructor = instructor
        self.time_slots = time_slots

    def __repr__(self) -> str:
        return f'COURSE: {self.major} {self.class_id}'


class CourseOffAPI:
    def __init__(self, email: str, password: str):
        self.root = 'https://api.courseoff.com/'
        self.session = requests.Session()
        login_response = self.session.post(self.root + '/signin', json={
            'user':{
                'email': email,
                'password': password
            }
        })
        if not login_response:
            raise ValueError('Login unsuccessful')

        terms_response = self.session.get('https://soc.courseoff.com/uga/terms')
        if not terms_response:
            raise ValueError('Unable to get terms for UGA')
        self.terms = self._parse_terms(terms_response.json())
        self.selected_term = None

    def select_term(self, term_name: str) -> None:
        term_name = term_name.strip()
        term_regex = r'^(Fall|Spring) 20[0-9]{2}$'
        valid_term_str = re.match(term_regex, term_name)
        if not valid_term_str:
            raise ValueError('Please enter the term in format: Season Year (Ex. Fall 2019)')

        self.selected_term = self.terms.get(term_name)

        if not self.selected_term:
            raise ValueError(f'No term found for {term_name}')

    def get_courses(self) -> List[Course]:
        if not self.selected_term:
            raise LookupError('Please select a term using \"select_term(term_name: str)\" before '
                              'calling get courses')

        courses_resp = self.session.get(f'{self.root}/schedules?university_id=uga&term_id={self.selected_term["id"]}')
        if not courses_resp:
            raise IOError('Error getting courses')
        courses_resp = courses_resp.json()[0]['courses']

        courses = []
        for course in courses_resp:
            crn = int(course['sections'].pop())
            ident = course['course_ident']
            major = course['major_ident']
            courses.append(self._get_individual_course(major, ident, crn))

        return courses

    def get_term_bounds(self):
        return self.selected_term['start_date'], self.selected_term['end_date']

    def _get_individual_course(self, major: str, ident: int, crn: int) -> Course:
        request_url = \
            f'https://soc.courseoff.com/uga/terms/{self.selected_term["id"]}/majors/{major}/courses/{ident}/sections'
        course_response = self.session.get(request_url)
        if not course_response:
            raise IOError(f'Error getting sessions for {major} {ident}')
        course_response = course_response.json()
        course_name_url = \
            f'https://soc.courseoff.com/uga/terms/{self.selected_term["id"]}/majors/{major}/courses/{ident}'
        course_name_resp = self.session.get(course_name_url)
        if not course_name_resp:
            raise IOError(f'Error getting name for {major} {ident}')
        course_name = course_name_resp.json()['name']

        for course in course_response:
            if course.get('call_number') == crn:
                instructor = ', '.join((course['instructor']['lname'],
                                        course['instructor']['fname']))
                time_slots = [self._parse_time_slot(time) for time in course['timeslots']]
                return Course(course_name, major, ident, crn, instructor, course['credits'], time_slots)

        raise IOError(f'Could not find the course specified by crn {crn}')

    @staticmethod
    def _parse_time(time_int: int) -> datetime.time:
        hours = time_int // 60
        minutes = time_int % 60
        return datetime.time(hour=hours, minute=minutes)

    @staticmethod
    def _parse_time_slot(raw_time_slot: dict) -> CourseTimeSlot:
        location_matching_regex = r'^(.*)(\s[0-9]+)$'
        location_search_result = re.match(location_matching_regex, raw_time_slot['location'])
        if not location_search_result:
            raise ValueError(f'Cannot parse location: {raw_time_slot["location"]}')
        building = location_search_result.group(1)
        room = location_search_result.group(2)

        date_table = {
            'M': DayOfTheWeek.MONDAY,
            'T': DayOfTheWeek.TUESDAY,
            'W': DayOfTheWeek.WEDNESDAY,
            'R': DayOfTheWeek.THURSDAY,
            'F': DayOfTheWeek.FRIDAY,
            'S': DayOfTheWeek.SATURDAY
        }
        day = date_table[raw_time_slot['day']]

        start_time = CourseOffAPI._parse_time(raw_time_slot['start_time'])
        end_time = CourseOffAPI._parse_time(raw_time_slot['end_time'])

        return CourseTimeSlot(building, room, day, start_time, end_time)

    @staticmethod
    def _parse_terms(terms_response: dict) -> dict:
        all_terms = {}
        for term in terms_response:
            term_start_date = datetime.datetime.fromtimestamp(term['start_date'] // 1000).date()
            term_end_date = datetime.datetime.fromtimestamp(term['end_date'] // 1000).date()
            term_name = ' '.join([term['semester'], str(term_start_date.year)])
            all_terms[term_name] = {
                'id': term['ident'],
                'start_date': term_start_date,
                'end_date': term_end_date
            }
        return all_terms

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()
