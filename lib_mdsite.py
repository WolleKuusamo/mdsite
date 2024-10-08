#!/usr/bin/python3
# -*- coding: utf-8 -*-

########################################################################
# imports
########################################################################

import os, sys, random, sqlite3, unicodedata, re, shutil, markdown, \
	datetime, codecs

########################################################################
# constants
########################################################################

defEnc = 'utf-8'

########################################################################
# common functions
########################################################################

def cancelScript (errorText):
	print ('ERROR:', errorText)
	print ('      ', 'script canceled')
	sys.exit (0)

def copyDir (source, dest):
	try:
		os.makedirs (dest)
	except:
		pass
	files = getFileList (source)
	for f in files:
		shutil.copy2 (os.path.join (source, f), os.path.join (dest, f))
		
def getFileList (fileDir, fileExt = (), fileSort = True):
	fList = []
	if os.path.isdir (fileDir) == False:
		return fList
	rawList = os.listdir (fileDir)
	for f in rawList:
		tempFile = os.path.join (fileDir, f)
		if os.path.isfile (tempFile):
			filename, ext = os.path.splitext (tempFile)
			ext = ext[1:]
			if fileExt in [(), []]:
				fList.append (f)
			else:
				if ext in fileExt:
					fList.append (f)
	if fileSort == True:
		fList.sort ()
	return fList

def getShortDate (isoDate):
	return isoDate[8:] + '.' + isoDate[5:7] + '.' + isoDate[:4]
	
def getTimestamp (timeFormat = "%H%M%S"):
	return datetime.datetime.now ().strftime ("%Y-%m-%d-" + timeFormat)

def normalizeString (oldName, defDash = '-'):
	newName = oldName.encode (defEnc).decode (defEnc)
	newName = unicodedata.normalize ('NFKD', newName)
	newName = newName.encode ('ascii', 'ignore').lower ()
	newName = re.sub (r'[^a-z0-9]+', defDash, newName.decode (defEnc)).strip (defDash)
	return newName
	
def readTextFile (fileName):
	newText = ""
	file = codecs.open (fileName, encoding = defEnc)
	for line in file:
		newText += line.rstrip () + "\n"
	file.close ()
	return newText[:-1]

def sliceList (sList, portions):
	result = []
	for i in range (portions):
		result.append ([])
	p = 0
	for e in sList:
		result[p].append (e)
		p += 1
		if p == portions:
			p = 0
	return result

def sqlString (string):
	if string == None:
		return ''
	return string.replace ("'", "''")

def writeTextFile (fileName, fileText):
	file = codecs.open (fileName, encoding = defEnc, mode = "w")
	try:
		file.write (fileText)
	except:
		file.write (fileText.decode (defEnc))
	file.close ()

########################################################################
# cConfFile
########################################################################

class cConfFile:
	
	def __init__ (self, filePath):
		self.filePath = filePath
		self.confLines = []
		self.encoding = 'utf-8'
		self.confDict = {}
		self.confComments = {}
	
	def getListValues (self, section):
		try:
			tempList = self.confDict[section]
			values = [d for d in tempList]
		except: # no key
			values = []
		return values
	
	def getListValuesPairs (self, section):
		listKeys = self.getListValues (section)
		pairs = []
		for lk in listKeys:
			pairs.append ([lk, self.getValue (section, lk)])
		return pairs
	
	def getSections (self):
		lSect = []
		for keys in self.confDict:
			lSect.append (keys)
		return lSect
	
	def getValue (self, section, key, default = None):
		try:
			value = self.confDict[section][key]
		except:
			value = default
		return value
	
	def parseFile (self):
		self.confDict = {}
		for l in self.confLines:
			if l != '' and l[0] == '[' and l[-1] == ']':
				self.confDict[l[1:-1]] = {}
		for keys in self.confDict:
			running = False
			for l in self.confLines:
				if running == True and l.strip () != '' and l.startswith ('[') == False:
					nKey = l.split ('=')[0].strip ()
					try:
						nVal = l.split ('=')[1].strip ()
					except:
						nVal = None
					self.confDict[keys][nKey] = nVal
				if l.strip () == '[' + keys + ']':
					running = True
				if running == True and (l.strip () == '' or l.strip ().startswith('[') == True and l.strip ()[1:-1] != keys):
					running = False
					break
	def readFile (self):
		self.confLines[:] = []
		try:
			cFile = codecs.open (self.filePath, encoding = self.encoding)
			for line in cFile:
				if line[:1] != '#':
					self.confLines.append (line.strip ())
			cFile.close ()
		except:
			pass
		self.parseFile ()
	
	def setComment (self, section, comment):
		self.confComments[section] = comment
	
	def setValue (self, section, key, value = None):
		if section not in self.confDict:
			self.confDict[section] = {}
		self.confDict[section][key] = value

	def writeFile (self):
		confText = ''
		if 'first_line' in self.confComments:
			confText += '# ' + self.confComments['first_line'] + '\n'
		for sect in self.confDict:
			if sect in self.confComments:
				confText += '# ' + self.confComments[sect] + '\n'
			confText += '[' + sect + ']\n'
			for key in self.confDict[sect]:
				if self.confDict[sect][key] != None:
					confText += key + ' = ' + self.confDict[sect][key] + '\n'
				else:
					confText += key + '\n'
			confText += '\n'
		cFile = codecs.open (self.filePath, encoding = self.encoding, mode = "w")
		cFile.write (confText)
		cFile.close ()

