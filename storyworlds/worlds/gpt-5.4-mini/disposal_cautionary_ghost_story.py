#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disposal_cautionary_ghost_story.py
==================================================================

A standalone story world for a tiny, cautionary ghost story about disposal:
a child finds a spooky old object, a ghost warns against tossing it into the
wrong place, a grown-up helps with careful disposal, and the ending proves the
lesson by showing a safer resting place.

The domain is intentionally small and classical:
- one haunted place
- one child
- one ghost guide
- one risky item
- one proper disposal method
- one safer replacement choice

The goal is to create a complete, child-facing story with a clear turn:
curiosity -> caution -> correction -> calm ending.
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
FEAR_TURN = 1.0
CLEAN_TURN = 1.0


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
    spooky: str
    disposal: str
    closet: str
    ending: str

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
    risk: str
    disposal_kind: str
    reason: str
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
class SafePlace:
    id: str
    label: str
    phrase: str
    purpose: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_fear(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["haunted"] >= THRESHOLD and ("ghost" not in world.fired):
            e.memes["fear"] += 1
            out.append("__ghost__")
            world.fired.add(("ghost",))
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
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


def reasonableness_gate(item: Item, place: SafePlace) -> bool:
    return item.disposal_kind in {"trash", "recycle", "return"} and place.id in {"bin", "box", "desk"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def outcome_of(params: "StoryParams") -> str:
    if params.response not in RESPONSES:
        return "?"
    return "safe"


def _smell_line(item: Item) -> str:
    return {
        "trash": "It was the kind of thing that should not stay in a bedroom one more night.",
        "recycle": "It needed a careful sorting, not a careless toss.",
        "return": "It was something that belonged back where it came from.",
    }.get(item.disposal_kind, "It needed careful hands.")


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get("child").meters["haunted"] += 1
    return {"fear": sim.get("child").memes["fear"]}


def begin(world: World, child: Entity, ghost: Entity, item: Item) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a rainy evening, {child.id} crept through the old house and found "
        f"{item.phrase} beside the dusty hall. {world.setting.spooky}"
    )
    world.say(
        f"A pale ghost floated from the doorway. Its voice was soft, like wind "
        f"in a hollow jar. \"{item.label} belongs in a careful {item.disposal_kind}, "
        f"not in the wrong {world.setting.disposal}.\""
    )


def tempt(world: World, child: Entity, item: Item) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"{child.id} stared at {item.phrase}. For a moment, {child.pronoun()} "
        f"thought it would be easier to hide it away fast."
    )


def warn(world: World, ghost: Entity, child: Entity, item: Item) -> None:
    child.meters["haunted"] += 1
    propagate(world, narrate=False)
    world.say(
        f'The ghost lifted one transparent finger. "{item.reason}," it whispered. '
        f'"{_smell_line(item)}"'
    )


def choose_safe(world: World, child: Entity, safe: SafePlace, item: Item) -> None:
    child.memes["caution"] += 1
    world.say(
        f"{child.id} nodded and held the item close instead of dropping it. "
        f"{child.pronoun().capitalize()} carried it to {safe.phrase}."
    )


def resolve(world: World, child: Entity, ghost: Entity, item: Item, safe: SafePlace) -> None:
    child.meters["sorted"] += 1
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    ghost.meters["haunted"] = 0.0
    world.say(
        f"At the table, {child.id} sorted the item the right way: one pile for "
        f"keep, one for recycle, and one for trash. Then {child.id} used "
        f"{safe.phrase} for the proper disposal."
    )
    world.say(
        f"The ghost's face brightened. The cold hallway felt less spooky at once, "
        f"and the old house seemed to breathe easier."
    )


def ending(world: World, child: Entity, ghost: Entity, item: Item) -> None:
    world.say(
        f"By the end, the {item.label} was gone from the floor, the safe pile was "
        f"tucked neatly away, and the ghost drifted up the stairs with a tiny smile."
    )
    world.say(
        f"{child.id} turned off the lamp and saw only a calm room, a tidy table, "
        f"and moonlight on the window glass."
    )


