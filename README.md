# RippleCSVDownloader

A simple tool which logs into https://rippleenergy.com/ and saves your actual/forecast data as CSV files.

The Python3 script requires "requests" which you may need to install first using apt/pip/virtual env/etc.

`sudo apt update&&sudo apt install python3-requests` or `pip3 install requests` for example.

If installing for the first time copy config.txt to config.py and edit to set your username/password.

If upgrading compare config.py with config.txt and add any new values to config.py you want to change.

## Running

`python3 RippleCSVDownloader.py` or `python RippleCSVDownloader.py` if your python is Python 3.

## CSV format

By default the CSV files are named as below for Graig Fatha and have the following format.

RippleEnergy-Graig_Fatha-forecast.csv - From "Next 4 days" chart
> \<date forecast made>,\<forecasted date>,\<kWh>,\<savings>

RippleEnergy-Graig_Fatha-hourly.csv - From "Today chart" includes both forecast which is replaced by actal data as it's updated
> \<date time>,\<kWh>,\<savings>,\<isForecast>

RippleEnergy-Graig_Fatha-forecast-hourly.csv - From "Today" chart but only includes forecast data
> \<date time>,\<kWh>,\<savings>

RippleEnergy-Graig_Fatha-daily.csv - From "Last 30 days" chart
> \<date>,\<kWh>,\<savings>

The CSV files are fully rewritten if any changes are detected.

## Things to note

I call "Today" 24:00 tomorrows 00:00 in the dates saved to the CSV for easlier manipulation.

You can never retrieve the last hours (24:00/00:00) non-forecasted stats for "Today" - it could probably be calculated once the daily stats include that day but as historical daily stats change it would need to be checked/recalculated frequently (RippleEnergy are aware you can't get the last hour stats so at some point they might be available via a "Yesterday" hourly chart or something).

Historical entries do change so the CSV files are fully rewritten (not appended to) every time an entry is added or updated.

You probably only need to run the script at most once per hour so please pick a random minute in the hour if you're scheduling it, if you only run the script once per day then I would advise running it a random minute after 23:00 so you have all of the hourly stats available for the day.
