import pygame
import pygame_gui

class bankWindow(pygame_gui.elements.UIWindow):
    def __init__(self, manager, pos):
        super().__init__((pos),
                        manager,
                        window_display_title='The Holy Bank',
                        object_id='#setup_window',
                        draggable=False)
        
        # "._" means ensuring this variable is private
        self._show_log = False
        self.on_show_log_changed = None

        windowSpacer = pos.height * .1
        logButtonWidth = pos.width * .2

        valueRect = pygame.Rect((0, windowSpacer), (pos.width, windowSpacer))
        amountRect = pygame.Rect((0, windowSpacer), (pos.width, 40))
        logRect = pygame.Rect((0, -(windowSpacer*2)), (logButtonWidth, 40))

        self.bank_label = pygame_gui.elements.UILabel(valueRect,
                                                    "Jackpot:",
                                                    manager=manager,
                                                    object_id="value_header",
                                                    container=self,
                                                    parent_element=self,
                                                    anchors={
                                                        "top": "top",
                                                        "centerx": "centerx"
                                                    })
        self.value_label = pygame_gui.elements.UILabel(amountRect,
                                                    "0",
                                                    manager=manager,
                                                    object_id="header_game",
                                                    container=self,
                                                    parent_element=self,
                                                    anchors={
                                                        "top_target": self.bank_label,
                                                        "centerx": "centerx"
                                                    })
        self.log_button = pygame_gui.elements.UIButton(logRect,
                                                    text='Log',
                                                    manager=manager,
                                                    container=self,
                                                    parent_element=self,
                                                    anchors={
                                                        "bottom": "bottom",
                                                        "centerx": "centerx"
                                                    })
        
    @property
    def show_log(self):
        return self._show_log

    @show_log.setter
    def show_log(self, value):
        self._show_log = value
        if self.on_show_log_changed:
            self.on_show_log_changed(value)
        
    # logic for detecting if log button was pressed                                                
    def process_event(self, event):
        handled = super().process_event(event)

        if (event.type == pygame_gui.UI_BUTTON_PRESSED):
            if (event.ui_element == self.log_button):
                self.show_log = not self.show_log