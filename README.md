
## Overview

The game simulates campus exploration with movement, item trading, quests, difficulty levels, and save/load support.

Core implementation goals:

- Match the required command loop behavior.
- Keep event clues and quest answers configurable from an external file.

## Project Files

- `main.py`: Main game logic and command loop.
- `event_info.json`: Location event messages and quest answers.

## Requirements

- Python 3.9+

## Run

```bash
python main.py
```

If you use the project virtual environment:

```bash
./.venv/bin/python main.py
```

## Commands

| Command | Description |
| --- | --- |
| 상태 | Show money, HP, location, and east/west/south/north neighbors |
| 동 / 서 / 남 / 북 | Move one tile in the specified direction |
| 상호작용 | Show available interactions at current place |
| 구매 | Buy items where buying is available |
| 판매 | Sell items where selling is available |
| 가방 | Show and consume bag items by name or index |
| 임무 | Start, progress, or report quests depending on location |
| 임무목록 | Show active quests |
| 난이도 | View/change difficulty (쉬움/보통/어려움) |
| 저장 | Save current state to JSON |
| 불러오기 | Load saved state by index or path |
| 종료 | Exit the game |

## Event Data Configuration

Edit `event_info.json` to change clue text and quest answers:

- `events`: keyed by place name.
- `quest_answers.corruption`: answer expected in 본관.
- `quest_answers.hygiene`: answer expected in 세브란스.

## Save/Load Format

Save files use JSON with:

- Player state (money, HP, bag)
- Current location
- Current time
- Difficulty
- Quest states
- Full input history

