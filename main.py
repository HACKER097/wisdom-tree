import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import curses
from curses import textpad
from pygame import mixer
import time
import random
import pickle
import glob

mixer.init()


def replaceNth(s, source, target, n): #code from stack overflow, replaces nth occurence of an item.
    inds = [i for i in range(len(s) - len(source)+1) if s[i:i+len(source)]==source]
    if len(inds) < n:
        return  s# or maybe raise an error
    s = list(s)  # can't assign to string slices. So, let's listify
    s[inds[n-1]:inds[n-1]+len(source)] = target  # do n-1 because we start from the first occurrence of the string, not the 0-th
    return ''.join(s)

def addtext(x, y, text, anilen, stdscr, color_pair): #adds and animates text in the center

	text= replaceNth(text[:int(anilen)], " ", "#", 8) # aads "#" after the 7th word to split line
	text=text.split("#")                              #splits text into 2 list
	for i in range(len(text)):
		stdscr.addstr(y+i,int(x-len(text[i])/2), str(text[i]), curses.color_pair(color_pair)) #displays the list in 2 lines

def getrandomline(file): #returns random quote
	lines = open(file).read().splitlines()
	myline =random.choice(lines)
	return myline

def getqt(): #returns random quote
	return getrandomline('qts.txt')

def printart(stdscr, file, x, y, color_pair): # prints line one by one to display text art, also in the middle
	with open(file,"r",encoding="utf8") as f:
	    lines = f.readlines()

	    for i in range(len(lines)):
	    	stdscr.addstr(y+i-len(lines), x-int(len(max(lines, key=len))/2), lines[i], curses.color_pair(color_pair))

def key_events(stdscr, tree1):
	key = stdscr.getch()

	if key == curses.KEY_UP:
		tree1.age +=1

	if key == curses.KEY_DOWN:
		tree1.age -=1

	if key == ord("q"):
		treedata = open('res/treedata', 'wb')
		pickle.dump(tree1.age, treedata, protocol=None )
		treedata.close()
		
		exit()

	if key == curses.KEY_RIGHT:
		tree1.music_list_num +=1
		if tree1.music_list_num > len(tree1.music_list)-1:
			tree1.music_list_num = len(tree1.music_list)-1
		music = mixer.music.load(tree1.music_list[tree1.music_list_num])
		mixer.music.play(-1)
		tree1.show_music = True

	if key == curses.KEY_LEFT:
		tree1.music_list_num -=1
		if tree1.music_list_num < 0:
			tree1.music_list_num = 0
		music = mixer.music.load(tree1.music_list[tree1.music_list_num])
		mixer.music.play(-1)
		tree1.show_music = True

	if key == ord(" "):
		mixer.music.pause()
		tree1.pause = True




class tree:
	def __init__(self, stdscr, age):
		self.stdscr =stdscr
		self.age = age
		self.show_music = False
		self.music_list = glob.glob("res/*.ogg")
		self.music_list_num = 0
		self.music = mixer.music.load(self.music_list[self.music_list_num])
		self.pause = False


	def display(self, maxx, maxy):
		if self.age >= 1 and self.age < 5:
			self.artfile = 'res/p1.txt'
		if self.age >= 5 and self.age < 10:
			self.artfile = 'res/p2.txt'
		if self.age >= 10 and self.age < 20:
			self.artfile = 'res/p3.txt'
		if self.age >= 20 and self.age < 30:
			self.artfile = 'res/p4.txt'
		if self.age >= 30 and self.age < 40:
			self.artfile = 'res/p5.txt'
		if self.age >= 40 and self.age < 60:
			self.artfile = 'res/p6.txt'
		if self.age >= 70 and self.age < 120:
			self.artfile = 'res/p7.txt'
		if self.age >= 120 and self.age < 200:
			self.artfile = 'res/p8.txt'
		if self.age >= 200:
			self.artfile = 'res/p9.txt'

		printart(self.stdscr, self.artfile, int(maxx/2), int(maxy*3/4), 1)
		addtext(int(maxx/2), int(maxy*3/4),"age: " +str(int(self.age))+ " " , -1, self.stdscr, 3)

		#RAIN

	def rain(self, maxx, maxy, seconds, intensity, speed, char, color_pair):
		random.seed(int(seconds/speed)) # this keeps the seed same for some time, so rains looks like its going slowly

		#printart(self.stdscr, 'res/rain1.txt', int(maxx/2), int(maxy*3/4), 4)
		for i in range(intensity):
			ry=random.randrange(int(maxy*1/4), int(maxy*3/4))
			rx=random.randrange(int(maxx/3), int(maxx*2/3))
			self.stdscr.addstr(ry, rx, char, curses.color_pair(color_pair))

		random.seed()




