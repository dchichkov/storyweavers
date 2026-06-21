#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/winnings_repetition_friendship_conflict_detective_story.py
=========================================================================================

A standalone story world for a tiny detective tale: a child detective, repeated
clues, a friendship strain, and a winnings mystery that resolves with honesty.

The world is built from typed entities with physical meters and emotional memes.
The plot is state-driven: a mystery begins with repeated small events, a conflict
grows from suspicion, a reveal connects the winnings to the true culprit, and the
ending proves what changed in the world.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/winnings_repetition_friendship_conflict_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/winnings_repetition_friendship_conflict_detective_story.py --qa
    python storyworlds/worlds/gpt-5.4-mini/winnings_repetition_friendship_conflict_detective_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/winnings_repetition_friendship_conflict_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"evidence": 0.0, "stress": 0.0, "trust": 0.0, "joy": 0.0, "guilt": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "stress": 0.0, "trust": 0.0, "guilt": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    noise: str
    clue_spot: str
    public: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Event:
    id: str
    phrase: str
    repeat_phrase: str
    clue: str
    clue_kind: str
    affects: str
    joy: int = 1

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Prize:
    id: str
    phrase: str
    winnings: str
    amount: int
    object_label: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    detective: str
    friend: str
    detective_gender: str
    friend_gender: str
    event: str
    prize: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "school_fair": Setting("school_fair", "the school fair", "music and laughter", "the prize table"),
    "library": Setting("library", "the library", "soft whispering", "the reading nook"),
    "park": Setting("park", "the park", "birds and bicycles", "the bench"),
}

EVENTS = {
    "missing_tokens": Event(
        "missing_tokens",
        "the blue tokens went missing",
        "the blue tokens went missing again",
        "blue glitter",
        "glitter",
        "paw prints",
    ),
    "repeated_notes": Event(
        "repeated_notes",
        "the note kept showing up twice",
        "the note kept showing up twice again",
        "crumbs of chalk",
        "chalk",
        "chalk dust",
    ),
    "double_footprints": Event(
        "double_footprints",
        "two small footprints appeared in a row",
        "two small footprints appeared in a row again",
        "tiny mud marks",
        "mud",
        "mud",
    ),
}

