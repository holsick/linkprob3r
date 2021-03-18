#!/usr/bin/python3

import re
import sys
import requests
from art import *
from colorama import Fore, Style
from optparse import OptionParser as op
from bs4 import BeautifulSoup as bs
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

class Prober:

    bright = Style.BRIGHT
    blue = Fore.BLUE
    green = Fore.GREEN
    yellow = Fore.YELLOW
    red = Fore.RED
    white = Fore.WHITE

    # Main list of found links
    links = []

    # List of subdomains after parsing
    subdomains = []

    # List of external domains after parsing
    externals = []

    # Default headers
    defaultHeaders = { 
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36' 
    }

    def __init__(self, url, headers=defaultHeaders):

        '''
        Initialize the start of the program with colors and the main header
        '''

        self.url = url
        self.headers = headers
        print(self.bright + self.blue + '')
        tprint('Holsick\'s Link Prob3r ---->', font='small')
        print(f'>>> Author: {self.green}@holsick{self.white}')
        print(f'{self.blue}>>> Version: {self.green}1.2{self.white}')
        print(f'{self.blue}>>> Quick and dirty way to find some information about your target website!')
        print(self.white + self.bright + '')
        print(f'[{self.yellow}*{self.white}] Target: {self.blue}{self.url}\n')

        if len(self.headers) == 1:
            if list(self.headers.values()) != list(self.defaultHeaders.values()):
                print(f'{self.white}[{self.yellow}*{self.white}] Modified Headers:\n')

                for key, value in self.headers.items():
                    self.defaultHeaders[key] = value

                    print(f'\t{key} : {value}')

        elif len(self.headers) > 1:
            for key, value in self.headers.items():
                self.defaultHeaders[key] = value

            print(f'{self.white}[{self.yellow}*{self.white}] Modified Headers:\n')
            
            for key, value in self.defaultHeaders.items():
                if key != 'User-Agent' or value != self.defaultHeaders['User-Agent']:
                    
                    print(f'\t{key} : {value}')


        print(f'\n{self.white}[{self.yellow}*{self.white}] Finding Links...\n')

    def getLinks(self):

        '''
        Grab all of the links available on the target page
        '''

        targetPage = requests.get(self.url, verify=False, headers=self.defaultHeaders)
        targetContent = targetPage.content
        soup = bs(targetContent, 'html.parser')

        for link in soup.findAll('a', attrs={ 'href': re.compile('^https://') }):
            self.links.append(link.get('href'))

        self.links = list(dict.fromkeys(self.links))
        self.displayFound(self.links)
        return self.links

    def displayFound(self, foundLinks):
        for found in foundLinks:
            print(f'\t[{self.green}+{self.white}] {found}')

    def getSubdomains(self):

        '''
        Detects if the link is a subdomain of the target.

        This basically just parses the list of found links,
        it will find the target domain name and to determine if the link
        is leading to a subdomain.
        '''

        print(f'\n[{self.yellow}*{self.white}] Subdomains found\n')

        for sub in self.links:
            if mainDomain in sub:
                self.subdomains.append(sub)

        filteredSubdomainList = []

        for subdomain in self.subdomains:
            try:
                subdomain = subdomain.partition(mainDomain)[0]
                subdomainFiltered = re.search(r'https://(.*?)\.', subdomain).group(1)
                filteredSubdomainList.append(subdomainFiltered)

            except:
                pass

        filteredSubdomainList = list(dict.fromkeys(filteredSubdomainList))
        
        # Clean the original subdomain list
        self.subdomains = filteredSubdomainList

        if len(self.subdomains) >= 1:
            self.subdomains = [f'https://{sub}.{mainDomain}' for sub in self.subdomains]
            self.displayFound(self.subdomains)
        else:
            print(f'\t[{self.red}-{self.white}] None Found')

        return self.subdomains

    def getExternalDomains(self):

        '''
        This basically does the same thing as getSubdomains(), however
        it will only detect if a link is pointing to some external domain.

        Examples would include a link to youtube, facebook, or twitter
        '''

        print(f'\n[{self.yellow}*{self.white}] External Domains\n')

        for ext in self.links:
            if mainDomain not in ext:
                self.externals.append(ext)

        # No need to filter further here, it's nice to see the full link
        if len(self.externals) >= 1:
            self.displayFound(self.externals)
        else:
            print(f'\t[{self.red}-{self.white}] None Found')

        return self.externals


