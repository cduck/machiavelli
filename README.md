# Machiavelli

A command-line solver for the card game [Machiavelli](https://en.wikipedia.org/wiki/Machiavelli_(Italian_card_game)).

In Machiavelli, cards are played and arranged in groups on the table.
You either draw one card or play any number of cards from your hand.
The only constraint is that at the end of your turn, all the cards on the table are grouped in valid sets or sequences of at least three each.
See the [complete rules here](https://en.wikipedia.org/wiki/Machiavelli_(Italian_card_game)).

Machiavelli is particularly nice to solve with a computer because the only game state that matters is the list of cards on the table and in your hand.
A valid grouping of cards can simply be recomputed from scratch with a [CSP](https://en.wikipedia.org/wiki/Constraint_satisfaction_problem) solver on each turn.
This solver translates the rules and objective of the game into an [integer program](https://en.wikipedia.org/wiki/Integer_programming) and uses [CVXPY](https://www.cvxpy.org/) to find the best move in a fraction of a second.

## Install

Machiavelli is available on PyPI:

```bash
python3 -m pip install machiavelli
```

## Usage

This package provides a command line tool to solve the card game Machiavelli.
The tool keeps track of the game state by prompting for cards drawn by you and cards played by anyone.
It will then tell you the "best" play (the play that uses the most cards from your hand).
1. Enter your initial hand of cards at the prompt e.g. `kh,td,jh,7d,3c,4s,7s,3d,2c,6s` (king of hearts, 10 of diamonds, ...).
2. Enter all cards played by others before your first turn e.g. `7c,8c,9c` (a sequence of clubs from 7 to 9).
3. Check the solution printout.
    - For output like `hand: 2c,3c,3d,4s,6s,7s,7d,td,jh,kh`, no cards are playable.  Draw one.
    - For output like `hand: 3d,7d,td,jc,jh,kh -- use: 1d,4s,5c,6s,7s`, the cards on the right are playable.  Rearrange the cards on the table and add yours as indicated e.g. `table: (1c,[1d],1h) ([5c],5d,5h) (2c,3c,4c) (2h,3h,4h) ([4s],5s,[6s],[7s]) (7c,8c,9c)`.
4. If you drew a card, enter it at the `Drawn card` prompt.
5. If you played, enter the cards you played at the prompt.
6. Record all cards played by the other players at the `Other plays` prompt.
7. Go to step 3 and repeat until you empty your hand.
8. Win.

## Demo Game
```bash
$ machiavelli --pretty --emoji
Enter starting hand: kh,jh,10d,7d,3c,4s,7s,3d,2c,6s	<- User input
Enter other plays: 9c,8c,7c				<- User input
Current game state: machiavelli 7c,8c,9c 2c,3c,3d,4s,
6s,7s,7d,td,jh,kh

### Before your play ###
table: (7♣️ 8♣️ 9♣️)

### Solve ###
--- 10 left ---
hand: 2♣️ 3♣️ 3♦️ 4♠️ 6♠️ 7♠️ 7♦️ 10♦️ J♥️ K♥️		<- Solver found no playable cards
table: (7♣️ 8♣️ 9♣️)

Enter drawn card(s) (or blank): jc			<- So draw one card
Enter my last play (or blank):
Enter other plays:					<- Other players only drew cards
Current game state: machiavelli 7c,8c,9c 2c,3c,3d,4s,
6s,7s,7d,td,jc,jh,kh

### Before your play ###
table: (7♣️ 8♣️ 9♣️)

### Solve ###
--- 11 left ---
hand: 2♣️ 3♣️ 3♦️ 4♠️ 6♠️ 7♠️ 7♦️ 10♦️ J♣️ J♥️ K♥️		<- Still no playable cards
table: (7♣️ 8♣️ 9♣️)

Enter drawn card(s) (or blank): ac			<- So draw another card
Enter my last play (or blank):
Enter other plays:
Current game state: machiavelli 7c,8c,9c 1c,2c,3c,3d,
4s,6s,7s,7d,td,jc,jh,kh

### Before your play ###
table: (7♣️ 8♣️ 9♣️)

### Solve ###
--- 9 left ---
hand: 3♦️ 4♠️ 6♠️ 7♠️ 7♦️ 10♦️ J♣️ J♥️ K♥️
                                -- use: A♣️ 2♣️ 3♣️	<- Solver found playable cards
table: (A♣️ 2♣️ 3♣️) (7♣️ 8♣️ 9♣️)			<- This is a valid play of
							   the cards on the table
Enter drawn card(s) (or blank):
Enter my last play (or "best"=1c,2c,3c): best
Enter other plays:
Current game state: machiavelli 1c,2c,3c,7c,8c,9c 3d,	<- (You can restart with these
4s,6s,7s,7d,td,jc,jh,kh					    arguments to restore game state)

...
...
...

Current game state: machiavelli 1c,1d,1d,1h,2s,2c,2d,
2d,2h,3s,3c,3d,3h,4s,4s,4c,4d,4h,5s,5c,5d,5h,6s,6c,6d,
6d,6h,7s,7s,7c,7c,7d,7d,7h,8s,8s,8c,8d,8d,8h,8h,9s,9s,
9c,9d,9h,ts,ts,tc,tc,td,th,th,js,js,jc,jc,jd,jd,jh,jh,
qs,qd,qh,ks,ks,kc,kh kh

### Before your play ###
table: (A♣️ A♦️ A♥️) (2♣️ 2♦️ 2♥️) (10♠️ 10♣️ 10♥️)
(J♠️ J♣️ J♦️ J♥️) (K♠️ K♣️ K♥️) (A♦️ 2♦️ 3♦️ 4♦️ 5♦️
6♦️ 7♦️ 8♦️ 9♦️ 10♦️ J♦️ Q♦️) (2♠️ 3♠️ 4♠️) (3♣️ 4♣️
5♣️ 6♣️ 7♣️) (3♥️ 4♥️ 5♥️ 6♥️ 7♥️ 8♥️) (4♠️ 5♠️ 6♠️
7♠️ 8♠️ 9♠️) (6♦️ 7♦️ 8♦️) (7♠️ 8♠️ 9♠️ 10♠️ J♠️ Q♠️
K♠️) (7♣️ 8♣️ 9♣️ 10♣️ J♣️) (8♥️ 9♥️ 10♥️ J♥️ Q♥️)

### Solve ###
--- 0 left ---
hand: WIN -- use: K♥️					<- Solver found a winning play!
table: (A♣️ A♦️ A♥️) (2♣️ 2♦️ 2♥️) (7♠️ 7♣️ 7♦️) (8♠️
8♦️ 8♥️) (10♠️ 10♣️ 10♥️) (J♠️ J♣️ J♦️ J♥️) (K♠️ K♣️
K♥️) (A♦️ 2♦️ 3♦️ 4♦️ 5♦️ 6♦️) (2♠️ 3♠️ 4♠️) (3♣️ 4♣️
5♣️ 6♣️ 7♣️ 8♣️ 9♣️ 10♣️ J♣️) (3♥️ 4♥️ 5♥️ 6♥️ 7♥️ 8♥️
9♥️ 10♥️ J♥️ Q♥️ K♥️) (4♠️ 5♠️ 6♠️ 7♠️ 8♠️ 9♠️) (6♦️
7♦️ 8♦️ 9♦️ 10♦️ J♦️ Q♦️) (9♠️ 10♠️ J♠️ Q♠️ K♠️)

Enter drawn card(s) (or blank): ^D
Quit
```

## Acknowledgements
Thanks to [Konstantinos Ameranis](https://github.com/kameranis) for help formulating the integer program and thanks to Konstantinos, Kevin, and Kunal for extensive play-testing and debugging.
