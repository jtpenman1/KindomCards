from deck import Deck
from card_ranker import CardRanker
from player import Player
from pot import Pot, TempPot
import random

class GameState:
  SMALL_BLIND = 5
  BIG_BLIND = 10

  def __init__(self, players):
    self.players = players
    self.game_active = False
    self.dealer_pos = random.randint(0, len(self.players))

  # Check which players can start a new game and return that number
  def ready_up_players(self):
    ready_players = 0
    for player in players:
      if player.chips == 0:
        player.last_action = "out"
      else:
        player.last_action = "wait"
        ready_players += 1
    return ready_players

  # Given a current player position, get the next player's
  # position who is still active (chips > 0 and necessary last_action)
  # THIS METHOD SHOULD NOT BE REACHABLE IF THERE ARE NO NEXT ACTIVE PLAYERS
  # THERE SHOULD BE PRIOR CHECKS IN PLACE FOR `self.is_round_over()` TO END ROUND
  def get_next_pos(self, pos):
    n_players = len(self.players)
    player_inactive = True
    while player_inactive:
      pos = (pos + 1) % n_players
      player_inactive = self.players[pos].chips <= 0 or self.players[pos].last_action in ["out", "fold", "all_in"]
    return pos

  def increment_curr_pos(self):
    self.curr_pos = self.get_next_pos(self.curr_pos)
    return self.curr_pos

  def increment_dealer_pos(self):
    self.dealer_pos = self.get_next_pos(self.dealer_pos)
    return self.dealer_pos

  # setup all variables for a new game state
  def start_game(self):
    # Don't start a new game if one is in progress already
    if self.game_active:
      print("Error: Cannot start a new game because a game is in progress.")
      return

    # Check if enough players have chips to start a new gme
    if self.ready_up_players() < 2:
      print("Error: Cannot start a new game because not enough players have chips.")
      return

    # Setup all variables
    self.deck = Deck()

    # keep track of a single pot that can be split into side pots
    # NOTE: at the end of the game, this pot will be forced into side pots
    # because `side_pots` is coupled with chip winnings distribution
    self.tmp_pot = TempPot(self.players)

    # keep track of all the side pots that break off of the tmp pot
    # store main & side pots for winnings distribution
    self.side_pots = []

    self.round = "preflop"
    self.community_cards = [Deck.UNKNOWN_CARD_SYMBOL for _ in range(5)]
    self.increment_dealer_pos()
    self.curr_pos = self.dealer_pos # game starts from dealer position
    self.game_active = True

  def await_player_action(self, player):
    print(GameState.divider("Player Action"))
    print(player)

    highest_bet = self.tmp_pot.highest_bet()

    p_action = None

    while p_action is None:
      p_action = input(f"Bet requirement: {self.tmp_pot.highest_bet() - self.tmp_pot.bets[player.id]}\nMake your move (fold, call, raise, all_in):")
      if p_action not in ["fold", "call", "raise", "all_in"]:
        p_action = None

    if p_action != "raise":
      return p_action, 0

    p_bet = None

    while p_bet is None:
      try:
        p_bet = int(input("What is your bet?"))
        print("Value input: " + p_bet)
      except:
        print("Error: Please enter a number.")
      if p_bet < 0 or p_bet > player.chips:
        p_bet = None

    return p_action, p_bet

  def execute_player_action(self, player, action, bet_amount):
    min_required_bid = self.tmp_pot.highest_bet() - self.tmp_pot.bets[player.id]

    if action == "fold":
      bet_amount = 0

    elif action == "all_in":
      bet_amount = player.chips

    elif action == "call":
      bet_amount = min(min_required_bid, player.chips)
      if bet_amount == player.chips:
        action = "all_in"
      elif bet_amount < min_required_bid:
        return False

    elif action == "raise":
      if bet_amount == player.chips:
        action = "all_in"
      elif bet_amount > player.chips:
        return False
      elif bet_amount < min_required_bid:
        return False

    player.last_action = action
    self.tmp_pot.add_to_pot(player.id, bet_amount)
    player.chips -= bet_amount
    player.curr_bet = self.tmp_pot.bets[player.id]

    return True


  # Initiate the next game step
  # E.g. start round, reveal community card, next player move, etc.
  def step(self, p_action, p_bet=None):
      if not self.game_active:
        print("Error: Cannot step to next game move because game is not in progress.")
        return

      # Detect start of game: round == preflop, pot == 0
      if self.round == "preflop" and self.tmp_pot.sum_bets() == 0:
        # if there are only 2 players, player with dealer chip is also small blind
        # otherwise small blind is the player after the dealer chip
        if len(self.players_that_can_do_action()) > 2:
          self.increment_curr_pos()

        p_sm = self.players[self.curr_pos]
        self.execute_player_action(p_sm, "raise", min(p_sm.chips, GameState.SMALL_BLIND))
        self.increment_curr_pos()

        p_b = self.players[self.curr_pos]
        self.execute_player_action(p_b, "raise", min(p_b.chips, GameState.BIG_BLIND))
      else:
        # If a play should not take place, end round immediately
        if self.is_round_over():
          self.end_round()
          return

        # individual player move
        curr_player = self.players[self.curr_pos]

        self.execute_player_action(curr_player, p_action, p_bet)


      # Check and handle if the round shound be over
      if self.is_round_over():
        print("end of round")
        self.end_round()

      # round is not over, move to next player
      else:
        self.increment_curr_pos()

  # OR n-1 players are either "out" or "fold", one person wins
  def is_round_over(self):
    # check if only one player is not out
    out_cnt = 0
    for p in self.players:
      if p.last_action in ["out", "fold"]:
        out_cnt += 1
    if out_cnt == len(self.players) - 1:
      return True

    # check if everyone has placed the minimum required bet and is not out
    highest_bet = self.tmp_pot.highest_bet()
    cnt = 0
    for p in self.players:
      if p.last_action == "wait":
        return False
      if not p.can_do_action() or (p.curr_bet == highest_bet and p.can_do_action()):
        cnt += 1
    # print(f"round over: {cnt == len(self.players)}")
    return cnt == len(self.players)

  # If a round begins where only one player has the ability place a bet, the game should end
  def should_round_begin(self):
    cnt = 0
    for p in self.players:
      if p.last_action == "wait":
        cnt += 1
      if cnt > 1:
        return True
    return False

  # update board when a round is over
  def end_round(self):
    round_is_over = True
    while round_is_over:
      # default all players action to wait at start of round
      for player in self.players:
        if player.last_action == "all_in":
          player.last_action = "pot_committed"

        if player.last_action != "out" and player.last_action != "pot_committed" and player.last_action != "fold":
          player.last_action = "wait"
          player.curr_bet = 0

      if self.round == "preflop":
        self.round = "flop"
        print("Flop")
        for i in range(3):
          self.community_cards[i] = Deck.scan()

      elif self.round == "flop":
        print("Turn")
        self.round = "turn"
        self.community_cards[3] = Deck.scan()

      elif self.round == "turn":
        print("River")
        self.round = "river"
        self.community_cards[4] = Deck.scan()

      elif self.round == "river":
        print("End")
        self.end_game()
        return

      else:
        print(f"Error: could not proceed to next round from '{self.round}'")
        return

      # split out sidepots
      self.side_pots += self.tmp_pot.to_sidepots()
      # curr_pot.to_sidepots() naturally returns player bets to 0
      round_is_over = self.is_round_over()

      if not self.should_round_begin():
        round_is_over = True

    # Move curr_pos to next active player after dealer if
    self.curr_pos = self.get_next_pos(self.dealer_pos)

  # Called after river betting & cards are revealed
  def end_game(self):
    for player in self.players:
      player.cards = [Deck.scan(), Deck.scan()]

    # split into pots one last time
    self.side_pots += self.tmp_pot.to_sidepots()

    # rank and calculate winnings for players based on cards
    winnings = CardRanker.rank_and_calculate_winnings(self.players, self.community_cards, self.side_pots)

    # distribute winnings
    for player in self.players:
      if player.id in winnings.keys():
        player.chips += winnings[player.id]

    # disperse pots over winner(s)
    print("WINNINGS:")
    print(winnings)

    # for each player with no chips, set player.last_action to "out"
    for p in self.players:
      if p.chips == 0:
        p.last_action = "out"
    self.game_active = False

  def players_that_can_do_action(self):
    res = []
    for player in self.players:
      if player.can_do_action():
        res.append(player)
    return res

  def divider(s):
    return "\n-------------------- " + s + " --------------------\n\n"

  def __str__(self):


    res = "\n\n\n"

    res += GameState.divider("General State")
    res += f"Round: {self.round}\n"
    res += f"Community Cards: {self.community_cards}\n"
    res += f"Dealer Position: {self.dealer_pos}\n"
    res += f"Current Position: {self.curr_pos}\n"

    res += GameState.divider(f"Players ({len(self.players)})")
    for player in self.players:
      res += f"ID{player.id}, chips:{player.chips}, cards:{player.cards}, last_action:{player.last_action}\n"

    res += GameState.divider("Current Pot")
    for key, value in self.tmp_pot.bets.items():
      res += f"{key}:${value}\t"
    res += GameState.divider("Final Pots")
    for i, pot in enumerate(self.side_pots):
      for key, value in pot.bets.items():
        res += f"{key}:${value}\t"

    return res


players = [
  Player("Bill", 100, cards=["AH", "AS"]), 
  Player("John", 200, cards=["KC", "8H"]), 
  Player("Sam", 300, cards=["2D", "2C"])
  ]

state = GameState(players)
state.start_game()


while state.game_active:
  p_action = input("Action:\n")
  p_bet = int(input("Bet:\n"))
  state.step(p_action, p_bet)
  print(state.players[state.curr_pos], state.curr_pos)
  if state.game_active:
   print(state)
