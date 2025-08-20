from datetime import datetime
def getClosestSeasonStart(everyXmonth):
    """
    Gives a timestamp that should be the start of the past season
    """
    currentDate = datetime.now()
    startMonths = [
     (12,currentDate.year-1),(12,currentDate.year-1),
     (3,currentDate.year),(3,currentDate.year),(3,currentDate.year),
     (6,currentDate.year),(6,currentDate.year),(6,currentDate.year),
     (9,currentDate.year),(9,currentDate.year),(9,currentDate.year),
     (12,currentDate.year),   
    ]
    startMonth, startYear = startMonths[currentDate.month-1]
    newTimestamp = int(datetime(day=1, month=startMonth, year=startYear).timestamp())
    print(currentDate)
    print(startMonth, startYear)
    return newTimestamp

def toDate(timestamp):
    date = datetime.fromtimestamp(timestamp)
    return str(date.month)+"/"+str(date.day)