#######################################################################
# class cMdWebsite
#######################################################################

'''
suitable for a collection of markdown files with included header like this:
---
title: Chapter 1
author: Firstname Lastname
date: yyyy-mm-dd
status: draft | publish | all
categories: category1,category2
tags: tag1,tag 2,tag3
comment: comments here, please
---
# Chapter 1

content
'''

'''
the source directory with the markdown files (ending: .md) must contain
a mdsite.conf file with the following information

[site]
title = title of the page
subtitle = subtitle of the page
target_dir = target directory for build (it will be saved in a subdirectory with timestamp)
image_dir = directory with image files
style_dir = style directory with css files, header image, fonts and other stuff

[articles]
selection = publish | draft | all (all = publish and draft)
datestamp = end | beginning | no (datestamp at end, beginning or none)
teaser = auto | more (auto for first paragraph, more for everything before <!--more--> tag)
image_figures = yes | no (replace img tag with figure/img/figcaption/figure
em_paragraphs = yes | no (replace emphasized paragraphs to p.em class)
question_paragraphs = yes | no (replace paragraphs starting with ?? TEXT to p.question)
'''

### class cMdWebsite

class cMdWebsite:
	def __init__(self, mdDir):
		self.mdDir = mdDir # base directory / content and conf
		self.initClass ()

	def initClass (self):
		self.confData = {} # settings in dictionary
		self.menuPages = '' # pages menu
		self.menuCategories = '' # category menu
		self.menuTags = '' # tag menu
		self.dbCon = None # sqlite3 database in memory
		self.dbCur = None # sqlite3 cursor
		self.readConfFile ()
		self.buildDir = os.path.join (self.confData['target_dir'], getTimestamp ())
		# TODO: check if confFile contains all necessary data and dirs are all valid

	def copyDependencies (self):
		# copy dependencies (images, stylesheets, ...) to buildDir
		styleFiles = getFileList (self.confData['style_dir'], ('jpg', 'css', 'ttf', 'png'))
		os.makedirs (os.path.join (self.buildDir, 'styles'))
		for sf in styleFiles:
			sFile = os.path.join (self.confData['style_dir'], sf)
			tFile = os.path.join (self.buildDir, 'styles', sf)
			shutil.copy2 (sFile, tFile)
		if self.confData['image_dir'] != '':
			copyDir (self.confData['image_dir'], os.path.join (self.buildDir, 'images'))

	def createMemDatabase (self):
		# create sqlite in-memory-database with all tables
		self.dbCon = sqlite3.connect (":memory:")
		self.dbCur = self.dbCon.cursor ()
		sql = '''CREATE TABLE tcontent (
			content_id integer NOT NULL,
			title varchar NOT NULL,
			filename varchar NOT NULL,
			type varchar NOT NULL,
			date varchar NOT NULL,
			status varchar NOT NULL,
			slug varchar NOT NULL,
			teaser varchar NOT NULL
		);'''
		self.dbCur.execute (sql)
		sql = '''CREATE TABLE tcategories (
			content_id integer NOT NULL,
			category varchar NOT NULL
		);'''
		self.dbCur.execute (sql)
		sql = '''CREATE TABLE tauthors (
			content_id integer NOT NULL,
			author varchar NOT NULL
		);'''
		self.dbCur.execute (sql)
		sql = '''CREATE TABLE ttags (
			content_id integer NOT NULL,
			tag varchar NOT NULL
		);'''
		self.dbCur.execute (sql)
		self.dbCon.commit ()

	def getMdInfo (self, fileName):
		# get all serious infos out of md file
		mdLines = readTextFile (fileName).split ('\n')
		mdInfo = {'title': '',
			'author': '',
			'date': '',
			'type': 'post',
			'status': 'draft',
			'categories': [],
			'tags': [],
			'content': '',
			'teaser': ''}
		headerSeps = [ix for ix in range (len (mdLines)) if '---' == mdLines[ix]]
		if len (headerSeps) > 1 and headerSeps[1] < 9: # header present
			for i in range (headerSeps[0] + 1, headerSeps[1]):
				tempLine = mdLines[i].split (':')
				nextKey = tempLine[0].strip ()
				tempVal = tempLine[1].strip ()
				if nextKey in ['categories', 'tags'] and tempVal.find (',') > -1:
					nextVal = tempVal.split (',')
					mdInfo[nextKey] = [d.strip () for d in nextVal]
				elif nextKey in ['categories', 'tags'] and tempVal.find (',') == -1:
					mdInfo[nextKey] = [tempVal]
				else:
					mdInfo[nextKey] = tempVal
			tempContent = mdLines[headerSeps[1] + 1:]
		else:
			tempContent = mdLines[0:]
		mdInfo['content'] = "\n".join (tempContent)
		if self.confData['articles_teaser'] == 'more':
			teaseFind = mdInfo['content'].find ('<!--more-->')
			if teaseFind > -1:
				tempTeaser = mdInfo['content'][:teaseFind]
				tempTeaser = tempTeaser.replace ('**', '')
				tempTeaser = tempTeaser.replace ('\n', '')
				mdInfo['teaser'] = tempTeaser
		if self.confData['articles_teaser'] == 'auto':
			tempLines = mdInfo['content'].split ('\n')
			for tl in tempLines:
				if tl == '' or tl.startswith ('# ') or tl.startswith ('## ') \
					or tl.startswith ('### ') or tl.startswith ('#### ') \
					or tl.startswith ('##### ') or tl.startswith ('###### ') \
					or tl.startswith ('_'):
					pass
				elif tl.startswith ('**') and tl.endswith ('**'):
					mdInfo['teaser'] = tl[2:-2]
					break
				else:
					mdInfo['teaser'] = tl
					break
		return mdInfo

	def getMenus (self):
		# get menus for categories, tags (tag cloud) and pages
		# author menu not needed now, keep it for future reasons
		sql = "SELECT distinct author FROM tauthors ORDER BY author"
		self.dbCur.execute (sql)
		result = self.dbCur.fetchall ()
		self.menuAuthors = ''
		for r in result:
			self.menuAuthors += '<a href="{{site.url}}author/' + normalizeString (r[0]) \
				+ '/">' + r[0] + '</a>\n'
		# categories
		sql = "SELECT category, COUNT(*) as catcount FROM tcategories GROUP BY category ORDER BY catcount DESC"
		self.dbCur.execute (sql)
		result = self.dbCur.fetchall ()
		self.menuCategories = ''
		for r in result:
			self.menuCategories += '<a href="{{site.url}}category/' + normalizeString (r[0]) \
				+ '/">' + r[0] + '</a>\n'
		# tags with tag cloud
		sql = "SELECT tag, COUNT(*) as tagcount FROM ttags GROUP BY tag ORDER BY tagcount DESC"
		self.dbCur.execute (sql)
		result = self.dbCur.fetchall ()
		tagCount = []
		for r in result:
			if r[1] not in tagCount:
				tagCount.append (r[1])
		sList = sliceList (tagCount, 5)
		self.menuTags = ''
		menuTagList = []
		for r in result:
			for i in range (0, 5):
				if r[1] in sList[i]:
					dWeight = 5 - i
					break
			menuTagList.append ('<a href="{{site.url}}tag/' + normalizeString (r[0]) \
				+ '/" class="fontweight' + str (dWeight) \
				+ ' tagcolor' + str (random.randint (1,4)) \
				+ '">' + r[0] + '</a>\n')
		random.shuffle (menuTagList)
		for e in menuTagList:
			self.menuTags += e
		# pages
		sql = "SELECT title, slug FROM tcontent WHERE type = 'page' ORDER BY title"
		self.dbCur.execute (sql)
		result = self.dbCur.fetchall ()
		self.menuPages = ''
		for r in result:
			self.menuPages += '<a href="{{site.url}}' + r[1] \
				+ '/">' + r[0] + '</a>\n'

	def getSiteContent (self):
		# reads all posts / pages into memory database
		selection = (self.confData['articles_selection'])
		if self.confData['articles_selection'] == 'all':
			selection = ['publish', 'draft']
		self.dbCur.execute ("DELETE FROM tcontent")
		self.dbCur.execute ('DELETE FROM tcategories')
		self.dbCur.execute ('DELETE FROM tauthors')
		self.dbCur.execute ('DELETE FROM ttags')
		contentFiles = getFileList (self.mdDir, ('md'))
		contentId = 0
		for cf in contentFiles:
			contentId += 1
			nextFile = os.path.join (self.mdDir, cf)
			nextInfo = self.getMdInfo (nextFile)
			# posts
			if nextInfo['type'] == 'post' and nextInfo['status'] in selection:
				tempTitle = nextInfo['title']
				if nextInfo['status'] == 'draft' and self.confData['articles_selection'] == 'all':
					tempTitle = nextInfo['title'] + ' (:draft:)' # mark as draft
				sql = "INSERT INTO tcontent (content_id, title, filename, type, date, status, slug, teaser) VALUES (" \
					+ str (contentId) + ", '" \
					+ sqlString (tempTitle) + "', '" \
					+ nextFile + "', '" \
					+ "post', '" \
					+ nextInfo['date'] + "', '" \
					+ nextInfo['status'] + "', '" \
					+ normalizeString (nextInfo['title']) + "', '" \
					+ sqlString (nextInfo['teaser']) + "')"
				self.dbCur.execute (sql)
				for e in nextInfo['categories']:
					sql = "INSERT INTO tcategories (content_id, category) VALUES (" \
						+ str (contentId) + ", '" + sqlString (e) + "')"
					self.dbCur.execute (sql)
				sql = "INSERT INTO tauthors (content_id, author) VALUES (" \
					+ str (contentId) + ", '" + sqlString (nextInfo['author']) + "')"
				self.dbCur.execute (sql)
				for e in nextInfo['tags']:
					sql = "INSERT INTO ttags (content_id, tag) VALUES (" \
						+ str (contentId) + ", '" + sqlString (e) + "')"
					self.dbCur.execute (sql)
			# page
			if nextInfo['type'] == 'page' and nextInfo['status'] in selection:
				sql = "INSERT INTO tcontent (content_id, title, filename, type, date, status, slug, teaser) VALUES (" \
					+ str (contentId) + ", '" \
					+ sqlString (nextInfo['title']) + "', '" \
					+ nextFile + "', '" \
					+ "page', '" \
					+ nextInfo['date'] + "', '" \
					+ nextInfo['status'] + "', '" \
					+ normalizeString (nextInfo['title']) + "', '')"
				self.dbCur.execute (sql)
		self.dbCon.commit ()

	def getTeasers (self, indexType = 'all', selection = ''):
		# gets teasers for blog (title), category and tag pages
		if indexType == 'all':
			sql = "SELECT ROW_NUMBER () OVER (ORDER BY c.date DESC) rownum, c.title, c.teaser, c.date, a.author, c.slug " \
				+ "FROM tcontent c JOIN tauthors a ON c.content_id = a.content_id WHERE c.type = 'post' ORDER BY date DESC"
		elif indexType == 'category':
			sql = "SELECT ROW_NUMBER () OVER (ORDER BY c.date DESC) rownum, c.title, c.teaser, c.date, a.author, c.slug " \
				+ "FROM tcontent c JOIN tauthors a ON c.content_id = a.content_id " \
				+ "JOIN tcategories s ON c.content_id = s.content_id WHERE c.type = 'post' AND s.category LIKE '" + selection + "' ORDER BY date DESC"
		elif indexType == 'tag':
			sql = "SELECT ROW_NUMBER () OVER (ORDER BY c.date DESC) rownum, c.title, c.teaser, c.date, a.author, c.slug " \
				+ "FROM tcontent c JOIN tauthors a ON c.content_id = a.content_id " \
				+ "JOIN ttags s ON c.content_id = s.content_id WHERE c.type = 'post' AND s.tag LIKE '" + selection + "' ORDER BY date DESC"
		elif indexType == 'author':
			sql = "SELECT ROW_NUMBER () OVER (ORDER BY c.date DESC) rownum, c.title, c.teaser, c.date, a.author, c.slug " \
				+ "FROM tcontent c JOIN tauthors a ON c.content_id = a.content_id " \
				+ "JOIN tauthors s ON c.content_id = s.content_id WHERE c.type = 'post' AND s.author LIKE '" + selection + "' ORDER BY date DESC"
		elif indexType == 'date':
			sql = "SELECT ROW_NUMBER () OVER (ORDER BY c.date DESC) rownum, c.title, c.teaser, c.date, a.author, c.slug " \
				+ "FROM tcontent c JOIN tauthors a ON c.content_id = a.content_id WHERE c.type = 'post' " \
				+ "AND (date LIKE '" + selection + "') ORDER BY title"
		else:
			print ("no valid indexType in function 'writePages'")
			return
		self.dbCur.execute (sql)
		result = self.dbCur.fetchall ()
		teasers = []
		for r in result:
			teasers.append ([r[0], r[1], r[2], r[3], r[4], r[5]])
		return teasers

	def getTemplateCopy (self, template = 'index.html', level = 0):
		# gets template named index.html, if you want an extra template for
		# tag, category, author pages, define category.html etc. in styles
		html = readTextFile (os.path.join (self.confData['style_dir'], template))
		html = html.replace ('{{site.title}}', self.confData['title'])
		html = html.replace ('{{site.description}}', self.confData['subtitle'])
		html = html.replace ('{{menu.pages}}', self.menuPages)
		html = html.replace ('{{menu.categories}}', self.menuCategories)
		html = html.replace ('{{menu.tags}}', self.menuTags)
		html = html.replace ('{{menu.authors}}', self.menuAuthors)
		# html = html.replace ('{{site.styles}}', 'styles/')
		# html = html.replace ('{{url.styles}}', '{{site.url}}/styles/')
		return html

	def processHtml (self, text):
		# some "normal" html tags will be replaced
		rePats = []
		if self.confData['articles_question_paragraphs'] == 'yes':
			rePats.append ([r'<p>\?{2}(.*?)\?{2}<\/p>', r'<p class="question">\1</p>']) # two ?? at beginning of paragraph will be transformed to p.question)
		if self.confData['articles_em_paragraphs'] == 'yes':
			rePats.append ([r'<p><em>(.*?)<\/em><\/p>', r'<p class="em">\1</p>']) # em paragraph will be transformed to p.em
		if self.confData['articles_image_figures'] == 'yes':
			rePats.append ([r'<p><img alt=\"(.*?)\" src=\"(.*?)\" \/><\/p>',
				r'<figure>\n<img src="' + '{{site.url}}images' + r'/\2"' \
					+ r' alt="\1" title="\1" />\n<figcaption>\1</figcaption>\n</figure>\n']) # image tags will be transformed into figure with figcaption
		rePats.append ([r'<a href="(?!http)(.*?)">', r'<a href="{{site.url}}' + r'\1">']) # resolve intern links
		newtext = text
		for r in rePats:
			newtext = re.sub (r[0], r[1], newtext, flags = re.MULTILINE)
		return newtext

	def readConfFile (self):
		cFile = os.path.join (self.mdDir, 'mdsite.conf')
		if os.path.isfile (cFile) == False:
			self.confData = {}
			return
		cf = cConfFile (cFile)
		cf.readFile ()
		self.confData['title'] = cf.getValue ('site', 'title')
		self.confData['subtitle'] = cf.getValue ('site', 'subtitle')
		self.confData['target_dir'] = cf.getValue ('site', 'target_dir')
		self.confData['image_dir'] = cf.getValue ('site', 'image_dir', '')
		self.confData['style_dir'] = cf.getValue ('site', 'style_dir')
		self.confData['css_version'] = cf.getValue ('site', 'css_version', 'yes')
		if self.confData['css_version'] == 'yes':
			self.confData['css_version'] = '1.' + str (random.randint (10000, 99999))
		self.confData['articles_selection'] = cf.getValue ('articles', 'selection')
		self.confData['articles_datestamp'] = cf.getValue ('articles', 'datestamp', 'end')
		self.confData['articles_teaser'] = cf.getValue ('teasers', 'text', 'auto') # more = before <!--more--> tag, auto = first paragraph
		self.confData['articles_image_figures'] = cf.getValue ('articles', 'image_figures', 'no')
		self.confData['articles_em_paragraphs'] = cf.getValue ('articles', 'em_paragraphs', 'no')
		self.confData['articles_question_paragraphs'] = cf.getValue ('articles', 'question_paragraphs', 'no')

	def writeContentPage (self, localDir, content, level, templateName = 'index.html'):
		# write content page index (or category or ...).html in local ...
		# ... directory with levelled links and using template file
		relUrl = level * '../'
		tempPage = self.getTemplateCopy (template = templateName, level = level)
		if self.confData['css_version'] not in ['', 'no']:
			tempPage = tempPage.replace ('.css"', '.css?v=' + self.confData['css_version'] + '"')
		tempPage = tempPage.replace ('{{content}}', content)
		tempPage = tempPage.replace ('{{site.url}}', relUrl)
		try:
			os.makedirs (localDir)
		except:
			pass
		indexFile = os.path.join (localDir, 'index.html')
		writeTextFile (indexFile, tempPage)

	def writePages (self, indexType = 'all', selection = ''):
		# writes blog, category and tag pages, if indexType = all, then startpage,
		# if indexType = category or tag, then you need a selection string
		localUrl = self.buildDir[:]
		baseLevel = 0
		if indexType != 'all':
			localUrl += '/' + indexType + '/' + normalizeString (selection) + '/'
			baseLevel = 2
		teasers = self.getTeasers (indexType, selection)
		###
		nextTeasers = teasers[:]
		content = '<div class="teasers">'
		for nt in nextTeasers:
			content += '<article class="teaser">\n' \
				+ '<h2><a href="' + '{{site.url}}' + nt[5] + '/">' \
				+ nt[1] + '</a></h2>\n' \
				+ '<p>' + nt[2] + '</p>\n' \
				+ '</article>\n'
		content += '</div><!--teasers-->\n'
		# content += self.getPagination (indexType, normalizeString (selection), totalPages, i + 1)
		tempUrl = localUrl
		tempLevel = baseLevel
		# if i > 0:
		# 	tempUrl += '/page/' + str (i + 1)
		# 	tempLevel = baseLevel + 2
		template = 'index.html'
		if indexType in ['category', 'tag']:
			if os.path.isfile (os.path.join (self.confData['style_dir'], 'category.html')):
				template = 'category.html'
			if os.path.isfile (os.path.join (self.confData['style_dir'], 'tag.html')):
				template = 'tag.html'
		self.writeContentPage (tempUrl, content, tempLevel, templateName = template)

	def writePosts (self):
		# write all posts
		sql = "SELECT title, filename, slug FROM tcontent"
		self.dbCur.execute (sql)
		result = self.dbCur.fetchall ()
		for r in result:
			nextFile = r[1]
			nextInfo = self.getMdInfo (nextFile)
			tempContent = nextInfo['content']
			md = markdown.Markdown (extensions = ['meta'])
			html = md.convert (tempContent)
			html = self.processHtml (html)
			content = '<article class="post">\n'
			# content += '<h1>' + nextInfo['title'] + '</h1>\n' # only add this line if md file does not contain '# title'
			topLine = ''
			if self.confData['articles_datestamp'] == 'beginning':
				topLine += '</h1>\n<p class="date">' + getShortDate (nextInfo['date']) + '</p>\n'
			# content += html
			content += html[:]
			if topLine != '':
				content = content.replace ('</h1>\n', topLine)
			if self.confData['articles_datestamp'] == 'end':
				content += '\n<p class="date">' + getShortDate (nextInfo['date']) + '</p>\n'
			content += '\n</article>\n'
			localUrl = os.path.join (self.buildDir, r[2])
			self.writeContentPage (localUrl, content, 1)

	def writeSite (self):
		# TODO: maybe add some logging?
		if self.confData == {}:
			return False
		print ('create memory database')
		self.createMemDatabase ()
		print ('get site content')
		self.getSiteContent ()
		print ('get menus')
		self.getMenus ()
		print ('make target directory')
		# this should not be needed because target dir will be subdired with timestamp
		# if os.path.isdir (outDir) == True:
		# 	shutil.rmtree (outDir)
		os.makedirs (self.buildDir)
		print ('copy dependencies')
		self.copyDependencies ()
		print ('write pages')
		self.writePages ()
		print ('write posts')
		self.writePosts ()
		print ('write category pages') # this also can be done with author pages
		self.dbCur.execute ('SELECT distinct category FROM tcategories')
		result = self.dbCur.fetchall ()
		for r in result:
			self.writePages ('category', r[0])
		print ('write tag pages')
		self.dbCur.execute ('SELECT distinct tag FROM ttags')
		result = self.dbCur.fetchall ()
		for r in result:
			self.writePages ('tag', r[0])
		print ('finished')
		return True