PRIZES = {
    "cup_money": Prize("cup_money", "a little silver cup", "winnings", 5, "cup"),
    "jar_money": Prize("jar_money", "a jar of winnings", "winnings", 7, "jar"),
    "ticket_money": Prize("ticket_money", "a ticket envelope with winnings inside", "winnings", 9, "envelope"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Noah", "Ben", "Theo", "Finn"]


def _reset_story_meters(e: Entity) -> None:
    e.meters["evidence"] = 0.0
    e.meters["stress"] = 0.0
    e.meters["trust"] = 0.0
    e.meters["joy"] = 0.0
    e.meters["guilt"] = 0.0
    e.memes["joy"] = 0.0
    e.memes["stress"] = 0.0
    e.memes["trust"] = 0.0
    e.memes["guilt"] = 0.0
    e.memes["pride"] = 0.0


def clue_repetition(event: Event) -> str:
    return f"{event.repeat_phrase}."


def tell(setting: Setting, detective_name: str, friend_name: str, detective_gender: str,
         friend_gender: str, event: Event, prize: Prize) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    prize_ent = world.add(Entity(id="prize", kind="thing", type="thing", label=prize.object_label, role="winnings"))

    _reset_story_meters(detective)
    _reset_story_meters(friend)
    detective.memes["trust"] = 2.0
    friend.memes["trust"] = 2.0

    detective.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon at {setting.place}, {detective.id} and {friend.id} opened their little detective club. "
        f"{setting.noise} floated around them, and {setting.clue_spot} looked like the best place to search."
    )
    world.say(
        f"They were excited because {prize.phrase} held the day’s {prize.winnings}, and everybody wanted to know where it had gone."
    )

    world.para()
    world.say(
        f"First came the clue: {event.phrase}. Then it happened again. And again. "
        f"{clue_repetition(event)}"
    )
    detective.meters["evidence"] += 1
    friend.meters["evidence"] += 1
    detective.memes["stress"] += 1
    friend.memes["stress"] += 1

    world.say(
        f"{detective.id} frowned and looked at {friend.id}. 'You were near the {setting.clue_spot} first,' "
        f"{detective.id} said softly, but the second clue made the room feel suddenly sharp."
    )
    friend.memes["stress"] += 1
    friend.memes["guilt"] += 1
    detective.memes["trust"] -= 1
    friend.memes["trust"] -= 1

    world.para()
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head. 'I didn't take the {prize.winnings},' "
        f"{friend.pronoun()} said, and the two friends stopped smiling for a moment."
    )
    world.say(
        f"The same clue had shown up more than once, so {detective.id} noticed it was not a simple mistake. "
        f"That repetition was the real clue."
    )

    culprit = world.add(Entity(id="helper", kind="character", type="boy", role="helper", label="the helper"))
    culprit.memes["guilt"] = 2.0
    culprit.memes["trust"] = 0.0

    world.para()
    world.say(
        f"{detective.id} counted the marks and followed the pattern to the {setting.clue_spot}. "
        f"There, {culprit.label_word} was trying to hide {prize.phrase} behind a stack of cups."
    )
    culprit.meters["stress"] += 1
    culprit.meters["guilt"] += 1
    detective.meters["evidence"] += 1
    world.say(
        f"'The clue repeats because someone kept moving it,' {detective.id} said. "
        f"'The winnings were never lost. They were being carried away and brought back.'"
    )

    world.para()
    friend.memes["joy"] += 1
    detective.memes["joy"] += 1
    detective.memes["trust"] += 2
    friend.memes["trust"] += 2
    friend.memes["guilt"] = 0.0
    culprit.memes["guilt"] = 0.0
    prize_ent.meters["evidence"] = 1.0
    world.say(
        f"{culprit.label_word.capitalize()} looked ashamed and admitted it. He had wanted to play hero with the {prize.winnings}, "
        f"but he only made trouble. {friend.id} forgave him, and {detective.id} told him to ask first next time."
    )
    world.say(
        f"Then the friends put the {prize.winnings} back where it belonged, and {setting.place} felt calm again."
    )
    world.say(
        f"At the end, {detective.id} and {friend.id} stood together by {setting.clue_spot}, smiling at the recovered prize and the quiet, solved case."
    )

    world.facts.update(
        setting=setting,
        detective=detective,
        friend=friend,
        culprit=culprit,
        event=event,
        prize=prize,
        prize_ent=prize_ent,
        repeated=True,
        conflict=True,
        resolved=True,
        winnings=prize.winnings,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    fr = f["friend"]
    event = f["event"]
    prize = f["prize"]
    return [
        f'Write a detective story for a 3-to-5-year-old that includes the word "{prize.winnings}" and a clue that repeats.',
        f"Tell a friendship story where {d.id} and {fr.id} disagree for a moment, then solve a mystery together.",
        f"Write a small detective tale where repetition helps reveal who took the winnings.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    fr = f["friend"]
    culprit = f["culprit"]
    event = f["event"]
    prize = f["prize"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer=f"It is a detective story about {d.id}, {fr.id}, and a missing set of {prize.winnings}. The repeated clue is what helps solve it."
        ),
        QAItem(
            question=f"Why did {d.id} and {fr.id} have a conflict?",
            answer=f"{d.id} thought {fr.id} might know something, so the friends felt upset for a moment. The repeated clue showed that the problem was bigger than one wrong guess."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{d.id} followed the repeating clue to the hiding place and found {culprit.id}. The winnings were returned, and the friends made up."
        ),
    ]


KNOWLEDGE = {
    "detective": [(
        "What does a detective do?",
        "A detective looks closely for clues and follows patterns to solve a mystery."
    )],
    "repetition": [(
        "Why can repetition be a clue?",
        "When the same thing happens again and again, it can show a pattern. A pattern can help a detective understand what is really going on."
    )],
    "friendship": [(
        "What helps friends after a conflict?",
        "Friends help each other by telling the truth, listening, and forgiving when someone makes a mistake."
    )],
    "winnings": [(
        "What are winnings?",
        "Winnings are money or prizes that someone wins. People should share fairly and not hide them."
    )],
}

WORLD_QA_ORDER = ["detective", "repetition", "friendship", "winnings"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in WORLD_QA_ORDER:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for eid in EVENTS:
            for pid in PRIZES:
                combos.append((sid, eid, pid))
    return combos


def explain_rejection(_: str = "", __: str = "", ___: str = "") -> str:
    return "(No story: this world accepts the listed combinations.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small detective story world with repetition, friendship, conflict, and winnings.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--detective")
    ap.add_argument("--friend")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.event is None or c[1] == args.event)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, event, prize = rng.choice(sorted(combos))
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if dg == "girl" else "girl")
    detective = args.detective or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES)
    friend_pool = [n for n in (GIRL_NAMES if fg == "girl" else BOY_NAMES) if n != detective]
    friend = args.friend or rng.choice(friend_pool)
    return StoryParams(setting, detective, friend, dg, fg, event, prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.detective, params.friend, params.detective_gender,
                 params.friend_gender, EVENTS[params.event], PRIZES[params.prize])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
choice(setting(S)) :- setting(S).
choice(event(E)) :- event(E).
choice(prize(P)) :- prize(P).
story_valid(S,E,P) :- setting(S), event(E), prize(P).
repetition(E) :- event(E).
conflict(S,E,P) :- story_valid(S,E,P), repetition(E).
resolved(S,E,P) :- story_valid(S,E,P), conflict(S,E,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid in EVENTS:
        lines.append(asp.fact("event", eid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_valid/3."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo logic.")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, event=None, prize=None, detective=None, friend=None, detective_gender=None, friend_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def explain_response(_: str) -> str:
    return "(No response refusal in this world.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show story_valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams("school_fair", "Mia", "Leo", "girl", "boy", "missing_tokens", "cup_money")),
            generate(StoryParams("library", "Noah", "Ava", "boy", "girl", "repeated_notes", "jar_money")),
            generate(StoryParams("park", "Lily", "Ben", "girl", "boy", "double_footprints", "ticket_money")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
