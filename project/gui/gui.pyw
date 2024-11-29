import pygame
import math
import pygame.gfxdraw
import sys

import serial

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 640

def rotate(point, x, y, angle):
	x0 = point[0]
	y0 = point[1]
	c = math.cos(math.radians(angle))
	s = math.sin(math.radians(angle))

	point[0] = (x0-x)*c - (y0-y)*s + x
	point[1] = (x0-x)*s + (y0-y)*c + y

def arc(surface, x, y, r, w, start, stop, color):
	points_outer = []
	points_inner = []
	parts = 360

	angle = abs(stop - start)/parts
	if start > stop:
		angle = (360 - abs(stop-start))/parts
	phi = start
	for i in range(parts+1):
		x0 = x+r*math.cos(math.radians(i*angle + phi))
		y0 = y-r*math.sin(math.radians(i*angle + phi))
		points_inner.append((x0, y0))
		x1 = x+(r-w)*math.cos(math.radians(i*angle + phi))
		y1 = y-(r-w)*math.sin(math.radians(i*angle + phi))
		points_outer.append((x1, y1))

	points_outer.reverse()
	points = points_inner + points_outer
	pygame.gfxdraw.filled_polygon(surface, points, color)
	#pygame.gfxdraw.aapolygon(surface, points, color)

def arcGradient(surface, x, y, radius, w, start, stop, color1, color2):
	angle = abs(stop - start)
	if start > stop:
		angle = (360 - abs(stop-start))

	for i in range(0, angle, 1):
		r = i/angle * color2[0] + (1 - i/angle) * color1[0]
		g = i/angle * color2[1] + (1 - i/angle) * color1[1]
		b = i/angle * color2[2] + (1 - i/angle) * color1[2]
		a = (i/angle) * 160 + 20
		#arc(surface, x, y, radius, w, start, stop - i, (r, g, b))
		arc(surface, x, y, radius, w, stop - (i+1), stop -i, (r, g, b, a))

def numberScale(surface, x, y, radius, w, start, stop, maximum, color, font):
	angle = abs(stop - start)
	if start > stop:
		angle = (360 - abs(stop-start))
	point1 = [x-radius, y]
	point2 = [x-radius+15, y]
	point3 = [x-radius+30, y]
	indicator_point = [x-radius+65, y]
	rotate(point1, x, y, -30)
	rotate(point2, x, y, -30)
	rotate(point3, x, y, -30)
	rotate(indicator_point, x, y, -30)

	numberOfindicators = round(maximum)
	deg = angle/numberOfindicators

	indicators = []
	for i in range(0, numberOfindicators+1, 10):
		indicators.append(font.render(str(i), 1, (255, 255, 255)))

	for i in range(0, numberOfindicators+1, 1):
		if i % 10 == 0:
			pygame.draw.line(surface, (255, 255, 255), (point1[0], point1[1]), (point3[0], point3[1]), 3)
			surface.blit(indicators[round(i/10)], (indicator_point[0] - indicators[round(i/10)].get_width()/2, indicator_point[1] - indicators[round(i/10)].get_height()/2))
		else:
			pygame.draw.aaline(surface, (255, 255, 255), (point1[0], point1[1]), (point2[0], point2[1]))

		rotate(point1, x, y, deg)
		rotate(point2, x, y, deg)
		rotate(point3, x, y, deg)
		rotate(indicator_point, x, y, deg)

def radialGradient(surface, x, y, radius, color1, color2):
	for i in range(radius, 0, -1):
		r = (radius - i)/radius * color1[0] + (1 - ((radius - i)/radius)) * color2[0]
		g = (radius - i)/radius * color1[1] + (1 - ((radius - i)/radius)) * color2[1]
		b = (radius - i)/radius * color1[2] + (1 - ((radius - i)/radius)) * color2[2]
		pygame.gfxdraw.filled_circle(surface, round(x), round(y), i, (r, g, b))

def arrow(surface, x, y, length, angle):
	p1 = [x, y-length]
	p2 = [x+8, y+40]
	p3 = [x-8, y+40]

	rotate(p1, x, y, angle - 120)
	rotate(p2, x, y, angle - 120)
	rotate(p3, x, y, angle - 120)
	points = (p1, p2, p3) 

	pygame.gfxdraw.filled_polygon(surface, points, (255, 0, 0))
	pygame.gfxdraw.aapolygon(surface, points, (255, 0, 0))
	pygame.draw.circle(surface, (255, 0, 0), (x, y), 12)
	pygame.draw.circle(surface, (0, 0, 0), (x, y), 10)
	radialGradient(surface, x, y, 10, (57, 161, 137), (0, 0, 0))


def main():
	# Initialize pygame specific elements
	pygame.init()

	screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
	meterBody = pygame.Surface([SCREEN_WIDTH, SCREEN_HEIGHT])
	arcBody = pygame.Surface([SCREEN_WIDTH, SCREEN_HEIGHT])

	# Load custom fonts
	pygame.display.set_caption("Speed indicator")
	currentSpeedFont = pygame.font.Font("digital-7.monoitalic.ttf", 60)
	indicatorFont = pygame.font.Font("digital-7.monoitalic.ttf", 30)

	# Initial states
	angle = 0
	speed = 0
	maxSpeed = 4096/16 	#256
	arrow_len = 260

	arcBody.fill((0, 0, 0, 124))
	# Blit static images for efficiency
	meterBody.fill((55, 55, 55))
	radialGradient(meterBody, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 310, (57, 161, 137), (0, 0, 0))
	arcGradient(meterBody, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 310, 40, 330, 210, (0, 255, 0), (255, 0, 0))
	numberScale(arcBody, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, 310, 40, 330, 210, maxSpeed, (255, 255, 255), indicatorFont)

	meterBody.blit(arcBody, (0, 0))

	# Initialize STM32 UART COM port
	ser = serial.Serial("COM9", 115200, timeout=1)
	print(ser.name)

	pot = 0
	prev = 0
	adc_val = 0	
	run = True
	while run:
		screen.fill((55, 55, 55))
		
		pot = ser.readline()[:-1]
		adc_val = pot.decode("utf-8").replace('\0', "")
		adc_val = -1 if adc_val == '' else int(adc_val)
		#print(adc_val)

		if adc_val >= 0:
			adc_val =  4096 - adc_val
			angle = 240*(speed/maxSpeed) if (speed <= maxSpeed) else 240
			speed = 256 * (adc_val/4096)

		screen.blit(meterBody, (0, 0))
		arrow(screen, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, arrow_len, angle)

		speedDisplay = currentSpeedFont.render(str(round(speed)), 1, (255, 255, 255))
		speedDisplay_shadow = currentSpeedFont.render(str(round(speed)), 1, (0, 0, 0))

		screen.blit(speedDisplay_shadow, ((SCREEN_WIDTH/2 - speedDisplay.get_width()/2) + 5, (SCREEN_HEIGHT/2 + arrow_len/2) + 5))
		screen.blit(speedDisplay, (SCREEN_WIDTH/2 - speedDisplay.get_width()/2, SCREEN_HEIGHT/2 + arrow_len/2))
		
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

		pygame.display.flip()
		
	ser.close()
	pygame.quit()

if __name__ == '__main__':
	main()