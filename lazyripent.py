import os
import sys
import winreg
import subprocess
import re
	
def Die(reason):
	print("ERROR: "+reason)
	print("Exiting..")
	exit() #brutal.
	
STEAM_IS32 = False
PATH_STEAM = None
	
def RegTest(rk):
	global PATH_STEAM
	hkey = None
	try:
		hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rk)
	except:
		print("HKey: \"HKEY_LOCAL_MACHINE\\{}\" failed.".format(rk))
		return
	
	try:
		PATH_STEAM = winreg.QueryValueEx(hkey, "InstallPath")[0]
	except:
		PATH_STEAM = None
	finally:
		print("Found steam: \"{}\"".format(PATH_STEAM))
	
if(len(sys.argv) < 3):
	Die("Not enough arguments!\nUsage: python lazyripent.py \"C:\Path\To\Bsps\" myrules")
	
PATH_BSP = sys.argv[1]
PATH_RULE = sys.argv[2]+".txt"

if not os.path.exists(PATH_BSP):
	Die("BSP Path \"{}\" does not exist!".format(PATH_BSP))
	
if not os.path.exists(PATH_RULE):
	Die("Rule File \"{}\" does not exist!".format(PATH_RULE))
	
print("BSP Path set to: \"{}\"\nRule file: \"{}\"".format(PATH_BSP, PATH_RULE))
	
print("Reading registry for steam path..")

REG_STEAM32 = "SOFTWARE\\Valve\\Steam"
REG_STEAM64 = "SOFTWARE\\Wow6432Node\\Valve\Steam"

RegTest(REG_STEAM64)

if PATH_STEAM == None:
	RegTest(REG_STEAM32)
	STEAM_IS32 = True

if PATH_STEAM == None:
	Die("Failed to find steam installation path! :(")
	
print("Using {} tools".format("32-bit" if STEAM_IS32 else "64-bit"))

PATH_SDK = "\\steamapps\\common\\Sven Co-op SDK\\mapping\\compilers"
PATH_RIPENT = "\\Ripent.exe" if STEAM_IS32 else "\\Ripent_x64.exe"
RIPENT = PATH_STEAM+PATH_SDK+PATH_RIPENT

if not os.path.exists(RIPENT):
	Die("Failed to find ripent! Please ensure that Sven Co-op SDK is fully installed!")
else:
	print("Ripent path set to: \"{}\"".format(RIPENT))
	

BSP_SOURCES = []
print("Pooling BSP files..")
for file in os.listdir(PATH_BSP):
	if file.endswith(".bsp"):
		print("Pooled: \"{}\"".format(os.path.join(PATH_BSP, file)))
		BSP_SOURCES.append(file)
		
if len(BSP_SOURCES) == 0:
	Die("No BSP files were found!")
	
print("Extracing BSP files..")
for bsp in BSP_SOURCES:
	bspfile = os.path.join(PATH_BSP, bsp)
	ent = bsp.replace(".bsp", ".ent")
	entfile = os.path.join(PATH_BSP, ent)
	subprocess.call([RIPENT, "-export", bspfile], stdout=open(os.devnull, "wb"))
	print("Extracted to: \"{}\"".format(entfile))

#load rule stuff

rules = []
		
class cRuleSelector:
	def __init__(self, type, key, value):
		self.type = type
		self.key = key
		self.value = value
		
class cRuleReplace:
	def __init__(self, key, value, parser):
		self.key = key
		self.value = value
		self.parser = parser
	
class cRule:
	def __init__(self):
		self.selectors = []
		self.removes = []
		self.adds = {}
		self.replaces = []
		self.newents = []
		
FILE_RULE = None

print("Reading rules..")
try:
	with open(PATH_RULE, "r") as content:
		FILE_RULE = content.read()
except:
	Die("Failed to read rule file!")
	
def isStrBlank(string):
	if string and string.strip():
		return False
	
	return True
	
if FILE_RULE == None or isStrBlank(FILE_RULE):
	Die("Rule file was empty!")
	
