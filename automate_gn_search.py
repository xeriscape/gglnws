import gn_scraper
from gn_scraper import main
import glob, os, datetime
#------------------------------------------------------------------------------
def get_days_in_range(start_date, end_date):
	start = datetime.datetime.strptime(start_date.strip(), "%Y-%m-%d")
	end = datetime.datetime.strptime(end_date.strip(), "%Y-%m-%d")
	step = datetime.timedelta(days=1)
	days = []

	while start <= end:
		days.append( datetime.datetime.strftime(start.date(), "%Y-%m-%d")  )
		start += step

	return days
#------------------------------------------------------------------------------
def main():
	for search_file in glob.glob("*.srch"):
		try:
			#Assemble query
			x = open(search_file, "r").readlines()
			query = str(x[0])
			query = query.replace("\n","").replace("\r","")
			
			query_items = query.split(" ")
			reassembled_query = []
			for item in query_items:
				if ((item[0] != "-") and (item != "lang:en")):
					reassembled_query.append(item)
					
			new_query = " ".join(reassembled_query)
		
			#Find out dates
			since = str(x[1]).replace("\n","").replace("\r","")
			until = str(x[2]).replace("\n","").replace("\r","")
			
			#Split search in half
			days = get_days_in_range(since, until)
			
			#search_string, access_url, username, password, starting_page
			#def main(query, start_date, end_date):
			if (len(days) >= 5): #Don't bother splitting for very short searches
				print("Executing search {0} from {1} to {2}".format(new_query, days[0], days[len(days)//3]) )
				gn_scraper.main(new_query, days[0], days[len(days)//3])
				print("Executing search {0} from {1} to {2}".format(new_query, days[len(days)//3 + 1], days[(len(days)//3)*2]) )
				gn_scraper.main(new_query, days[len(days)//3 + 1], days[(len(days)//3)*2])
				print("Executing search {0} from {1} to {2}".format(new_query, days[(len(days)//3)*2+1], days[len(days)-1]))
				gn_scraper.main(new_query, days[(len(days)//3)*2+1], days[len(days)-1])
			else:
				print("Executing search {0} from {1} to {2} (unsplit)".format(new_query, days[0], days[len(days)-1]))
				gn_scraper.main(new_query, days[0], days[len(days)-1])
			
		except (KeyboardInterrupt, SystemExit):
			print("Process aborted.")
			raise
			
		except Exception as e:
			#print(e)
			raise

#------------------------------------------------------------------------------
if __name__ == "__main__":
	''' The usual boilerplate... '''
	main()
