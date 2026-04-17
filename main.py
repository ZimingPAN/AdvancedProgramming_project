from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Callable


DIRECTION_DELTAS: dict[str, tuple[int, int]] = {
    "동": (0, 1),
    "서": (0, -1),
    "남": (1, 0),
    "북": (-1, 0),
}

DIFFICULTY_HP_COST: dict[str, float] = {
    "쉬움": 0.5,
    "보통": 1.0,
    "어려움": 2.0,
}

ITEM_HP_GAIN: dict[str, float] = {
    "두쫀쿠": 10.0,
    "카페라떼": 5.0,
}

MAP_GRID: list[list[str | None]] = [
    ["종합관", "본관", "경영관", "노천극장", "새천년관", "이윤재관"],
    ["백양관", "백양로5", "대강당", "음악관", "알렌관", "ABMRC"],
    ["중앙도서관", "독수리상", "학생회관", "루스채플", "재활병원", "치과대학"],
    ["체육관", "백양로3", "공터2", "광혜원", "어린이병원", "세브란스"],
    ["공학관", "백양로2", "백주년기념관", "안과병원", "제중관", None],
    ["공학원", "백양로1", "공터1", "암병원", "의과대학", None],
    ["연대앞 버스정류장", "정문", "스타벅스", "세브란스 버스정류장", None, None],
]

DEFAULT_EVENT_DATA = {
    "events": {
        "중앙도서관": "자리에 짐을 잔뜩 올려서 차지하고, 키오스크에서 배석받은 학생이 와도 비켜주지 않는 빌런이 있다.",
        "공터2": "학생회관에서 버린 음식물쓰레기가 부패하여 학생회관으로 흘러들어가고있다!",
        "노천극장": "암표를 팔고있는 사람이 보인다.",
    },
    "quest_answers": {
        "corruption": "중앙도서관",
        "hygiene": "공터2",
    },
}


@dataclass
class Place:
    name: str
    buy_prices: dict[str, int] = field(default_factory=dict)
    sell_prices: dict[str, int] = field(default_factory=dict)


@dataclass
class Quest:
    quest_id: str
    title: str
    description: str
    status: str = "inactive"


