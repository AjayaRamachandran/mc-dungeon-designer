from PIL import Image
import io
import pygame
import os
import random
from math import *
import time
from tkinter.filedialog import asksaveasfile

###### SETUP ######

hdRatio = 1
pygame.init()
elementList = []
mouseTask = False

###### CLASSES ######

class GUI:
    def __init__(self, x, y):
        self.x = x * hdRatio
        self.y = y * hdRatio
        elementList.append(self)

    def moveTo(self, x, y):
        self.x = x * hdRatio
        self.y = y * hdRatio

class Title(GUI):
    def __init__(self, x, y, text, textColor, fontSize=20, fontOverride=None):
        super().__init__(x, y)
        self.text = text
        self.textColor = textColor
        self.fontSize = int(fontSize * hdRatio)
        if fontOverride:
            self.font = pygame.font.Font(fontOverride, fontSize)
        else:
            self.font = pygame.font.Font('Minecraftia-Regular.ttf', fontSize)
  
    def setTitle(self, newTitle):
        self.text = newTitle
    
    def draw(self, screen):
        textSurface = self.font.render(self.text, True, self.textColor)
        textRect = textSurface.get_rect(center=(self.x, self.y))
        screen.blit(textSurface, textRect)

class Window(GUI):
    def __init__(self, name, x, y, width, height, cornerRadius, color, scale):
        super().__init__(x, y)
        self.name = name
        self.rect = pygame.Rect(x-width*scale/2, y-height*scale/2, width*scale, height*scale)
        self.color = color
        self.width = int(width * hdRatio)
        self.height = int(height * hdRatio)
        self.scale = scale
        self.cornerRadius = cornerRadius

    def draw(self, screen):
        pygame.draw.rect(
            screen, self.color, self.rect, border_radius=self.cornerRadius
        )

class Button(GUI):
    def __init__(self, name, x, y, width, height, cornerRadius, color, text, scale, fontSize=20, fontOverride=None):
        super().__init__(x, y)
        self.name = name
        self.rect = pygame.Rect((x-width*scale/2)*hdRatio, (y-height*scale/2)*hdRatio, width*scale*hdRatio, height*scale*hdRatio)
        self.color = color
        self.text = text
        self.width = int(width * hdRatio)
        self.height = int(height * hdRatio)
        self.scale = scale
        self.cornerRadius = cornerRadius
        self.textColor = (255, 255, 255)
        self.fontSize = int(fontSize * hdRatio)
        if fontOverride:
            self.font = pygame.font.Font(fontOverride, fontSize)
        else:
            self.font = pygame.font.Font('Minecraftia-Regular.ttf', fontSize)

    def draw(self, screen, mode=0):
        buttonColor = self.color
        if self.rect.collidepoint(pygame.mouse.get_pos()) or mode == 1:
            buttonColor = (max(0, self.color[0]-30), max(0, self.color[1]-30), max(0, self.color[2]-30))

        pygame.draw.rect(screen, buttonColor, self.rect, border_radius=self.cornerRadius)

        shadowColor = [self.color[0]*0.6,self.color[1]*0.6,self.color[2]*0.6]
        shadowSurface = self.font.render(self.text, True, shadowColor)
        textSurface = self.font.render(self.text, True, self.textColor)

        shadowRect = shadowSurface.get_rect(center=[self.rect.center[0], self.rect.center[1]+self.fontSize/30])
        textRect = textSurface.get_rect(center=self.rect.center)

        screen.blit(shadowSurface, shadowRect)
        screen.blit(textSurface, textRect)

    def isClicked(self):
        global mouseTask
        status = (self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == 1) and not mouseTask
        if status:
            mouseTask = True
            print(self, ' clicked')
        return status

class Textbox(GUI):
    def __init__(self, name, x, y, width, height, exampleText, scale, color=(255, 255, 255), fontSize=20, textColor=(0, 0, 0), characterLimit=None):
        super().__init__(x, y)
        self.name = name
        self.rect = pygame.Rect((x-width*scale/2)*hdRatio, (y-height*scale/2)*hdRatio, width*scale*hdRatio, height*scale*hdRatio)
        self.selected = False
        self.color = color
        self.exampleText = exampleText
        self.text = ""
        self.width = int(width * hdRatio)
        self.height = int(height * hdRatio)
        self.scale = scale
        self.textColor = textColor
        self.fontSize = int(fontSize * hdRatio)
        self.font = pygame.font.Font("fonts/Inter-Regular.ttf", self.fontSize)
        self.characterlimit = characterLimit

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        if self.selected:
            pygame.draw.rect(screen, self.textColor, self.rect, width=4, border_radius=5)
            textSurface = self.font.render(self.text, True, self.textColor)
            if int(time.time()) % 2 == 0:
                textSurface = self.font.render(self.text + "|", True, self.textColor)
        else:
            pygame.draw.rect(screen, self.textColor, self.rect, width=2, border_radius=5)
            if self.text == "":
                fadedTextColor = [int((self.color[value] * 2 + self.textColor[value] * 1) / 3) for value in range(len(self.color))]
                textSurface = self.font.render(self.exampleText, True, fadedTextColor)
            else:
                textSurface = self.font.render(self.text, True, self.textColor)
        textRect = textSurface.get_rect(center=self.rect.center)
        screen.blit(textSurface, textRect)

    def isClicked(self):
        return self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == 1

    def isUnclicked(self):
        return not self.rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0] == 1

    def dynamicInteraction(self, pressedKey):
        if self.isClicked():
            self.selected = True
        if self.isUnclicked():
            self.selected = False
        if self.selected:
            if pressedKey == "keyBKSPC":
                self.text = self.text[:-1]
            else:
                if self.characterlimit != None:
                    if len(self.text) < self.characterlimit:
                        self.text = self.text + pressedKey
                else:
                    self.text = self.text + pressedKey

class Scrollable(GUI):
    def __init__(self, data, name, x, y, width, height, subHeight, cornerRadius, color, text, scale, fontSize=20):
        super().__init__(x, y)
        self.name = name
        self.rect = pygame.Rect((x-width*scale/2)*hdRatio, (y-height*scale/2)*hdRatio, width*scale*hdRatio, height*scale*hdRatio)
        self.color = color
        self.text = text
        self.width = int(width * hdRatio)
        self.height = int(height * hdRatio)
        self.scale = scale
        self.cornerRadius = cornerRadius
        self.textColor = (255, 255, 255)
        self.fontSize = int(fontSize * hdRatio)
        self.font = pygame.font.Font("fonts/Inter-Regular.ttf", self.fontSize)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=self.cornerRadius)
