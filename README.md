# Machiavelli

A command-line solver for the card game [Machiavelli](https://en.wikipedia.org/wiki/Machiavelli_(Italian_card_game)).

# Install

Machiavelli is available on PyPI:

```bash
python3 -m pip install machiavelli
```

# Usage

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

```bash
$ machiavelli
...
```