class TextAdventureGame:
    def __init__(self) -> None:
        self.grid = MAP_GRID
        self.places = self._build_places()

        self.position = self._find_position("연대앞 버스정류장")
        if self.position is None:
            raise RuntimeError("시작 위치를 지도에서 찾을 수 없습니다.")

        self.money = 10000
        self.hp = 10.0
        self.current_time = "11:00"
        self.difficulty = "보통"
        self.bag: dict[str, int] = {}
        self.input_history: list[str] = []
        self.game_over = False

        self.quests: dict[str, Quest] = {
            "intro_news": Quest(
                quest_id="intro_news",
                title="독수리상에서 소식 듣기",
                description="학교에서 어떤 일들이 일어나고있는지 소식들이 모이는 독수리상에서 알아보자.",
            ),
            "corruption": Quest(
                quest_id="corruption",
                title="교내 부조리 수사",
                description="교내 어딘가에서 부조리가 일어나고있다. 이동하고 상호작용을 해서 부조리를 찾아서 본관에 보고하라.",
            ),
            "hygiene": Quest(
                quest_id="hygiene",
                title="교내 위생사건 수사",
                description="학생들이 단체로 식중독에 걸렸다. 이동하고 상호작용을 해서 위생사건의 원인을 찾아서 세브란스에 보고하라.",
            ),
        }

        self.events: dict[str, str] = {}
        self.quest_answers: dict[str, str] = {
            "corruption": "중앙도서관",
            "hygiene": "공터2",
        }
        self._load_event_data()

        self.command_map: dict[str, Callable[[], None]] = {
            "상태": self.show_status,
            "임무목록": self.show_quest_list,
            "가방": self.open_bag,
            "구매": self.buy_items,
            "판매": self.sell_items,
            "임무": self.quest_interaction,
            "상호작용": self.interaction_menu,
            "저장": self.save_game,
            "불러오기": self.load_game,
            "난이도": self.change_difficulty,
            "도움말": self.show_help,
        }

    @property
    def current_place_name(self) -> str:
        row, col = self.position
        name = self.grid[row][col]
        if name is None:
            raise RuntimeError("현재 위치가 비어있는 칸입니다.")
        return name

    @property
    def current_place(self) -> Place:
        return self.places[self.current_place_name]

    def run(self) -> None:
        self._print_intro()
        self.show_help()

        while not self.game_over:
            command = self.ask("입력: ").strip()
            if not command:
                continue

            if command in DIRECTION_DELTAS:
                self.move(command)
                continue

            if command in {"종료", "quit", "exit"}:
                print("게임을 종료합니다.")
                break

            action = self.command_map.get(command)
            if action is None:
                print("알 수 없는 입력입니다. 도움말을 확인하세요.")
                continue

            action()

    def _print_intro(self) -> None:
        print("송도 생활을 마치고 신촌에 처음 도착했다. 연대앞 버스정류장이다.")
        print("학교에 들어가기 위해 정문에서 상호작용을 한다.")
        print("학교에서 어떤 일이 벌어지고있을까?")
        print("배가 고프다. 처음의 배고픈 상태는 HP=10이다.")
        print("계좌에는 10,000원이 들어있다.")

    def show_help(self) -> None:
        print("가능한 입력: 상태, 동/서/남/북, 구매, 판매, 임무, 임무목록, 가방, 저장, 불러오기, 난이도, 상호작용, 종료")

    def ask(self, prompt: str) -> str:
        try:
            value = input(prompt).strip()
        except EOFError:
            self.game_over = True
            return "종료"
        self.input_history.append(value)
        return value

    def _build_places(self) -> dict[str, Place]:
        places: dict[str, Place] = {}
        for row in self.grid:
            for name in row:
                if name is None:
                    continue
                places[name] = Place(name=name)

        for name in ["학생회관"]:
            places[name].buy_prices = {"두쫀쿠": 5000, "카페라떼": 3000}

        for name in ["스타벅스", "ABMRC"]:
            if name in places:
                places[name].buy_prices = {"두쫀쿠": 4000, "카페라떼": 2000}

        high_sell = ["체육관", "공학관", "공학원", "재활병원", "어린이병원", "종합관", "노천극장"]
        for name in high_sell:
            places[name].sell_prices = {"두쫀쿠": 7000, "카페라떼": 4000}

        medium_sell = [
            "중앙도서관",
            "독수리상",
            "백양관",
            "대강당",
            "백주년기념관",
            "안과병원",
            "암병원",
            "새천년관",
            "알렌관",
            "제중관",
            "의과대학",
            "치과대학",
            "세브란스",
            "본관",
            "경영관",
        ]
        for name in medium_sell:
            if name in places:
                places[name].sell_prices = {"두쫀쿠": 6000, "카페라떼": 3000}

        return places

    def _load_event_data(self) -> None:
        data_path = Path(__file__).resolve().parent / "event_info.json"

        if not data_path.exists():
            data = DEFAULT_EVENT_DATA
        else:
            try:
                data = json.loads(data_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                print("event_info.json 형식이 잘못되어 기본 데이터를 사용합니다.")
                data = DEFAULT_EVENT_DATA

        self.events = dict(data.get("events", {}))

        loaded_answers = data.get("quest_answers", {})
        corruption_answer = loaded_answers.get("corruption", self.quest_answers["corruption"])
        hygiene_answer = loaded_answers.get("hygiene", self.quest_answers["hygiene"])
        self.quest_answers = {
            "corruption": str(corruption_answer),
            "hygiene": str(hygiene_answer),
        }

    def _find_position(self, place_name: str) -> tuple[int, int] | None:
        for r, row in enumerate(self.grid):
            for c, name in enumerate(row):
                if name == place_name:
                    return (r, c)
        return None

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < len(self.grid) and 0 <= col < len(self.grid[row])

    def _neighbor_name(self, delta: tuple[int, int]) -> str:
        row, col = self.position
        nr, nc = row + delta[0], col + delta[1]
        if not self._in_bounds(nr, nc):
            return "막힘"

        name = self.grid[nr][nc]
        if name is None:
            return "막힘"
        return name

    def _format_number(self, value: float) -> str:
        if float(value).is_integer():
            integer_value = int(value)
            if abs(integer_value) >= 10000:
                return f"{integer_value:,}"
            return str(integer_value)
        return f"{value:,.1f}"

    def _available_interactions(self) -> list[str]:
        interactions: list[str] = []

        if self.current_place.buy_prices:
            interactions.append("구매")
        if self.current_place.sell_prices:
            interactions.append("판매")
        if self.current_place_name in {"정문", "독수리상", "본관", "세브란스", "이윤재관"}:
            interactions.append("임무")

        return interactions

    def show_status(self) -> None:
        east = self._neighbor_name((0, 1))
        west = self._neighbor_name((0, -1))
        south = self._neighbor_name((1, 0))
        north = self._neighbor_name((-1, 0))

        print(f"계좌의 잔액 = {self._format_number(self.money)}원")
        print(f"HP = {self._format_number(self.hp)}")
        print(f"현재위치 = {self.current_place_name}")
        print(f"동서남북 = {east}, {west}, {south}, {north}")

    def show_quest_list(self) -> None:
        active_quests = [q for q in self.quests.values() if q.status == "active"]
        if not active_quests:
            print("진행 중인 임무가 없다.")
            return

        for quest in active_quests:
            print(f"{quest.title} - {quest.description}")

    def move(self, direction: str) -> None:
        delta = DIRECTION_DELTAS[direction]
        row, col = self.position
        nr, nc = row + delta[0], col + delta[1]

        if not self._in_bounds(nr, nc) or self.grid[nr][nc] is None:
            print("그 방향은 막혔어.")
            return

        self.position = (nr, nc)
        self.hp = max(0.0, self.hp - DIFFICULTY_HP_COST[self.difficulty])

        interactions = self._available_interactions()
        move_line = f"{self.current_place_name}에 도착했다."
        if interactions:
            move_line += f" [{', '.join(interactions)}]"
        print(move_line)

        event_message = self.events.get(self.current_place_name)
        if event_message:
            print(event_message)

    def open_bag(self) -> None:
        if not self._has_any_item():
            print("가방이 비어있다.")
            return

        while True:
            print("가방을 엽니다 [" + self._bag_summary() + "]")
            choice = self.ask("물건 이름 또는 번호 입력 (엔터=종료): ")
            if choice == "":
                print("가방을 닫습니다.")
                return

            item_name = self._resolve_item_choice(choice)
            if item_name is None or self.bag.get(item_name, 0) <= 0:
                print("사용할 수 없는 물건이다.")
                continue

            self.bag[item_name] -= 1
            self.hp += ITEM_HP_GAIN[item_name]
            print(f"{item_name}를 먹었습니다. HP={self._format_number(self.hp)}")

    def _has_any_item(self) -> bool:
        return any(count > 0 for count in self.bag.values())

    def _bag_summary(self) -> str:
        visible = [f"{name} x{count}" for name, count in self.bag.items() if count > 0]
        if not visible:
            return "비어있음"
        return ", ".join(visible)

    def _resolve_item_choice(self, choice: str, items: list[str] | None = None) -> str | None:
        target_items = items if items is not None else list(ITEM_HP_GAIN.keys())
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(target_items):
                return target_items[index]
            return None

        if choice in target_items:
            return choice

        return None

    def buy_items(self) -> None:
        price_table = self.current_place.buy_prices
        if not price_table:
            print("여기서는 구매할 수 없다.")
            return

        item_names = list(price_table.keys())
        while True:
            for idx, item_name in enumerate(item_names, start=1):
                price = price_table[item_name]
                hp_gain = ITEM_HP_GAIN[item_name]
                print(f"{idx}) {item_name}: {price}원, HP가 {self._format_number(hp_gain)}만큼 증가한다.")
            print(f"{len(item_names) + 1}) 종료")

            choice = self.ask("입력: ")
            if choice == str(len(item_names) + 1):
                print("구매를 종료합니다.")
                return

            item_name = self._resolve_item_choice(choice, item_names)
            if item_name is None:
                print("잘못된 입력이다.")
                continue

            price = price_table[item_name]
            if self.money < price:
                print(f"{item_name} 구매를 실패했다. 계좌 잔액이 부족하다.")
                continue

            self.money -= price
            self.bag[item_name] = self.bag.get(item_name, 0) + 1
            print(f"{item_name}를 구매해서 가방에 넣었다. 계좌 잔액 = {self._format_number(self.money)}원")

    def sell_items(self) -> None:
        price_table = self.current_place.sell_prices
        if not price_table:
            print("여기서는 판매할 수 없다.")
            return

        while True:
            sellable_items = [
                name for name, count in self.bag.items() if count > 0 and name in price_table
            ]
            if not sellable_items:
                print("팔 것이 없어서 종료합니다.")
                return

            print("무엇을 판매하시겠습니까?")
            for idx, item_name in enumerate(sellable_items, start=1):
                print(f"{idx}) {item_name} x{self.bag[item_name]}")
            print(f"{len(sellable_items) + 1}) 종료")

            choice = self.ask("입력: ")
            if choice == str(len(sellable_items) + 1):
                print("판매를 종료합니다.")
                return

            item_name = self._resolve_item_choice(choice, sellable_items)
            if item_name is None:
                print("잘못된 입력이다.")
                continue

            self.bag[item_name] -= 1
            earned = price_table[item_name]
            self.money += earned
            print(
                f"{item_name}를 판매해서 {self._format_number(earned)}원을 벌었다. 계좌 잔액 = {self._format_number(self.money)}원"
            )

    def interaction_menu(self) -> None:
        options = self._available_interactions()
        if not options:
            print("여기서는 할 수 있는 상호작용이 없다.")
            return

        print("가능한 상호작용: " + ", ".join(options))
        choice = self.ask("실행할 상호작용 (엔터=취소): ")
        if choice == "":
            return

        if choice not in options:
            print("현재 위치에서는 그 상호작용을 할 수 없다.")
            return

        if choice == "구매":
            self.buy_items()
        elif choice == "판매":
            self.sell_items()
        elif choice == "임무":
            self.quest_interaction()

    def quest_interaction(self) -> None:
        location = self.current_place_name

        if location == "정문":
            self._quest_at_gate()
            return
        if location == "독수리상":
            self._quest_at_eagle_statue()
            return
        if location == "본관":
            self._quest_at_main_building()
            return
        if location == "세브란스":
            self._quest_at_severance()
            return
        if location == "이윤재관":
            self._quest_at_classroom()
            return

        print("여기서는 임무 상호작용이 없다.")

    def _quest_at_gate(self) -> None:
        intro = self.quests["intro_news"]
        if intro.status == "inactive":
            intro.status = "active"
            print("학교에서 어떤 일들이 일어나고있는지 소식들이 모이는 독수리상에서 알아보자.")
            print("[임무목록]에 임무가 추가되었습니다.")
            return

        if intro.status == "active":
            print("독수리상으로 가서 소식을 확인하자.")
            return

        print("정문 임무는 이미 완료했다.")

    def _quest_at_eagle_statue(self) -> None:
        intro = self.quests["intro_news"]
        if intro.status == "inactive":
            # Spec requires no extra message here if intro quest was never received.
            return

        if intro.status == "active":
            intro.status = "completed"
            print("다음의 임무가 해결되었다! [학교에서 어떤 일들이 일어나고있는지 소식들이 모이는 독수리상에서 알아보자.]")

        newly_activated = []
        for key in ["corruption", "hygiene"]:
            quest = self.quests[key]
            if quest.status == "inactive":
                quest.status = "active"
                newly_activated.append(quest)

        if newly_activated:
            for quest in newly_activated:
                print(f"{quest.title} - {quest.description}")
            return

        active = [q for q in [self.quests["corruption"], self.quests["hygiene"]] if q.status == "active"]
        if active:
            print("진행 중인 임무가 있다. 임무목록을 확인하자.")
            return

        print("독수리상에서 받을 수 있는 임무를 모두 완료했다.")

    def _quest_at_main_building(self) -> None:
        quest = self.quests["corruption"]
        if quest.status == "inactive":
            print("보고할 교내 부조리 수사가 없다.")
            return

        if quest.status == "completed":
            print("교내 부조리 수사는 이미 완료했다.")
            return

        answer = self.ask("교내 어디에 부조리가 있나? ")
        if self._normalize_text(answer) == self._normalize_text(self.quest_answers["corruption"]):
            quest.status = "completed"
            print("다음의 임무가 해결되었다! [교내 부조리 수사]")
            print("수업들으러 이윤재관 가야지!")
            return

        print("정답이 아니다. 사건관련정보를 더 찾아보자.")

    def _quest_at_severance(self) -> None:
        quest = self.quests["hygiene"]
        if quest.status == "inactive":
            print("보고할 교내 위생사건 수사가 없다.")
            return

        if quest.status == "completed":
            print("교내 위생사건 수사는 이미 완료했다.")
            return

        answer = self.ask("교내 어디에 식중독 원인이 있나? ")
        if self._normalize_text(answer) == self._normalize_text(self.quest_answers["hygiene"]):
            quest.status = "completed"
            print("다음의 임무가 해결되었다! [교내 위생사건 수사]")
            print("수업들으러 이윤재관 가야지!")
            return

        print("정답이 아니다. 사건관련정보를 더 찾아보자.")

    def _quest_at_classroom(self) -> None:
        corruption_done = self.quests["corruption"].status == "completed"
        hygiene_done = self.quests["hygiene"].status == "completed"

        if corruption_done and hygiene_done:
            print("부조리와 식중독 수사를 완료했구나! 수업은 이걸로 끝입니다. 또 만나요~")
            self.game_over = True
            return

        if corruption_done and not hygiene_done:
            print("부조리 수사를 완료했구나! 식중독 원인도 찾아주세요~")
            return

        if hygiene_done and not corruption_done:
            print("식중독 수사를 완료했구나! 부조리도 찾아주세요~")
            return

        if self.quests["intro_news"].status != "completed":
            print("독수리상에서 임무를 먼저 받아오자.")
            return

        print("아직 수사를 완료하지 못했다. 임무를 계속 진행하자.")

    def change_difficulty(self) -> None:
        print(f"현재 난이도 = {self.difficulty}")
        print("1) 쉬움")
        print("2) 보통")
        print("3) 어려움")

        choice = self.ask("변경할 난이도 입력 (엔터=유지): ")
        if choice == "":
            print("난이도를 유지합니다.")
            return

        mapping = {
            "1": "쉬움",
            "2": "보통",
            "3": "어려움",
            "쉬움": "쉬움",
            "보통": "보통",
            "어려움": "어려움",
        }
        selected = mapping.get(choice)
        if selected is None:
            print("지원하지 않는 난이도다.")
            return

        self.difficulty = selected
        print(f"난이도가 {self.difficulty}으로 변경되었다.")

    def save_game(self) -> None:
        filename = self.ask("저장 파일명 입력 (엔터=자동 생성): ")
        if filename == "":
            filename = f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.save.json"

        save_path = Path(filename).expanduser()
        if not save_path.is_absolute():
            save_path = Path.cwd() / save_path

        if save_path.suffix == "":
            save_path = save_path.with_name(save_path.name + ".save.json")

        payload = {
            "player": {
                "money": self.money,
                "hp": self.hp,
                "bag": self.bag,
            },
            "location": self.current_place_name,
            "time": self.current_time,
            "difficulty": self.difficulty,
            "quests": {key: quest.status for key, quest in self.quests.items()},
            "input_history": self.input_history,
        }

        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"저장 완료: {save_path}")

    def load_game(self) -> None:
        save_files = sorted(Path.cwd().glob("*.save.json"))
        if save_files:
            print("현재 폴더의 저장 파일:")
            for idx, save_file in enumerate(save_files, start=1):
                print(f"{idx}) {save_file.name}")

        choice = self.ask("불러올 번호 또는 파일 경로 입력: ")
        if choice == "":
            print("불러오기를 취소했다.")
            return

        if choice.isdigit() and save_files:
            index = int(choice) - 1
            if 0 <= index < len(save_files):
                target_path = save_files[index]
            else:
                print("잘못된 번호다.")
                return
        else:
            target_path = Path(choice).expanduser()
            if not target_path.is_absolute():
                target_path = Path.cwd() / target_path

        if not target_path.exists():
            print("해당 파일을 찾을 수 없다.")
            return

        try:
            payload = json.loads(target_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("불러오기에 실패했다. 파일 형식이 잘못되었다.")
            return

        self._apply_loaded_data(payload)
        print(f"불러오기 완료: {target_path}")

    def _apply_loaded_data(self, payload: dict) -> None:
        player = payload.get("player", {})
        self.money = int(player.get("money", self.money))
        self.hp = float(player.get("hp", self.hp))

        loaded_bag = player.get("bag", {})
        if isinstance(loaded_bag, dict):
            self.bag = {str(name): int(count) for name, count in loaded_bag.items() if int(count) >= 0}

        location_name = str(payload.get("location", self.current_place_name))
        location = self._find_position(location_name)
        if location is not None:
            self.position = location

        self.current_time = str(payload.get("time", self.current_time))

        loaded_difficulty = str(payload.get("difficulty", self.difficulty))
        if loaded_difficulty in DIFFICULTY_HP_COST:
            self.difficulty = loaded_difficulty

        quest_states = payload.get("quests", {})
        if isinstance(quest_states, dict):
            for key, status in quest_states.items():
                if key in self.quests and status in {"inactive", "active", "completed"}:
                    self.quests[key].status = status

        loaded_history = payload.get("input_history", self.input_history)
        if isinstance(loaded_history, list):
            self.input_history = [str(item) for item in loaded_history]

    def _normalize_text(self, text: str) -> str:
        return text.replace(" ", "").strip()


def main() -> None:
    game = TextAdventureGame()
    game.run()


if __name__ == "__main__":
    main()
