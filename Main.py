
# Load all fanzine (plus clubzine plus apazine) names from Fancy 3
# Include redirects

# Get list of all fanzine directories from Fanac

# Produce a list of all directories on Fanac that don't have a fanzine on Fancy.  Note those which match a redirect.

import os
import re as RegEx
import xml.etree.ElementTree as ET


# The goal of this program is to produce an index to all of the names on Fancy 3 and fanac.org with links to everything interesting about them.
# We'll construct a master list of names with a preferred name and zero or more variants.
# This master list will be derived from Fancy with additions from fanac.org
# The list of interesting links will include all links in Fancy 3, and all non-housekeeping links in fanac.org
#   A housekeeping link is one where someone is credited as a photographer or having done scanning or the like
# The links will be sorted by importance
#   This may be no more than putting the Fancy 3 article first, links to fanzines they edited next, and everything else after that

# The strategy is to start with Fancy 3 and get that working, then bring in fanac.org.

# We'll work entirely on the local copies of the two sites.

# There will be a dictionary, nameVariants, indexed by every form of every name. The value will be the canonical form of the name.
# There will be a second dictionary, people, indexed by the canonical name and containing an unordered list of Reference structures
# A Reference will contain:
#       The canonical name
#       The as-used name
#       An importance code (initially 1, 2 or 3 with 3 being least important)
#       If a reference to Fancy, the name of the page (else None)
#       If a reference to fanac.org, the URL of the relevant page (else None)
#       If a redirect, the redirect name

nameVariants={}
peopleReferences={}

#Test

# ----------------------------------------------------------
# Read a page's tags and title
def ReadTagsAndTitle(pagePath: str):
    tree=ET.ElementTree().parse(os.path.splitext(pagePath)[0]+".xml")

    titleEl=tree.find("title")
    if titleEl is None:
        title=None
    else:
        title=titleEl.text

    tags=[]
    tagsEl=tree.find("tags")
    if tagsEl is not None:
        tagElList=tagsEl.findall("tag")
        if len(tagElList) != 0:
            for el in tagElList:
                tags.append(el.text)
    return tags, title


#*******************************************************
# Is this page a redirect?  If so, return the page it redirects to.
def IsRedirect(pageText: str):
    pageText=pageText.strip()  # Remove leading and trailing whitespace
    if pageText.lower().startswith('[[module redirect destination="') and pageText.endswith('"]]'):
        return pageText[31:].rstrip('"]')
    return None


#*******************************************************
# Read a page and return a tuple:
#   True if it has a Fanzine-like tag, False otherwise)
#   The name of the redirect or None if this is a regular page
# pagePath will be the path to the page's source (i.e., ending in .txt)
def GetRedirect(path: str, page: str):
    pagePath=os.path.join(path, page)+".txt"

    if not os.path.isfile(pagePath):
        #log.Write()
        return None

    # Load the page's source
    with open(os.path.join(pagePath), "rb") as f:   # Reading in binary and doing the funny decode is to handle special characters embedded in some sources.
        source=f.read().decode("cp437") # decode("cp437") is magic to handle funny foreign characters

    tags, title=ReadTagsAndTitle(pagePath)
    isFanzine="fanzine" in tags or "apazine" in tags or "clubzine" in tags

    # If the page is a redirect, we're done.
    return IsRedirect(source), isFanzine, title

fancySitePath=r"C:\Users\mlo\Documents\usr\Fancyclopedia\Python\site"

# The local version of the site is a pair (sometimes also a folder) of files with the Wikidot name of the page.
# <name>.txt is the text of the current version of the page
# <name>.xml is xml containing meta date. The metadata we need is the tags
# If there are attachments, they're in a folder named <name>. We don't need to look at that in this program

# Create a list of the pages on the site by looking for .txt files and dropping the extension
print("***Creating a list of all Fancyclopedia pages")
allFancy3PagesCanon = [f[:-4] for f in os.listdir(fancySitePath) if os.path.isfile(os.path.join(fancySitePath, f)) and f[-4:] == ".txt"]
#allFancy3PagesCanon= [f for f in allFancy3PagesCanon if f[0] in "ab"]        # Just to cut down the number of pages for debugging purposes

fancyRedirects={}
fancyTitle={}

print("***Scanning Fancyclopedia fanzine pages for redirects")
for pageCanName in allFancy3PagesCanon:
    if pageCanName.startswith("index_"):  # Don't look at the index_ pages
        continue
    redirect, isFanzine, title=GetRedirect(fancySitePath, pageCanName)

    if isFanzine:
        fancyRedirects[pageCanName]=redirect
        fancyTitle[pageCanName]=title

print("***Converting to ultimate redirects")
for key in fancyRedirects.keys():
    redirect=fancyRedirects[key]
    while redirect in fancyRedirects.keys():
        redirect=fancyRedirects[redirect]
    fancyRedirects[key]=redirect

# Now we have a dictionary where the keys are all the fanzine pages on Fancy and the values are the ultimate redirects.
keys=list(fancyTitle.keys())
keys=sorted(keys)

for key in keys:
    if fancyRedirects[key] is not None:
        print(key+": "+fancyRedirects[key]+"  ("+fancyTitle[key]+")")
    else:
        print(key+": None  ("+fancyTitle[key]+")")

i=0
