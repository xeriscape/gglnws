import glob, os, csv, sys
import time
import datetime
import glob
import re
import locale

def main():
	#Prepwork
	csv.field_size_limit(sys.maxsize)
	csv_headers = ["News_Source", "Fulltext", "GNewsDate", "Polarity_Pos", "Polarity_Neg", "Polarity_Neu", "Explanation"]
	csv.register_dialect('excel-two', delimiter=";", doublequote=True, escapechar=None, lineterminator="\r\n", quotechar='"', quoting=csv.QUOTE_MINIMAL,skipinitialspace=True)

	for search_file in glob.glob("*.srch"):
		#Identify number
		f = open(search_file)
		number = "sents_*{0}*.csv".format(re.findall(r'\d+', f.name)[0])
		
		#Get search terms
		x = f.readlines()
		query = str(x[0])
		query = query.replace("\n","").replace("\r","").replace('"',"")
			
		#Enable the tool to use the same search files as Twtscrp. Make the neccessary adjustments (no lang parameter, no -)
		query_items = query.split(" ")
		reassembled_query = []
		for item in query_items:
			if ((item[0] != "-") and (item != "lang:en")):
				reassembled_query.append(item.lower())
		
		
		#Identify file belonging to search file
		for items_file in glob.glob(number):
			print(items_file)
		
			f2 = open(items_file)
			
			#Prepare output facilities
			output_name = "clean_{0}".format(f2.name)
			output_file = open(output_name, 'ab')
			output_writer = csv.writer(output_file, dialect='excel-two')
			output_writer.writerow(csv_headers)
			
			#Step through CSV file line by line
			input_file = open(items_file)
			input_reader = csv.reader(input_file, dialect='excel-two')
			for current_row in input_reader:
				do_write = 0
				#Only write if the search terms appears in the result fulltext
				#print(current_row[1])
				
				for search_term in reassembled_query:
					try:
						if (search_term in current_row[1].lower()):
							do_write = 1
							
					except:
						print(".")
						
				if (do_write > 0):
					#Unmangle date. Format: Apr 7, 2013
					locale.setlocale(locale.LC_ALL, 'en_US')

					xyz = current_row[2]
					xyz = xyz.replace(",","")
					xyz = xyz.split(" ")
					if len(xyz[1]) < 2: #Zero-pad day of month
						xyz[1] = "0{0}".format(xyz[1])
					xyz = " ".join(xyz)
					
					to_date = datetime.datetime.strptime(xyz, "%b %d %Y") #Read in
					output = to_date.strftime("%Y-%m-%d")
				
					current_row[2] = output
				
					output_writer.writerow(current_row)
					
				
	

#------------------------------------------------------------------------------
if __name__ == "__main__":
	''' The usual boilerplate... '''
	main()