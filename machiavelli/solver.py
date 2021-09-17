import sys
import os
import itertools
from collections import defaultdict, Counter
import re

import numpy as np
import cvxpy as cp


NUMBERS = '123456789tjqk'  # Allowed alternate inputs: a->1, 0->t, 10->t, emoji
SUITS = 'scdh'
CARDS = [
    n+s
    for n, s in itertools.product(NUMBERS, SUITS)
]


class Solver:
    def __init__(self, quiet=False, pretty=True, color=True, emoji=True):
        self.quiet = quiet
        self.pretty = pretty
        self.color = color
        self.emoji = emoji

    def solve(self, cards, optional_cards=()):
        # Count cards
        cards = list(cards)
        card_codes = cards_to_codes(cards)
        optional_cards = list(optional_cards)
        assert min((Counter(cards)-Counter(optional_cards)).values(),
                   default=0) >= 0, (
            'optional_cards must be a subset of cards')
        card_counts = Counter(cards)
        optional_counts = Counter(optional_cards)

        # Make grid of cards to find sets and sequences
        seq_arr = np.zeros((len(SUITS), len(NUMBERS+NUMBERS[0:1])), dtype=int)
        for i, j in card_codes:
            seq_arr[i, j] += 1

        seq_arr[:, -1] = seq_arr[:, 0]
        seq_nonzero = (seq_arr > 0).astype(int)

        # Extract sets, sequences, and find disconnected cards
        find_seq = np.concatenate([
                seq_nonzero[:, 0:1] + seq_nonzero[:, 1:2],
                seq_nonzero[:, :-2] + seq_nonzero[:, 1:-1] + seq_nonzero[:, 2:],
            ], axis=1)
        alone = find_seq * seq_nonzero[:, :-1] == 1
        alone[:, 0] &= seq_nonzero[:, -2] == 0
        find_set = np.sum(seq_nonzero, axis=0)[:-1]
        alone[:, find_set >= 3] = False

        # Build a list of all possible sequences using the current cards
        seq_list = []  # Only the max length sequences, no overlap
        seq_list_full = []
        for i in range(len(SUITS)):
            j = 0
            while j < len(NUMBERS):
                if find_seq[i, j] >= 3:
                    jj = j+1
                    while jj < len(NUMBERS) and find_seq[i, jj] >= 3:
                        jj += 1
                    seq = (np.array([np.full(jj-j+2, i), range(j-1, jj+1)]).T
                           % len(NUMBERS))
                    seq_list.append(seq[:13])
                    seq_list_full.append(seq[:13])
                    for l in reversed(range(3, min(13, len(seq)))):
                        for ll in range(len(seq)-l+1):
                            seq_list_full.append(seq[ll:l+ll])
                    j = jj - 1
                j += 1

        # Build a list of all possible sets using the current cards
        set_list = []  # Only the max length sets, no overlap
        set_list_full = []
        arange4 = np.arange(4)
        for j in range(len(NUMBERS)):
            if find_set[j] < 3:
                continue
            group = np.array([
                    arange4[seq_nonzero[:, j] > 0],
                    np.full(find_set[j], j)
                ]).T
            set_list.append(group)
            set_list_full.append(group)
            if len(group) == 4:
                set_list_full.append([group[0], group[1], group[2]])
                set_list_full.append([group[1], group[2], group[3]])
                set_list_full.append([group[0], group[2], group[3]])
                set_list_full.append([group[0], group[1], group[3]])

        # Map each card to the list of groups it could participate in
        card_options = defaultdict(list)
        for seq in itertools.chain(set_list_full, seq_list_full):
            for i, j in seq:
                card_options[i, j].append(frozenset((i, j) for i, j in seq))

        def clean_solution(sol):
            '''Make pretty strings to display a solution'''
            if sol is None:
                return 'no solution', ''
            selected = sorted((
                    name
                    for name, cnt in sol.items()
                    for _ in range(cnt)
                ),
                key=sort_key
            )
            remaining_cnt = (
                Counter(cards)
                - Counter(c
                          for name, cnt in sol.items()
                          for name2 in [name] * cnt
                          for c in name.replace('_', '').split(','))
            )
            hand = ','.join(sorted_cards(remaining_cnt.elements()))
            using_cnt = Counter(optional_cards) - remaining_cnt
            hand_use = ','.join(sorted_cards(using_cnt.elements()))
            out = f"({') ('.join(selected)})"
            for card in using_cnt.keys():
                if using_cnt[card] <= 1:
                    i = out.find(card)
                    if i >= 0:
                        out = f'{out[:i]}[ {card} ]{out[i+2:]}'
                else:
                    out = out.replace(card, f'[ {card} ]')
            if not sol:
                out = 'no cards'
            else:
                out = self.pretty_cards(out)
            if not hand:
                hand = 'WIN'
            else:
                hand = self.pretty_cards(hand)
            if hand_use:
                hand = f'{hand} -- use: {self.pretty_cards(hand_use)}'
            return out, hand

        def solution_size(sol):
            '''The number of cards used by the solution.'''
            if sol is None:
                return 0
            return sum(
                len(name.split(',')) * cnt
                for name, cnt in sol.items()
            )

        def print_sol(sol):
            '''Print the solution.'''
            extra = len(card_codes)-solution_size(sol)
            table, hand = clean_solution(sol)
            if optional_cards:
                msg = f'--- {extra} left ---'
                if self.color:
                    import termcolor
                    if extra >= len(optional_cards):
                        self.print(termcolor.colored(msg, 'yellow'))
                    elif extra > 0:
                        self.print(termcolor.colored(msg, 'green'))
                    else:
                        self.print(termcolor.colored(msg, 'green',
                                                     attrs=['reverse']))
                else:
                    self.print(msg)
                self.print(f'hand: {hand}')
            self.print(f'table: {table}')

        # Check for an empty solution (otherwise causes the solver to fail)
        if len(seq_list_full) + len(set_list_full) == 0:
            # No solutions
            if cards == optional_cards:  # Set comparison
                sol = {}
            else:
                sol = None
            print_sol(sol)
            return sol

        # Encode as an integer program
        possible_groups = [
            codes_to_cards(group)
            for group in itertools.chain(set_list_full, seq_list_full)
        ]
        card_idx = {card: i for i, card in enumerate(card_counts)}
        card_mat = np.zeros((len(possible_groups), len(card_counts)),
                            dtype=bool)
        for i, group in enumerate(possible_groups):
            for card in group:
                card_mat[i, card_idx[card]] = True
        card_min = np.zeros(len(card_counts), dtype=int)
        card_max = np.zeros(len(card_counts), dtype=int)
        for card in card_counts.keys():
            max_count = card_counts[card]
            min_count = max_count - optional_counts[card]
            card_min[card_idx[card]] = min_count
            card_max[card_idx[card]] = max_count
        group_max = np.array([
            1 + all(card_counts[card] >= 2 for card in group)
            for group in possible_groups
        ])

        # Setup CVXPY
        x = cp.Variable(len(possible_groups), integer=True)
        constraints = [
            card_mat.T @ x >= card_min,
            card_mat.T @ x <= card_max,
            x <= group_max,
            x >= 0
        ]
        obj = cp.Maximize(sum(card_mat.T @ x) - sum(x) / 1024)
        problem = cp.Problem(obj, constraints)

        # Solve
        cost = problem_solve_suppress_stdout(problem, verbose=False)
        if isinstance(cost, str) or x.value is None:
            self.print_err(f'solver failed: {problem.status} ({cost})',
                           RuntimeError)
        if x.value is None:
            sol = None
            print_sol(sol)
            return sol
        else:
            sol = {
                cards_to_str(group): round(val)
                for group, val in zip(possible_groups, x.value)
                if round(val) > 0
            }

        # Verify valid solution
        sol_card_counts = sum((
                Counter(group_str.split(','))
                for group_str, cnt in sol.items()
                for _ in range(cnt)
            ),
            start=Counter()
        )
        remaining_counts = Counter(card_counts)
        remaining_counts.subtract(sol_card_counts)
        used_hand_counts = Counter(optional_counts)
        used_hand_counts.subtract(remaining_counts)
        if (any(val < 0 for val in remaining_counts.values())
                or any(val < 0 for val in used_hand_counts.values())):
            # Invalid solution
            sol = None

        # Print and return in a sorted, easy-to-use form
        print_sol(sol)
        selected = [
            name.split(',')
            for name in sorted((
                    name
                    for name, cnt in sol.items()
                    for _ in range(cnt)
                ),
                key=sort_key
            )
        ]
        return selected

    def play_hand(self, table, hand=''):
        '''Convenience method to parse and check inputs and check the table
        state is solvable before solving table+hand.'''
        if isinstance(table, str):
            table = parse_cards(table)
        if isinstance(hand, str):
            hand = parse_cards(hand)
        if isinstance(table, Counter):
            table = list(table.elements())
        if isinstance(hand, Counter):
            hand = list(hand.elements())
        if max(Counter(table+hand).values(), default=0) > 2:
            for c, n in Counter(table+hand).most_common(1):
                self.print_err(f'more than two of card: {c} (x{n})', ValueError)
        for c in table+hand:
            if c not in CARDS:
                raise ValueError(f'invalid card: {c}')
        self.print()
        if hand:
            self.print('### Before your play ###')
            self.solve(table)
            self.print()
        self.print('### Solve ###')
        return self.solve(table+hand, hand)

    def print(self, *args, **kwargs):
        if not self.quiet:
            print(*args, **kwargs)

    def print_err(self, msg, err_type):
        if self.quiet:
            raise err_type(msg)
        else:
            if self.color:
                import termcolor
                print(termcolor.colored(f'Error: {msg}', 'red'),
                      file=sys.stderr)
            else:
                print(f'Error: {msg}', file=sys.stderr)

    def pretty_cards(self, cards_str):
        if self.emoji:
            cards_str = cards_str.replace('s', '♠️ ').replace('c', '♣️ ')
            cards_str = cards_str.replace('d', '♦️ ').replace('h', '♥️ ')
        if self.pretty:
            cards_str = cards_str.replace('1', 'A').replace('t', '10')
            cards_str = cards_str.replace(',', ' ').upper()
        if self.emoji:
            if self.color:
                import termcolor
                end_marks = termcolor.colored('____', 'white', attrs=['reverse']
                                             ).split('____')
                def mark(match):
                    return (
                        end_marks[-1]
                        + termcolor.colored(match[1], 'green',
                                            attrs=['reverse'])
                        + end_marks[0]
                    )
                cards_str = re.sub(r'\[ ([^\]]*) \]', mark, cards_str)
                cards_str = termcolor.colored(cards_str, 'white',
                                              attrs=['reverse'])
        elif self.color:
            import termcolor
            def mark(match):
                return termcolor.colored(match[1], 'green', attrs=['underline'])
            cards_str = re.sub(r'\[ ([^[\]]*) \]', mark, cards_str)
        return cards_str

