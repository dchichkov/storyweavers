#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rabbi_reading_nook_quest_whodunit.py
======================================================================

A standalone tiny storyworld for a whodunit quest in a reading nook.

Premise
-------
A rabbi and a child search a cozy reading nook for a missing clue-object
(bookmark / note / key), follow small signs, and solve the mystery by noticing
who moved what and why.

The simulation is small but state-driven:
- typed entities carry physical meters and emotional memes
- clues are objects with locations and visibility
- suspects can move objects or leave traces
- a forward-chained rule engine turns hidden facts into visible suspicion and
  then into deduction, accusation, recovery, and resolution

The story reads like a little whodunit: there is a mystery, clues, a turn, and
an ending image that proves what changed.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/rabbi_reading_nook_quest_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/rabbi_reading_nook_quest_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/rabbi_reading_nook_quest_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "rabbi"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"rabbi": "the rabbi"}.get(self.type, self.label or self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    cozy_detail: str
    quest_focus: str
    light: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    trace: str
    kind: str
    hidden_until_found: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    alibi: str
    honesty: int
    likes_reading: bool = False
    clue_move: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Quest:
    id: str
    goal: str
    asks: str
    answer_image: str
    clue_needed: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_notice_trace(world: World) -> list[str]:
    out: list[str] = []
    nook = world.get("nook")
    for clue in [e for e in world.entities.values() if e.kind == "clue"]:
        if clue.found or clue.hidden_until_found:
            continue
        if clue.meters["visible"] >= THRESHOLD and clue.id not in world.fired:
            world.fired.add(( "notice", clue.id))
            nook.meters["mystery"] += 1
            out.append("__notice__")
    return out


def _r_deduce(world: World) -> list[str]:
    out: list[str] = []
    rabbi = world.get("rabbi")
    if rabbi.meters["clue_count"] >= THRESHOLD and ("deduce",) not in world.fired:
        world.fired.add(("deduce",))
        rabbi.memes["certainty"] += 1
        out.append("__deduce__")
    return out


CAUSAL_RULES = [Rule("notice_trace", "mystery", _r_notice_trace), Rule("deduce", "mystery", _r_deduce)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_visible(clue: Clue) -> bool:
    return clue.hidden_until_found is False


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for q in QUESTS:
        for c in CLUES:
            if q.clue_needed == c.id:
                out.append((q.id, c.id))
    return out


@dataclass
class StoryParams:
    setting: str
    quest: str
    clue: str
    suspect: str
    rabbi_name: str
    seeker_name: str
    seed: Optional[int] = None
    reveal_suspect: bool = False
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SETTINGS = {
    "reading_nook": Setting(
        id="reading_nook",
        place="a reading nook",
        cozy_detail="soft pillows leaned against a little shelf of books",
        quest_focus="the missing bookmark",
        light="a lamp with a warm yellow glow",
        tags={"reading_nook", "books"},
    )
}

QUESTS = {
    "find_bookmark": Quest(
        id="find_bookmark",
        goal="find the missing bookmark",
        asks="Who moved the bookmark, and where did it end up?",
        answer_image="the bookmark tucked back inside the open book",
        clue_needed="blue_thread",
        tags={"quest", "bookmark", "whodunit"},
    )
}

CLUES = {
    "blue_thread": Clue(
        id="blue_thread",
        label="blue thread",
        phrase="a tiny blue thread snagged on the shelf",
        where="under the lowest shelf",
        trace="the suspect's sweater had a loose blue thread",
        kind="fabric",
        tags={"thread", "fabric"},
    ),
    "page_mark": Clue(
        id="page_mark",
        label="page mark",
        phrase="a bent page left open like a pointing finger",
        where="inside the open book",
        trace="someone had paused at that page to hide something",
        kind="paper",
        tags={"book", "paper"},
    ),
}

SUSPECTS = {
    "quiet_child": Suspect(
        id="quiet_child",
        label="the quiet child",
        motive="to borrow the bookmark for a secret game",
        alibi="I only read beside the lamp",
        honesty=4,
        likes_reading=True,
        clue_move=True,
        tags={"child", "whodunit"},
    )
}

RABBI_TYPES = {"rabbi"}
GIRL_NAMES = ["Mina", "Sara", "Hannah", "Leah", "Noa", "Talia"]
BOY_NAMES = ["Ezra", "Noam", "Ari", "Matan", "Yosef", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit quest in a reading nook.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--rabbi-name")
    ap.add_argument("--seeker-name")
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


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "reading_nook"), asp.fact("quest", "find_bookmark")]
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    lines.append(asp.fact("needs", "find_bookmark", "blue_thread"))
    lines.append(asp.fact("grounds", "reading_nook", "find_bookmark"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q,C) :- quest(Q), clue(C), needs(Q,C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_ok(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.quest in QUESTS and params.clue in CLUES and params.suspect in SUSPECTS and QUESTS[params.quest].clue_needed == params.clue


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this quest needs the bookmark clue to solve cleanly in the reading nook.)"


def _setup(world: World, setting: Setting, quest: Quest) -> None:
    world.say(
        f"In {setting.place}, {setting.cozy_detail}. {setting.light} glowed over the books, "
        f"and everyone could feel that {quest.goal} was missing."
    )


def _inspect(world: World, rabbi: Entity, clue: Clue, suspect: Suspect) -> None:
    rabbi.memes["curiosity"] += 1
    world.say(
        f"The rabbi looked carefully at {clue.where}. {clue.phrase} made a small but useful clue."
    )
    world.say(
        f'"It feels like a whodunit," {rabbi.id} said. "{clue.trace}."'
    )
    world.get(clue.id).found = True
    world.get(clue.id).hidden = False
    world.get("rabbi").meters["clue_count"] += 1
    world.get("nook").meters["mystery"] += 1
    propagate(world, narrate=False)


def _question(world: World, rabbi: Entity, seeker: Entity, suspect: Suspect) -> None:
    world.say(
        f"{rabbi.id} and {seeker.id} followed the clue to the quiet child. "
        f'When they asked, {suspect.label} blinked and said, "{suspect.alibi}."'
    )
    if suspect.honesty < 5:
        world.say(
            f"But the answer sounded too neat, and {rabbi.id} noticed that the blue thread on {suspect.label} matched the shelf."
        )


def _solve(world: World, rabbi: Entity, clue: Clue, quest: Quest, suspect: Suspect) -> None:
    world.say(
        f"Then the rabbi smiled. The clue had pointed the way all along: {suspect.label} had slipped the bookmark into the open book while reading."
    )
    world.say(
        f"{rabbi.id} reached inside the book and found it. The missing bookmark was back where it belonged."
    )
    world.say(
        f'“The mystery is solved,” {rabbi.id} said. “A small clue can tell the whole truth.”'
    )
    world.say(
        f"At the end, {quest.answer_image} sat in the lamp light, and the reading nook felt calm again."
    )


def tell(setting: Setting, quest: Quest, clue: Clue, suspect: Suspect, rabbi_name: str, seeker_name: str) -> World:
    world = World()
    nook = world.add(Entity(id="nook", kind="place", type="room", label=setting.place, meters={"mystery": 0.0}))
    rabbi = world.add(Entity(id=rabbi_name, kind="character", type="rabbi", label="rabbi", role="seeker"))
    seeker = world.add(Entity(id=seeker_name, kind="character", type="child", label="the child", role="helper"))
    clue_ent = world.add(Entity(id=clue.id, kind="clue", type="clue", label=clue.label, hidden=True, movable=True, tags=set(clue.tags)))
    world.add(Entity(id=suspect.id, kind="character", type="child", label=suspect.label, role="suspect", tags=set(suspect.tags)))

    _setup(world, setting, quest)
    world.para()
    _inspect(world, rabbi, clue, suspect)
    _question(world, rabbi, seeker, suspect)
    world.para()
    _solve(world, rabbi, clue, quest, suspect)

    world.facts.update(rabbi=rabbi, seeker=seeker, clue=clue, suspect=suspect, quest=quest, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit-style quest story set in a reading nook that includes the word "rabbi" and ends with the missing {f["quest"].goal} found.',
        f"Tell a cozy mystery where {f['rabbi'].id} investigates a reading nook clue and solves the case with a child helper.",
        f"Write a short children's whodunit about a rabbi, a reading nook, and a clue that reveals who moved the bookmark.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was the missing bookmark in the reading nook. The rabbi had to follow a clue and figure out where it had been hidden."
        ),
        QAItem(
            question="How did the rabbi solve the whodunit?",
            answer=f"The rabbi noticed a small clue and compared it with the suspect's story. That careful looking showed where the bookmark had gone, and the rabbi found it inside the open book."
        ),
        QAItem(
            question="What changed by the end?",
            answer="The missing bookmark was back in its place, and the reading nook felt calm again. The clue that started the mystery also helped prove the answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rabbi?",
            answer="A rabbi is a Jewish religious teacher and leader. Rabbis help people learn, ask questions, and understand traditions."
        ),
        QAItem(
            question="What is a reading nook?",
            answer="A reading nook is a cozy little corner for books and quiet reading. It often has pillows, a chair, or a lamp."
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story about figuring out who did something. The clues lead the characters toward the answer."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden:
            bits.append("hidden")
        if e.found:
            bits.append("found")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or "reading_nook"
    quest = args.quest or "find_bookmark"
    clue = args.clue or QUESTS[quest].clue_needed
    suspect = args.suspect or "quiet_child"
    rabbi_name = args.rabbi_name or "Rabbi Eli"
    seeker_name = args.seeker_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    params = StoryParams(setting=setting, quest=quest, clue=clue, suspect=suspect, rabbi_name=rabbi_name, seeker_name=seeker_name)
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.quest and args.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if not reasonableness_ok(params):
        raise StoryError(explain_rejection(params))
    return params


def generate(params: StoryParams) -> StorySample:
    if not reasonableness_ok(params):
        raise StoryError(explain_rejection(params))
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], CLUES[params.clue], SUSPECTS[params.suspect], params.rabbi_name, params.seeker_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="reading_nook", quest="find_bookmark", clue="blue_thread", suspect="quiet_child", rabbi_name="Rabbi Eli", seeker_name="Mina"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in ASP/Python parity")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"generate smoke test failed: {exc}")
        return 1
    print("OK: ASP/Python parity and generate smoke test passed.")
    return 0


def valid_combo_objects() -> list[tuple[str, str]]:
    return valid_combos()


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for q in QUESTS.values():
        for c in CLUES.values():
            if q.clue_needed == c.id:
                combos.append((q.id, c.id))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for q, c in combos:
            print(f"{q} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.rabbi_name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
