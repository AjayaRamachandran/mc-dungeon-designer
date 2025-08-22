###### IMPORT ######

import pygame
import random
import time
from math import *
import numpy as np
import copy
import bisect
import pickle as pkl
from tkinter.filedialog import asksaveasfile
from tkinter.filedialog import askopenfilename

import gui
import gen

###### SETUP ######

windowSize = (1440, 900)

pygame.display.set_caption("Dungeon Designer") # Sets title of window
screen = pygame.display.set_mode(windowSize) # Sets the dimensions of the window to the windowSize
floorSurface = pygame.Surface(windowSize, pygame.SRCALPHA)
wallsSurface = pygame.Surface(windowSize, pygame.SRCALPHA)

font = pygame.font.Font("Minecraftia-Regular.ttf", 12)

mode = "skills"
pointSelected = [0, 0]
selector = "edit"
initialReverse = False
totalCurve = []
version = "bezier"
pressingVersionSwitch = False
pressingExport = False

POINTSPACING = 0.5 / 144
SAMPLINGRESOLUTION = 500

###### INITIALIZE ######

fps = 60
clock = pygame.time.Clock()

appTitle = gui.Title(
    x=1275,
    y=40,
    text='Dungeon Creator',
    textColor=[255, 255, 255],
    fontSize=24,
    fontOverride='Minercraftory.ttf'
)

addFloorButton = gui.Button(
    name="add_floor_button",
    width=300,
    height=40,
    cornerRadius = 8,
    color=[100, 100, 100],
    text="Add Floor",
    x=1275,
    y=120,
    scale=1,
    fontSize=20
)

editWalls = gui.Button(
    name="edit_walls_button",
    width=140,
    height=40,
    cornerRadius = 8,
    color=[100, 100, 100],
    text="Walls",
    x=1195,
    y=600,
    scale=1,
    fontSize=20
)

editFloor = gui.Button(
    name="edit_floor_button",
    width=140,
    height=40,
    cornerRadius = 8,
    color=[100, 100, 100],
    text="Floor",
    x=1355,
    y=600,
    scale=1,
    fontSize=20
)

drawButton = gui.Button(
    name="draw_button",
    width=140,
    height=40,
    cornerRadius = 8,
    color=[100, 100, 100],
    text="Draw",
    x=1195,
    y=660,
    scale=1,
    fontSize=20
)

eraseButton = gui.Button(
    name="erase_button",
    width=140,
    height=40,
    cornerRadius = 8,
    color=[100, 100, 100],
    text="Erase",
    x=1355,
    y=660,
    scale=1,
    fontSize=20
)

exportButton = gui.Button(
    name="export_button",
    width=300,
    height=40,
    cornerRadius = 8,
    color=[70, 110, 70],
    text="Export .schem",
    x=1275,
    y=860,
    scale=1,
    fontSize=20
)



###### FUNCTIONS ######

def dist(point1, point2): # calculates the distance between two points
    return sqrt((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)

def dir(point1, point2): # calculates the direction between one point and another
    return atan2((point2[1] - point1[1]), (point2[0] - point1[0]))

def screenSpaceToPixels(coords):
    return (coords[0] // gridScalePx, coords[1] // gridScalePx)


floors = [{ 'name' : 'Floor 1' , 'cells' : {}}]
selectedFloor = 0

floorButtons = []

mode = 'walls'
brush = 'draw'

gridWidth = 60
gridHeight = 60
gridScalePx = 15

###### MAINLOOP ######

running = True # Runs the game loop

while running:
    screen.fill((25,25,25))
    floorSurface.fill((0, 0, 0, 0))
    wallsSurface.fill((0, 0, 0, 0))

    if pygame.mouse.get_pos()[0] < gridWidth * gridScalePx and pygame.mouse.get_pressed()[0]:
        if brush == 'draw':
            floors[selectedFloor]['cells'][*screenSpaceToPixels(pygame.mouse.get_pos()), mode] = True
        if brush == 'erase':
            try:
                del floors[selectedFloor]['cells'][*screenSpaceToPixels(pygame.mouse.get_pos()), mode]
            except Exception as e:
                #print(e)
                None
    
    for cell, bool in floors[selectedFloor]['cells'].items():
        # print(cell, bool)
        coords = (cell[0], cell[1])
        typ = cell[2]

        pygame.draw.rect(floorSurface if typ == 'floor' else wallsSurface, [255, 255, 255, (typ == mode)*200 + 55], [coords[0] * gridScalePx, coords[1] * gridScalePx, gridScalePx, gridScalePx])

    screen.blit(floorSurface, [0, 0])
    screen.blit(wallsSurface, [0, 0])

    # draws all the GUI elements to the screen using the GUI library
    appTitle.draw(screen)
    addFloorButton.draw(screen)
    editWalls.draw(screen, mode=int(mode=='walls'))
    editFloor.draw(screen, mode=int(mode=='floor'))

    drawButton.draw(screen, mode=int(brush=='draw'))
    eraseButton.draw(screen, mode=int(brush=='erase'))

    exportButton.draw(screen)

    # detects if any GUI elements are interacted with, using GUI library
    if addFloorButton.isClicked():
        floors.append({ 'name' : f'Floor {len(floors)}' , 'cells' : {}})
    if editWalls.isClicked():
        mode = 'walls'
    if editFloor.isClicked():
        mode = 'floor'
    if drawButton.isClicked():
        brush = 'draw'
    if eraseButton.isClicked():
        brush = 'erase'
    if exportButton.isClicked():
        gen.createSchematic(floors)

    i = 0
    floorButtons = []
    for f in floors:
        i += 1
        floorButtons.append(gui.Button(
            name=f"floor_{i}",
            width=300,
            height=30,
            cornerRadius = 8,
            color=[80, 80, 80],
            text=f"Floor {i}",
            x=1275,
            y=i*35 + 125,
            scale=1,
            fontSize=17
        ))
    
    i = -1
    for floorButton in floorButtons:
        i += 1
        floorButton.draw(screen, mode=int(i == selectedFloor))
        if floorButton.isClicked():
            selectedFloor = i
    
    for x in range(gridWidth + 1):
        pygame.draw.line(screen, (40, 40, 40), [x * gridScalePx, 0], [x * gridScalePx, gridHeight * gridScalePx])
    for y in range(gridHeight + 1):
        pygame.draw.line(screen, (40, 40, 40), [0, y * gridScalePx], [gridWidth * gridScalePx, y * gridScalePx])


    for event in pygame.event.get(): # checks if program is quit, if so stops the code
        if event.type == pygame.QUIT:
            running = False

    if not pygame.mouse.get_pressed()[0]:
        gui.mouseTask = False

    # runs framerate wait time
    clock.tick(fps)
    # update the screen
    pygame.display.update()

# quit Pygame
pygame.quit()