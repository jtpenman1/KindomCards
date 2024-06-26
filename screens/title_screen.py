import pygame
import pygame_gui
import random, os
from pygame_gui.elements import UIButton, UILabel, UIWindow
from objects.screenstate import ScreenState
from objects.scheme import Scheme

from webcam import WebcamCapture

cam = WebcamCapture(show_window=True)
Colors = Scheme()

class titleScreen:
    def __init__(self, manager, window, state):
        self.state = state
        self.width = manager.window_resolution[0]
        self.height = manager.window_resolution[1]
        self.clock = pygame.time.Clock()
        self.window = window
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(Colors.window_bg)

        self.header = None
        self.quit_button = None
        self.load_button = None
        self.play_button = None
        self.config = None

        self.animate = True # animation flag

        # animation calculations
        self.rotation_angle = 0.0 # animation rotation angle

        suits = [
            "assets/cards/clubs",
            "assets/cards/diamonds",
            "assets/cards/hearts",
            "assets/cards/spades"
        ]
        card_filenames = []
        num_cards = 10

        for folder in suits:
            images = [f for f in os.listdir(folder) if f.endswith('.png')]
            image_paths = [os.path.join(folder, image_file) for image_file in images]
            card_filenames.extend(image_paths)
        if len(card_filenames) >= num_cards:
            card_filenames = random.sample(card_filenames, num_cards)
        
        #print(card_filenames)

        self.cards = []
        for filename in card_filenames:
            image = pygame.image.load(filename)
            # apply scale after to improve quality
            card_height = self.height * 0.236
            card_width = card_height * 0.714
            image_scaled = pygame.transform.smoothscale(image, (card_width, card_height))
            self.cards.append(image_scaled)
        
        self.circle_radius = self.width//3.5
        self.circle_center = (self.width//2, self.height)
        self.circle_surface = pygame.Surface(((self.height*1.25), (self.height*1.25)))
        self.angle_increment = 360 // num_cards

        self.cards_cache = {}
        for i in range(num_cards):
            current_card = self.cards[i]
            angle = i * self.angle_increment
            tilt_angle = -angle
            rotated_card = pygame.transform.rotozoom(current_card, angle=tilt_angle - 90, scale=1)
            self.cards_cache[angle] = rotated_card

    def load(self, manager, state):
        global debugswitch
        debugswitch = False
        self.state = state
        header_rect = pygame.Rect(0, self.height*.15, self.width, 150)

        self.header = UILabel(relative_rect=header_rect,
                              text='Kingdom Cards',
                              manager=manager,
                              object_id='header',
                              anchors={
                                  'centerx': 'centerx',
                                  'top': 'top'
                              })
        
        b_height = self.height*0.05
        b_width = self.width*0.09
        b_pad = self.height*0.063
        b_pos = ( (self.circle_surface.get_height()) - (self.height*2.236) )/8

        quit_button_rect = pygame.Rect(0, b_pos, b_width, b_height)
        load_button_rect = pygame.Rect(0, -b_pad, b_width, b_height)
        play_button_rect = pygame.Rect(0, -b_pad, b_width, b_height)

        self.quit_button = UIButton(relative_rect=quit_button_rect,
                                                 text='Quit',
                                                 manager=manager,
                                                 anchors={
                                                     'centerx': 'centerx',
                                                     'bottom': 'bottom'
                                                 })

        self.load_button = UIButton(relative_rect=load_button_rect,
                                                 text='Load Game',
                                                 manager=manager,
                                                 anchors={
                                                     'centerx': 'centerx',
                                                     'bottom': 'bottom',
                                                     'bottom_target': self.quit_button
                                                 })
        
        self.play_button = UIButton(relative_rect=play_button_rect,
                                                 text='New Game',
                                                 manager=manager,
                                                 anchors={
                                                     'centerx': 'centerx',
                                                     'bottom': 'bottom',
                                                     'bottom_target': self.load_button
                                                 })
        
        self.place_animation() # draw ring

    # places images in self.cards around circle
    def place_animation(self):
        self.circle_surface.fill(Colors.window_bg)
        for i, card in enumerate(self.cards):
            angle = i * self.angle_increment
            rotated_card = self.cards_cache[angle]

            x = int(self.circle_surface.get_width() // 2 + self.circle_radius * pygame.math.Vector2(1, 0).rotate(angle).x - rotated_card.get_width() // 2)
            y = int(self.circle_surface.get_height() // 2 + self.circle_radius * pygame.math.Vector2(1, 0).rotate(angle).y - rotated_card.get_height() // 2)

            self.circle_surface.blit(rotated_card, (x, y))

    def run(self, manager):
        self.isConfClicked = False
        cfg_width = 350
        cfg_height = 500
        cfgpos = pygame.Rect((300, 350), (cfg_width, cfg_height))

        while True:
            time_delta = self.clock.tick(60) / 1000.0
            keys = pygame.key.get_pressed()

            for event in pygame.event.get():
                # buttons
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.play_button:
                        print('TITLE: Starting game')
                        self.state = ScreenState.START
                    if event.ui_element == self.quit_button:
                        print('TITLE: Quitting')
                        return ScreenState.QUIT
                    # if (event.ui_element == self.settings_button and not self.isConfClicked):
                    #     print('TITLE: Drawing config')
                    #     self.config = configWindow(manager=manager, pos=cfgpos)
                    #     self.isConfClicked = True
                    if (event.ui_element == self.load_button):
                        print('TITLE: Loading saved game')
                        save_file_exists = os.path.exists("saved_game.pickle")
                        if (save_file_exists):
                            self.state = ScreenState.LOAD

                # cfg window position
                if (event.type == pygame_gui.UI_WINDOW_MOVED_TO_FRONT and self.config != None):
                    cfgpos = self.config.rect
                
                # cfg snap to bounds
                if (self.isConfClicked):
                    if (cfgpos.x < 0):
                        self.config.set_position((0, cfgpos.y))
                    if ((cfgpos.x+cfg_width) > manager.window_resolution[0]):
                        self.config.set_position((manager.window_resolution[0]-cfg_width, cfgpos.y))
                    if (cfgpos.y < 0):
                        self.config.set_position((cfgpos.x, 0))
                    if ((cfgpos.y+cfg_height) > manager.window_resolution[1]):
                        self.config.set_position((cfgpos.x, manager.window_resolution[1]-cfg_height))
                
                # quit program handling
                if event.type == pygame.QUIT:
                    return ScreenState.QUIT

                manager.process_events(event)

            manager.update(time_delta)
            self.window.blit(self.background, (0,0))

            # drawing animation
            # (don't draw on different screens to save memory)
            if (self.animate and self.state == ScreenState.TITLE):
                self.rotation_angle += 10 * time_delta # update rotation
                rotated_circle = pygame.transform.rotate(self.circle_surface, self.rotation_angle)
                rc_rect = rotated_circle.get_rect(center=self.circle_center)
                self.window.blit(rotated_circle, rc_rect.topleft)

            manager.draw_ui(self.window)

            pygame.display.flip()

            if (debugswitch):
                self.state = ScreenState.DEBUG

            if (self.isConfClicked):
                if not self.config.alive():
                    self.isConfClicked = False

            if (self.state != ScreenState.TITLE):
                return self.state

    def delete(self, manager):
        print('TITLE: Deleting objects')
        manager.clear_and_reset()
   
class configWindow(pygame_gui.elements.UIWindow):
    def __init__(self, manager, pos):
        super().__init__((pos),
                        manager,
                        window_display_title='Settings',
                        object_id='#config_window')
        
        self.debug_category_label = pygame_gui.elements.UILabel(pygame.Rect((10, 10), (150, 40)),
                                                                "Debug options",
                                                                manager=manager,
                                                                object_id="config_window_label",
                                                                container=self,
                                                                parent_element=self,
                                                                anchors={
                                                                    "left": "left"
                                                                })
        
        self.start_cam_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 10), (-1, 40)),
                                                            text='Start cam',
                                                            manager=manager,
                                                            #object_id="",
                                                            container=self,
                                                            parent_element=self,
                                                            anchors={
                                                                "top_target": self.debug_category_label,
                                                            })
        
        self.stop_cam_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 10), (-1, 40)),
                                                             text='Stop cam',
                                                             manager=manager,
                                                             #object_id="",
                                                             container=self,
                                                             parent_element=self,
                                                             anchors={
                                                                 "top_target": self.debug_category_label,
                                                                 "left_target": self.start_cam_button,
                                                                 "left": "left"
                                                             })
        
        start_width = self.start_cam_button.drawable_shape.containing_rect.width
        stop_width = self.stop_cam_button.drawable_shape.containing_rect.width
        
        self.interface_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((10, 10), ((start_width + stop_width + 10), 40)),
                                                             text='Nothing button',
                                                             manager=manager,
                                                             container=self,
                                                             parent_element=self,
                                                             anchors={
                                                                 "top_target": self.stop_cam_button
                                                             })
        
    def process_event(self, event):
        global cam
        handled = super().process_event(event)

        if (event.type == pygame_gui.UI_BUTTON_PRESSED):
            if (event.ui_element == self.start_cam_button):
                print('TITLE: Start cam')
                cam.start()
            if (event.ui_element == self.stop_cam_button):
                print('TITLE: Stop cam')
                cam.stop()
        