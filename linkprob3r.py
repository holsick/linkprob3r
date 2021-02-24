#!/usr/bin/python3
# ToDo: 
## output files and output file format -- fix this
## create cewl style wordlist from found items
## implement authentication option

import re
import sys
import string
import requests
from art import *
from time import sleep
from colorama import Fore, Style
from optparse import OptionParser as op
from bs4 import BeautifulSoup as bs
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# command line args and options
parser = op()
parser.add_option('-u', '--url', type='string', dest='url', help='target url')
parser.add_option('-r', '--recursive', action='store_true', dest='recursive', default=False, help='recursively find forms and their info on found links')
parser.add_option('-j', '--javascript', action='store_true', dest='javascript', default=False, help='include javascript files in output')
parser.add_option('-o', '--outfile', type='string', dest='outfile', help='file to save results to')
parser.add_option('-w', '--wordlist', action='store_true', dest='wordlist', help='create a custom wordlist based on parsing the HTML of the found links')
(options, args) = parser.parse_args()

if not options.url:
	print(f'\n\t{Style.BRIGHT}[{Fore.YELLOW}!{Fore.WHITE}] Please provide a target. Use -h or --help for usage\n')
	sys.exit()

# just print some pretty colors
def header(url):
	print(Fore.BLUE + Style.BRIGHT + '')
	tprint('Holsick\'s Link Prob3r ---->', font='small')
	print(f'>>> Author: {Fore.GREEN}@holsick{Fore.WHITE}')
	print(f'{Fore.BLUE}>>> Version: {Fore.GREEN}1.0{Fore.WHITE}')
	print(f'{Fore.BLUE}>>> Quick and dirty way to find some information about your target website!')
	print(Fore.WHITE + Style.BRIGHT + '')
	print(f'[{Fore.YELLOW}*{Fore.WHITE}] Target: {Fore.BLUE}{url}\n')
	print(f'{Fore.WHITE}[{Fore.YELLOW}*{Fore.WHITE}] Finding Links...\n')

# grab all links on the target
def getLinks(url):
	targetPage = requests.get(url)
	targetContent = targetPage.content
	soup = bs(targetContent, 'html.parser')
	links = []
	for link in soup.findAll('a', attrs={'href' : re.compile('^https://')}):
		links.append(link.get('href'))
	links = list(dict.fromkeys(links))
	return links

def displayFound(foundList):
	for found in foundList:
		print(f'\t[{Fore.GREEN}+{Fore.WHITE}] {found}')

# detects if link is a subdomain of the target (dealing with lots of lists)
def getSubdomains(lst):
	print(f'\n[{Fore.YELLOW}*{Fore.WHITE}] Subdomains Found\n')
	subdomains = []
	filteredList = []
	for found in lst:
		if mainDomain in found:
			subdomains.append(found)
	for subdomain in subdomains:
		try:
			subdomain = subdomain.partition(mainDomain)[0]
			filtered = re.search(r'https://(.*?)\.', subdomain).group(1)
			filteredList.append(filtered)
		except:
			pass
	filteredList = list(dict.fromkeys(filteredList))
	if len(filteredList) >= 1:
		for subs in filteredList:
			print(f'\t[{Fore.GREEN}+{Fore.WHITE}] https://{subs}.{mainDomain}')
	else:
		print(f'\t[{Fore.RED}-{Fore.WHITE}] None Found')
	return filteredList

# detects if link is not related to the target
def getExternalDomains(lst):
	print(f'\n[{Fore.YELLOW}*{Fore.WHITE}] External Domains\n')
	externals = []
	for found in lst:
		if mainDomain not in found:
			externals.append(found)
	if len(externals) >= 1:
		for ext in externals:
			print(f'\t[{Fore.GREEN}+{Fore.WHITE}] {ext}')
	else:
		print(f'\t[{Fore.RED}-{Fore.WHITE}] None Found')
	return externals

# This could be cleaner, but its ok for now
# This function will make the bulk of the requests
# recursively follow each found link and detect available forms (within target scope)
def recursiveFind(lst):
	print(f'\n[{Fore.YELLOW}*{Fore.WHITE}] Links with Forms\n')
	for link in lst:
		if mainDomain in link:
			recurse = requests.get(link, allow_redirects=False)
			if recurse.status_code == 200:
				page = recurse.content.decode('latin-1')
				soup = bs(page, 'html.parser')
				forms = soup.find_all('form')
				if forms is not None:
					if len(forms) > 0:
						print(f'\t[{Fore.BLUE}form{Fore.WHITE}] {Fore.GREEN}{link}{Fore.WHITE}')
						for i, form in enumerate(forms, start=1):
							try:
								formDetails = getFormDetails(form)
								print('\t' + f'{Fore.BLUE}=' * 60 + Fore.WHITE, f'form #{i}', f'{Fore.BLUE}=' * 60 + Fore.WHITE)
								print(f'\t{Fore.BLUE}Action:{Fore.WHITE} {formDetails["action"]}')
								print(f'\t{Fore.BLUE}Method:{Fore.WHITE} {formDetails["method"]}')
								for _input in formDetails['inputs']:
									print(f'\t{Fore.BLUE}Inputs:{Fore.WHITE} {_input}')
							except:
								pass
							print('\n')
				else:
					print(f'\t[{Fore.RED}!{Fore.WHITE}] None Found')
					return
			statusCodes = [
				301, 302, 401, 403
			]
			if recurse.status_code in statusCodes:
				print(f'\t[{Fore.RED}!{Fore.WHITE}] WARNING: {link} either redirected to another page, or requires authentication\n')

