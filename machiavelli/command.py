import argparse
from collections import Counter

from .solver import (
    Solver, parse_cards, input_cards, ParseError, sorted_cards, cards_to_str
)

try:
    import termcolor
    import colorama
except ImportError:
    NO_COLOR = True
else:
    NO_COLOR = False


def main_inner(table='', hand='', pretty=True, color=True, emoji=False):
    table = table or ''
    hand = hand or ''

    # Configure solver
    solver = Solver(pretty=pretty, color=color, emoji=emoji)

    def print_game_state():
        last_hand_str = ','.join(sorted_cards(hand.elements()))
        last_table_str = ','.join(sorted_cards(table.elements()))
        if not last_table_str:
            last_table_str = "''"
        if last_hand_str:
            last_hand_str = ' '+last_hand_str
        print(f'Current game state: machiavelli {last_table_str}{last_hand_str}')

    # Get initial hand and table state
    try:
        hand = Counter(parse_cards(hand))
        table = Counter(parse_cards(table))
    except ParseError as e:
        solver.print_err(str(e), type(e))
        return
    if not hand and not table:
        h = input_cards('Enter starting hand: ')
        p = []
        t = input_cards('Enter other plays: ')
        hand += Counter(h)
        hand -= Counter(p)
        table += Counter(p)
        table += Counter(t)
        print_game_state()

    # Loop for each game round
    while True:
        # Solve the table then table+hand
        sol = None
        try:
            sol = solver.play_hand(table, hand)
        except (KeyboardInterrupt, EOFError):
            print()
            print('Solver Canceled')

        print()
        h = input_cards('Enter drawn card(s) (or blank): ')
        if sol:
            best_cards = Counter(card for group in sol for card in group)
            best_cards.subtract(table)
            best = cards_to_str(best_cards.elements())
        else:
            best = ''
        if best:
            p = input_cards(f'Enter my last play (or "best"={best}): ',
                            shortcuts={'b': best, 'best': best})
        else:
            p = input_cards(f'Enter my last play (or blank): ',
                            shortcuts={'b': '', 'best': ''})
        t = input_cards('Enter other plays: ')
        hand += Counter(h)
        hand -= Counter(p)
        table += Counter(p)
        table += Counter(t)

        # Print current game state
        print_game_state()

def main(table='', hand='', pretty=False, color=True, emoji=False):
    try:
        main_inner(table, hand, pretty=pretty, color=color, emoji=emoji)
    except (KeyboardInterrupt, EOFError):
        print()
        print('Quit')


def run_from_command_line():
    parser = argparse.ArgumentParser(
        description='Solves the card game Machiavelli.')
    parser.add_argument('table', type=str, nargs='?', help=
        'The cards currently played on the table.  '
        'Example: 1c,2c,3c,4c,7c,8c,9c')
    parser.add_argument('hand', type=str, nargs='?', help=
        'The cards currently in your hand.  Example: 3d,7d,kh')
    parser.add_argument('--pretty', action='store_true', help=
        'Prints cleaner looking card displays')
    parser.add_argument('--simple', action='store_false', dest='pretty', help=
        'Disables --pretty')
    parser.add_argument('--color', action='store_true', default=not NO_COLOR,
        help=
        'Enables terminal colors')
    parser.add_argument('--nocolor', action='store_false', dest='color', help=
        'Disables terminal colors')
    parser.add_argument('--emoji', action='store_true', help=
        'Prints cards suits using Emoji (♠️ , ♣️ , ♦️ , ♥️ ) intead of (s, c, d, h)')
    parser.add_argument('--noemoji', action='store_false', dest='emoji', help=
        'Prints cards suits using the letters s, c, d, h for spades, clubs, diamonds, hearts')

    args = parser.parse_args()
    if args.color:
        colorama.init()
    main(args.table, args.hand, pretty=args.pretty, color=args.color,
         emoji=args.emoji)
