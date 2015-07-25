# -*- coding: utf-8 -*-

''' Place this file in the same directory as your SentiStrengthCom.jar,
    your SentiStrength_Data folder and your CSV files to be analyzed. '''

import time
from time import sleep
import datetime
import glob
import csv
import shlex, subprocess
import re

def scrub_string(input_string):
	''' Force string into ASCII for analysis. '''
	to_scrub = input_string.decode('utf-8', errors='replace')
	clean = to_scrub.encode('ascii', errors='replace')
	return clean

def get_sentiment(sentiString, p, count):
	'''Take text, pass it to SentiStrengthCom.jar, compute sentiment. You can supply a pre-existing subprocess (p) e. g. if you want to use a nonstandard configuration. Note that it is strongly recommended to supply p even if you want to use the default configuration, as it makes very little sense to constantly close and re-open subprocesses. This function is partially based on the usage sample provided by Alec Larsen, University of the Witwatersrand, South Africa, 2012 (it's in the SentiStrength manual).'''
	#If no process is supplied, open a subprocess using shlex to get the command line string into the correct args list format. Note that supplying 

	#print "Computing..."
	#Communicate, via stdin, the string to be rated. Note that all spaces are replaced with +.
	sentiString = sentiString.replace(" ","+").replace("\n","+").replace("\t","+").replace("\r","+")
	#print "Sending..."
	p.stdin.write(sentiString)
	#print "Sending..."
	p.stdin.write("\n")
	#stdout_text = p.communicate(sentiString+"\n")[0]
	#p.stdin.write("\n")
	
	#print "Reading..."
	#Read, via stdout, the results of the compotation. Remove linebreaks and quotes to make later analysis easier.
	stdout_text = p.stdout.readline()

	p.stdout.flush()

	#print stdout_text
	stdout_text = stdout_text.replace('"', '^')
	stdout_text = stdout_text.replace("\n", "")

	#As the results of the computation are tab-delimited, the result string needs to be split on \t.
	ret_val = stdout_text.split("\t")

	sleep(0.01)

	#Returns (by default) positive, negative, neutral, explanation
	return ret_val


def main(tweets_file):
	#Set up default parameters for sentiment getting.
	#TODO: Have this input-dependent in some way...
	p = subprocess.Popen(shlex.split("java -jar ./SentiStrengthCom.jar trinary sentenceCombineTot paragraphCombineTot explain stdin sentidata ./SentiStrength_Data/"),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

	#Set up a pattern for (very basic!) URL recognition (see below)
	url_pattern = re.compile("http(s)*:[^\s]+")

	#Check if tweets_file exists, prompt user for input if not

	#Prepare CSV boilerplate. Change this if your CSV setup does.
	csv.register_dialect('excel-two', delimiter=";", doublequote=True, escapechar=None, lineterminator="\r\n", quotechar='"', quoting=csv.QUOTE_MINIMAL,skipinitialspace=True)
	#csv_headers = ["Tweet", "Date", "Hour", "Polarity_Pos", "Polarity_Neg", "Polarity_Neu", "Explanation"]
	
	
	input_headers= ["URL", "GNewsDate", "Pub_Date", "News_Source", "Headline", "Fulltext"]
	csv_headers = ["News_Source", "Fulltext", "GNewsDate", "Polarity_Pos", "Polarity_Neg", "Polarity_Neu", "Explanation"]
	
	
	
	#Find a list of CSV files in the specified path...
	list_files = glob.glob('gn_*.csv')

	#For each file
	for lf in list_files:
		with open(lf, 'rb') as input_file:
			print "Now considering {0}".format(lf)
			#Set up output file: Open and write headers
			output_name = 'sents_{0}'.format(input_file.name)
			with open(output_name, 'ab') as output_file:
				output_writer = csv.writer(output_file, dialect='excel-two')
				output_writer.writerow(csv_headers)

				#Step through CSV file line by line
				rowcount = 0
				input_reader = csv.reader(input_file, dialect='excel-two')
				for current_row in input_reader:
					try:
						if ((current_row[0] != input_headers[0]) and (len(current_row)==len(input_headers))): #Skip the row with the CSV file headers, skip malformed rows
							#Do process shenanigans
							if ((rowcount % 100 ==0) or (p is None)):	
								if p is not None:
									p.communicate(None)
									#print "New process..."
									sleep(0.1)
								p = subprocess.Popen(shlex.split("java -jar SentiStrengthCom.jar trinary sentenceCombineTot paragraphCombineTot explain stdin sentidata ./SentiStrength_Data/"),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE, bufsize=1)

							#Some data can just be copied
							news_date = current_row[1]
							news_src  = current_row[3]
								
								
							#print "Doing",current_row
							#Force Tweet into ASCII and remove URLs (those confuse SentiStrength)
							article_text = scrub_string(current_row[4]) + " " + scrub_string(current_row[5])

							#Strip URLs - those confuse SentiStrength as they contain dots, which are interpreted as sentence ends						
							article_text = re.sub(url_pattern, "<URL>", article_text)

							#Compute polarities of Text. Pad list if needed.
							cur_polarities = ["","","",""]
							cur_polarities = get_sentiment(article_text, p, rowcount)
							cur_polarities += [''] * (4 - len(cur_polarities))

							#The data has now been assembled and can be saved.
							output_writer.writerow([news_src, article_text, news_date,  cur_polarities[0], cur_polarities[1], cur_polarities[2], cur_polarities[3].replace('\n', '').replace("\n", " ").replace("\r", " ")])
				
							#Occasionally let user know we're still live
							rowcount += 1
							if (rowcount % 100 == 0): print "Rows processed: {0}".format(rowcount);
						else:
							print "Row skipped: ",current_row
					except Exception as e:
							print e
							print "Row skipped: ",current_row
	
	#We're done!
	print "Analysis complete."


if __name__ == '__main__':
	#TODO: Input path about here
	main("./")
