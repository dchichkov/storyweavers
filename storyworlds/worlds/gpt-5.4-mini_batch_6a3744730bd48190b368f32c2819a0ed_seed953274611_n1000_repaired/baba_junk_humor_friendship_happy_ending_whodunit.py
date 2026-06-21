#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/baba_junk_humor_friendship_happy_ending_whodunit.py
====================================================================================

A small storyworld for a kid-friendly whodunit with humor, friendship, and a
happy ending. Two children and Baba investigate a mysterious mess of junk in a
cozy home, follow clues, laugh at false leads, and discover that the "case" is a
harmless surprise cleanup that ends with everyone helping each other.

The world is intentionally tiny and state-driven:
- typed entities with meters and memes,
- a simple causal engine,
- a reasonableness gate,
- a Python/ASP parity twin,
- grounded QA sets derived from world state, not rendered English.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandfather": "baba", "father": "dad", "mother": "mom"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    hiding_spot: str
    clutter_spot: str
    mood: str
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
    funny_note: str
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
class Case:
    id: str
    mystery: str
    suspect: str
    reveal: str
    solution: str
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
class StoryParams:
    setting: str
    clue: str
    case: str
    hero: str
    friend: str
    baba: str
    seed: Optional[int] = None
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


class World:
    def __init__(self) -> None:
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_accuse_junk(world: World) -> list[str]:
    out: list[str] = []
    if world.get("junk").meters["mess"] >= THRESHOLD and ("accuse",) not in world.fired:
        world.fired.add(("accuse",))
        for c in world.characters():
            c.memes["curiosity"] += 1
        out.append("__accuse__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    if world.get("junk").meters["sorted"] >= THRESHOLD and ("smile",) not in world.fired:
        world.fired.add(("smile",))
        for c in world.characters():
            c.memes["joy"] += 1
            c.memes["relief"] += 1
        out.append("__smile__")
    return out


CAUSAL_RULES = [
    _r_accuse_junk,
    _r_smile,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_case(setting: Setting, clue: Clue, case: Case) -> bool:
    return "junk" in setting.tags and clue.id in case.tags


def suspect_innocent(case: Case) -> bool:
    return case.id in {"missing_cookie", "lost_keys"}


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if params.case not in CASES:
        raise StoryError("Unknown case.")
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    case = CASES[params.case]
    if not valid_case(setting, clue, case):
        raise StoryError("This clue does not fit the case in this setting.")
    if params.hero not in NAMES or params.friend not in NAMES or params.baba not in BABA_NAMES:
        raise StoryError("Unknown character choice.")

    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type="girl" if params.hero in GIRL_NAMES else "boy", role="detective"))
    friend = w.add(Entity(id=params.friend, kind="character", type="girl" if params.friend in GIRL_NAMES else "boy", role="helper"))
    baba = w.add(Entity(id=params.baba, kind="character", type="grandfather", role="grownup"))
    junk = w.add(Entity(id="junk", kind="thing", type="thing", label="junk pile"))
    room = w.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    w.facts.update(setting=setting, clue=clue, case=case, hero=hero, friend=friend, baba=baba, junk=junk, room=room)
    return w


def tell(w: World) -> None:
    f = w.facts
    setting: Setting = f["setting"]
    clue: Clue = f["clue"]
    case: Case = f["case"]
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    baba: Entity = f["baba"]
    junk: Entity = f["junk"]

    hero.memes["playful"] += 1
    friend.memes["playful"] += 1

    w.say(
        f"On a bright afternoon in {setting.place}, {hero.id} and {friend.id} were playing detective. "
        f"They had a notebook, a pencil, and very serious faces that made them look funny anyway."
    )
    w.say(
        f"Then they found a mystery: {setting.clutter_spot} was full of junk, and a {clue.label} had gone missing. "
        f'"This case has crumbs all over it," {friend.id} whispered. "Crumbs and nonsense."'
    )

    w.para()
    w.say(
        f"{hero.id} pointed at the junk pile. " +
        f'"That is either a clue or a very grumpy mountain," {hero.pronoun()} said. '
        f"{baba.id} peeked over their shoulders and chuckled. "
        f'"In my day, we called that "fancy clutter,"' f" {baba.pronoun()} said."
    )
    w.say(
        f"{friend.id} lifted one sock, then another, and both children laughed when a toy spoon rolled out like it was late for a meeting."
    )

    w.para()
    junk.meters["mess"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    w.say(
        f"Still, the case felt serious. {hero.id} thought the junk might hide the missing {clue.label}, "
        f"so {hero.pronoun()} and {friend.id} searched carefully under {setting.hiding_spot}."
    )
    w.say(
        f"{baba.id} checked the mess too, and {baba.pronoun()} found {case.suspect} tucked behind the pile. "
        f'"Aha," {baba.id} said, "the villain was never a thief. It was just lost in the laundry of life."'
    )

    w.para()
    junk.meters["sorted"] += 1
    propagate(w, narrate=False)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    baba.memes["joy"] += 1
    w.say(
        f"Everyone burst out laughing. The missing {clue.label} was right where nobody expected, and the junk turned out to be a harmless mix-up."
    )
    w.say(
        f"The three of them put the good things back, set the junk in a neat bag, and made a tiny label for it so the next mystery would be easier."
    )
    w.say(
        f"By evening, {setting.place} was tidy again, {friend.id} had the {clue.label}, and {hero.id} and {baba.id} were sharing a grin over the solved case."
    )
    w.say(
        f"It was the best kind of whodunit: nobody was in trouble, everybody helped, and the only thing that stayed suspicious was the cheese sandwich on the table."
    )

    w.facts.update(outcome="happy", solved=True, clue=clue, case=case, setting=setting)


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f'Write a funny whodunit for a young child that includes the words "{f["baba"].label_word}" and "junk".',
        f"Tell a friendship mystery where {f['hero'].id}, {f['friend'].id}, and {f['baba'].id} investigate {f['clue'].phrase} near a pile of junk.",
        f"Write a happy-ending detective story with a small clue, a silly false lead, and a warm ending in {f['setting'].place}.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    baba: Entity = f["baba"]
    clue: Clue = f["clue"]
    case: Case = f["case"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="Who were the detectives?",
            answer=f"{hero.id} and {friend.id} were the detectives, and {baba.id} helped them like a calm grown-up detective. They worked together as a team, which made the mystery feel friendly instead of scary.",
        ),
        QAItem(
            question="What made the children think there was a mystery?",
            answer=f"They saw junk in {setting.clutter_spot} and noticed that {clue.label} was missing. That made them think something strange had happened, so they started asking questions and following clues.",
        ),
        QAItem(
            question=f"What was the real answer to the case?",
            answer=f"The real answer was that {case.suspect} was just hiding behind the junk, not causing any trouble. {baba.id} found it, and everyone laughed because the mystery was smaller than it first looked.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily with the room tidied up, the missing {clue.label} found, and everyone smiling together. The junk was sorted into a neat bag, so the place looked better than before.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is junk?",
            answer="Junk is a bunch of old or messy things that are not put away yet. It can make a room look cluttered, even when nothing bad is happening.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and asks questions to solve a mystery. Good detectives pay attention to tiny details and work carefully.",
        ),
        QAItem(
            question="Why is it nice to have a friend help with a mystery?",
            answer="A friend can notice different clues and make the work feel less serious. When friends help each other, the job can also become more fun.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(w: World) -> str:
    out = ["--- world model state ---"]
    for e in w.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        out.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(n for n, *_ in w.fired)}")
    return "\n".join(out)


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", hiding_spot="the chair", clutter_spot="the floor", mood="cozy", tags={"junk"}),
    "hall": Setting(id="hall", place="the hallway", hiding_spot="the umbrella stand", clutter_spot="the bench", mood="busy", tags={"junk"}),
    "garage": Setting(id="garage", place="the garage", hiding_spot="the shelf", clutter_spot="the workbench", mood="dusty", tags={"junk"}),
}

