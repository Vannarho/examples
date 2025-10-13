# Copyright (C) 2025 Growth Mindset Pty Ltd 
# All rights reserved.
# 
# import os
import VRE as vre

startDateString = '2020-05-01'
calendarString = 'Japan'
tenorString = '1M'
businessDayConventionString = 'F'
# Delta (wheel-first): resolve XML relative to this script for robustness
_here = os.path.abspath(os.path.dirname(__file__))
_repo = os.path.abspath(os.path.join(_here, os.pardir, os.pardir))
calAdjXml = os.path.join(_repo, "Input", "calendaradjustment.xml")
if not os.path.exists(calAdjXml):
    alt = [
        os.path.join(_here, "..", "Input", "calendaradjustment.xml"),
    ]
    for a in alt:
        if os.path.exists(a):
            calAdjXml = os.path.abspath(a)
            break

startDate = vre.parseDate(startDateString)
calendar = vre.parseCalendar(calendarString)
tenor =  vre.parsePeriod(tenorString)
bdc = vre.parseBusinessDayConvention(businessDayConventionString)
endOfMonth = False

## ADVANCE DATE -- pre adjustment
endDate = calendar.advance(startDate, tenor, bdc, endOfMonth)
print('---------------------------')
print("advance start date by", tenorString)
print("startDate", startDate.to_date())
print("endDate  ", endDate.to_date())

## EXPLORE QL/VRE JAPAN CALENDAR
print('---------------------------')
print('holidays (pre adjustment):')
holidayList = calendar.holidayList(startDate, endDate)
for idx in holidayList:
    print(idx.to_date())

## MAKE USE OF CALENDAR ADJUSTMENT
## new holiday : 2020-06-01
## new business day (previously holiday) : 2020-05-05
calAdj = vre.CalendarAdjustmentConfig()
# Prefer snake_case method exposed by wheel
try:
    calAdj.from_file(calAdjXml)
except Exception:
    calAdj.fromFile(calAdjXml)

# Re-parse calendar so any adjustments registered in the global parser are picked up
calendar = vre.parseCalendar(calendarString)

print('---------------------------')
print('holidays (post adjustment):')
holidayList = calendar.holidayList(startDate, endDate)
for idx in holidayList:
    print(idx.to_date())

## ADVANCE DATE -- post adjustment
endDate = calendar.advance(startDate, tenor, bdc, endOfMonth)
print('---------------------------')
print("advance start date by", tenorString)
print("startDate", startDate.to_date())
print("endDate  ", endDate.to_date())
print('---------------------------')