def problem_solve_suppress_stdout(problem, **kwargs):
    '''Suppress diagnostic messages printed by CVXPY C-libraries.'''
    dup_success = False
    stdout_cp = None
    devnull = None
    try:
        stdout_cp = os.dup(1)
        devnull = open(os.devnull, 'w')
        os.dup2(devnull.fileno(), 1)
        dup_success = True
        return problem.solve(**kwargs)
    except:
        if dup_success:
            raise
        else:
            # Give up and run without stdout suppression
            return problem.solve(**kwargs)
    finally:
        if devnull is not None:
            devnull.close()
        if stdout_cp is not None:
            os.dup2(stdout_cp, 1)
            os.close(stdout_cp)

def sort_key(s):
    s = s.lower()
    s = s.replace('a', '1').replace('q', 'i')
    s = s.replace('j', 'h').replace('s', 'b').replace('t', 'b')
    # Sort sequences after sets
    if ',' in s and not all(ss[:1] == s[:1] for ss in s.split(',')):
        s = 'z_' + s
    return s

def sort_key_k(s):
    return sort_key(s).replace('1', 'l')

def sorted_cards(cards):
    '''Returns the cards sorted nicely.'''
    cards = list(cards)
    if (any('k' in card for card in cards)
            and not any('2' in card for card in cards)):
        cards.sort(key=sort_key_k)
    else:
        cards.sort(key=sort_key)
    return cards

