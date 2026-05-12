from glob import glob 
import os 
import datetime
import csv
import re 

#sort exercises based on key
def ex_sort_key(s):
    m = re.match(r"ex(\d+)([a-z]?)", s, re.IGNORECASE)
    number = int(m.group(1))
    letter = m.group(2) or ""  # empty string if no letter
    return (number, letter)

#ensure safety for leap years 
def add_year_safe(dt, years=1):
    """
    Add `years` years to a datetime, safely handling Feb 29 and end-of-month.
    """
    try:
        # Try the normal case first
        return dt.replace(year=dt.year + years)
    except ValueError:
        # This happens only for Feb 29 on non-leap years
        # Fallback: move to Feb 28
        return dt.replace(month=2, day=28, year=dt.year + years)
    
if __name__=="__main__":
    """
    Script to update schedule.csv automatically.
    This allows completely resetting the public repository automatically in a simple fashion. 
    Currently implemented to add in newly added exercises into the schedule automatically. 
    """
    filename = "schedule.csv"
    all_exercises = glob("raw/*/")
    all_exercises = [d.replace("raw/","").replace("/","") for d in all_exercises] #remove raw/ prefix
    all_exercises = [d for d in all_exercises if d.lower().startswith("ex")]
    EXERCISES_TO_APPEND = False
    now = datetime.datetime.now()
    fmt = "%Y-%m-%d %H:%M"
    all_exercises = sorted(all_exercises,key=ex_sort_key)

    if os.path.exists(filename):
        print(f"Found existing csv {filename}. Reading and checking")
        scheduled_exercises = []
        release_times = []
        with open(filename, "r") as f: 
            csv_reader = csv.reader(f)
            for line in csv_reader:
                scheduled_exercises.append(line[0])
                release_times.append(line[-1])

        if len(all_exercises)!=len(scheduled_exercises):
            EXERCISES_TO_APPEND = True 
            print(f"Found {len(all_exercises)} folders in raw/, but only {len(scheduled_exercises)} in {filename}\n Appending missing exercises and giving a random start time. Please fix this later.")
        
        #extract missing exercise weeks     
        if EXERCISES_TO_APPEND:
            for i, exc in enumerate(set(all_exercises).difference(set(scheduled_exercises))):
                new_release_time = datetime.datetime.strptime(release_times[-1],fmt)+datetime.timedelta(days=7*(i+1))
                print(f"Adding new exercise {exc} with release time {new_release_time} to {filename}")
                scheduled_exercises.append(exc)
                release_times.append(new_release_time) #placeholder-value 
        
        #increment by a year except for the setup material 
        release_times = [datetime.datetime.strptime(x,fmt) if isinstance(x,str) else x for x in release_times]
        release_times = [add_year_safe(dt) if "ex1-setup" not in scheduled_exercises[i] else dt for i, dt in enumerate(release_times)]
        out_str = "Updated"
        
    else:
        release_times = [now + datetime.timedelta(days=7*(i+3)) if "ex1-setup" not in exc else add_year_safe(now,years=-10) for i, exc in enumerate(all_exercises)] #"YYYY-MM-DD HH:MM"
        out_str = "Generated"

    release_times = [x.strftime(fmt) for x in release_times] #remove seconds format 
    output = []
    for a, b in zip(all_exercises,release_times):
        output.append([a,b])
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(output)
    
    print(f"{out_str} {filename}")
        

        
        