# extract the contents of each form
def getFormDetails(form):
	global method
	global action # Extremely lazy way to fix UnboundLocalError
	details = {}
	try:
		if form.attrs.get('action') is not None:
			action = form.attrs.get('action').lower()
		else:
			action = form.attrs.get('action')
		if form.attrs.get('action') is not None:
			method = form.attrs.get('method').lower()
		else:
			method = form.attrs.get('method')
	except AttributeError:
		pass
	inputs = []
	for inputTag in form.find_all('input'):
		inputType = inputTag.attrs.get('type', 'text')
		inputName = inputTag.attrs.get('name')
		inputValue = inputTag.attrs.get('value', '')
		inputs.append({
			'type' : inputType,
			'name' : inputName,
			'value' : inputValue
		})
	details['action'] = action
	details['method'] = method
	details['inputs'] = inputs
	return details

# get all the linked javascript files
def getJSFiles(lst):
	jsFile = []
	print(f'\n[{Fore.YELLOW}*{Fore.WHITE}] JavaScript Files\n')
	for _link in lst:
		if mainDomain in _link:
			jsReq = requests.get(_link, allow_redirects=False)
			if jsReq.status_code == 200:
				jsContent = jsReq.content.decode('latin-1')
				soup = bs(jsContent, 'html.parser')
				jsFile = [i.get('src') for i in soup.find_all('script') if i.get('src')]
	if len(jsFile) >= 1:
		for js in jsFile:
			print(f'\t[{Fore.GREEN}+{Fore.WHITE}] {js}')
		print('\n')
	else:
		print(f'\t[{Fore.RED}-{Fore.WHITE}] None Found\n')
	return jsFile

def fileOutput(filename):
	with open(filename, 'w+') as f:
		f.write('Target: ' + options.url + '\n\n')
		f.write('Links\n--------------------\n')
		for item in linkList:
			f.write(item + '\n')
		if options.javascript:
			f.write('\nLinked Javascript Files\n--------------------\n')
			for _js in getJSFiles(linkList):
				f.write(_js + '\n')
	print(f'\n[{Fore.GREEN}+{Fore.WHITE}] Output written to {options.outfile}')
	return

def cewl(targetUrl):
	wordlist = []
	badchars = list(string.punctuation)
	badchars.remove('/')
	request = requests.get(
		targetUrl,
		allow_redirects=False,
		verify=False
	)
	if request.status_code == 200 and len(request.text) != 0:
		result = stripTags(request.text)
		words = result.split()
		for word in words:
			if not word[0] == [i for i in badchars]:
				wordlist.append(word)
	for _word in wordlist:
		if _word[0] in badchars or _word[-1] in badchars:
			wordlist.remove(_word)
		else:
			print(_word)
	

def stripTags(htmlContent):
	htmlContent = str(htmlContent)
	start = htmlContent.find('<p>')
	end = htmlContent.rfind('<br />')
	htmlContent = htmlContent[start:end]
	inside = 0
	text = ''
	for char in htmlContent:
		if char == '<':
			inside = 1
		elif (inside == 1 and char == '>'):
			inside = 0
		elif inside == 1:
			continue
		else:
			text += char
	return text


# request 1: check if the target site is up or if it exists
try:
	check = requests.get(options.url, timeout=3.0)
	if check.status_code == 200:
		print(f'[{Fore.GREEN}!{Fore.WHITE}] INFO: Connected to target website')
except requests.exceptions.ConnectionError:
	print(f'[{Fore.RED}!{Fore.WHITE}] WARNING: Could not connect to target website')
	sys.exit()

# request 2
# Process the return value of getLinks to avoid making too many unneeded requests
linkList = []
for link in getLinks(options.url):
	linkList.append(link)

if len(options.url.split('.')) >= 3:
	mainDomain = options.url.split('.')[-2] + '.' + options.url.split('.')[-1]
else:
	mainDomain = options.url.split('.')[0].strip('https://') + '.' + options.url.split('.')[1]

def main():
	header(options.url)
	if len(linkList) >= 1:
		displayFound(linkList)
		getSubdomains(linkList)
		getExternalDomains(linkList)
	else:
		print(f'\t[{Fore.RED}!{Fore.WHITE}] None Found\n')
		sys.exit()
	if options.recursive:
		recursiveFind(linkList)
	if options.javascript:
		getJSFiles(linkList)
	if options.outfile:
		fileOutput(options.outfile)
	if options.wordlist:
		cewl(options.url)

if __name__ == '__main__':
	main()