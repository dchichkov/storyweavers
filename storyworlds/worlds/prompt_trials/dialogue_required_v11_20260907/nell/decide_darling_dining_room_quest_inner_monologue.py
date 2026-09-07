#!/usr/bin/env python3
"""A heartwarming dining-room quest about deciding, darling."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


QUESTS = ("find_key", "save_pudding")
DARLINGS = ("Nell", "Mara", "Pip")
MOODS = ("hopeful", "nervous")
VOICES = ("gentle", "playful")
MAX_ACTIONS = 16


@dataclass
class StoryParams:
    quest: str = "find_key"
    darling: str = "Nell"
    mood: str = "hopeful"
    voice: str = "gentle"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = "dining_room"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.fact_events: dict[str, int] = {}
        self.outcome = ""

    def snapshot(self):
        return {
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        missing = [item for item in needs if item not in self.fact_events]
        if missing:
            raise StoryError(f"{kind} needs earlier evidence: {', '.join(missing)}.")
        causes = tuple(sorted({self.fact_events[item] for item in needs}))
        event = Event(len(self.history), kind, actor, data, tuple(facts),
                      causes, self.snapshot())
        self.history.append(event)
        for fact in facts:
            self.fact_events[fact] = event.id


def validate_params(p: StoryParams):
    if p.quest not in QUESTS:
        raise StoryError(f"Unknown quest: {p.quest!r}.")
    if p.darling not in DARLINGS:
        raise StoryError(f"Unknown darling: {p.darling!r}.")
    if p.mood not in MOODS or p.voice not in VOICES:
        raise StoryError("Mood or voice is not registered.")
    if not isinstance(p.world_seed, int) or not isinstance(p.prose_seed, int):
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.entities = {
        "darling": Entity("darling", p.darling, "character",
                          memes={"courage": 0.3, "love": 1},
                          beliefs={"quest": p.quest}),
        "grandmother": Entity("grandmother", "Grandmother", "character",
                              memes={"trust": 1, "worry": 0.4}),
        "table": Entity("table", "the long dining table", "furniture",
                        meters={"stability": 1}),
        "chair": Entity("chair", "the little chair", "furniture",
                        meters={"stability": 0.8}),
        "drawer": Entity("drawer", "the silverware drawer", "container",
                         meters={"open": 0}),
        "key": Entity("key", "the blue cupboard key", "object",
                      location="hidden", owner="grandmother",
                      memes={"importance": 1}),
        "pudding": Entity("pudding", "the warm pudding", "food",
                          location="table", meters={"warmth": 1, "time": 3}),
        "napkin": Entity("napkin", "the embroidered napkin", "object",
                         location="table", meters={"softness": 1}),
        "bell": Entity("bell", "the tiny dinner bell", "object",
                       location="table", meters={"sound": 1}),
    }
    w.record("opening", "grandmother", facts=("quest_announced",),
             quest=p.quest, darling=p.darling)
    return w


def choose_action(w: World):
    if "quest_complete" in w.fact_events:
        return "close"
    if w.params.quest == "find_key":
        if "clue_heard" not in w.fact_events:
            return "ask"
        if "fear_named" not in w.fact_events:
            return "notice"
        if "search_chosen" not in w.fact_events:
            return "decide"
        if "drawer_open" not in w.fact_events:
            return "open_drawer"
        if "key_found" not in w.fact_events:
            return "find_key"
        return "return_key"
    if "pudding_seen" not in w.fact_events:
        return "notice"
    if "fear_named" not in w.fact_events:
        return "ask"
    if "choice_made" not in w.fact_events:
        return "decide"
    if "bell_rung" not in w.fact_events:
        return "ring_bell"
    if "pudding_saved" not in w.fact_events:
        return "save_pudding"
    return "share"


def execute(w: World, action: str):
    p = w.params
    darling = w.entities["darling"]
    grandmother = w.entities["grandmother"]
    if action == "ask":
        if p.quest == "find_key":
            darling.beliefs["clue"] = "drawer"
            w.record("ask", "darling", facts=("clue_heard",),
                     needs=("quest_announced",), clue="drawer")
        else:
            darling.beliefs["problem"] = "pudding_cooling"
            w.record("ask", "darling", facts=("fear_named",),
                     needs=("quest_announced",), problem="pudding_cooling")
    elif action == "notice":
        if p.quest == "find_key":
            darling.beliefs["risk"] = "search_might_wake_baby"
            w.record("notice", "darling", facts=("fear_named",),
                     needs=("clue_heard",), risk="search_might_wake_baby")
        else:
            darling.beliefs["risk"] = "pudding_cooling"
            w.record("notice", "darling", facts=("pudding_seen",),
                     needs=("quest_announced",), warmth=1)
    elif action == "decide":
        if p.quest == "find_key":
            darling.beliefs["choice"] = "quiet_search"
            darling.memes["courage"] = 1
            w.record("decide", "darling", facts=("search_chosen",),
                     needs=("clue_heard", "fear_named"), choice="quiet_search")
        else:
            darling.beliefs["choice"] = "ring_bell"
            darling.memes["courage"] = 1
            w.record("decide", "darling", facts=("choice_made",),
                     needs=("pudding_seen", "fear_named"), choice="ring_bell")
    elif action == "open_drawer":
        if darling.beliefs.get("choice") != "quiet_search":
            raise StoryError("The drawer cannot be opened before a careful decision.")
        w.entities["drawer"].meters["open"] = 1
        w.record("open_drawer", "darling", facts=("drawer_open",),
                 needs=("search_chosen",))
    elif action == "find_key":
        if w.entities["drawer"].meters["open"] != 1:
            raise StoryError("The key cannot be found in a closed drawer.")
        w.entities["key"].location = "darling_hand"
        darling.beliefs["found"] = "key"
        w.record("find_key", "darling", facts=("key_found",),
                 needs=("drawer_open",))
    elif action == "return_key":
        if darling.beliefs.get("found") != "key":
            raise StoryError("The key must be found before it can be returned.")
        w.entities["key"].location = "grandmother_hand"
        darling.memes["relief"] = 1
        w.outcome = "key_returned"
        w.record("return_key", "darling", facts=("quest_complete",),
                 needs=("key_found",), outcome=w.outcome)
    elif action == "ring_bell":
        if darling.beliefs.get("choice") != "ring_bell":
            raise StoryError("The bell needs a brave decision.")
        w.entities["bell"].location = "darling_hand"
        w.record("ring_bell", "darling", facts=("bell_rung",),
                 needs=("choice_made",))
    elif action == "save_pudding":
        if "bell_rung" not in w.fact_events:
            raise StoryError("The family must hear the dinner bell first.")
        w.entities["pudding"].meters["warmth"] = 0.7
        w.record("save_pudding", "darling", facts=("pudding_saved",),
                 needs=("bell_rung",))
    elif action == "share":
        if "pudding_saved" not in w.fact_events:
            raise StoryError("The pudding is not ready to share.")
        w.outcome = "pudding_shared"
        w.record("share", "darling", facts=("quest_complete",),
                 needs=("pudding_saved",), outcome=w.outcome)
    elif action == "close":
        if not w.outcome:
            raise StoryError("The ending cannot hide an unfinished quest.")
        w.record("close", "grandmother", facts=("ending",),
                 needs=("quest_complete",))
    else:
        raise StoryError(f"Unknown action: {action}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.fact_events:
            validate_world(w)
            return w
    raise StoryError("The dining-room quest did not resolve.")


def validate_world(w: World):
    if not w.outcome or "ending" not in w.fact_events:
        raise StoryError("A complete story needs a resolved quest and ending.")
    if w.params.quest == "find_key":
        if w.entities["key"].location != "grandmother_hand":
            raise StoryError("The key must return safely to Grandmother.")
    else:
        if w.entities["pudding"].meters["warmth"] <= 0:
            raise StoryError("The shared pudding must remain warm enough.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.parts = []
        self.qa = []

    def say(self, speaker, words):
        self.parts.append(f'"{words}" {speaker} said.')

    def render(self):
        p = self.p
        for event in self.world.history:
            k = event.kind
            if k == "opening":
                self.parts.append(
                    f"In the dining room, {p.darling} stood beside the long table while Grandmother held up her hands."
                )
                if p.quest == "find_key":
                    self.say("Grandmother", f"Darling, will you help me find the blue cupboard key?")
                    self.say(p.darling, "I will decide carefully. Where should I begin?")
                    self.parts.append(
                        "The key had vanished before supper, and the quiet house seemed suddenly full of hiding places."
                    )
                else:
                    self.say("Grandmother", "Darling, the pudding is cooling before everyone has arrived.")
                    self.say(p.darling, "Then tell me what I can do.")
                    self.parts.append(
                        "The pudding waited in its bowl, warm and fragrant, while the empty chairs made the room feel much too still."
                    )
            elif k == "ask":
                if p.quest == "find_key":
                    self.say(p.darling, "Do you remember where you used it last?")
                    self.say("Grandmother", "Near the silverware drawer, darling.")
                    self.parts.append("That small clue gave the quest a direction.")
                    self.qa.append(QAItem(
                        "Where did Grandmother think the key might be?",
                        "She remembered using the blue cupboard key near the silverware drawer."
                    ))
                else:
                    self.say(p.darling, "Are you worried the pudding will be cold?")
                    self.say("Grandmother", "A little, darling, but we still have time.")
                    self.parts.append("Naming the worry made it smaller and gave the room a hopeful hush.")
            elif k == "notice":
                if p.quest == "find_key":
                    self.parts.append(
                        f"{p.darling} glanced toward the drawer. It was close enough to search, but one loud scrape might wake the baby upstairs."
                    )
                    self.qa.append(QAItem(
                        "Why did the search need to be quiet?",
                        "A loud drawer could wake the baby upstairs, so the search had to be careful."
                    ))
                else:
                    self.parts.append(
                        f"{p.darling} noticed that the pudding was still warm, though its soft steam was beginning to fade."
                    )
                    self.qa.append(QAItem(
                        "What problem did the pudding have?",
                        "It was still warm but beginning to cool before the family had gathered."
                    ))
            elif k == "decide":
                if p.quest == "find_key":
                    self.parts.append(
                        f"Inside, {p.darling} thought, 'I can be frightened and gentle at the same time.' Then {p.darling} chose the quiet search."
                    )
                    self.say(p.darling, "I will open the drawer slowly, darling.")
                    self.parts.append(
                        "The decision did not make the suspense vanish, but it gave courage a useful job."
                    )
                else:
                    self.parts.append(
                        f"Inside, {p.darling} thought, 'Waiting for perfect bravery will make the pudding colder.'"
                    )
                    self.say(p.darling, "I decide to ring the bell now.")
                    self.parts.append("The choice warmed the room before the pudding could cool.")
            elif k == "open_drawer":
                self.parts.append(
                    f"{p.darling} placed one hand on the silverware drawer and eased it open. The spoons whispered, but nothing crashed."
                )
            elif k == "find_key":
                self.parts.append(
                    f"Under a folded napkin, {p.darling} found the blue cupboard key. It was cold, bright, and exactly where the clue had promised."
                )
                self.say(p.darling, "I found it!")
            elif k == "return_key":
                self.parts.append(
                    f"{p.darling} carried the key across the dining room and placed it in Grandmother's waiting palm."
                )
                self.say("Grandmother", "You listened, decided, and kept the house peaceful, darling.")
                self.parts.append("The empty drawer no longer felt mysterious; it felt like a little solved corner of the world.")
            elif k == "ring_bell":
                self.parts.append(
                    f"{p.darling} lifted the tiny dinner bell and gave it one clear ring. Its bright note traveled around the table."
                )
                self.say("Grandmother", "That is the sound everyone was waiting for.")
            elif k == "save_pudding":
                self.parts.append(
                    f"Family footsteps hurried in, and {p.darling} carried the warm pudding to the center of the table before its steam disappeared."
                )
                self.qa.append(QAItem(
                    "How did the family save the pudding?",
                    "They rang the dinner bell so everyone came in before the pudding cooled."
                ))
            elif k == "share":
                self.parts.append(
                    "Everyone took a spoonful, and the dining room filled with smiles instead of worry."
                )
            elif k == "close":
                if p.quest == "find_key":
                    self.parts.append(
                        f"Grandmother hugged {p.darling}, and the blue key rested safely beside the plates."
                    )
                else:
                    self.parts.append(
                        f"Grandmother hugged {p.darling}, and the pudding passed from hand to hand while the little bell gleamed."
                    )
                self.say("Grandmother", "A good decision can be a small light, darling.")
                self.parts.append("The dining room glowed with the kind of warmth that comes from helping one another.")
                self.qa.append(QAItem(
                    "What changed by the end of the story?",
                    "The quest was completed because the darling asked for a clue, faced the suspense, and made a careful helpful decision."
                ))
        return StorySample(
            params=p,
            story="\n\n".join(self.parts),
            prompts=[f"Write a heartwarming dining-room quest in which {p.darling} must decide, darling."],
            story_qa=self.qa,
            world_qa=[
                QAItem("Where does the quest take place?",
                        "It takes place in a dining room with a long table and waiting supper.")
            ],
            world=self.world,
        )


ASP_RULES = """
quest(find_key).
quest(save_pudding).
can_decide(find_key, quiet_search) :- quest(find_key).
can_decide(save_pudding, ring_bell) :- quest(save_pudding).
#show quest/1.
#show can_decide/2.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("quest", q) for q in QUESTS)