def main():
	run = True
	stdscr = curses.initscr()
	stdscr.nodelay(True)
	stdscr.keypad(True)
	curses.curs_set(0)
	curses.start_color()
	curses.noecho()
	curses.cbreak()

	curses.init_pair(1, 113, 0) #passive selected text inner, outer
	curses.init_pair(2, 85, 0)  #timer color inner, outer
	curses.init_pair(3, 3, 0) #active selected inner, outer
	curses.init_pair(4, 51, 0)  #border coloer inner,outer
	curses.init_pair(5, 15, 0)
	curses.init_pair(6, 1, 0)


	tree_grow = mixer.Sound('res/growth.waw')

	seconds = 1
	anilen=1
	anispeed=0.2

	music_volume=0
	music_volume_max=1

	quote = getqt()
	tree_grow.play()

	tree1 = tree(stdscr, 1)
	mixer.music.play(-1)

	treedata_in = open('res/treedata', 'rb')
	tree1.age = pickle.load(treedata_in)





	try:
		while run:

			try:
				stdscr.erase()
				maxy,maxx = stdscr.getmaxyx()


				addtext(int(maxx/2), int(maxy*5/6), quote, anilen, stdscr, 2)
				anilen+=anispeed
				if anilen>150:
					anilen=150

				if seconds%3000 == 0: #show another quote every 5 min, and grow tree
					quote = getqt()
					tree1.age+=1
					anilen = 1
					tree_grow.play()


				if seconds%200 == 0: #show another quote every 5 min, and grow tree
					tree1.show_music = False

				if tree1.show_music:
					showtext = "Playing: " + tree1.music_list[tree1.music_list_num].split("/")[1]
					stdscr.addstr(int(maxy/10), int(maxx/2-len(showtext)/2), showtext, curses.A_BOLD)


				music_volume+=0.001#fade in music
				if music_volume > music_volume_max:
					music_volume = music_volume_max

				tree1.display(maxx, maxy)

				tree1.rain(maxx, maxy, seconds, 30, 30, "/",  4)

				mixer.music.set_volume(music_volume)

				key_events(stdscr, tree1)

				while tree1.pause:
					stdscr.erase()
					stdscr.addstr(int(maxy*3/5), int(maxx/2-len("PAUSED")/2), "PAUSED", curses.A_BOLD)
					key = stdscr.getch()
					if key == ord(" "):
						tree1.pause = False
						mixer.music.unpause()
						stdscr.refresh()
					if key == ord("q"):
						exit()


				time.sleep(0.01)
				seconds += 1

			except KeyboardInterrupt:

				try:
					stdscr.erase()
					stdscr.addstr(int(maxy*3/5), int(maxx/2-len("PRESS 'q' TO EXIT")/2), "PRESS 'q' TO EXIT", curses.A_BOLD)
					stdscr.refresh()
					time.sleep(1)
				except KeyboardInterrupt:
					pass


				
			stdscr.refresh()


	finally:
		curses.echo()
		curses.nocbreak()
		curses.curs_set(1)
		stdscr.keypad(False)
		stdscr.nodelay(False)
		curses.endwin()

main()
