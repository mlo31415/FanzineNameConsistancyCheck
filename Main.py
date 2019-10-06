import os
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests


# Load all fanzine , clubzine, and apazine names from Fancy 3
#   Include redirects
# Get list of all fanzine directories from Fanac
# Produce a list of all directories on Fanac that don't have a fanzine on Fancy.  Note those which match a redirect.

# ----------------------------------------------------------
# Read a Fancy page's tags and title
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
# Is this Fancy page a redirect?  If so, return the page it redirects to.
def IsRedirect(pageText: str):
    pageText=pageText.strip()  # Remove leading and trailing whitespace
    if pageText.lower().startswith('[[module redirect destination="') and pageText.endswith('"]]'):
        return pageText[31:].rstrip('"]')
    return None


#*******************************************************
# Read a Fancy page and return a tuple:
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


# ====================================================================================
# Read fanac.org/fanzines/Classic_Fanzines.html amd /Modern_Fanzines.html
# Read the table to get a list of all the fanzines on Fanac.org
# Return a list of tuples (name on page, name of directory)
#       The name on page is the display named used in the Classic and Modern tables
#       The name of directory is the name of the directory pointed to

def ReadClassicModernPages():
    print("***Begin reading Classic and Modern tables")
    # This is a list of fanzines on Fanac.org
    # Each item is a tuple of (compressed name,  link name,  link url)
    fanacFanzineDirectories=[]
    directories=["http://www.fanac.org/fanzines/Classic_Fanzines.html", "http://www.fanac.org/fanzines/Unusual_Items.html"]
    for dirs in directories:
        ReadModernOrClassicTable(fanacFanzineDirectories, dirs)

    print("***Done reading Classic and Modern tables")
    return fanacFanzineDirectories


# ======================================================================
# Read one of the main fanzine directory listings and append all the fanzines directories found to the dictionary
def ReadModernOrClassicTable(fanacFanzineDirectories, url):
    h=requests.get(url)
    s=BeautifulSoup(h.content, "html.parser")
    # We look for the first table that does not contain a "navbar"
    tables=s.find_all("table")
    for table in tables:
        if "sortable" in str(table.attrs) and not "navbar" in str(table.attrs):
            # OK, we've found the main table.  Now read it
            trs=table.find_all("tr")
            for i in range(1, len(trs)):
                # Now the data rows
                name=trs[i].find_all("td")[1].contents[0].contents[0].contents[0]
                dirname=trs[i].find_all("td")[1].contents[0].attrs["href"][:-1]
                AddFanacDirectory(fanacFanzineDirectories, name, dirname)
    return


# -------------------------------------------------------------------------
# We have a name and a dirname from the fanac.org Classic and Modern pages.
# The dirname *might* be a URL in which case it needs to be handled as a foreign directory reference
def AddFanacDirectory(fanacFanzineDirectories, name: str, dirname: str):

    # We don't want to add duplicates. A duplicate is one which has the same dirname, even if the text pointing to it is different.
    dups=[e2 for e1, e2 in fanacFanzineDirectories if e2 == dirname]
    if len(dups) > 0:
        print("   duplicate: name="+name+"  dirname="+dirname)
        return

    if dirname[:3]=="http":
        print("    ignored, because is HTML: "+dirname)
        return

    # Add name and directory reference
    fanacFanzineDirectories.append((name, dirname))
    return

#=============================================================================================
# Remove the duplicates from a fanzine list
def RemoveDuplicates(fanzineList):
    # Sort in place on fanzine's Directory's URL followed by file name
    fanzineList.sort(key=lambda fz: fz.URL if fz.URL is not None else "")
    fanzineList.sort(key=lambda fz: fz.DirectoryURL if fz.DirectoryURL is not None else "")

    # Any duplicates will be adjacent, so search for adjacent directoryURL+URL
    last=""
    dedupedList=[]
    for fz in fanzineList:
        this=fz.DirectoryURL+fz.URL if fz.URL is not None else ""
        if this != last:
            dedupedList.append(fz)
        last=this
    return dedupedList


