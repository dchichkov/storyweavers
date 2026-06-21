#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/coast_rubbish_mystery_to_solve_sharing_animal.py
=================================================================================

A tiny animal-story world about a seaside mystery: something on the coast looks
wrong, the animals investigate, they share tools and clues, and they solve the
rubbish puzzle together.

Seed words: coast, rubbish
Features: Mystery to Solve, Sharing
Style: Animal Story
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"she", "girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"he", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
    coast_word: str
    place_line: str
    weather: str
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
class Mystery:
    id: str
    clue: str
    wrong_guess: str
    truth: str
    reveal: str
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
class Item:
    id: str
    label: str
    phrase: str
    share_text: str
    useful_for: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.memes["worry"] >= THRESHOLD and ("worry", e.id) not in world.fired:
            world.fired.add(("worry", e.id))
            world.get("scene").meters["tension"] += 1
            out.append("__tension__")
    return out


def _r_share(world: World) -> list[str]:
    out = []
    if world.facts.get("shared") and ("share",) not in world.fired:
        world.fired.add(("share",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["warmth"] += 1
        out.append("__warm__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_predict(world: World, mystery: Mystery) -> str:
    return f"{mystery.clue} and a few dropped scraps"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for mid in MYSTERIES:
            for iid in ITEMS:
                if sid in {"coast"} and mid in {"rubbish"} and iid in {"net", "bucket", "bag"}:
                    combos.append((sid, mid, iid))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    item: str
    hero1: str
    hero1_type: str
    hero2: str
    hero2_type: str
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


SETTINGS = {
    "coast": Setting(
        id="coast",
        coast_word="coast",
        place_line="The coast was bright with shells, gulls, and little pools left by the tide.",
        weather="breezy",
        tags={"coast"},
    ),
}

MYSTERIES = {
    "rubbish": Mystery(
        id="rubbish",
        clue="a shiny trail of rubbish near the rocks",
        wrong_guess="a crab's treasure",
        truth="a torn snack bag caught in the sea grass",
        reveal="The shiny trail was only rubbish from a picnic drifting in the wind.",
        tags={"rubbish", "mystery"},
    ),
}

ITEMS = {
    "net": Item(
        id="net",
        label="net",
        phrase="a small net",
        share_text="shared the net",
        useful_for="lifting the rubbish without tearing it",
        tags={"share", "tool"},
    ),
    "bucket": Item(
        id="bucket",
        label="bucket",
        phrase="a bucket",
        share_text="shared the bucket",
        useful_for="carrying the rubbish away",
        tags={"share", "tool"},
    ),
    "bag": Item(
        id="bag",
        label="bag",
        phrase="a cloth bag",
        share_text="shared the bag",
        useful_for="holding the rubbish after they picked it up",
        tags={"share", "tool"},
    ),
}

ANIMAL_NAMES = ["Milo", "Pip", "Nora", "Tia", "Otis", "Luna", "Bram", "Mina", "Roo", "Nell"]
ANIMAL_TYPES = ["fox", "rabbit", "badger", "otter", "hedgehog", "seal", "mouse", "duck"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal coast mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero1-type", choices=ANIMAL_TYPES)
    ap.add_argument("--hero2")
    ap.add_argument("--hero2-type", choices=ANIMAL_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection() -> str:
    return "(No story: this world needs a coast mystery about rubbish, plus a shareable item.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError(explain_rejection())
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError(explain_rejection())
    if args.item and args.item not in ITEMS:
        raise StoryError(explain_rejection())
    combos = [c for c in valid_combos()
              if (not args.setting or c[0] == args.setting)
              and (not args.mystery or c[1] == args.mystery)
              and (not args.item or c[2] == args.item)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, mystery, item = rng.choice(combos)
    hero1 = args.hero1 or rng.choice(ANIMAL_NAMES)
    hero2 = args.hero2 or rng.choice([n for n in ANIMAL_NAMES if n != hero1])
    hero1_type = args.hero1_type or rng.choice(ANIMAL_TYPES)
    hero2_type = args.hero2_type or rng.choice([t for t in ANIMAL_TYPES if t != hero1_type])
    return StoryParams(setting=setting, mystery=mystery, item=item,
                       hero1=hero1, hero1_type=hero1_type,
                       hero2=hero2, hero2_type=hero2_type)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    item = ITEMS[params.item]
    a = world.add(Entity(id=params.hero1, kind="character", type=params.hero1_type, role="solver"))
    b = world.add(Entity(id=params.hero2, kind="character", type=params.hero2_type, role="helper"))
    scene = world.add(Entity(id="scene", kind="thing", type="place", label=setting.coast_word))
    a.memes["curiosity"] += 1
    b.memes["kindness"] += 1

    world.say(f"{a.id} and {b.id} were walking along the coast when they noticed {mystery.clue}.")
    world.say(setting.place_line)
    world.say(f'"Look," said {a.id}, "it might be {mystery.wrong_guess}."')
    world.say(f'{b.id} shook {b.pronoun("possessive")} head. "Let\'s solve the mystery first."')
    world.para()
    a.memes["worry"] += 1
    world.get("scene").meters["tension"] += 1
    world.say(f"They followed the trail carefully, because the coast wind kept pushing the rubbish around.")
    world.say(f"Then they found {mystery.truth}.')
    world.say(mystery.reveal)
    world.facts["shared"] = True
    world.para()
    world.say(f'{a.id} and {b.id} smiled and {item.share_text} so they could clean it up together.')
    world.say(f"The {item.label} was useful for {item.useful_for}, and the rubbish went into it one piece at a time.")
    world.say(f"In the end, the coast looked tidy again, and the gulls hopped by as if they approved.")
    propagate(world, narrate=False)
    world.facts.update(setting=setting, mystery=mystery, item=item, shared=True)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write an animal story about a coast mystery with rubbish that gets solved by sharing.",
        "Tell a gentle seaside story where two animals follow a clue, share a tool, and clean up rubbish.",
        "Write a short animal mystery set on the coast that ends with friends sharing and tidying the rubbish.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What mystery did the animals find?",
            answer="They found a shiny trail of rubbish near the rocks. At first it looked strange, but it turned out to be blown there by the wind.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer="They followed the clue together and shared a tool to clean up the rubbish. Working side by side helped them see what the shiny trail really was.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The coast was tidy again, and the animals were happy because they had solved the mystery and shared their work.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a coast?",
            answer="A coast is the land right next to the sea. It can have rocks, sand, shells, and windy air.",
        ),
        QAItem(
            question="What is rubbish?",
            answer="Rubbish is trash or waste that people should throw away. It does not belong on the ground or in the sea.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because two helpers can do a job together. It often makes hard work easier and kinder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("\n== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
setting(coast).
mystery(rubbish).
item(net).
item(bucket).
item(bag).
shareable(net).
shareable(bucket).
shareable(bag).
valid(S, M, I) :- setting(S), mystery(M), item(I), S = coast, M = rubbish, shareable(I).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "coast"),
        asp.fact("mystery", "rubbish"),
        asp.fact("item", "net"),
        asp.fact("item", "bucket"),
        asp.fact("item", "bag"),
        asp.fact("shareable", "net"),
        asp.fact("shareable", "bucket"),
        asp.fact("shareable", "bag"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    if rc == 0:
        print("OK: ASP matches Python, and story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(setting="coast", mystery="rubbish", item="net",
                hero1="Milo", hero1_type="fox", hero2="Pip", hero2_type="rabbit"),
    StoryParams(setting="coast", mystery="rubbish", item="bucket",
                hero1="Nora", hero1_type="otter", hero2="Tia", hero2_type="seal"),
    StoryParams(setting="coast", mystery="rubbish", item="bag",
                hero1="Bram", hero1_type="hedgehog", hero2="Luna", hero2_type="duck"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