def tell(setting: Setting, item: Item, safe: SafePlace,
         child_name: str = "Maya", child_gender: str = "girl",
         ghost_name: str = "Ghost", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    ghost = world.add(Entity(id=ghost_name, kind="character", type="thing", role="ghost", label="the ghost"))
    item_ent = world.add(Entity(id="item", type="thing", label=item.label))
    stash = world.add(Entity(id="stash", type="thing", label=safe.label))
    begin(world, child, ghost, item)
    world.para()
    tempt(world, child, item)
    warn(world, ghost, child, item)
    world.para()
    choose_safe(world, child, safe, item)
    resolve(world, child, ghost, item, safe)
    world.para()
    ending(world, child, ghost, item)
    world.facts.update(child=child, parent=parent, ghost=ghost, item=item, item_ent=item_ent, safe=safe, stash=stash)
    return world


SETTINGS = {
    "old_house": Setting(
        "old_house",
        "the old house",
        "The wallpaper was faded, the floorboards creaked, and the air seemed to whisper at the edges.",
        "disposal chute",
        "front closet",
        "Moonlight silvered the hallway, and every corner looked like it might hide a story.",
    ),
    "apartment": Setting(
        "apartment",
        "the apartment hall",
        "The hallway lights flickered, and the trash room rattled like it was listening.",
        "trash chute",
        "lobby closet",
        "The elevator hummed, and the building felt wide awake in the dark.",
    ),
    "attic_room": Setting(
        "attic_room",
        "the attic room",
        "The rafters sighed, the little window rattled, and dust made pale trails in the lamp light.",
        "downstairs bin",
        "blue crate",
        "The room looked tiny and brave in the moonlight.",
    ),
}

ITEMS = {
    "music_box": Item("music_box", "the music box", "a cracked music box", "fragile", "trash", "It could break apart and leave sharp little pieces behind.", {"spooky", "fragile"}),
    "battery_toy": Item("battery_toy", "the battery toy", "an old battery toy", "batteries", "recycle", "Batteries should be taken out and sorted carefully, not tossed into any chute.", {"battery", "recycle"}),
    "broken_doll": Item("broken_doll", "the broken doll", "a broken doll with a torn dress", "fragile", "trash", "It was too broken to keep, but it still needed to be wrapped and thrown away carefully.", {"fragile", "spooky"}),
}

SAFE_PLACES = {
    "bin": SafePlace("bin", "the bin", "the covered bin", "proper disposal", {"trash"}),
    "box": SafePlace("box", "the sorting box", "the sorting box", "careful sorting", {"recycle", "return"}),
    "desk": SafePlace("desk", "the desk drawer", "the desk drawer", "safe storage", {"return"}),
}

RESPONSES = {
    "sort": Response("sort", 3, 4, "sorted it carefully and asked what should be kept, recycled, or thrown away", "tried to sort it, but the wrong pile kept growing", "sorted it carefully into the right pile", {"sort"}),
    "wrap": Response("wrap", 2, 3, "wrapped the item in paper, carried it down, and placed it in the proper bin", "wrapped it, but the chute was already jammed", "wrapped the item and placed it in the proper bin", {"trash"}),
    "return": Response("return", 3, 4, "carried it back to where it belonged and left it there safely", "tried to return it, but the night was too busy and the path got lost", "carried it back where it belonged", {"return"}),
}

GIRL_NAMES = ["Maya", "Nina", "Ivy", "June", "Lena"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Finn", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for spid, safe in SAFE_PLACES.items():
                if reasonableness_gate(item, safe):
                    combos.append((sid, iid, spid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    safe: str
    child: str
    child_gender: str
    parent: str
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


KNOWLEDGE = {
    "trash": [("What goes in the trash?",
               "Things that cannot be kept, fixed, reused, or recycled safely can go in the trash. They should be put there carefully so they do not make a mess.")],
    "recycle": [("What does recycle mean?",
                 "Recycle means sorting things so they can be made into new things again. It helps keep useful material from being wasted.")],
    "return": [("What does return mean?",
               "Return means taking something back to where it belongs. That is safer than hiding it or dropping it anywhere.")],
    "battery": [("Why should batteries be handled carefully?",
                 "Batteries can leak or break if they are tossed around. They should be sorted the way a grown-up says.")],
    "fragile": [("What does fragile mean?",
                 "Fragile means something can break easily. Fragile things need gentle hands and careful packing.")],
    "ghost": [("What is a ghost in a story?",
               "A ghost is a spooky-looking character that can warn, guide, or surprise the other characters.")],
}

KNOWLEDGE_ORDER = ["ghost", "fragile", "battery", "trash", "recycle", "return"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    return [
        f'Write a cautionary ghost story for a young child that includes the word "disposal".',
        f"Tell a spooky but gentle story where {f['child'].id} finds {item.phrase} and a ghost warns about disposal.",
        f"Write a short ghost story with a clear lesson about where {item.label} should go instead of the disposal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    safe = f["safe"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, the ghost, and a spooky object that needed careful disposal."),
        ("What did the ghost warn about?",
         f"The ghost warned that {item.label} should not be tossed into the disposal the wrong way. It explained that the item needed careful hands so it would not cause trouble."),
        ("How did the child solve the problem?",
         f"{child.id} listened, sorted the item the right way, and used {safe.phrase} for the proper disposal. That kept the room tidy and made the ghost smile."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags)
    tags.add("ghost")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(item: Item, safe: SafePlace) -> str:
    return f"(No story: {item.label} and {safe.label} do not fit a careful disposal plan.)"


ASP_RULES = r"""
careful_disposal(I,S) :- item(I), safe(S), kind(I,K), supports(S,K).
story_ok(Set,I,S) :- setting(Set), careful_disposal(I,S).
outcome(safe) :- story_ok(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("kind", iid, item.disposal_kind))
    for sid, safe in SAFE_PLACES.items():
        lines.append(asp.fact("safe", sid))
        for tag in safe.tags:
            lines.append(asp.fact("supports", sid, tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    import asp  # lazy via helper style
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in gate:")
        print("  only python:", sorted(py - cl))
        print("  only clingo:", sorted(cl - py))
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, safe=None, child=None, child_gender=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation completed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary ghost story about careful disposal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--safe", choices=SAFE_PLACES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.safe is None or c[2] == args.safe)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, safe = rng.choice(sorted(combos))
    itm = ITEMS[item]
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, item, safe, child, child_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SAFE_PLACES[params.safe], params.child, params.child_gender, "Ghost", params.parent)
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


CURATED = [
    StoryParams("old_house", "music_box", "bin", "Maya", "girl", "mother"),
    StoryParams("apartment", "battery_toy", "box", "Noah", "boy", "father"),
    StoryParams("attic_room", "broken_doll", "desk", "Ivy", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
