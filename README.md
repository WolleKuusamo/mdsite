# mdsite

The mdsite script transforms dozens or hundreds of structured markdown files into a static website. The script is written entirely in Python and can be started from the command line.

## Prerequisites

You need python installed on your computer. The script requires standard libraries os, sys, random, sqlite3, unicodedata, re, shutil, markdown, datetime, codecs.

## Pages and posts

You can use mdsite for sites with pages and posts; the posts may belong to multiple categories and keywords (tags).

All posts and pages are stored in a single directory - I will call it *BASE_DIRECTORY* in this description.

Each post and page is stored in a single markdown file with extension ".md"; the filename will be used as a subadress and for internal links and should only contain basic ascii letters and hyphens, for example "berlin-city.md".

## Markdown structure

The posts and pages consist of regular markdown, but they also must have included a structured header like this:

```
---
title: Title of the post or page
author: Firstname Lastname
date: yyyy-mm-dd
status: draft OR publish
categories: category1,category2
tags: tag1,tag 2,tag3
comment: comments here, please
---
# Title of the post or page

content
```

## Configuration file

In the *BASE_DIRECTORY* there has to be a configuration file, named "mdsite.conf" with the following lines:

```
[site]
title = Title of the website
subtitle = Description of the website
target_dir = base directory, where the build is stored
image_dir = directory, where the images are stored - images, you use in pages and posts
style_dir = directory, where the style template is stored

[articles]
selection = publish | draft | all // you can select the content files by status: publish OR draft OR all
datestamp = end | beginning | no // do you want a datestamp on the posts?
teaser = auto | more // how is teaser extracted: auto for first paragraph, more for everything before <!--more--> tag)
image_figures = yes | no // img tags are transformed to <figure> and <figcaption> struct with caption from alt text
em_paragraphs = yes | no // whole paragraphs with <em> will be transformed to <p class="em">
```

## Style template

In the style template directory you store the files, that are used for transforming your markdown files into a website. The directory has to contain at least an "index.html", but it also can contain stylesheets (.css), fonts (.ttf) or header images (.jpg).

### Html file

The most important file in the style directory is the "index.html" template - like this:

```
<!DOCTYPE html>
<html lang="de-DE">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />	
	<title>{{site.title}}</title>
	<link rel="stylesheet" type="text/css" href="{{site.url}}styles/reset.css" />
	<link rel="stylesheet" type="text/css" href="{{site.url}}styles/style.css" />
	<meta name="robots" content="index, follow" />
</head>

<body>

<div class="header">
	<img src="{{site.url}}styles/header.jpg" />
	<div class="overlay">
		<div class="title">
			<h3><a href="{{site.url}}">{{site.title}}</a></h3>
			<p>{{site.description}}</p>
		</div><!--title-->
	</div><!--overlay-->
</div><!--header-->
<div class="menu categories">
{{menu.categories}}
</div><!--menu categories-->

<div class="content">
{{content}}
</div><!--content-->

<div class="menu pages">
{{menu.pages}}
</div><!--menu pages-->

<div class="tagcloud">
{{menu.tags}}
</div> <!--tagcloud-->

</body>
</html>
```

I'll try to explain a few parts of this file.

All parts with double curly brackets will be replaced during the build process.

- {{site.title}} will be filled with \[site\] title information of the configuration file
- {{site.url}} will be used for the site base url (you don't have to care about this)
- {{site.description}} will be filled with \[site\] subtitle information of the configuration file
- {{content}} will be filled with the page / post content
- {{menu.categories}} will be the category menu
- {{menu.pages}} will be the (single) pages menu
- {{menu.tags}} will the the tag cloud

You don't have to use these items in the file. If the script doesn't find (for example) {{menu.tags}}, there will be no tag cloud.

```
<link rel="stylesheet" type="text/css" href="{{site.url}}styles/reset.css" />
<link rel="stylesheet" type="text/css" href="{{site.url}}styles/style.css" />
```

These lines are for the stylesheets; it is recommended to use a reset.css there.

### Stylesheets

If you use the "index.html" template like the example above, your style template directory should contain a file "style.css" with styles for the following tags:

```
* {padding: 0px; margin: 0px;}

body {}

/* header */
div.header {}
div.header img {}
div.header div.overlay {}
div.header div.overlay div.title {}
div.header div.overlay div.title h3 {}
div.header a {}
div.header div.overlay div.title p {}

/* menus top / category and bottom /pages */
div.menu {}
div.menu a {}
div.menu a:hover {}

/* content */
div.content {}
div.teasers {}
@media (max-width: 840px) {}

/* teaser pages */
div.content article.teaser {}
div.content article.teaser h2 {}
div.content article.teaser p {}
div.content article.teaser h2 a {}

/* posts / articles */
div.content h1 {}
div.content h2 {}
div.content p {}
div.content p.strong {}
div.content p.em {}
div.content p.em:before {}
div.content ul li a {}
div.content ul li a::before {}
div.content ul {}
div.content p.date {}
div.content p.date::before {}
div.content a {}
figure {}
figure img {}
figure figcaption {}

/* tagcloud */
div.tagcloud {}
div.tagcloud a {}
div.tagcloud a.fontweight1 {font-size: 10pt;}
div.tagcloud a.fontweight2 {font-size: 13pt;}
div.tagcloud a.fontweight3 {font-size: 17pt;}
div.tagcloud a.fontweight4 {font-size: 22pt;}
div.tagcloud a.fontweight5 {font-size: 28pt;}
div.tagcloud a.tagcolor1 {}
div.tagclouda.tagcolor2 {}
div.tagcloud a.tagcolor3 {}
div.tagcloud a.tagcolor4 {}
```

### Images and fonts

The (header) images should have the extension .jpg, the fonts should be in truetype format with extension .ttf. I don't have to tell you, where you can get excellent fonts, do I?

## Build process

You call the mdsite script from a terminal with *BASE_DIRECTORY* argument - that's all.

The script will produce the following:

- in the target directory (target_dir in configuration file) there will be the "index.html", the entry point for your website
- for every page and post there will be a subdirectory with a "index.html"
- for every category there will be a "index.html" in subdirectory "category/CATEGORY_TITLE" (of course the category title will be transformed to a small letter format with ascii letters, that can be handled by your server)
- for every tag there will be a "index.html" in subdirectory "tag/TAG_TITLE"
- all the images from image_dir (in configuration file) will be copied to subdirectory "images"
- all stylesheets, header images and fonts will be copied to subdirectory "styles"

### Use the build on a web server

On a web server, wenn you click navigation links, the subdirectory of the page / post / category / tag is called and the "index.html" in this subdirectory opens.

### Use the build locally

On your local computer without a webserver you can also click the navigation links, but then your browser (normally) shows an index of the subdirectory, so you'll have to click the "index.html" to see the desired result. This is just useful for testing reasons.


