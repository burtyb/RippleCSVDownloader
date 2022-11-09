#
# RippleCSVDownloader
# https://github.com/burtyb/RippleCSVDownloader
#
# (c) 8086 Consultancy 2022
#
 
from datetime import datetime,timedelta
#from pprint import pprint

import json
import requests
import csv
import os.path
import shutil
import time

import config

def main():
	username = getattr(config, 'username', 'unconfigured')
	password = getattr(config, 'password', 'unconfigured')
	csvfileprefix = getattr(config, 'csvfileprefix', 'RippleEnergy-')
	createbackup = getattr(config, 'createbackup', False)
	testdata = getattr(config, 'testdata', None)
	outputtestdata = getattr(config, 'outputtestdata', False)
	verbose = getattr(config, 'verbose', 3)

	authurl = 'https://rippleenergy.com/graphql?TokenAuth'
	statsurl = 'https://rippleenergy.com/graphql?WindFarmGenerationData'

	authdata = "{\"operationName\":\"TokenAuth\",\"variables\":{\"input\":{\"email\":\""+username+"\",\"password\":\""+password+"\"}},\"query\":\"mutation TokenAuth($input: TokenAuthenticationInput!) {\\n  tokenAuth(input: $input) {\\n    errors {\\n      message\\n      code\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\"}"

	statsdata = "{\"operationName\":\"WindFarmGenerationData\",\"variables\":{},\"query\":\"query WindFarmGenerationData {\\n  member {\\n    id\\n    memberships {\\n      id\\n      capacity\\n      coop {\\n        id\\n        firstYearEstimatedBillSavingsPerWattHour\\n        currency {\\n          precision\\n          code\\n          symbol\\n          __typename\\n        }\\n        generationfarm {\\n          id\\n          name\\n          capacity\\n          operationalStatus\\n          generationData {\\n            title\\n            dataSet {\\n              netPowerOutputKwh\\n              dateTime\\n              isForecastData\\n              savingsForPeriod\\n              __typename\\n            }\\n            __typename\\n          }\\n          __typename\\n        }\\n        __typename\\n      }\\n      __typename\\n    }\\n    __typename\\n  }\\n}\\n\"}"

	newsdata = "{\"operationName\":\"GetNews\",\"variables\":{},\"query\":\"query GetNews {\\n  getNews {\\n    news {\\n      id\\n      title\\n      body\\n      publishDate\\n      hidden\\n      newsDocuments {\\n        id\\n        createdAt\\n        category\\n        file\\n        documentUrl\\n        __typename\\n      }\\n      __typename\\n    }\\n    errors {\\n      message\\n      code\\n      __typename\\n    }\\n    __typename\\n  }\\n}\"}"

	headers = {
		'Content-type': 'application/json', 'Accept': 'text/plain',
		'User-Agent': 'RippleCSVDownloader/0.1 (https://github.com/burtyb/RippleCSVDownloader)',
		}

	# If we're not using test data retrieve it from RippleEnergy website
	if testdata is None:
		with requests.session() as session:
			# Login
			response = session.post(authurl, data=authdata, headers=headers)
			# Get stats
			response = session.post(statsurl, data=statsdata, headers=headers)
			out = json.loads(response.text)

			# Display returned string if requested
			if outputtestdata:
				print("Stats")
				print(response.text)

			# Get news
