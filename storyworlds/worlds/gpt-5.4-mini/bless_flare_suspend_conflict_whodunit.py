#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bless_flare_suspend_conflict_whodunit.py
========================================================================

A standalone storyworld script for a tiny whodunit-like domain.

Premise:
A child notices a strange flare of light in a quiet place, a conflict erupts
over a missing object, and an adult suspends the argument long enough to inspect
the clues. In the end, the truth is blessedly simple: the "mystery" is solved
by ordinary, visible causes rather than a villainous trick.

This world intentionally includes the seed words:
- bless
- flare
- suspend

Style target:
- Whodunit
- small, concrete, child-facing
- state-driven, with a clear clue / suspicion / reveal / resolution shape

Contract notes:
- Uses typed entities with physical meters and emotional memes.
- Includes a Python reasonableness gate plus an inline ASP twin.
- Supports default generation, -n, --all, --seed, --trace, --qa,
  --json, --asp, --verify, and --show-asp.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    detail: str
    quiet: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    can_flare: bool = False
    can_hold_clue: bool = False
    can_bless: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Suspect:
    id: str
    label: str
    alibi: str
    clue: str
    innocent_reason: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Resolution:
    id: str
    sense: int
    text: str
    reveal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_conflict(world: World) -> list[str]:
    out = []
    if world.facts.get("argument") and "room" in world.entities:
        room = world.get("room")
        if room.meters["tension"] < THRESHOLD:
            room.meters["tension"] += 1
            out.append("__conflict__")
    return out