#find rule definitions
_bracketregex = re.compile(r"{(?:\n)([^}]*)(?:\n)}", re.I|re.M)
_ruleregex = re.compile(r"([^\s]+)\s+\"([^\s]+)\"(?:\s+\"([^\s]+)\"(?:\s+\"([^\s]+)\")?)?", re.I|re.M)
for regrule in re.findall(_bracketregex, FILE_RULE):
	rule = cRule()
	
	for regparse in re.finditer(_ruleregex, regrule):
		word = regparse.group(1).upper()
		if(isStrBlank(word)):
			Die("Rule error: action not defined!")
		if(isStrBlank(regparse.group(2))):
			Die("Rule error: key not defined!")
		if(word == "MATCH" or word == "NOTMATCH"):#selectors
			if(isStrBlank(regparse.group(3))):
				Die("Rule error: value not defined!")
			rule.selectors.append(cRuleSelector(word, regparse.group(2), regparse.group(3)))
		elif(word == "HAVE" or word == "NOTHAVE"):
			rule.selectors.append(cRuleSelector(word, regparse.group(2), None))
		elif(word == "ADD"):#modifiers
			if(isStrBlank(regparse.group(3))):
				Die("Rule error: value not defined!")
			rule.adds[regparse.group(2)] = regparse.group(3)
		elif(word == "REMOVE"):
			rule.removes.append(regparse.group(2))
		elif(word == "REPLACE"):
			if(isStrBlank(regparse.group(3))):
				Die("Rule error: value not defined!")
			rule.replaces.append(cRuleReplace(regparse.group(2), regparse.group(3), regparse.group(4)))
		elif(word == "NEWENT"):
			rule.newents.append(regparse.group(2))
		else:
			Die("Rule error: unknown action!")
			
	rules.append(rule)
	
print("Rules parsed. # of rules: {}".format(len(rules)))