def cards_to_codes(cards):
    '''Converts a list of card names to (suit_index, rank_index) tuples.'''
    return np.array([
        (SUITS.index(s), NUMBERS.index(n))
        for n, s in cards
    ])

def codes_to_cards(codes):
    '''Converts a list of (suit_index, rank_index) tuples to card names.'''
    return [
        f'{NUMBERS[j]}{SUITS[i]}'
        for i, j in codes
    ]

def codes_to_str(codes):
    '''Converts a list of card codes (index tuples) to a sorted,
    comma-separated, printable string.'''
    return cards_to_str(codes_to_cards(codes))

def cards_to_str(cards):
    '''Converts a list of card names to a sorted, comma-separated, printable
    string.'''
    return ','.join(sorted_cards(cards))


class ParseError(RuntimeError): pass

def parse_cards(cards_str):
    '''Parse a comma-separated list of cards.

    Converts common variants of card names such as 10s->ts, ah->1h, 0d->td
    K♥️ ->kh.
    '''
    # Normalize
    cards_nrm = cards_str.lower()
    cards_nrm = cards_nrm.replace('10', 't').replace('a', '1').replace('0', 't')
    cards_nrm = cards_nrm.replace('♠️', 's').replace('♣️', 'c')
    cards_nrm = cards_nrm.replace('♦️', 'd').replace('♥️', 'h')
    # Parse
    cards = [s.strip() for s in cards_nrm.split(',')]
    # Verify no invalid cards
    for i, card in enumerate(cards):
        if card and card not in CARDS:
            raise ParseError(f'''Invalid card "{cards_str.split(',')[i]}"''')
    cards = [card for card in cards if card]
    return cards

def input_cards(input_msg, shortcuts=None):
    '''Prompts for input of a list of cards and returns the parsed list.

    If the input is invalid, prints an error and prompts again.
    If 'x' is entered, raises a KeyboardInterrupt.
    If a shortcuts dictionary is given and `user_input in shortcuts`
    shortcuts[user_input] will be parsed instead (ensuring user_input is
    lowercase).
    '''
    while True:
        try:
            cards_str = input(input_msg)
            cards_str = cards_str.strip().lower()
            if cards_str == 'x':
                raise KeyboardInterrupt()
            if shortcuts and cards_str in shortcuts:
                cards_str = shortcuts[cards_str]
            return parse_cards(cards_str)
        except ParseError as e:
            print(str(e), file=sys.stderr)
