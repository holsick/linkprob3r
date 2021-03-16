# linkprob3r
A quick and dirty way to gather some information about your target website

## Installation
```bash
git clone https://github.com/holsick/linkprob3r.git
cd linkprob3r
pip3 install -r requirements.txt
```

## Basic Usage
```bash
python3 linkprob3r.py --help

Usage: linkprob3r.py [options]

Options:
  -h, --help            show this help message and exit
  -u URL, --url=URL     target url
  -r, --recursive       recursively find forms and their info on found links
  -j, --javascript      include javascript files in output
  -o OUTFILE, --outfile=OUTFILE
                        file to save results to
  -w, --wordlist        create a custom wordlist based on parsing the HTML of
                        the found links
```

## Example Usage
```bash
# Simple Case
python3 linkprob3r.py -u https://example.com

# Include JavaScript file detection
python3 linkprob3r.py -u https://example.com -j

# Find forms and their content recursively
python3 linkprob3r.py -u https://example.com -j -r

# Output results to an organized file
python3 linkprob3r.py -u https://example.com -j -r -o outputfile.txt

# Create a custom wordlist using any data discovered (in progress)
python3 linkprob3r.py -u https://example.com -j -r -w
```

## Development
> For all of the original features, use the original script. I am currently working on the linkprob3r-dev.py script by refactoring the code to try and make it more robust and reliable. Some of the features are not yet implemented and it is not completely finished yet, but it is being actively worked on and will have the original features plus some soon.

**For usage with the linkprob3r-dev.py script**:
> So far there are no command line options implemented yet, to test the script edit the `target` variable with a url, and comment/uncomment any function calls below depending on what you want to run.

