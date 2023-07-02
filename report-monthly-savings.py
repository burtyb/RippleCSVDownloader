#!/usr/bin/python3
# Outputs table of savings by month (including todays hourly data)

from datetime import datetime,timedelta
from pprint import pprint

import json
import requests
import csv
import os.path
import shutil
import time

import config

# Adjustment to add/subtract from data in csv (i.e. for periods before using using the scripts)
monthdata = { # Amounts are in pence!
#	'202203':1234,
#	'202204':123,
}

def main():

	total = 0

	csvfileprefix = getattr(config, 'csvfileprefix', 'RippleEnergy-')

	dailycsvfilename = csvfileprefix+'Graig_Fatha-daily.csv'
	hourlycsvfilename = csvfileprefix+'Graig_Fatha-hourly.csv'

	dailystats = {}
	lastday = ""

	if os.path.isfile(dailycsvfilename):
		with open(dailycsvfilename, mode='r') as csv_file:
			csv_reader = csv.reader(csv_file)
			for row in csv_reader:
				dailystats[row[0]] = row
				lastday = row[0]

	nextday = str(datetime.strptime(lastday, "%Y-%m-%d") + timedelta(days=1))[0:10]

	partialday = 0
	if os.path.isfile(hourlycsvfilename):
		with open(hourlycsvfilename, mode='r') as csv_file:
			csv_reader = csv.reader(csv_file)
			for row in csv_reader:
				if (str(row[0])[0:10] == nextday) and (row[3] == "0"):
					partialday = partialday + float(row[2])
	nextym = nextday[0:4]+nextday[5:7]

	for data in dailystats:
		ym = data[0:4]+data[5:7]
		if ym in monthdata:
			tmp = float(monthdata[ym])+float(dailystats[data][2])
			monthdata.update( {ym:tmp} )
		else:
			monthdata.update( {ym:float(dailystats[data][2])} )

	print("Monthly Savings")
	for k in sorted(monthdata):
		if partialday != 0 and nextym == k:
			print("{} {:.2f} ({:.2f}+{:.2f})".format(str(k)[0:4]+'-'+str(k)[4:6],((monthdata[k]+partialday)/100), monthdata[k]/100, partialday/100 ))
			total = total + round((monthdata[k]+partialday)/100,2)
			partialday = 0
		else:
			print("{} {:.2f}".format(str(k)[0:4]+'-'+str(k)[4:6],(monthdata[k]/100) ))
			total = total + round(monthdata[k]/100,2)

	# First day of month so we only have partial day data
	if partialday != 0:
		print("{} {:.2f} (0+{:.2f})".format(nextday[0:7],partialday/100,partialday/100) )
		total = total + round(partialday/100,2)

	print("Total   {:.2f}".format(total) )

if __name__ == '__main__':
        main()


