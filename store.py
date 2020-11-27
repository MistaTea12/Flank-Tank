
from config import *
from client import Button


class Shop:

	def __init__(self):
		self.skins = []
		self.buttons = []
		self.addSkins()
		self.button()

	def addSkins(self):
		for i in range(2):
			self.skins.append('sprites/skins/skin{}.png'.format(i))

	def button(self):
		x = 75
		i = 1
		for skin in self.skins:
			self.buttons.append(Button(str(i), SCREENWIDTH / 3 + x, SCREENHEIGHT / 2, 50, 50, blue))
			x += 100
			i += 1

	def buy(self):
		pass

	def currency(self):
		pass

	def changeSkin(self):
		pass

	def draw(self):
		for button in self.buttons:
			if button.click:
				print("BOUGHT")
			button.draw()

	def update(self):
		self.draw()
