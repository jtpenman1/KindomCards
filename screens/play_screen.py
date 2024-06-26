import pygame
import pygame_gui
import threading
import pickle
import time
from pygame_gui.elements import UILabel
from pygame_gui.elements import UITextBox

from objects.screenstate import ScreenState
from objects.gamestate import GameState
from objects.scheme import Scheme
from windows.results_window import resultsWindow

from windows.setup import setupWindow
from windows.pause_window import pauseWindow
from windows.player_window import playerWindow
from windows.bank_window import bankWindow
from windows.log_window import logWindow
from windows.table_window import tableWindow
from windows.player_name_setup import playerNameSetupWindow
from windows.bet_window import betWindow
from windows.cam_window import camWindow
from windows.info_window import infoWindow
from windows.church_window import churchWindow

from game_logic.game import GameInstance
from game_logic.player import Player

from local_ml.card_detection import classify_card
from local_ml.agent import Agent

import pygame.camera

# image proc
import cv2
import base64
import requests
import json
import numpy as np

homeswitch = False
pickleswitch = False
save_state = None

class playScreen:
    def __init__(self, manager, window, state):
        global save_state

        if (state == ScreenState.LOAD):
            with open('saved_game.pickle', 'rb') as f:
                save_state = pickle.load(f)

            self.offload_card_detection = True
            Colors = Scheme()
            self.state = ScreenState.LOAD

            self.width = manager.window_resolution[0]
            self.height = manager.window_resolution[1]
            self.clock = pygame.time.Clock()
            self.window = window
            self.background = pygame.Surface((self.width, self.height))
            self.background.fill(Colors.window_bg)

            self.header = None
            self.camwindow = None
            self.betwindow = None

            self.results_displayed = False
            self.camClicked = False
            self.aiThinking = save_state['aithinking']

            # Class variable for a new GameInstance from game_logic/game.py.
            # This variable is updated after number of players/AI is selected.

            # For future save game functions, this class variable should be loaded
            # from the saved game's GameInstance object.
            # (more on this functionality later)
            self.game_instance = save_state['game_instance']

            self.game_state = save_state['game_state']

            self.e_p = self.width*0.007 # edge padding
            self.b_width = self.width*0.055 # button width
            self.b_height = self.height*0.045 # button height

            self.player_actions = []
        else:
            self.offload_card_detection = True
            Colors = Scheme()
            self.state = state

            self.width = manager.window_resolution[0]
            self.height = manager.window_resolution[1]
            self.clock = pygame.time.Clock()
            self.window = window
            self.background = pygame.Surface((self.width, self.height))
            self.background.fill(Colors.window_bg)

            self.header = None
            self.camwindow = None
            self.betwindow = None

            self.results_displayed = False
            self.camClicked = False
            self.aiThinking = 0

            # Class variable for a new GameInstance from game_logic/game.py.
            # This variable is updated after number of players/AI is selected.

            # For future save game functions, this class variable should be loaded
            # from the saved game's GameInstance object.
            # (more on this functionality later)
            self.game_instance = None

            self.game_state = None

            self.e_p = self.width * 0.007  # edge padding
            self.b_width = self.width * 0.055  # button width
            self.b_height = self.height * 0.045  # button height

            self.player_actions = []
        self.bible_verses = ["Matthew 16:26 - For ywhat will it profit a man if he gains the whole world and forfeits his soul? Or what shall a man give in return for his soul?",
                            "2 Peter 3:18 - But grow in the grace and knowledge of our Lord and Savior Jesus Christ. To him be the glory both now and to the day of eternity. Amen.",
                            "Colossians 3:2 - Set your minds on things that are above, not on things that are on earth.",
                            "Ephesians 4:24 - and to put on the new self, created after the likeness of God in true righteousness and holiness.",
                            "Romans 8:18 - For I consider that the sufferings of this present time are not worth comparing with the glory that is to be revealed to us.",
                            "Ephesians 2:8 - For by grace you have been saved through faith. And this is not your own doing; it is the gift of God, James 2:17 - So too, faith by itself, if it does not result in action, is dead.",
                            "2 Corinthians 9:7 - Each one must give as he has decided in his heart, not reluctantly or under compulsion, for God loves a cheerful giver.",
                            "Philippians 2:3 - Do nothing from selfish ambition or conceit, but in humility count others more significant than yourselves."]

    def load(self, manager, state):
        global save_state
        if (state == ScreenState.LOAD):
            self.state = ScreenState.LOAD

            header_rect = pygame.Rect(0, self.height * .01, self.width // 3, 150)

            self.header = UILabel(relative_rect=header_rect,
                                  text=save_state['header_text'],       # LOAD FROM SAVED PICKLE
                                  manager=manager,
                                  object_id='header_game',
                                  anchors={
                                      'centerx': 'centerx',
                                      'top': 'top'
                                  })

            stp_width = 500
            stp_height = 500
            stppos = pygame.Rect(((self.width / 2) - (stp_width / 2), (self.height / 2) - (stp_height / 2)),
                                 (stp_width, stp_height))

            # pause button
            pause_button_rect = pygame.Rect(self.e_p, self.e_p, self.b_width, self.b_height)
            self.pause_button = pygame_gui.elements.UIButton(relative_rect=pause_button_rect,
                                                             text='Pause',
                                                             manager=manager,
                                                             anchors={
                                                                 'left': 'left',
                                                                 'top': 'top'
                                                             })

            # end round button
            dealing_button_rect = pygame.Rect(15, -100, 250, 50)
            self.dynamic_button = pygame_gui.elements.UIButton(relative_rect=dealing_button_rect,
                                                               text=save_state['dynamic_text'],     # LOAD FROM SAVED PICKLE
                                                               manager=manager,
                                                               anchors={
                                                                   'centerx': 'centerx',
                                                                   'bottom': 'bottom'
                                                               })

            # info button
            info_button_rect = pygame.Rect(-self.e_p - self.b_width / 2.5, self.e_p, self.b_width / 2.5, self.b_height)
            self.info_button = pygame_gui.elements.UIButton(relative_rect=info_button_rect,
                                                            text='i',
                                                            manager=manager,
                                                            anchors={
                                                                'right': 'right'
                                                            })

            # donation button
            self.church_button_rect = pygame.Rect(0, self.e_p, -1, self.b_height)
            self.church_button = pygame_gui.elements.UIButton(relative_rect=self.church_button_rect,
                                                              text='DONATE TO MAGNOLIA CHURCH',
                                                              manager=manager)

            # LOAD FROM SAVED PICKLE
            self.player_index = save_state['player_index']  # keep track of which player we are operating on
            self.card_index = save_state['card_index']  # which card are we scanning
            self.cards_scanned = save_state['cards_scanned']

            # bet set up
            result_width = self.width * .3
            result_height = self.height * .22
            results_rect = pygame.Rect(((self.width * .50) - (result_width // 2), self.height / 1.8),
                                       (result_width, result_height))

            self.result_text = UITextBox(' ',
                                         relative_rect=results_rect,
                                         manager=manager,
                                         object_id='result_textbox',
                                         anchors={
                                             'left': 'left',
                                             'top': 'top'
                                         })

            # do not show results if they are not displayed from save state
            if (not save_state['results_displayed']):
                self.result_text.hide()

            bible_width = self.width * .8
            bible_height = self.height * .15
            bible_rect = pygame.Rect(((self.width * .50) - (bible_width // 2), self.height / 3.8),
                                     (bible_width, bible_height))
            self.bible_text = UITextBox(
                'Proverbs 3:6 - In all your ways acknowledge him, and he will make your paths straight.',
                relative_rect=bible_rect,
                manager=manager,
                object_id='result_textbox',
                anchors={
                    'left': 'left',
                    'top': 'top'
                })
            self.bible_text.hide()

            character_width = 250
            character_height = character_width * 1.2

            imgsurf = pygame.Surface(size=(character_width, character_height))
            imgsurf.fill((40, 62, 51))
            char_rect = pygame.Rect((self.width * .3, self.height * .5), (character_width, character_height))
            self.ai_character = pygame_gui.elements.UIImage(relative_rect=char_rect,
                                                            image_surface=imgsurf,
                                                            manager=manager,
                                                            anchors={
                                                                "left": "left",
                                                            })

            # Do not setup game, since we are loading from save
            # self.setup = setupWindow(manager, stppos)
            self.players_loaded = False
        else:
            self.state = state

            header_rect = pygame.Rect(0, self.height*.01, self.width//3, 150)

            self.header = UILabel(relative_rect=header_rect,
                                text='Set Up Names...',
                                manager=manager,
                                object_id='header_game',
                                anchors={
                                    'centerx': 'centerx',
                                    'top': 'top'
                                })
            self.header.hide()

            stp_width = 500
            stp_height = 500
            stppos = pygame.Rect(((self.width/2)-(stp_width/2), (self.height/2)-(stp_height/2)), (stp_width, stp_height))

            # pause button
            pause_button_rect = pygame.Rect(self.e_p, self.e_p, self.b_width, self.b_height)
            self.pause_button = pygame_gui.elements.UIButton(relative_rect=pause_button_rect,
                                                text='Pause',
                                                manager=manager,
                                                anchors={
                                                'left': 'left',
                                                'top': 'top'
                                                })
            self.pause_button.hide()

            # end round button
            dealing_button_rect = pygame.Rect(15, -100, 250, 50)
            self.dynamic_button = pygame_gui.elements.UIButton(relative_rect=dealing_button_rect,
                                                text='Scan AI\'s Hand',
                                                manager=manager,
                                                anchors={
                                                'centerx': 'centerx',
                                                'bottom': 'bottom'
                                                })
            self.dynamic_button.hide()

            # info button
            info_button_rect = pygame.Rect(-self.e_p-self.b_width/2.5, self.e_p, self.b_width/2.5, self.b_height)
            self.info_button = pygame_gui.elements.UIButton(relative_rect=info_button_rect,
                                                    text='i',
                                                    manager=manager,
                                                    anchors={
                                                    'right': 'right'
                                                    })
            self.info_button.hide()

            # donation button
            self.church_button_rect = pygame.Rect(0, self.e_p, -1, self.b_height)
            self.church_button = pygame_gui.elements.UIButton(relative_rect=self.church_button_rect,
                                                            text='DONATE TO MAGNOLIA CHURCH',
                                                            manager=manager)
            self.church_button.hide()

            self.player_index = 0 # keep track of which player we are operating on
            self.card_index = 0 # which card are we scanning
            self.cards_scanned = []

            # bet set up
            result_width = self.width*.3
            result_height = self.height*.22
            results_rect = pygame.Rect(((self.width*.50)-(result_width//2), self.height/1.8), (result_width, result_height))

            self.result_text = UITextBox(' ',
                                relative_rect=results_rect,
                                manager=manager,
                                object_id='result_textbox',
                                anchors={
                                    'left': 'left',
                                    'top': 'top'
                                })
            self.result_text.hide()

            bible_width = self.width*.8
            bible_height = self.height*.15
            bible_rect = pygame.Rect(((self.width*.50)-(bible_width//2), self.height/3.8), (bible_width, bible_height))
            self.bible_text = UITextBox('Proverbs 3:6 - In all your ways acknowledge him, and he will make your paths straight.',
                                relative_rect=bible_rect,
                                manager=manager,
                                object_id='result_textbox',
                                anchors={
                                    'left': 'left',
                                    'top': 'top'
                                })
            self.bible_text.hide()

            character_width = 250
            character_height = character_width*1.2

            imgsurf = pygame.Surface(size=(character_width, character_height))
            imgsurf.fill((40, 62, 51))
            char_rect = pygame.Rect((self.width*.3, self.height*.5), (character_width, character_height))
            self.ai_character = pygame_gui.elements.UIImage(relative_rect=char_rect,
                                                            image_surface=imgsurf,
                                                            manager=manager,
                                                            anchors = {
                                                                "left": "left",
                                                            }
            )

            self.setup = setupWindow(manager, stppos)

    def run(self, manager):
        global homeswitch
        global pickleswitch
        global save_state
        pauseClicked = False
        infoClicked = False
        churchClicked = False
        logClicked = False

        # pause set up
        pause_width = 350
        pause_height = 400
        pausepos = pygame.Rect(((self.width/2)-pause_width/2, (self.height/2)-pause_height/2), (pause_width, pause_height))
        
        # player set up
        players_width = self.width*.25
        players_height = self.height*.55
        playerspos = pygame.Rect((0, self.height-players_height), (players_width, players_height))

        # bank set up
        bank_width = self.width*.25
        bank_height = self.height*.275
        bankpos = pygame.Rect((self.width - (bank_width), self.height-(bank_height)), (bank_width, bank_height))

        # log set up
        log_width = self.width*.25
        log_height = self.height*.275
        logpos = pygame.Rect((self.width - (log_width), self.height-(log_height*3)), (log_width, log_height))

        # table set up
        tablepos = pygame.Rect((self.width - (bank_width), self.height-(bank_height*2)), (bank_width, bank_height))

        # results set up
        resultpos = pygame.Rect(((self.width/2)-(self.width*.3/2), (self.height/2.8)-(bank_height/2)), (self.width*.3, bank_height))

        # action header set up
        playerSetup_width = self.width*.26
        playerSetup_height = self.height*.46
        playerSetuppos = pygame.Rect(((self.width/2)-(playerSetup_width/2), (self.height/2)-(playerSetup_height/2)), (playerSetup_width, playerSetup_height))

        # bet set up
        bet_width = self.width*.25
        bet_height = self.height*.50
        betpos = pygame.Rect(((self.width*.50)-(bet_width//2), self.height*.25), (bet_width, bet_height))

        # cam set up
        cam_width = self.width*.4
        cam_height = self.height*.7
        campos = pygame.Rect(((self.width*.5)-(cam_width//2), self.height*.125), (cam_width, cam_height))

        # info icon set up
        info_width = self.width*.20
        info_height = self.height*.4
        infopos = pygame.Rect(((self.width)-(info_width+self.e_p), (self.height/2.15)-(info_height)), (info_width, info_height))

        # church icon set up
        church_width = self.width*.2
        church_height = self.height*.45
        churchpos = pygame.Rect(((self.width)-(church_width*3), (self.height/2)-(church_height/2)), (church_width, church_height))

        # bypass pygame_gui bug where right aligned objects do not anchor right properly
        donate_width = self.church_button.rect.width
        self.church_button_rect.x = (self.width - self.info_button.rect.width - self.e_p*2 - donate_width)
        self.church_button.relative_rect = self.church_button_rect
        self.church_button.rebuild()

        while True:
            time_delta = self.clock.tick(60) / 1000.0
            keys = pygame.key.get_pressed()                

            # if setup window is closed, open player window and pause button
            if (setupWindow.startClicked):
                # show header
                self.header.show()
                self.playerSetUp = playerNameSetupWindow(manager, playerSetuppos, setupWindow.player_count)
                setupWindow.startClicked = False

            # START THE GAME
            if (self.state == ScreenState.LOAD):
                if (not self.players_loaded):
                    # print("BEFORE: -----------" + str(len(self.playerSetUp.playerNames)) + "-----------")
                    chip_count = []
                    # player_actions = []
                    for player in self.game_instance.players:
                        print("Load player: " + player.name)
                        chip_count.append(player.chips)
                        # player_actions.append(player.last_action)

                    self.players = playerWindow(manager, playerspos, [],[], 0, False)
                    self.players.load(manager, playerspos, self.game_instance.players, chip_count)

                    self.pause_button.show()
                    playerNameSetupWindow.submitPlayerClicked = False

                    self.header.show()
                    self.info_button.show()
                    self.church_button.show()

                    self.table = tableWindow(manager=manager, pos=tablepos)
                    if (self.game_instance.community_cards != ['NA', 'NA', 'NA', 'NA', 'NA']):
                        self.updateTable(self.game_instance.community_cards)  # update the table from saved community cards

                    self.result_table = resultsWindow(manager=manager, pos=resultpos)
                    self.result_table.hide()

                    self.bank = bankWindow(manager=manager, pos=bankpos)
                    self.bank.value_label.set_text(str(self.game_instance.get_total_pot_value()))

                    self.logwindow = logWindow(manager=manager, pos=logpos)
                    self.logwindow.hide()

                    self.bank.on_show_log_changed = lambda value: self.viewLog(value)

                    setupWindow.startClicked = False

                    print("LOAD: Resuming from last state " + str(save_state['game_state']))
                    self.game_state = save_state['game_state']  # resume from last state
                    self.players_loaded = True
                    pickleswitch = False
                    homeswitch = False
                    self.state = ScreenState.START

            if (playerNameSetupWindow.submitPlayerClicked):
                #print("BEFORE: -----------" + str(len(self.playerSetUp.playerNames)) + "-----------")
                self.players = playerWindow(manager, playerspos, self.playerSetUp.playerNames, setupWindow.chip_count, setupWindow.ai_player_count, True)
                self.pause_button.show()
                playerNameSetupWindow.submitPlayerClicked = False

                self.header.show()
                self.info_button.show()
                self.church_button.show()

                self.table = tableWindow(manager=manager, pos=tablepos)
                self.result_table = resultsWindow(manager=manager, pos=resultpos)
                self.result_table.hide()
                self.bank = bankWindow(manager=manager, pos=bankpos)
                self.logwindow = logWindow(manager=manager, pos=logpos)
                self.logwindow.hide()
                
                self.bank.on_show_log_changed = lambda value: self.viewLog(value)

                setupWindow.startClicked = False

                # Process player/AI combo tuple
                # self.playerSetUp.playerNames - input player names
                # self.players.aiplayercount - selected AI count
                # self.players.aiPlayerNames - shuffled AI player names
                game_participants = []
                chips = setupWindow.chip_count
                curr_id = 0
                
                for player in self.playerSetUp.playerNames:
                    person = Player(name=player, is_ai=False, chips=chips, id=curr_id)
                    game_participants.append(person)
                    curr_id += 1
                
                for i in range(self.players.aiplayercount):
                    ai = Player(name=self.players.aiPlayerNames[i], is_ai=True, chips=chips, id=curr_id)
                    game_participants.append(ai)
                    curr_id += 1

                # update chips for player window
                self.game_instance = GameInstance(game_participants) # // START GAME INSTANCE //
                self.game_state = GameState.SCAN_AI_HAND # begin the game by scanning the AI's cards

            for event in pygame.event.get():
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if (event.ui_element == self.pause_button and not pauseClicked): # PAUSE BUTTON
                        print('PLAY: Drawing pause dialog')
                        pauseClicked = True
                        self.pause = pauseWindow(manager=manager, pos=pausepos)
                        self.pause.set_blocking(True)

                    if (event.ui_element == self.info_button and not infoClicked): # INFO BUTTON
                        print('PLAY: Drawing info dialog')
                        infoClicked = True
                        self.info = infoWindow(manager=manager, pos=infopos)
                        self.info.set_blocking(False)

                    if (event.ui_element == self.church_button and not churchClicked): # DONATION BUTTON
                        print('PLAY: Drawing donation dialog')
                        churchClicked = True
                        self.church = churchWindow(manager=manager, pos=churchpos)
                        self.church.set_blocking(False)

                if event.type == pygame.QUIT:
                    return ScreenState.QUIT
                # if keys[pygame.K_ESCAPE]:
                #     print('PLAY: Switching to TITLE')
                #     self.killCamera()
                #     self.killGame()
                #     homeswitch = True

                manager.process_events(event)

            # --------------------
            # GAME FLOW STATEMENTS
            # --------------------
            if (self.game_state == GameState.SCAN_AI_HAND):
                self.header.set_text('Scan AI Cards')

                if (self.camClicked):
                    cards_to_scan = 2

                    while (self.player_index < len(self.game_instance.players) and not self.game_instance.players[self.player_index].is_ai):
                        self.player_index += 1
                    
                    if (self.player_index < len(self.game_instance.players)):
                        curr_player = self.game_instance.players[self.player_index]
                        
                        self.camwindow.instruction_label.set_text( "%s's cards - %d of 2" % (curr_player.name, self.card_index+1) )

                        if (self.camwindow.snaptaken):
                            self.cards_scanned.append(self.scanCard())
                            self.card_index += 1
                        
                        if (self.card_index >= cards_to_scan):
                            self.card_index = 0
                            curr_player.cards = self.cards_scanned
                            self.cards_scanned = []
                            self.player_index += 1
                    else: # done scanning cards
                        self.camwindow.scanning_ai_cards = False
                        self.player_index = 0
                        self.card_index = 0
                        self.cards_scanned = []

                        self.game_instance.start_game()
                        self.game_instance.step() # perform small and big blinds
                        self.killCamera()
                        print("AI CARDS SCANNED")
                        self.game_state = GameState.PREFLOP_BETS
                else:
                    self.viewCamera(manager, campos) # open camera window
                    self.camwindow.scanning_ai_cards = True # hide AI cards from player

            player_blinds = {}

            if (self.game_state == GameState.PREFLOP_BETS or self.game_state == GameState.POST_FLOP_BETS or 
                self.game_state == GameState.POST_TURN_BETS or self.game_state == GameState.FINAL_BETS):
                # get the current player details with
                player_pos = self.game_instance.curr_pos
                player_action_label = self.players.player_action_list[player_pos]
                player_label = self.players.player_labels_list[player_pos]
                self.player_actions = self.player_actions[-10:]
                if (self.game_state == GameState.PREFLOP_BETS and player_blinds == {}):
                    player_blinds = self.game_instance.tmp_pot.bets
                    for player_index, blind_value in player_blinds.items():
                        #print(self.players.player_action_list)
                        #print(player_blinds.items())
                        self.players.player_action_list[player_index].set_text(str(blind_value))
                        # player_label.set_text(self.game_instance.players[player_index].name + ":  " + str(self.game_instance.players[player_index].chips) + "  |  ")

                self.next_state = GameState.UNCHANGED_STATE

                player = self.game_instance.players[self.game_instance.curr_pos].name # returns Player instance from player.py
                # show bet dialogue & collect input action, bet for that player
                self.header.set_text(player + "'s Turn")
                self.min_bet = self.game_instance.get_min_required_bet()
                if (self.betwindow == None):
                    self.betwindow = betWindow(manager, betpos, self.min_bet)
                    self.betwindow.yourmoney_label.set_text("You have " + str(self.game_instance.players[self.game_instance.curr_pos].chips) + " chips")
                    if (self.game_instance.players[player_pos].is_ai):
                        self.betwindow.hide()
                    else:
                        self.betwindow.show()
                    print('PLAY: Drawing bet window')
                else: # bet window open
                    pl = self.game_instance.players[player_pos]
                    if pl.is_ai:
                        if (self.aiThinking == 0):
                            thread = threading.Thread(target=self.threadMethod)
                            thread.start()
                        if self.aiThinking == 1:
                            self.betwindow.kill()
                            fileName= "assets/ai_characters/" + pl.name + ".png"
                            self.ai_character.set_image(pygame.image.load(fileName))
                            self.ai_character.show()
                            self.header.set_text(player + " is thinking...")
                            self.bible_text.show()
                        if self.aiThinking == 2:
                            p_action, p_bet = Agent.predict(self.game_instance.get_state_ai(player_pos))
                            if p_action == 'fold':
                                self.next_state = self.game_instance.step(p_action)
                            else:
                                self.next_state = self.game_instance.step(p_action, p_bet)
                            player_action_label.set_text(p_action)
                            self.player_actions.append(player + f" has {p_action}")
                            self.updateGameLog(self.player_actions)
                            self.player_chips = self.game_instance.players[player_pos].chips
                            player_label.set_text(player + ":  " + str(self.player_chips) + "  |  ")
                            self.betwindow = None
                            self.bible_text.hide()
                            self.ai_character.hide()
                            self.aiThinking = 0
                    else:
                        if (self.betwindow.folds):
                            self.betwindow.kill()
                            self.betwindow = None
                            self.next_state = self.game_instance.step('fold')
                            player_action_label.set_text("fold")
                            self.player_actions.append(player + " has folded, womp womp")
                            self.updateGameLog(self.player_actions)
                        elif (self.betwindow.placed_bet != None):
                            self.player_chips = self.game_instance.players[player_pos].chips
                            if (self.betwindow.placed_bet == "0"):
                                self.next_state = self.game_instance.step('call', int(self.betwindow.placed_bet))
                                player_action_label.set_text("Check")
                                self.player_actions.append(player + " has checked")
                                self.updateGameLog(self.player_actions)
                            elif (int(self.betwindow.placed_bet) <= self.min_bet):
                                self.next_state = self.game_instance.step('call', int(self.betwindow.placed_bet))
                                player_action_label.set_text(self.betwindow.placed_bet)
                                self.player_actions.append(player + " has called the current bet")
                                self.updateGameLog(self.player_actions)
                            elif (int(self.betwindow.placed_bet) == self.player_chips):
                                self.next_state = self.game_instance.step('raise', int(self.betwindow.placed_bet))
                                player_action_label.set_text(self.betwindow.placed_bet)
                                self.player_actions.append(player + " has went all in with " + self.betwindow.placed_bet + " chips!")
                                self.updateGameLog(self.player_actions)
                            else:
                                # print('Player bet ' + self.betwindow.placed_bet + " chips")
                                player_action_label.set_text(self.betwindow.placed_bet)
                                self.next_state = self.game_instance.step('raise', int(self.betwindow.placed_bet))
                                self.player_actions.append(player + " has raised by " + self.betwindow.placed_bet + " chips")
                                self.updateGameLog(self.player_actions)
                            # current player's chips
                            player_label.set_text(player + ":  " + str(self.player_chips) + "  |  ")
                            self.bible_text.set_text(self.bible_verses[np.random.randint(0, len(self.bible_verses))])
                            self.betwindow.kill()
                            self.betwindow = None

                if  self.next_state == GameState.SCAN_FLOP:
                    self.bank.value_label.set_text(str(self.game_instance.get_total_pot_value()))
                    for players in self.players.player_action_list:
                        if players.text == "fold" or players.text == "0" or players.text == "5":
                            players.set_text('fold')
                        else:
                            players.set_text('')
                    self.game_state = GameState.SCAN_FLOP
                    self.header.set_text('Scan Flop')

                if  self.next_state == GameState.SCAN_TURN:   
                    self.bank.value_label.set_text(str(self.game_instance.get_total_pot_value()))
                    for players in self.players.player_action_list:
                        if players.text == "fold":
                            players.set_text('fold')
                        else:
                            players.set_text('')
                    self.game_state = GameState.SCAN_TURN
                    self.header.set_text('Scan Turn Card')

                if  self.next_state == GameState.SCAN_RIVER:
                    self.bank.value_label.set_text(str(self.game_instance.get_total_pot_value()))
                    for players in self.players.player_action_list:
                        if players.text == "fold":
                            players.set_text('fold')
                        else:
                            players.set_text('')
                    self.game_state = GameState.SCAN_RIVER
                    self.header.set_text('Scan River Card')

                if  self.next_state == GameState.SCAN_PLAYER_HAND:
                    self.bank.value_label.set_text(str(self.game_instance.get_total_pot_value()))
                    for players in self.players.player_action_list:
                        if players.text == "fold":
                            players.set_text('fold')
                        else:
                            players.set_text('')
                    self.game_state = GameState.SCAN_PLAYER_HAND
                    self.player_index = 0
                    self.header.set_text('Scan Player Hands')

            if (self.game_state == GameState.SCAN_FLOP):
                if (self.camClicked):
                    cards_to_scan = 3

                    if (self.card_index < cards_to_scan):
                        self.camwindow.instruction_label.set_text( "Scan flop - %d of 3" % (self.card_index+1) )

                        if (self.camwindow.snaptaken):
                            card = self.scanCard()
                            self.game_instance.community_cards[self.card_index] = card
                            self.updateTable(self.game_instance.community_cards) # update the table
                            self.card_index += 1
                    if (self.card_index == cards_to_scan):
                        self.killCamera()
                        print(self.game_instance.community_cards)
                        self.game_state = GameState.POST_FLOP_BETS
                else:
                    self.viewCamera(manager, campos) # open camera window

            if (self.game_state == GameState.SCAN_TURN):
                if (self.camClicked):
                    cards_to_scan = 4

                    if (self.card_index < cards_to_scan):
                        self.camwindow.instruction_label.set_text( "Scan turn - %d of 1" % (self.card_index+1-3) )

                        if (self.camwindow.snaptaken):
                            card = self.scanCard()
                            self.game_instance.community_cards[self.card_index] = card
                            self.updateTable(self.game_instance.community_cards) # update the table
                            self.card_index += 1
                    if (self.card_index == cards_to_scan):
                        self.killCamera()
                        print(self.game_instance.community_cards)
                        self.game_state = GameState.POST_TURN_BETS
                else:
                    self.viewCamera(manager, campos) # open camera window

            if (self.game_state == GameState.SCAN_RIVER):
                if (self.camClicked):
                    cards_to_scan = 5

                    if (self.card_index < cards_to_scan):
                        self.camwindow.instruction_label.set_text( "Scan river - %d of 1" % (self.card_index+1-4) )

                        if (self.camwindow.snaptaken):
                            card = self.scanCard()
                            self.game_instance.community_cards[self.card_index] = card
                            self.updateTable(self.game_instance.community_cards) # update the table
                            self.card_index += 1
                    if (self.card_index == cards_to_scan):
                        self.card_index = 0
                        self.killCamera()
                        print(self.game_instance.community_cards)
                        self.game_state = GameState.FINAL_BETS
                else:
                    self.viewCamera(manager, campos) # open camera window

            # Reached end of game before all community cards have been scanned
            if self.game_state == GameState.SCAN_PLAYER_HAND and self.game_instance.community_cards[-1] == 'NA':
                if (self.camClicked):
                    cards_to_scan = 5

                    if (self.card_index < cards_to_scan):
                        self.camwindow.instruction_label.set_text( "Scan river - %d of 5" % (self.card_index+1) )

                        if (self.camwindow.snaptaken):
                            card = self.scanCard()
                            self.game_instance.community_cards[self.card_index] = card
                            self.updateTable(self.game_instance.community_cards) # update the table
                            self.card_index += 1
                    if (self.card_index == cards_to_scan):
                        self.card_index = 0
                        print(self.game_instance.community_cards)
                        self.bank.value_label.set_text(str(self.game_instance.get_total_pot_value()))
                        for players in self.players.player_action_list:
                            players.set_text('')
                        self.game_state = GameState.SCAN_PLAYER_HAND
                        self.player_index = 0
                        self.header.set_text('Scan Player Hands')
                else:
                    self.viewCamera(manager, campos) # open camera window

            # end of game, scan player hands
            if (self.game_state == GameState.SCAN_PLAYER_HAND and self.game_instance.community_cards[-1] != 'NA'):
                if (self.camClicked):
                    self.camwindow.scanning_ai_cards = False
                    cards_to_scan = 2

                    while (self.player_index < len(self.game_instance.players) and (self.game_instance.players[self.player_index].is_ai or self.game_instance.players[self.player_index].last_action == 'fold')):
                        self.player_index += 1
                    
                    if (self.player_index < len(self.game_instance.players) and self.game_instance.players[self.player_index].last_action != 'fold'):
                        curr_player = self.game_instance.players[self.player_index]
                        
                        self.camwindow.instruction_label.set_text( "%s's cards - %d of 2" % (curr_player.name, self.card_index+1) )

                        if (self.camwindow.snaptaken):
                            self.cards_scanned.append(self.scanCard())
                            self.card_index += 1
                        
                        if (self.card_index >= cards_to_scan):
                            self.card_index = 0
                            print("PLAYER %s CARDS:" % (curr_player.name))
                            curr_player.cards = self.cards_scanned
                            self.game_instance.players[self.player_index].cards = curr_player.cards
                            print(curr_player.cards)
                            self.cards_scanned = []
                            self.player_index += 1
                    else: 
                        self.player_index = 0
                        self.card_index = 0
                        self.cards_scanned = []
                        for players in self.players.player_action_list:
                            players.set_text('')

                        self.killCamera()
                        self.game_state = GameState.END_ROUND # ready for reveal
                        rankings, results = self.game_instance.end_game()
                else:
                    self.viewCamera(manager, campos) # open camera window

            if (self.game_state == GameState.END_ROUND):
                self.result_text.show()
                self.dynamic_button.set_text('Next Round')
                self.dynamic_button.show()
                if (len(results) >= 2):
                    text = 'Split pot: '
                    winning_hand = rankings[0][0][2]
                    for position, chips in results.items():
                        player = self.game_instance.players[position]
                        text += f"{player.name} wins {chips} chips, "
                        self.player_chips = player.chips
                        player_label = self.players.player_labels_list[position]
                        player_label.set_text(player.name + ":  " + str(self.player_chips) + "  |  ")
                    self.result_text.set_text(text[:-2] + "\nTop Hand: " + winning_hand + "\n") 
                    self.header.set_text('Split Pot!')
                    # self.player_actions.append("Split pot between the players shown!")
                    # self.updateGameLog(self.player_actions)
                    
                else:
                    winning_hand = rankings[0][0][2]
                    for position, chips in results.items():
                        player = self.game_instance.players[position]
                        self.result_text.set_text(f"{player.name} wins {chips} chips.\nTop Hand: {winning_hand}")
                        self.header.set_text(f"{player.name} wins {chips} chips!")
                        self.player_chips = player.chips
                        player_label = self.players.player_labels_list[position]
                        player_label.set_text(player.name + ":  " + str(self.player_chips) + "  |  ")
                        # self.player_actions.append(player.name + " has won this round! yippee!")
                        # self.updateGameLog(self.player_actions)

                if (self.results_displayed == False):
                    self.updateResultTable(rankings)
                    self.result_table.show()
                    self.results_displayed = True
                if (self.dynamic_button.pressed):
                    self.result_text.hide()
                    self.dynamic_button.hide()
                    self.result_table.hide()
                    self.clearTable(manager, tablepos)
                    if (player.chips == setupWindow.chip_count*len(self.game_instance.players)):
                        self.dynamic_button.pressed = False
                        self.game_state = GameState.END_SCREEN
                    else:
                        self.player_actions.append("A new round has started!")
                        self.game_state = GameState.SCAN_AI_HAND
                        self.updateGameLog(self.player_actions)
                        self.bank.value_label.set_text("0")

            if (self.game_state == GameState.END_SCREEN):
                self.header.set_text('Game Over!')
                self.dynamic_button.set_text('Quit')
                self.result_text.set_text(player.name + ' is the winner! better luck next time!')
                self.bible_text.set_text('Even if you lost, remember John 3:16: "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life." So Even though you lost, you can still have eternal life!')
                self.bible_text.show()
                self.result_text.show()
                self.dynamic_button.show()
                if (self.dynamic_button.pressed):
                    self.killGame()
                    return ScreenState.TITLE

            manager.update(time_delta)     
            self.window.blit(self.background, (0,0))
            
            if self.camwindow != None:
                self.camwindow.draw_camera()

            manager.draw_ui(self.window)

            # Check and reset flags
            if (pauseClicked):
                if not self.pause.alive():
                    pauseClicked = False
                if self.pause.homeswitch:
                    self.pause.homeswitch = False
                    homeswitch = True
                if self.pause.pickleswitch:
                    self.pause.pickleswitch = False
                    # Do not allow saving if gamestate is SCAN_AI_HAND
                    if (self.game_state == GameState.SCAN_AI_HAND):
                        pickleswitch = False
                    else:
                        pickleswitch = True
            
            if (infoClicked):
                if not self.info.alive():
                    infoClicked = False
            if (churchClicked):
                if not self.church.alive():
                    churchClicked = False

            pygame.display.update()

            if (homeswitch):
                if (self.camwindow != None):
                    self.killCamera()
                self.state = ScreenState.TITLE
                homeswitch = False
            if (pickleswitch):
                # SAVE GAME
                save_state = {
                    # "header": self.header,                            - CANNOT STORE THREADED PYGAME OBJECTS
                    # "camwindow": self.camwindow,                      - CANNOT STORE THREADED PYGAME OBJECTS
                    # "screenstate": self.state,                        # screen location (unneeded since we only save from PLAY)

                    "camclicked": self.camClicked,                      # is the camera open

                    "header_text": self.header.text,                    # save header's text
                    "dynamic_text": self.dynamic_button.text,           # save dynamic button's text
                    "results_displayed": self.results_displayed,        # are game results displayed

                    "aithinking": self.aiThinking,                      # is the ai thinking
                    "player_actions": self.player_actions,              # used for log window

                    "player_index": self.player_index,                  # needed if we save during scanning cards
                    "card_index": self.card_index,                      # needed if we save during scanning cards
                    "cards_scanned": self.cards_scanned,                # needed if we save during scanning cards

                    # "pauseClicked": pauseClicked,                     # we do not care about reopening pause (unneeded)
                    "infoClicked": infoClicked,                         # is info button clicked
                    "churchClicked": churchClicked,                     # is church button clicked
                    "logClicked": logClicked,                           # is log button clicked

                    "game_state": self.game_state,                      # see gamestate.py
                    "game_instance": self.game_instance                 # the backend
                }
                print(save_state)

                if (self.camwindow != None):
                    if (self.camwindow.alive()):
                        save_state["cw_scanning_ai"] = self.camwindow.scanning_ai_cards   # were we scanning ai cards
                        save_state["cw_label"] = self.camwindow.instruction_label.text  # cam's instructions

                with open('saved_game.pickle', 'wb') as f:
                    pickle.dump(save_state, f)

                homeswitch = True

            if (self.state != ScreenState.START):
                return self.state

    def updateGameLog(self, player_actions):
        log_text = ""
        for action in player_actions:
            log_text += action + "\n"

        # just to remove trailing newline character
        log_text = log_text[:-1]
        self.logwindow.game_log.set_text(log_text)

    def threadMethod(self):
        random_time = np.random.randint(2, 7)
        self.aiThinking = 1
        time.sleep(random_time)
        self.aiThinking = 2

    def delete(self, manager):
        print('PLAY: Deleting objects')
        manager.clear_and_reset()

    def viewCamera(self, manager, pos):
        self.camwindow = camWindow(manager, pos)
        self.camClicked = True
    
    def viewLog(self, isAlive):
        if isAlive:
            self.logwindow.show()
        else:
            self.logwindow.hide()
    
    def killCamera(self):
        # only call if self.camwindow != None
        if (self.camwindow != None):
            self.camwindow.drawcam = False
            self.camwindow.webcam.release()
            self.camwindow.kill()
        self.game_state = None
        self.camClicked = False
        self.camwindow = None
    
    def scanCard(self):
        card = self.sendImg(self.camwindow.img) # send lambda call
        self.camwindow.snaptaken = False
        self.camwindow.drawcam = True

        return card
    
    def sendImg(self, img):
        img = cv2.resize(img, dsize=(224, 224), interpolation=cv2.INTER_CUBIC)
        img = np.array(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if self.offload_card_detection:
            # offloaded card detection ai
            response = classify_card(img)
            return response
        else:
            img_bytes = img.tobytes()
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')

            response = requests.post('URL', json={'b64img': str(img_b64)})
            response = json.loads(response.text)
            
            return response["class"]
        
    def clearTable(self, manager, tablepos):
        self.table.kill()
        self.table = None
        self.table = tableWindow(manager=manager, pos=tablepos)

    def updateTable(self, community_cards):
        suit = None
        id = None
        for index in range(len(community_cards)):
            card = community_cards[index]
            if card != 'NA':
                if card[1] == "H":
                    suit = "assets/cards/hearts"
                elif card[1] == "D":
                    suit = "assets/cards/diamonds"
                elif card[1] == "C":
                    suit = "assets/cards/clubs"
                elif card[1] == "S":
                    suit = "assets/cards/spades"
                
                if card[0] == "T":
                    id = suit + "/10.png"
                else:
                    id = suit + "/" + card[0] + ".png"
            
                card_element = getattr(self.table, f"card{index + 1}")
                card_element.set_image(pygame.image.load(id))
                #print("Table card " + str(index+1) + " set to " + id)

            index = index + 1
        #print("-- Done updating --")

    def updateResultTable(self, rankings):
        for index in range(len(rankings[0][0][3])):
            card = rankings[0][0][3][index]
            if card != 'NA':
                if card[1] == "H":
                    suit = "assets/cards/hearts"
                elif card[1] == "D":
                    suit = "assets/cards/diamonds"
                elif card[1] == "C":
                    suit = "assets/cards/clubs"
                elif card[1] == "S":
                    suit = "assets/cards/spades"
                if card[0] == "T":
                    id = suit + "/10.png"
                else:
                    id = suit + "/" + card[0] + ".png"
            card_element = getattr(self.result_table, f"card{index + 1}")
            card_element.set_image(pygame.image.load(id))

    def killGame(self):
        self.game_state = None
        self.player_index = 0
        self.card_index = 0
        self.game_instance = None
        Player.id = 0
        self.players = None