#start applying rules
print("Applying rules..")
print("!! This part may take some time")
_kvregex = re.compile(r"^\"([^\s]+)\"\s+\"([^\"]+)\"", re.I|re.M)
_starregex = re.compile(r"(?:\*)?([^*]+)(?:\*)?", re.I|re.M)
for bsp in BSP_SOURCES:
	ent = bsp.replace(".bsp", ".ent")
	entfile = os.path.join(PATH_BSP, ent)
	print("Loading: {}".format(ent))
	file = None
	newfile = None
	appendents = []
	try:
		with open(entfile, "r", newline="\n") as content:
			file = content.read()
	except:
		Die("Failed to read ent file!")
	
	for index, rule in enumerate(rules):
		print("Testing for rule: #{}".format(index+1))
		modded = 0
		if newfile != None:
			file = newfile
			newfile = ""
		else:
			newfile = ""
		for entblock in re.findall(_bracketregex, file):
			accepted = 0
			for selector in rule.selectors:
				if len(rule.selectors) == 0:
					Die("Impossible rule: no selectors!")
				#must match
				if(selector.type == "MATCH"): # key = key, value = value
					for entkv in re.finditer(_kvregex, entblock):
						if(entkv.group(1) == selector.key):
							if("*" in selector.value):
								wild = re.match(_starregex, selector.value)
								if wild.group(1) in entkv.group(2):
									accepted += 1
									break
							else:
								if(entkv.group(2) == selector.value):
									accepted += 1
									break
				elif(selector.type == "NOTMATCH"): # key = key, value != value
					for entkv in re.finditer(_kvregex, entblock):
						if(entkv.group(1) == selector.key):
							if("*" in selector.value):
								wild = re.match(_starregex, selector.value)
								if wild.group(1) not in entkv.group(2):
									accepted += 1
									break
							else:
								if(entkv.group(2) != selector.value):
									accepted += 1
									break
				elif(selector.type == "HAVE"): # key = key
					for entkv in re.finditer(_kvregex, entblock):
						if(entkv.group(1) == selector.key):
							accepted += 1
							break
				elif(selector.type == "NOTHAVE"): # key != key
					hasKey = False
					for entkv in re.finditer(_kvregex, entblock):
						if(entkv.group(1) == selector.key):
							hasKey = True
							break
					if not hasKey:
						accepted += 1
			if accepted == len(rule.selectors): #process
				modded += 1
				newentblock = ""
				tempentblock = ""
				#order of operations: remove, add, replace, newent
				if len(rule.removes) > 0:
					for toRemove in rule.removes:
						for entkv in re.finditer(_kvregex, entblock):
							if(toRemove != entkv.group(1)):
								tempentblock += "\"{}\" \"{}\"\n".format(entkv.group(1), entkv.group(2))
				else:
					tempentblock = entblock;
						
				newentblock = tempentblock
				tempentblock = ""
				
				for toAdd in rule.adds:
					newentblock += "\n\"{}\" \"{}\"".format(toAdd, rule.adds[toAdd])
					
				for toReplace in rule.replaces:
					if(isStrBlank(toReplace.parser)): #simple
						for entkv in re.finditer(_kvregex, newentblock):
							if(toReplace.key == entkv.group(1)):
								tempentblock += "\"{}\" \"{}\"\n".format(toReplace.key, toReplace.value)
							else:
								tempentblock += "\"{}\" \"{}\"\n".format(entkv.group(1), entkv.group(2))
					else: #complex
						for entkv in re.finditer(_kvregex, newentblock):
							if(toReplace.key == entkv.group(1)):
								fixedval = entkv.group(2).replace(toReplace.parser, "")
								newval = toReplace.value.replace("?", fixedval)
								tempentblock += "\"{}\" \"{}\"\n".format(toReplace.key, newval)
							else:
								tempentblock += "\"{}\" \"{}\"\n".format(entkv.group(1), entkv.group(2))
							
				if len(rule.replaces) > 0:
					newentblock = tempentblock
					tempentblock = ""
								
				for newent in rule.newents:
					kvlist = newent.split(":")
					fixedkvlist = ""
					if len(kvlist)%2 == 1:
						Die("Uneven amount of key/value pairs in NEWENT")
					for index, item in enumerate(kvlist):
						isvalue = True if index%2==1 else False
						
						if not isvalue:
							if index == 0:
								fixedkvlist += item
							else:
								fixedkvlist += ":{}".format(item)
						else:
							if item.startswith("$"):
								fixeditem = item.replace("$","")
								didFind = False
								for entkv in re.finditer(_kvregex, newentblock):
									if(entkv.group(1) == fixeditem):
										fixedkvlist += ":{}".format(entkv.group(2))
										didFind = True
										break
								if not didFind:
									Die("Did not find key \"{}\" in selected ent while trying to fill in new entity info".format(fixeditem))
							else:
								fixedkvlist += ":{}".format(item)
					appendents.append(fixedkvlist)
						
				if not isStrBlank(newentblock):
					newfile += "{{\n{}\n}}\n".format(newentblock)
				else:
					Die("Managed to make empty entity block!")
			else: #dont process, but still write to new file.
				newfile += "{{\n{}\n}}\n".format(entblock)
		print("Matched {} entities.".format(modded))
	if len(appendents) > 0:
		print("Appending new ents..")
		for newent in appendents:
			newentblock = "{\n"
			kvlist = newent.split(":")
			if len(kvlist)%2 == 1:
				Die("Uneven amount of key/value pairs while appending new entity!")
			for index, item in enumerate(kvlist):
				if(index % 2 == 0):
					newentblock += "\"{}\" ".format(item)
				else:
					newentblock += "\"{}\"\n".format(item)
			newentblock += "}\n"
			newfile += newentblock
			
	print("Cleaning up newlines..")
	file = ""
	for line in newfile.splitlines():
		if not re.match(r"^\s*$", line):
			file += line+"\n"
				
	print("Saving: {}".format(ent))
	try:
		with open(entfile, "w", newline="\n") as content:
			content.write(file)
	except:
		Die("Failed to write new ent file!")
				
# .ent->.bsp

print("Importing ENT files..")
for bsp in BSP_SOURCES:
	bspfile = os.path.join(PATH_BSP, bsp)
	ent = bsp.replace(".bsp", ".ent")
	entfile = os.path.join(PATH_BSP, ent)
	subprocess.call([RIPENT, "-import", entfile], stdout=open(os.devnull, "wb"))
	print("Imported: \"{}\"".format(entfile))
	
print("Cleaning up..")
for bsp in BSP_SOURCES:
	ent = bsp.replace(".bsp", ".ent")
	entfile = os.path.join(PATH_BSP, ent)
	os.remove(entfile)
	print("Removed: \"{}\"".format(entfile))
		
print("All done!")