#			response = session.post(statsurl, data=newsdata, headers=headers)
#			news = json.loads(response.text)
#			# Display returned string if requested
#			if outputtestdata:
#				print("News")
#				print(response.text)

	else:
		# Load output from test data string
		out = json.loads(testdata)

	# If there are 'memberships' loop through them
	if out['data']['member']['memberships']:
		for membership in out['data']['member']['memberships']:
			capacity = membership['capacity']
			name = membership['coop']['generationfarm']['name']
			status = membership['coop']['generationfarm']['operationalStatus']

			# Generate filenames for CSV files
			dailycsvfilename = csvfileprefix+name.replace(' ', '_')+'-daily.csv'
			dailycsvfilenamebak = 'bak/'+csvfileprefix+name.replace(' ', '_')+'-daily-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.csv'
			hourlycsvfilename = csvfileprefix+name.replace(' ', '_')+'-hourly.csv'
			hourlycsvfilenamebak = 'bak/'+csvfileprefix+name.replace(' ', '_')+'-hourly-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.csv'
			forecastcsvfilename = csvfileprefix+name.replace(' ', '_')+'-forecast.csv'
			forecastcsvfilenamebak = 'bak/'+csvfileprefix+name.replace(' ', '_')+'-forecast-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.csv'
			hourlyforecastcsvfilename = csvfileprefix+name.replace(' ', '_')+'-forecast-hourly.csv'
			hourlyforecastcsvfilenamebak = 'bak/'+csvfileprefix+name.replace(' ', '_')+'-hourlyforecast-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.csv'

			# Only generate files for operational farms
			if status == 'OPERATIONAL':
				if verbose > 0: print("Parsing data for", name)

				dailystats = {}
				hourlystats = {}
				forecaststats = {}
				hourlyforecaststats = {}

				# Open existing forecast csv file for this generationfarm
				if os.path.isfile(forecastcsvfilename):
					with open(forecastcsvfilename, mode='r') as csv_file:
						csv_reader = csv.reader(csv_file)
						for row in csv_reader:
							forecaststats[row[0]+'-'+row[1]] = row

				# Open existing daily csv file for this generationfarm
				if os.path.isfile(dailycsvfilename):
					with open(dailycsvfilename, mode='r') as csv_file:
						csv_reader = csv.reader(csv_file)
						for row in csv_reader:
							dailystats[row[0]] = row

				# Open existing hourly csv file for this generationfarm
				if os.path.isfile(hourlycsvfilename):
					with open(hourlycsvfilename, mode='r') as csv_file:
						csv_reader = csv.reader(csv_file)
						for row in csv_reader:
							hourlystats[row[0]] = row

				# Open existing hourly forecast csv file for this generationfarm
				if os.path.isfile(hourlyforecastcsvfilename):
					with open(hourlyforecastcsvfilename, mode='r') as csv_file:
						csv_reader = csv.reader(csv_file)
						for row in csv_reader:
							hourlyforecaststats[row[0]] = row

				forecastchanged = False
				dailychanged = False
				hourlychanged = False
				hourlyforecastchanged = False

				# Loop through each type of generationData
				for generationData in membership['coop']['generationfarm']['generationData']:
					if (generationData['title'] == "NEXT_14_DAYS") or (generationData['title'] == "NEXT_14_DAYS"):
						initial = True
						for dataSet in generationData['dataSet']:
							# We don't need the time portion as the forecast is for the whole day
							datestring = datetime.strptime(dataSet['dateTime'][0:10],'%d/%m/%Y').strftime('%Y-%m-%d')
							# If it's the first entry calculate todays date 
							if initial:
								today = datetime.strptime(dataSet['dateTime'][0:10],'%d/%m/%Y')-timedelta(days=1)
								today = today.strftime('%Y-%m-%d')
								initial = False
							kwh = dataSet['netPowerOutputKwh']
							savings = dataSet['savingsForPeriod']

							# Do we already have an entry for this day?
							if today+'-'+datestring in forecaststats.keys():
								# Is the forecast different vs the CSV data?
								if forecaststats[today+'-'+datestring] != [ today, datestring, str(kwh), str(savings) ]:
									if verbose & 1: print(" Forecast data changed", forecaststats[today+'-'+datestring], "to", [ today, datestring, str(kwh), str(savings) ] )
									forecastchanged = True
							else:
								# No old data for this entry so it's new
								if verbose & 2: print(" Daily forcast data", [ today, datestring, str(kwh), str(savings) ] )
								forecastchanged = True

							if forecastchanged:
								forecaststats[today+'-'+datestring] = [ today, datestring, str(kwh), str(savings) ]
							
					if generationData['title'] == "TODAY":
						for dataSet in generationData['dataSet']:
							# Parse date - for some reason it's in different formats depending on being forecast or actual
							try:
								datestring = datetime.strptime(dataSet['dateTime'], '%d/%m/%Y %H:%M:%S')
							except:
								try:
									datestring = datetime.strptime(dataSet['dateTime'].replace('T',' ').replace('z',''), '%Y-%m-%d %H:%M:%S')
								except:
									# Doesn't parse "24:00:00" but it's the day after and is always be forecast
									datestring = datetime.strptime(dataSet['dateTime'][0:10],'%Y-%m-%d')+timedelta(days=1)

							# Format the date/time how we want to store it in the CSV
							datestring = datestring.strftime('%Y-%m-%d %H:%M:%S')
							forecast = dataSet['isForecastData']
							kwh = dataSet['netPowerOutputKwh']
							savings = dataSet['savingsForPeriod']
							# Convert boolean forecast into '1'/'0' string for CSV
							if forecast:
								forecast = '1'
								# Save forecast data separately
								# Do we already have an entry for this day/hour?
								if datestring in hourlyforecaststats.keys():
									# Is the forecast data different vs the CSV data?
									if hourlyforecaststats[datestring] != [ datestring, str(kwh), str(savings) ]:
										if verbose & 1: print(" Hourly forecast data changed", hourlyforecaststats[datestring], "to", [ datestring, str(kwh), str(savings) ] )
										hourlyforecastchanged = True
								else:
									# No old data for this entry so it's new
									if verbose & 2: print(" Hourly forecast data ", [ datestring, str(kwh), str(savings) ] )
									hourlyforecastchanged = True

								if hourlyforecastchanged:
									hourlyforecaststats[datestring] = [ datestring, str(kwh), str(savings) ]
							else:
								forecast = '0'

							# Do we already have an entry for this day/hour?
							if datestring in hourlystats.keys():
								# Is the forecast/actual data different vs the CSV data?
								if hourlystats[datestring] != [ datestring, str(kwh), str(savings), forecast ]:
									if verbose & 1: print(" Hourly data changed", hourlystats[datestring], "to", [ datestring, str(kwh), str(savings), forecast ] )
									hourlychanged = True
							else:
								# No old data for this entry so it's new
								if verbose & 2: print(" Hourly data ", [ datestring, str(kwh), str(savings), forecast ] )
								hourlychanged = True

							if hourlychanged:
								hourlystats[datestring] = [ datestring, str(kwh), str(savings), forecast ]
								
					if generationData['title'] == "LAST_30_DAYS":
						for dataSet in generationData['dataSet']:
							datestring = datetime.strptime(dataSet['dateTime'], '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d')
							forecast = dataSet['isForecastData']
							kwh = dataSet['netPowerOutputKwh']
							savings = dataSet['savingsForPeriod']

							# Do we already have an entry for this day?
							if datestring in dailystats.keys():
								# Is the new data different vs the CSV data?
								if dailystats[datestring] != [ datestring, str(kwh), str(savings) ]:
									if verbose & 1: print(" Daily data changed", dailystats[datestring], "to", [ datestring, str(kwh), str(savings) ] )
									dailychanged = True
							else:
								if verbose & 2: print(" Daily data", [ datestring, str(kwh), str(savings) ] )
								dailychanged = True

							if dailychanged:
								dailystats[datestring] = [ datestring, kwh, savings ]

					# We don't do anything with "LAST_7_DAYS" as it's already covered by "LAST_30_DAYS"

				# If we're making backups make sure the directory exists
				if createbackup:
					if not os.path.exists('bak'):
						os.makedirs('bak')

				# Backup and write stats back to CSV files if there was a change
				if forecastchanged:
					if createbackup and os.path.isfile(forecastcsvfilename):
						shutil.copyfile(forecastcsvfilename, forecastcsvfilenamebak)
					with open(forecastcsvfilename, 'w') as f:
						writer = csv.writer(f)
						for k,entry in sorted(forecaststats.items()):
							writer.writerow(entry)
				if hourlychanged:
					if createbackup and os.path.isfile(hourlycsvfilename):
						shutil.copyfile(hourlycsvfilename, hourlycsvfilenamebak)
					with open(hourlycsvfilename, 'w') as f:
						writer = csv.writer(f)
						for k,entry in sorted(hourlystats.items()):
							writer.writerow(entry)

				if hourlyforecastchanged:
					if createbackup and os.path.isfile(hourlyforecastcsvfilename):
						shutil.copyfile(hourlyforecastcsvfilename, hourlyforecastcsvfilenamebak)
					with open(hourlyforecastcsvfilename, 'w') as f:
						writer = csv.writer(f)
						for k,entry in sorted(hourlyforecaststats.items()):
							writer.writerow(entry)

				if dailychanged:
					if createbackup and os.path.isfile(dailycsvfilename):
						shutil.copyfile(dailycsvfilename, dailycsvfilenamebak)
					with open(dailycsvfilename, 'w') as f:
						writer = csv.writer(f)
						for k,entry in sorted(dailystats.items()):
							writer.writerow(entry)

				if verbose > 0: print("Done.")
			else:
				if verbose > 0: print("Skipping "+name+" (Status:"+status+")")

if __name__ == '__main__':
	main()
