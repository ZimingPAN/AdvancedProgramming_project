# Advanced Programming Text Adventure

This project implements the Yonsei advanced programming text game with movement, shopping, quests, save/load, dynamic event clues, and reproducible run logs.

## Run

Recommended command (grading format):

```bash
python run.py main.py
```

You can also run directly:

```bash
python main.py
```

## Required Output Files

Each run generates two numbered log files in the project root:

- `player_input.txt`: all user inputs with global sequence numbers
- `game_output.txt`: all game outputs with global sequence numbers

These files are overwritten at the start of each run for reproducibility.

## Event Data (Pickle)

The game loads dynamic event clues and mission answers from:

- `event_info.pkl`

Expected payload format:

```python
{
  "events": {
    "노천극장": "암표를 팔고있다.",
    "대강당": "행사 도시락이 방치되어 부패했다."
  },
  "answers": {
    "교내 부조리 수사": "노천극장",
    "교내 위생사건 수사": "대강당"
  }
}
```

If the pickle file is missing, the game will use defaults and create a default `event_info.pkl`.

## Commands

- `상태`: print money, HP, current location, and neighbors
- `동`/`서`/`남`/`북`: move one tile (blocked movement handled)
- `구매`: buy items when available
- `판매`: sell items when available
- `가방`: print inventory and consume items
- `임무`: quest interaction based on location
- `임무목록`: print active quests
- `난이도`: set 쉬움/보통/어려움
- `저장`: save state/location/quests/difficulty/input history
- `불러오기`: load from numbered list or relative/absolute path
- `상호작용`: choose from location-available interactions
- `종료`: exit game

## Notes

- Core domain classes include `Place`, `Quest`, and `Player`.
- `Player` encapsulates movement and status composition for modular scoring criteria.
