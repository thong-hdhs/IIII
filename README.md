# Mines 8x8 Multiclient Game

Simple two-player Mines game (8x8) with two modes: `survival` and `scoring`.

Files:

-   `server.py`: matchmaker and game session server.
-   `client.py`: Tkinter GUI client.
-   `common.py`: small JSON-line protocol helpers.

Quick start:

1. Start server:

```bash
python server.py
```

2. Start two clients (on same machine or different machines that can reach the server):

```bash
python client.py
```

Usage notes:

-   Use the Game->Connect menu to join a queue. Server pairs clients by mode (Survival/Scoring).
-   Each turn is 10s. In Survival, timeout = opponent wins. In Scoring, timeout = lose turn.
-   In Survival hitting a mine immediately loses. In Scoring hitting a mine subtracts a point; safe picks add a point.

This is a minimal, readable implementation intended to be extended. Contributions: improve error handling, authentication, visual polish, and persistent lobby.