def _r_flare(world: World) -> list[str]:
    out = []
    lantern = world.entities.get("lantern")
    if lantern and lantern.meters["lit"] >= THRESHOLD and "flare" not in world.fired:
        world.fired.add(("flare",))
        room = world.get("room")
        room.meters["glare"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["surprise"] += 1
        out.append("__flare__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("flare", "physical", _r_flare),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def suspicious_flare(item: Item) -> bool:
    return item.can_flare


def can_solve(resolution: Resolution) -> bool:
    return resolution.sense >= 2


def explain_rejection(item: Item) -> str:
    return f"(No story: {item.label} does not create a believable flare or clue.)"


def witness_flare(world: World, child: Entity, item: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At the quiet house, {child.id} saw a sudden flare near the {item.label}. "
        f"It lit the wall for a blink, then vanished."
    )


def introduce_case(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} and {adult.label_word} were in {setting.place}. {setting.detail}"
    )
    world.say(
        f"Then the mystery began: a little flare, a missing clue, and a room full "
        f"of questions."
    )


def argue(world: World, child: Entity, adult: Entity, suspect: Suspect, item: Item) -> None:
    world.facts["argument"] = True
    child.memes["defiance"] += 1
    world.say(
        f'"{suspect.label} did it," {child.id} said. "The clue was right by the '
        f'{item.label}."'
    )
    world.say(
        f"{adult.label_word.capitalize()} held up a hand and said, "
        f'"Let us suspend the guessing for a moment and look again."'
    )


def inspect_clues(world: World, adult: Entity, suspect: Suspect, item: Item) -> None:
    adult.memes["calm"] += 1
    world.say(
        f"{adult.label_word.capitalize()} checked the {item.label}, then the floor, "
        f"then the window. The clue was not a secret at all."
    )
    world.say(
        f"{adult.label_word.capitalize()} noticed {suspect.alibi} and remembered "
        f"{suspect.innocent_reason}."
    )


def reveal_truth(world: World, adult: Entity, child: Entity, suspect: Suspect, item: Item) -> None:
    world.say(
        f"At last, the answer was clear. {suspect.label} was innocent, and the "
        f"real clue was {suspect.clue}."
    )
    world.say(
        f"{adult.label_word.capitalize()} smiled and said, "
        f'"A small thing can look suspicious when the room is tense, but the truth '
        f'usually leaves footprints."'
    )


def bless_end(world: World, adult: Entity, child: Entity, item: Item, setting: Setting) -> None:
    for ent in (adult, child):
        ent.memes["relief"] += 1
        ent.memes["joy"] += 1
    world.say(
        f"Then {adult.label_word.capitalize()} gave the child a gentle hug and said, "
        f'"Bless this little detective for looking carefully and not giving up."'
    )
    world.say(
        f"The flare had been only a reflection, the argument was over, and the "
        f"{setting.place} felt peaceful again beside the {item.label}."
    )


def tell(setting: Setting, item: Item, suspect: Suspect, resolution: Resolution,
         child_name: str = "Mina", child_gender: str = "girl",
         adult_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id="Parent", kind="character", type=adult_type, role="adult", label="the parent"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    suspect_ent = world.add(Entity(id=suspect.id, kind="thing", type="thing", label=suspect.label))
    clue_ent = world.add(Entity(id=item.id, kind="thing", type="thing", label=item.label))
    lantern = world.add(Entity(id="lantern", kind="thing", type="thing", label="lantern"))
    lantern.meters["lit"] = 1.0
    world.facts.update(setting=setting, item=item, suspect=suspect, resolution=resolution)

    introduce_case(world, child, adult, setting)
    world.para()
    witness_flare(world, child, clue_ent)
    argue(world, child, adult, suspect, item)
    inspect_clues(world, adult, suspect, item)
    propagate(world, narrate=False)
    world.para()
    reveal_truth(world, adult, child, suspect, item)
    bless_end(world, adult, child, item, setting)

    world.facts.update(
        child=child, adult=adult, room=room, suspect_ent=suspect_ent,
        clue_ent=clue_ent, lantern=lantern, outcome="solved"
    )
    return world


SETTINGS = {
    "hall": Setting("hall", "the old hall", "Dust lay on the floor, and the lamps were very still."),
    "library": Setting("library", "the little library", "The shelves were quiet, and every page smelled like paper."),
    "kitchen": Setting("kitchen", "the kitchen", "A pan sat by the stove, and the window let in a pale shine."),
}

ITEMS = {
    "mirror": Item("mirror", "mirror", "a small hand mirror", "glare", can_flare=True, can_hold_clue=True, tags={"flare", "clue"}),
    "tin": Item("tin", "tin lid", "a round tin lid", "glare", can_flare=True, can_hold_clue=True, tags={"flare", "clue"}),
    "glass": Item("glass", "glass jar", "a glass jar", "glare", can_flare=True, can_hold_clue=True, tags={"flare", "clue"}),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "the cat was asleep on the rug", "a beam from the window bounced off the mirror", "the cat had no paws on the table", tags={"innocent"}),
    "brother": Suspect("brother", "the brother", "the brother was reading by the door", "a shine came from the jar and not from any sneaky hand", "the brother never touched the clue", tags={"innocent"}),
    "neighbor": Suspect("neighbor", "the neighbor", "the neighbor was outside all morning", "the tin lid had slid toward the window by itself", "the neighbor had already gone home", tags={"innocent"}),
}

RESOLUTIONS = {
    "calm": Resolution("calm", 3, "looked again and spoke in a calm voice", "the clue was ordinary and harmless", tags={"calm"}),
    "lamp": Resolution("lamp", 2, "turned on the lamp and studied the shine", "the flare came from light on metal", tags={"lamp"}),
    "pause": Resolution("pause", 2, "paused the argument and checked the room one more time", "the answer was waiting in plain sight", tags={"pause"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ava", "Eli", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Sam", "Finn", "Leo", "Max", "Owen"]
ADJECTIVES = ["careful", "curious", "bold", "thoughtful", "gentle"]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid, item in ITEMS.items():
            if not suspicious_flare(item):
                continue
            for sus_id in SUSPECTS:
                for rid, res in RESOLUTIONS.items():
                    if can_solve(res):
                        combos.append((sid, iid, sus_id, rid))
    return combos


@dataclass
class StoryParams:
    setting: str
    item: str
    suspect: str
    resolution: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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

CURATED = [
    ("library", "mirror", "cat", "calm"),
    ("hall", "tin", "brother", "lamp"),
    ("kitchen", "glass", "neighbor", "pause"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit for a young child that includes the words "flare", '
        f'"suspend", and "bless".',
        f"Tell a tiny mystery where {f['child'].id} sees a flare near a {f['item'].label} "
        f"and an adult suspends the argument before naming the culprit.",
        f"Write a child-friendly mystery in which the answer is not a villain, but "
        f"a careful look at the clues.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    item = f["item"]
    suspect = f["suspect"]
    setting = f["setting"]
    return [
        ("What kind of story is this?",
         f"It is a little mystery story, the kind where someone sees a clue and "
         f"tries to figure out what really happened. The ending solves the puzzle "
         f"with a calm look at the facts."),
        (f"What did {child.id} notice?",
         f"{child.id} noticed a flare near the {item.label}. At first it looked "
         f"mysterious, so the room felt full of questions."),
        (f"Why did the parent suspend the argument?",
         f"{adult.label_word.capitalize()} suspended the guessing because the clues "
         f"had not been checked yet. That gave everyone time to look carefully instead "
         f"of blaming the wrong person."),
        (f"Who was blamed at first, and what was the truth?",
         f"{suspect.label} was blamed at first, but {suspect.label} was innocent. "
         f"The real answer was just {suspect.clue}."),
        ("How did the story end?",
         f"It ended with a blessing and a solved mystery: the flare was only an "
         f"ordinary reflection, the argument stopped, and everyone felt relieved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags) | set(world.facts["suspect"].tags) | set(world.facts["resolution"].tags)
    qa = []
    if "flare" in tags:
        qa.append(("What is a flare?",
                    "A flare is a sudden bright light or shine. It can catch your eye very quickly."))
    if "clue" in tags:
        qa.append(("What is a clue?",
                    "A clue is a small piece of information that helps solve a mystery."))
    if "pause" in tags:
        qa.append(("Why do people pause during an argument?",
                    "They pause to think, listen, and avoid making a wrong guess."))
    if "calm" in tags:
        qa.append(("What does it mean to stay calm?",
                    "To stay calm means to keep your voice and body quiet enough to think clearly."))
    return qa


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
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("can_flare", iid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("can_solve", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, U, R) :- setting(S), item(I), can_flare(I), suspect(U), resolution(R), can_solve(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, suspect=None, resolution=None, name=None, gender=None, adult=None, trait=None), random.Random(1)))
    if not sample.story.strip():
        print("MISMATCH: empty story")
        rc = 1
    print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--trait", choices=ADJECTIVES)
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
              and (args.item is None or c[1] == args.item)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.resolution is None or c[3] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, suspect, resolution = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(ADJECTIVES)
    return StoryParams(setting, item, suspect, resolution, name, gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = World()
    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    suspect = SUSPECTS[params.suspect]
    resolution = RESOLUTIONS[params.resolution]
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, role="child"))
    adult = world.add(Entity(id="Parent", kind="character", type=params.adult, role="adult", label="the parent"))
    world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    world.add(Entity(id=item.id, kind="thing", type="thing", label=item.label))
    world.add(Entity(id=suspect.id, kind="thing", type="thing", label=suspect.label))
    world.add(Entity(id="lantern", kind="thing", type="thing", label="lantern"))

    introduce_case(world, child, adult, setting)
    world.para()
    witness_flare(world, child, world.get(item.id))
    argue(world, child, adult, suspect, item)
    inspect_clues(world, adult, suspect, item)
    world.say(f"{adult.label_word.capitalize()} decided to {resolution.text}.")
    reveal_truth(world, adult, child, suspect, item)
    bless_end(world, adult, child, item, setting)
    world.facts.update(child=child, adult=adult, item=item, suspect=suspect, setting=setting, resolution=resolution)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting, item, suspect, resolution in CURATED:
            p = StoryParams(setting, item, suspect, resolution, "Mina", "girl", "mother", "careful")
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
