from __future__ import annotations
import datetime
import pyzt
from enum import Enum


class DayOfTheWeek(Enum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    def to_gday(self):
        conversion_table = {
            'SUNDAY': 'SU',
            'MONDAY': 'MO',
            'TUESDAY': 'TU',
            'WEDNESDAY': 'WE',
            'THURSDAY': 'TH',
            'FRIDAY': 'FR',
            'SATURDAY': 'SA'
        }
        
        r = conversion_table.get(self.name)
        if r:
            return r
        raise ValueError(f'Invalid day of the week {self.name}')

    @staticmethod
    def weekday_of(day: datetime):
        return DayOfTheWeek((day.weekday() + 1) % 7)

    @staticmethod
    def find_first_day_after_date(start_date: datetime.date, weekday: DayOfTheWeek):
        day = start_date
        while DayOfTheWeek.weekday_of(day) != weekday:
            day += datetime.timedelta(days=1)
        return day
