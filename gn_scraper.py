import urllib
from lxml import html
import lxml
import requests
import os
import time
import copy
import sqlite3
import re
import datetime
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
import langdetect
from newspaper import Article
import csv
import sys
import uuid


#TODO: The split-by-day feature seems more trouble than it's worth...
#-----------------------------------------------------------------------
def set_up_browser(chromedriver): 
	os.environ["webdriver.chrome.driver"] = chromedriver
	opt = webdriver.ChromeOptions()
	driver = webdriver.Chrome(chromedriver, chrome_options=opt)
	
	return driver
#-----------------------------------------------------------------------
def get_search_chunk(driven_browser, url):
	#XPath queries for later
	article_information = "//div[@id='ires']//text()"; article_bodies = "//div[@class='st']//text()"; article_links = "//div[@id='ires']//a/@href"
	article_datetimes = "//span[@class='f nsa _uQb']/text()"

	#Preparation for later: (Re)Set temporary variables and such
	r = None; tree = None; 
	current_links = None; element = None; 

	#Retrieve page, keep trying until it works
	success = False
	next_page = ""

	while (not success):
		try:
			if ("&start=0" in url):
				driven_browser.get( url )
			else:
				if (next_page == ""):
					tree = html.fromstring(driven_browser.page_source)
					next_page = tree.xpath("//a[@id='pnnext']/@href")
				if (len(next_page) >= 1):
					print("https://www.google.de{0}".format(next_page[0]) )
					driven_browser.get("https://www.google.de{0}".format(next_page[0]) ) 

			time.sleep(2)
			success = True
			#It's likely we'll eventually hit Google's anti-spam protection. This requires user action.
			if "To continue, please type the characters below:" in driven_browser.page_source:
				input("\n\nWe triggered Google's antispeam measures. Please switch to the Chrome window, enter the Captcha, select 'Sort by Date', then press Enter to continue...\n")
				time.sleep(30)
			if "did not match any news results" in driven_browser.page_source:
				return [[],[]]
			element = WebDriverWait(driven_browser, 15).until(EC.presence_of_element_located((By.ID, "ires")))
			time.sleep(4)
		except (KeyboardInterrupt, SystemExit): raise;
		except Exception as e:
			print(e)
			#raise
			success = False
			time.sleep(3)
				
	#Put into tree form for querying
	tree = html.fromstring(driven_browser.page_source)

	#Locate various bits of information
	current_links = tree.xpath(article_links)
	current_dates = tree.xpath(article_datetimes)


	return [current_links, current_dates]