class DeepInspect(Prober):

    # Extracted form details
    details = {}

    # List of JavaScript files after parsing
    jsFiles = []

    def __init__(self, url):
        self.url = url

    def getFormDetails(self, form):

        '''
        Extract contents from each found form if applicable.

        The output will be in dictionary format and can be enumerated
        using loops to get a clear output and view of the extracted form.

        The underlying functionality returns the HTML details of a form,
        including action, method and list of form controls.

        https://www.thepythoncode.com/code/extracting-and-submitting-web-page-forms-in-python
        '''
        
        action = form.attrs.get('action')
        method = form.attrs.get('method')

        formInputs = []

        for inputTag in form.find_all('input'):
            inputType = inputTag.attrs.get('type', 'text')
            inputName = inputTag.attrs.get('name')
            inputValue = inputTag.attrs.get('value', '')

            formInputs.append({
                'type': inputType,
                'name': inputName,
                'value': inputValue
            })

        self.details['action'] = action
        self.details['method'] = method
        self.details['inputs'] = formInputs

        return self.details

    def recursiveFind(self):

        '''
        This function will make the bulk of the requests.

        If this option is ran, the program will recursively follow each found
        link and detect available forms on each page (within the target scope).

        For each page that it visits, a counter will be started to keep track of
        the amount of forms on each page while displaying their contents in the terminal.
        '''

        print(f'\n[{super().yellow}*{super().white}] Links with Forms\n')

        for link in super().links:
            if mainDomain in link:
                recurse = requests.get(
                    link, 
                    allow_redirects=False, 
                    verify=False,
                    headers=super().defaultHeaders
                )

                if recurse.status_code == 200:
                    page = recurse.content.decode('latin-1')
                    soup = bs(page, 'html.parser')
                    forms = soup.find_all('form')

                    if forms is not None and len(forms) > 0:
                        print(f'\t[{super().blue}form{super().white}] {super().green}{link}{super().white}')
                        for i, form in enumerate(forms, start=1):
                            try:
                                formDetails = self.getFormDetails(form)
                                print('\t' + f'{super().blue}=' * 60 + super().white, f'form #{i}', f'{super().blue}=' * 60 + super().white)
                                print(f'\t{super().blue}Action:{super().white} {formDetails["action"]}')
                                print(f'\t{super().blue}Method:{super().white} {formDetails["method"]}')

                                for _input in formDetails['inputs']:
                                    print(f'\t{super().blue}Inputs:{super().white} {_input}')

                            except:
                                pass

                            print('\n')

                    else:
                        print(f'\t[{super().red}!{super().white}] None Found')
                        return

                statusCodes = [301, 302, 401, 403]

                if recurse.status_code in statusCodes:
                    print(f'\t[{super().red}!{super().white}] WARNING: {link} either redirected to another page, or requires authentication\n')


    def getJSFiles(self):

        '''
        Grab all of the linked JavaScript files on the page

        This is done just by detecting the .js extension in the filename
        '''

        print(f'\n[{super().yellow}*{super().white}] JavaScript Files\n')

        for link in super().links:
            if mainDomain in link:
                jsRequest = requests.get(
                    link, 
                    allow_redirects=False, 
                    verify=False,
                    headers=super().defaultHeaders
                )

                if jsRequest.status_code == 200:
                    jsContent = jsRequest.content.decode('latin-1')
                    soup = bs(jsContent, 'html.parser')
                    self.jsFiles = [i.get('src') for i in soup.find_all('script') if i.get('src')]

        if len(self.jsFiles) >= 1:
            super().displayFound(self.jsFiles)
            print('\n')
            return self.jsFiles
        else:
            print(f'\t[{super().red}-{super().white}] None Found\n')
            return


class FileManager(DeepInspect):

    def __init__(self, url, filename, javascript=[]):
        self.url = url
        self.filename = filename
        self.javascript = javascript

    def fileOutput(self):

        '''
        Write contents to a file for later. It will not
        include HTML form data, and does not include JavaScript files
        by default. JavaScript inclusion should be explicitly specified.
        '''

        with open(self.filename, 'w+') as f:
            f.write('Target: ' + self.url + '\n\n')
            f.write('Links\n-----------------\n')

            for item in super().links:
                f.write(item + '\n')

            if len(self.javascript) > 0:
                f.write('\nLinked JavaScript Files\n-------------------------\n')

                for _js in self.javascript:
                    f.write(_js + '\n')

        print(f'\n[{super().green}+{super().white}] Output written to {self.filename}')
        return

if __name__ == '__main__':

    # parse command line options

    parser = op()

    parser.add_option('-u', '--url', type='string', dest='url', help='target url')
    parser.add_option('-r', '--recursive', action='store_true', dest='recursive', default=False, help='recursively find forms and their info on found links')
    parser.add_option('-j', '--javascript', action='store_true', dest='javascript', default=False, help='include javascript files in the output')
    parser.add_option('-o', '--outfile', type='string', dest='outfile', help='file to save results to')
    parser.add_option('-H', '--headers', type='string', dest='headers', help='Use custom HTTP headers (separated by commas)')

    (options, args) = parser.parse_args()

    if not options.url:
        print(f'\n\t{Style.BRIGHT}[{Fore.YELLOW}!{Fore.WHITE}] Please provide a target. Use -h or --help for usage\n')
        sys.exit()

    try:
        # Request 1: check if the target site is up or if it exists
        check = requests.get(
            options.url,
            timeout=3.0,
            verify=False,
            allow_redirects=True
        )

        if check.status_code == 200:
            print(f'[{Fore.GREEN}!{Fore.WHITE}] INFO: Connected to target website')

    except requests.exceptions.ConnectionError:
        print(f'[{Fore.RED}!{Fore.WHITE}] WARNING: Could not connect to target website')
        sys.exit()

    if len(options.url.split('.')) >= 3:
        mainDomain = options.url.split('.')[-2] + '.' + options.url.split('.')[-1]
    else:
        mainDomain = options.url.split('.')[0].strip('https://') + '.' + options.url.split('.')[1]

    # Begin Program

    # Parse any custom headers
    if options.headers:
        customHeaders = {}
        headersList = options.headers.split(',')

        for header in headersList:
            if 'http' in header or 'https' in header:
                header = header.split(':')
                headerValue = header[1].strip() + ':' + header[2]
                customHeaders[header[0]] = headerValue
            else:
                header = header.split(':')
                customHeaders[header[0]] = header[1].strip()

        linkprobe = Prober(options.url, customHeaders)

    else:
        linkprobe = Prober(options.url)

    linkprobe.getLinks()
    linkprobe.getSubdomains()
    linkprobe.getExternalDomains()

    if options.recursive or options.javascript:
        inspect = DeepInspect(options.url)

        if options.recursive:
            inspect.recursiveFind()

        if options.javascript:
            inspect.getJSFiles()

            if options.outfile:
                outfile = FileManager(options.url, options.outfile, inspect.jsFiles)
                outfile.fileOutput()
    
    if options.outfile and not options.javascript:
        outfile = FileManager(options.url, options.outfile)
        outfile.fileOutput()