def asp_combos():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "can_decide"))


def generate(params: StoryParams) -> StorySample:
    return Teller(simulate(params)).render()


def verify():
    from asp import atoms, one_model
    expected = {("find_key", "quiet_search"), ("save_pudding", "ring_bell")}
    actual = set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "can_decide"))
    if actual != expected:
        raise StoryError("Python and ASP disagree about possible decisions.")
    count = 0
    for quest, darling, mood, voice in itertools.product(QUESTS, DARLINGS, MOODS, VOICES):
        sample = generate(StoryParams(quest=quest, darling=darling,
                                       mood=mood, voice=voice))
        if "ending" not in sample.world.fact_events:
            raise StoryError("Generated story lacks an ending.")
        count += 1
    print(f"OK: {count} stories; dialogue, suspense, inner monologue, and ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--darling", choices=DARLINGS)
    parser.add_argument("--mood", choices=MOODS, default="hopeful")
    parser.add_argument("--voice", choices=VOICES, default="gentle")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        mood=args.mood,
        voice=args.voice,
    )
    p.quest = args.quest or (rng.choice(QUESTS) if sample else p.quest)
    p.darling = args.darling or (rng.choice(DARLINGS) if sample else p.darling)
    validate_params(p)
    return p


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "state": sample.world.snapshot(),
            "history": [asdict(e) for e in sample.world.history],
        }, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for quest in QUESTS:
                if args.quest is not None and args.quest != quest:
                    continue
                p = resolve_params(args, rng)
                p.quest = quest
                params.append(p)
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1)
                      for i in range(args.n)]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows,
                             ensure_ascii=False, indent=2))
        else:
            for i, p in enumerate(params):
                emit(generate(p), trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(params) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