#-----------------------------------------------------------------------
def main(query, start_date, end_date):
	'''Assemble the initial set of search pages'''
	query_urls = []; article_urls = []; article_datetimes = [];

	'''Set up browser'''
	driver = set_up_browser("./chromedriver/chromedriver")

	#Set up the base search string, with dates and query to be filled in
	base_search_url = "https://www.google.com/search?cf=all&ned=us&hl=en&tbm=nws&as_q={0}&as_occt=title&as_drrb=b&as_mindate={1}&as_maxdate={2}&tbs=cdr:1,cd_min:{3},cd_max:{4}&authuser=0&gws_rd=ssl#q=allintitle:{0}&hl=en&gl=us&as_drrb=b&authuser=0&tbs=cdr:1,cd_min:{3},cd_max:{4},sbd:1&tbm=nws"

	#Mangle YYYY-MM-DD into MM-DD-YYYY dates
	start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date(); q_start = datetime.datetime.strftime(start, "%m/%d/%Y")
	end   = datetime.datetime.strptime(end_date, "%Y-%m-%d").date(); q_end = datetime.datetime.strftime(end, "%m/%d/%Y")

	#Prepare query URLs
	query_urls.append(base_search_url.format(query, q_start, q_end, q_start, q_end)) #In this version there's just one, this is a historical artefact

	#Prepare output facilities
	search_id = str(uuid.uuid4())
	file_name = "gn_"+search_id+".csv"
	meta_name = "gn_"+search_id+".meta"

	csv.register_dialect('excel-two', delimiter=';', doublequote=True, escapechar=None, lineterminator="\r\n", quotechar='"', quoting=csv.QUOTE_MINIMAL, skipinitialspace=True)
	csv_headers= ["URL", "GNewsDate", "Pub_Date", "News_Source", "Headline", "Fulltext"]
	csv_file = open(file_name, "w", newline="")
	csv_writer = csv.writer(csv_file, dialect='excel-two')
	csv_writer.writerow(csv_headers)
	meta_file = open(meta_name, "ab")

	curtime = str(datetime.datetime.now())
	meta_file.write(bytes(curtime+"\n"+query+"\n"+start_date+"\n"+end_date+"\n\n\n", "UTF-8"))

	'''Ok, execute search & loop through results'''
	for query_url in query_urls:
		print(query_url)
		found_new = True; found_new_last_time = True; next_start_point = 0
		
		#Keep going while we can still find new results (and haven't been redirected)
		while (found_new or found_new_last_time):
			#Reset temporary variables (for later)
			found_new_last_time = found_new; i=0;
			found_new = False; previous_result_count = len(article_urls)

			#Get next search chunk
			link_candidates, date_time = get_search_chunk(driver, query_url+"&start={0}".format(next_start_point))

			#See if we can find any new links to add
			while (i < len(link_candidates)):
				link = link_candidates[i]
				link = link.replace("/url?q=", "")
				if link not in article_urls and "news.google.com/news" not in link:
					article_urls.append(link)
					to_append = min(i, len(date_time)-1)
					try:
						article_datetimes.append(date_time[to_append])
					except IndexError:
						try:
							article_datetimes.append( date_time[0] )
						except IndexError:
							article_datetimes.append("???")
					meta_file.write(bytes(link+"\n", "UTF-8"))	
					found_new = True
				i += 1
			#If we didn't, then the search is done

			#Continue to the next page (assuming found_new is true)
			next_start_point += 10
			if (next_start_point >= 1000): 
				meta_file.write(bytes("\n\n!!! More than 1000 results !!!\n\n", "UTF-8"))
				break #For searches that return >1k results, manual splitting is needed

			#Keep the user updated as we find new articles
			print(len(article_urls))
	

	'''Once article URLs are retrieved, it is time to visit the article'''
	i = -1
	print(article_urls)
	for article_url in article_urls:
		date = ""
		i = i + 1
		print("Now looking at #{0}: {1}".format(i, article_url))
		try:
			#Retrieve article
			article = Article(article_url)
			time.sleep(1)
			article.download()
			for rrr in range(0,5):
				if (article.is_downloaded):
					break
				else:
					time.sleep(1)
			time.sleep(1)
			article.parse()

			#Figure out a name for the source
			srcname = article_url.replace("http://", "").replace("https://", "").split("/")[0]
		
			#Pull article information
			news_src = (srcname)
			date = (article.publish_date) 
			
			#Figure out some stuff about the URL
			if (langdetect.detect(article.text) != "en"):
				csv_writer.writerow([article_datetimes[i], date, news_src, "NON-ENGLISH", "NON-ENGLISH"])
				meta_file.write(bytes("{0} non-English\n".format(article_url), "UTF-8"))
				print(" ^ Not English\n")
				
			elif (len(article.text) > 5 ): #We only process English-language articles that actually have content in them)
				headline = (article.title.replace("\n", "  ").replace("\r", "  ").replace(";",","))
				fulltext = (article.text.replace("\n", "  ").replace("\r", "  ").replace(";",","))

				#Write to file
				csv_writer.writerow([article_url, article_datetimes[i], date, news_src, headline, fulltext])
				
				#Update .meta
				meta_file.write(bytes("{0} retrieved OK\n".format(article_url), "UTF-8"))
				print(" ^ Retrieved OK\n")
				
			else:
				meta_file.write(bytes("{0} skipped: Too short?\n".format(article_url), "UTF-8"))
				print(" ^  skipped: Too short?\n")
				csv_writer.writerow([article_url, article_datetimes[min(i, len(article_datetimes)-1)], date, news_src, "ERR", "ERR"])

		except Exception as e:
			print(" ^ Error: {0}".format(e))
			print(e)
			#raise
			meta_file.write(bytes("Error retrieving {0}: {1}\n\n".format(article_url, e), "UTF-8"))
			csv_writer.writerow([article_url, article_datetimes[i], "ERR", "ERR", "ERR", "ERR"])
		
	#Build a local database of links and articles
	#while (len(search_pages) > 0):
		#Pop the next search_page
		

		#Locate various bits of information on the page via XPATH

		#Append the next page of the search results to search_pages




if __name__ == '__main__':
	main("sony", "2011-04-23", "2011-04-25")