#=============================================================================================
# Convert a Fancy name to Fanac form
#   Drop punctuation
#   Change spaces to underscores
#   Change non-English letters to English
#   Capitalize 1st letter of all words
#   Retain internal capitals
#   Drop leading articles
def FancyToFanacForm(name: str):
    name=name.replace("  ", " ").replace("  ", " ").replace(" ", "_")    # Strings of blanks go to a single underscore
    funnyForeignCharacters={"é" : "e",
                            "É" : "E",
                            "ë" : "e",
                            "Ó" : "O",
                            "ö" : "oe",
                            "è" : "e",
                            "í" : "i"}
    punctuation="!"
    i=0
    out=[]
    while i < len(name):
        if name[i] in punctuation:
            i+=1
            continue
        if name[i] in funnyForeignCharacters.keys():
            out.append(funnyForeignCharacters[name[i]])
            i+=1
            continue
        if name[i] == "_":
            out.append(name[i])
            out.append(name[i+1].upper())
            i+=2
            continue
        out.append(name[i])
        i+=1
    out[0]=out[0].upper()
    name="".join(out)


    if name.startswith("A_"):
        name=name[2:]
    elif name.startswith("An_"):
        name=name[3:]
    elif name.startswith("The_"):
        name=name[4:]

    return name


#=============================================================================================
# Convert a string to Wikidot's cannonical form: All lower case; All spans of special characters reduced to a hyphen; No leading ro trailing hyphens.
# The strategy is to iterate through the name, copying characters to a list of characters which is later merged into the return string. (Appending to a string is too expensive.)
def CanonicizeWikidotName(name):
    funnyForeignCharacters={"é" : "e",
                            "É" : "E",
                            "ë" : "e",
                            "Ó" : "O",
                            "ö" : "oe",
                            "è" : "e",
                            "í" : "i"}
    out = []
    inAlpha = False
    inJunk = False
    for c in name:
        if c in funnyForeignCharacters.keys():
            c=funnyForeignCharacters[c]
        if c.isalnum() or c == ':':     # ":", the category separator, is an honorary alphanumeric
            if inJunk:
                out.append("-")
            out.append(c.lower())
            inJunk = False
            inAlpha = True
        else:
            inJunk = True
            inAlpha = False

    # Remove any leading or trailing "-"
    canname=''.join(out)
    if len(canname) > 1:
        if canname[0] == "-":
            canname=canname[1:]
        if canname[:-1] == "-":
            canname=canname[:-1]
    return canname


#=================================================================================
#=================================================================================
#=================================================================================
# Begin Main
#=================================================================================
fancySitePath=r"C:\Users\mlo\Documents\usr\Fancyclopedia\Python\site"

# The local version of the site is a pair (sometimes also a folder) of files with the Wikidot name of the page.
# <name>.txt is the text of the current version of the page
# <name>.xml is xml containing meta date. The metadata we need is the tags
# If there are attachments, they're in a folder named <name>. We don't need to look at that in this program

# Create a list of the pages on the site by looking for .txt files and dropping the extension
print("***Creating a list of all Fancyclopedia pages")
allFancy3PagesCanon = [f[:-4] for f in os.listdir(fancySitePath) if os.path.isfile(os.path.join(fancySitePath, f)) and f[-4:] == ".txt"]
#allFancy3PagesCanon= [f for f in allFancy3PagesCanon if f[0] in "ab"]        # Just to cut down the number of pages for debugging purposes

redirectFromCanName={}
fancyTitleFromFancyCanName={}   # fancyTitle is a dictionary: key=Fancy page's canonical name, value=Fancy page's title

print("***Scanning Fancyclopedia fanzine pages for redirects")
for pageCanName in allFancy3PagesCanon:
    if pageCanName.startswith("index_"):  # Don't look at the index_ pages
        continue
    redirect, isFanzine, title=GetRedirect(fancySitePath, pageCanName)

    if isFanzine:
        if redirect is not None:
            redirectFromCanName[pageCanName]=redirect
        fancyTitleFromFancyCanName[pageCanName]=title

print("***Converting to ultimate redirects")
for key in redirectFromCanName.keys():
    redirect=redirectFromCanName[key]
    if redirect is not None:
        while CanonicizeWikidotName(redirect) in redirectFromCanName.keys():
            redirect=redirectFromCanName[CanonicizeWikidotName(redirect)]
        redirectFromCanName[key]=redirect

# Now we have a dictionary where the keys are all the fanzine pages on Fancy and the values are the ultimate redirects.

# Read the fanac.org fanzine directory and produce a list of all issues and all newszines present
# This is a list of tuples: fanac page title, fanac directory name
fanacFanzineDirectories=ReadClassicModernPages()

