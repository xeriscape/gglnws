import gn_scraper
from gn_scraper import execute_search
import glob, os
import datetime
#------------------------------------------------------------------------------
# Do a search for the week BEFORE a starting date. This is a bad solution to a 
# problem I should've foreseen - four days isn't nearly enough! - but I specialise
# in those, so here we are.

def get_days_in_range(start_date, end_date):
	start = datetime.datetime.strptime(start_date.strip(), "%Y-%m-%d")
	end = datetime.datetime.strptime(end_date.strip(), "%Y-%m-%d")
	step = datetime.timedelta(days=1)
	days = []

	while start <= end:
		days.append( datetime.datetime.strftime(start.date(), "%Y-%m-%d")  )
		start += step

	return days
	
	

def main():
	for search_file in glob.glob("*.srch"):
		try:
			#Assemble query
			f = open(search_file, "rb")
			x = f.readlines()
			query = str(x[0])
			query = query.replace("\n","").replace("\r","")
			
			#Enable the tool to use the same search files as Twtscrp. Make the neccessary adjustments (no lang parameter, no -)
			query_items = query.split(" ")
			reassembled_query = []
			for item in query_items:
				if ((item[0] != "-") and (item != "lang:en")):
					reassembled_query.append(item)
					
			new_query = " ".join(reassembled_query)
		
			#Find out dates
			since = str(x[1]).replace("\n","").replace("\r","")
			until = str(x[2]).replace("\n","").replace("\r","")
			
			since_to_date = datetime.datetime.strptime(since, "%Y-%m-%d")
			since_to_date = since_to_date - datetime.timedelta(days=7)
			
			new_since = since_to_date.strftime("%Y-%m-%d")
			
			appendix = f.name
			appendix = appendix.replace(".srch","")
			name = "gn_neg_"+appendix
		
			#Since Google limits searches to 1,000 results, long searches must be split.
			days = get_days_in_range(new_since, since)
			print(days)
			
			if (len(days) >= 10): #Don't bother splitting for very short searches
				print("Executing search {0} from {1} to {2}".format(new_query, days[0], days[len(days)//3]) )
				gn_scraper.execute_search(new_query, days[0], days[len(days)//3], name)
				print("Executing search {0} from {1} to {2}".format(new_query, days[len(days)//3 + 1], days[(len(days)//3)*2]) )
				gn_scraper.execute_search(new_query, days[len(days)//3 + 1], days[(len(days)//3)*2], name)
				print("Executing search {0} from {1} to {2}".format(new_query, days[(len(days)//3)*2+1], days[len(days)-1]))
				gn_scraper.execute_search(new_query, days[(len(days)//3)*2+1], days[len(days)-1], name)
			else:
				print("Executing search {0} from {1} to {2} (unsplit)".format(new_query, days[0], days[len(days)-1]))
				gn_scraper.execute_search(new_query, days[0], days[len(days)-1], name)
			
			#
			
		except (KeyboardInterrupt, SystemExit):
			print "Process aborted."
			raise
			
		except:
			print "Error at ", x

#------------------------------------------------------------------------------
if __name__ == "__main__":
	''' The usual boilerplate... '''
	main()