#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os, re, io
import requests, queue, threading
from PIL import Image

# Using google script seeks better quality copies of given images.
# Parses given dir with images, seeks similar with google and if there is a similar enough pic with bigger width, script replaces/adds it.

# Requires installed findimagedupes and imagemagick

# Uploader was copied from Rast1234
# https://github.com/Rast1234/imagesearch/blob/master/imagesearch.py

##################################################

# number of threads; google might block your IP and redirect to captcha-checks if thread_count exceeds 5 or so
thread_count = 3
# timeout for connection to image's url in sec.
dtimeout = 10
# number of images to get from google; google sorts them by size, so 5 is enough
depth = 10
# similarity for findimagedupes; in percentage
similarity = 98
# True, if you want to replace old images with found ones
# otherwise found images will be named [filename]_new.[extension] and placed alongside
move = 1
# dir with images
imdir = os.path.expanduser('~/d/pic/')
# processed images will be moved to this dir; slash at the end
imdir_done = os.path.expanduser('~/d/pic2/')
# dir for temporary images; will be created with mkdir -p; slash at the end
# !!! It will be removed at the end of execution
tmpdir = '/tmp/dev/gimgs/'

def fs (line):
	import subprocess
	PIPE = subprocess.PIPE
	p = subprocess.Popen(line, shell=isinstance('', str),bufsize=-1, stdin=PIPE, stdout=PIPE,stderr=subprocess.STDOUT, close_fds=True)

	return p.stdout.read().decode('utf-8').strip()

def tow(filename, data):
	idop = open(filename, 'w')
	idop.write(data)
	idop.close()

def towb(filename, data):
	idop = open(filename, 'wb')
	#idop.write(bytes(data, 'UTF-8'))
	idop.write(data)
	idop.close()

def worker(dir_num):
	cur_tmpdir = tmpdir + str(dir_num) + '/'
	fs('mkdir -p "' + cur_tmpdir + '"')

	while 1:
		try:
			print(str(aicount) + '/' + str(q.qsize()) + '/' + str(threading.activeCount() - 1))
			image = q.get(False)

			######################################

			# required input name and file name
			if not os.path.isfile(image):
				print(image)
				continue

			fileDict = {'encoded_image': (image, open(image, 'rb'))}

			# submit file via multipart/form-data, other fields not required
			r = requests.post(postUrl, files=fileDict, cookies=grail.cookies, headers=headers)

			# get the last redirect url, thank you Wireshark!
			result = r.history[-1].url
			#print(result)

			########################################

			# getting page with link to google-images
			dd = requests.get(result, headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'}).text

			#tow('ddc' + str(dir_num) + '.htm', dd)

			ll = re.findall('<span class="gl"><a href="(.*?)">Все размеры</a>', dd)
			#print(ll)
			
			try:
				ll = ll[0].replace('&amp;', '&')
			except:
				if 'Изображения других размеров не найдены' in dd:
					fs('mv "' + image + '" "' + image.replace(imdir, imdir_done) + '"')
					continue
				elif 'This page appears when Google automatically detects requests coming from your computer network which appear to be in violation of the' in dd:
					print('CAPTCHA!!! exiting...')
					break
				else:
					#tow('dd' + str(dir_num) + '.htm', dd)
					print('pushing image back')
					q.put(image)

			# getting page with links to images
			dd = requests.get('https://www.google.ru' + ll, headers={'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.111 Safari/537.36'}).text
			#tow('ddc' + str(dir_num) + '.htm', dd)
			
			links = re.findall('"ou":"(.*?)"', dd)
			#print(links)

			# download images
			cur_n = 1
			for url in links:
				try:
					dd = requests.get(url, timeout = dtimeout).content
					Image.open(io.BytesIO(dd)).verify()

					towb(cur_tmpdir + url.split('/')[-1], dd)

					if depth > cur_n:
						cur_n += 1
					else:
						break
				except:
					pass

			best_size = 0

			for img in fs('ls ' + cur_tmpdir).split('\n'):
				s_image = fs('identify -format "%w" "' + image + '"')
				#print(s_image)
				dupe = fs('findimagedupes -q -t ' + str(similarity) + '% -i \'VIEW(){ identify -format "%w" "$1"; echo ---$1; identify -format "%w" "$2"; echo ---$2; }\' -- "' + image + '" "' + cur_tmpdir + img + '"').replace(s_image + '---' + image, '').strip().split('---')

				if len(dupe) == 2:
					if int(dupe[0]) > best_size:
						best_size = int(dupe[0])
						best_image = dupe[1]

			if best_size > int(s_image)*1.05:
				print(s_image + ' -> ' + str(best_size) + ' ' + image.replace(imdir, ''))

				if move:
					if not os.path.isfile(image.replace(imdir, imdir_done)):
						fs('mv "' + best_image + '" "' + image.replace(imdir, imdir_done) + '"')
						fs('rm "' + image + '"')
				else:
					if not os.path.isfile(image.replace(imdir, imdir_done).rsplit('.',1)[0] + '_new.' + image.rsplit('.',1)[1]):
						fs('mv "' + best_image + '" "' + image.replace(imdir, imdir_done).rsplit('.',1)[0] + '_new.' + image.rsplit('.',1)[1] + '"')
						fs('mv "' + image + '" "' + image.replace(imdir, imdir_done) + '"')
			else:
				if not os.path.isfile(image.replace(imdir, imdir_done)):
					fs('mv "' + image + '" "' + image.replace(imdir, imdir_done) + '"')

			fs('rm ' + cur_tmpdir + '*')

		except queue.Empty:
			fs('rmdir ' + cur_tmpdir)
			break
		except:
			print('        Some Error!!!')


############################
url = "https://www.google.ru/imghp"
postUrl = "https://www.google.ru/searchbyimage/upload"

headers = {'User-agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) \\'
								'Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1',
		  'origin': 'https://www.google.ru',
		  'referer': 'https://www.google.ru/imghp'
	}

# crusade for cookies
grail = requests.get(url, headers = headers)
############################

fs('mkdir -p "' + imdir_done + '"')

q = queue.Queue()
for image in fs('ls "' + imdir + '"').split('\n'):
	image = imdir + image
	q.put(image)

aicount = q.qsize()

for i in range(thread_count):
	t = threading.Thread(target=worker, args = (i,))
	t.start()

fs('rmdir ' + tmpdir)