# Now go through the directories in fanacFanzineDirectories and divide them into catagories:
#   The Fanac directory name is the Fanac form of a Fancy 3 ultimate redirect (ultimate redirects are the prefered form of the name)
#   The Fanac directory name is the Fanac form of a Fancy 3 page which is *not* an ultimate redirect
#   The Fanac directory name can't be found on Fancy 3

# We start by creating a list of Fancy 3 fanzine names turned into their Fanac forms

print("***Analyzing results")
fanacNamesOfFancyPages=[]   # List of the Fanac canonical form of names in Fancy
fancyTitleFromFanacFormToFancyForm={}                      # Dictionary which takes the Fanac canonical form of a Fancy name and gives you the Fancy name
# This will be a dictionary: key=Fancy page's title, value=Fanac form of key
for key in fancyTitleFromFancyCanName.keys():
    fanacNamesOfFancyPages.append(FancyToFanacForm(fancyTitleFromFancyCanName[key]))
    fancyTitleFromFanacFormToFancyForm[FancyToFanacForm(fancyTitleFromFancyCanName[key])]=fancyTitleFromFancyCanName[key]


# fancyTitle is a dictionary: key=Fancy page's Fancy canonical name, value=Fancy page's title
# canonNames is a dictionary: key=Fancy page's title, value=Fanac form of key

preferred=[]        # Fanac directories with the preferred name
unpreferred=[]      # Fanac directories with a varient name, but still recognizable
missing=[]          # Can't find these on Fancy
uncanonical=[]      # Fanac directories with names that are not canonical by Fanac standards

for ignore, fanacDirectory in fanacFanzineDirectories:  # fanacDirectory is the name of a Fanac fanzine directory


    canFanacDirectory=FancyToFanacForm(fanacDirectory)
    if canFanacDirectory != fanacDirectory:
        uncanonical.append((fanacDirectory, canFanacDirectory))

    # We want to discover if the fanac directory name is a properly canonical fanac directory name and if it is found in Fancy
    found=False
    found_fanzine=False
    if fanacDirectory in fanacNamesOfFancyPages:
        found=True
        fancyName=fancyTitleFromFanacFormToFancyForm[fanacDirectory]
    elif (fanacDirectory+"_(fanzine)") in fanacNamesOfFancyPages:
        fancyName=fancyTitleFromFanacFormToFancyForm[fanacDirectory+"_(fanzine)"]
        found=True
        found_fanzine=True
    if found:
        fancyCanonical=CanonicizeWikidotName(fancyName)
        if fancyName in fancyTitleFromFancyCanName.values() and fancyCanonical in fancyTitleFromFancyCanName.keys() and fancyTitleFromFancyCanName[fancyCanonical] == fancyName and not found_fanzine:
            preferred.append((fanacDirectory, fancyName))
        else:
            unpreferred.append((fanacDirectory, fancyName))
    else:
        missing.append(fanacDirectory)

print("***Writing results")
with open("Uncanonical Fanac.org directories.txt", "w+") as f:
    f.write("List of Fanac.org Fanzine directory names which are not in Fanac.org's canonical form\n\n")
    f.write("Actual    -->    Canonical\n\n")
    for u in uncanonical:
        f.write(u[0]+"     -->     "+u[1]+"\n")

with open("Matches between Fancy 3 and Fanac.org.txt", "w+") as f:
    f.write("List of Fanac.org Fanzine directory names which are presently in Fancy\n\n")
    f.write("Fancy Name    -->    Fanac Directory\n\n")
    for p in preferred:
        f.write(p[1]+"     -->     "+p[0]+"\n")

with open("Uncanonical matches between Fancy 3 and Fanac.org.txt", "w+") as f:
    f.write("List of Fanac.org Fanzine directory names which match a Fancy redirect\n\n")
    f.write("Fanac Directory    -->    Fancy Match    -->    Fancy Redirect\n\n")
    for u in unpreferred:
        canU=CanonicizeWikidotName(u[1])
        redir="None"
        if canU is not None and canU in redirectFromCanName.keys():
            redir=redirectFromCanName[canU]
        f.write(u[0]+"     -->     "+u[1]+"     -->     "+redir+"\n")

with open("Fanac.org directories with no match on Fancy 3.txt", "w+") as f:
    f.write("List of Fanac.org Fanzine directory names which can't be found in Fancy 3\n\n")
    f.write("Fanac Directory\n\n")
    for m in missing:
        f.write(m+"\n")

pass