CLUES = {
    "biscuit": Clue(id="biscuit", label="missing biscuit", phrase="a missing biscuit", funny_note="crumbly", tags={"biscuit", "junk"}),
    "key": Clue(id="key", label="missing key", phrase="a missing key", funny_note="tiny", tags={"key", "junk"}),
    "sock": Clue(id="sock", label="missing sock", phrase="a missing sock", funny_note="wobbly", tags={"sock", "junk"}),
}

CASES = {
    "missing_cookie": Case(id="missing_cookie", mystery="who took the cookie", suspect="the cookie tin", reveal="the cookie tin was on the shelf", solution="the cookie was only moved", tags={"biscuit"}),
    "lost_keys": Case(id="lost_keys", mystery="who hid the key", suspect="a coat pocket", reveal="the key was in a pocket", solution="the key was not stolen", tags={"key"}),
    "lost_sock": Case(id="lost_sock", mystery="where the sock went", suspect="behind the hamper", reveal="the sock was behind the hamper", solution="the sock was not lost forever", tags={"sock"}),
}

BABA_NAMES = ["Baba", "Abu", "Dada"]
GIRL_NAMES = ["Mina", "Lina", "Sana", "Nori"]
BOY_NAMES = ["Omar", "Tariq", "Jamal", "Ilyas"]
NAMES = set(BABA_NAMES + GIRL_NAMES + BOY_NAMES)

CURATED = [
    StoryParams(setting="kitchen", clue="biscuit", case="missing_cookie", hero="Mina", friend="Omar", baba="Baba"),
    StoryParams(setting="hall", clue="key", case="lost_keys", hero="Lina", friend="Tariq", baba="Abu"),
    StoryParams(setting="garage", clue="sock", case="lost_sock", hero="Sana", friend="Jamal", baba="Dada"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for c_id, clue in CLUES.items():
            for case_id, case in CASES.items():
                if valid_case(setting, clue, case):
                    combos.append((s_id, c_id, case_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a funny whodunit with baba, junk, friendship, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--baba", choices=BABA_NAMES)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.case is None or c[2] == args.case)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, case = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend_choices = [n for n in GIRL_NAMES + BOY_NAMES if n != hero]
    friend = args.friend or rng.choice(friend_choices)
    baba = args.baba or rng.choice(BABA_NAMES)
    return StoryParams(setting=setting, clue=clue, case=case, hero=hero, friend=friend, baba=baba)


def generate(params: StoryParams) -> StorySample:
    w = build_world(params)
    tell(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
valid(S,C,K) :- setting(S), clue(C), case(K), setting_has_junk(S), clue_fits_case(C,K).
happy_end(S,C,K) :- valid(S,C,K), not bad_case(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "junk" in s.tags:
            lines.append(asp.fact("setting_has_junk", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for kid, k in CASES.items():
        lines.append(asp.fact("case", kid))
        for tag in k.tags:
            lines.append(asp.fact("clue_fits_case", tag, kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # smoke test ordinary generation too
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and python valid_combos()")
        print("only in clingo:", sorted(clingo_set - python_set))
        print("only in python:", sorted(python_set - clingo_set))
        return 1
    print("OK: verify passed, smoke test passed, and ASP matches Python.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show happy_end/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, c, k in asp_valid_combos():
            print(f"  {s:8} {c:8} {k}")
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
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
