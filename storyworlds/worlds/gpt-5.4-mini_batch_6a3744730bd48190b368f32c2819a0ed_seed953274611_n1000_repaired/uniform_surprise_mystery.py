#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/uniform_surprise_mystery.py
===========================================================

A small storyworld in a mystery style with a surprise turn.

Premise:
- A child notices a strange uniform in a quiet place.
- Clues about footprints, pockets, and a missing object build tension.
- The surprise is that the "mystery" is friendly: the uniform belongs to a helper
  who has been quietly preparing a gift or rescue.
- The ending proves what changed in the world: the hidden helper is found and
  the missing item is returned.

This script follows the shared Storyweavers contract:
- stdlib-only prose engine
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- Python reasonableness gate + inline ASP twin
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    scene: str
    shadows: str
    clues: str
    surprising: str
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
class MysteryItem:
    id: str
    label: str
    phrase: str
    missing_text: str
    found_text: str
    secret_text: str
    surprise_text: str
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
class SurpriseFix:
    id: str
    power: int
    text: str
    reveal_text: str
    ending_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("clue", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    item.meters["clue"] += 1
    out.append("A clue was there, but it did not yet answer the question.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    item = world.get("item")
    if helper.meters["revealed"] < THRESHOLD:
        return out
    sig = ("surprise", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["kindness"] += 1
    item.meters["found"] += 1
    out.append("The surprise turned the mystery into a friendly answer.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("clue", "mystery", _r_clue),
    Rule("surprise", "mystery", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def surprise_is_reasonable(place: Place, item: MysteryItem, fix: SurpriseFix) -> bool:
    return "uniform" in item.tags and fix.power >= 1 and "mystery" in place.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for fid, fix in FIXES.items():
                if surprise_is_reasonable(place, item, fix):
                    combos.append((pid, iid, fid))
    return combos


def mystery_depth(item: MysteryItem) -> int:
    return 1 if "uniform" in item.tags else 0


def can_resolve(fix: SurpriseFix, item: MysteryItem) -> bool:
    return fix.power >= mystery_depth(item)


def predict(world: World, item_id: str, fix_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["missing"] += 1
    sim.get(fix_id).meters["revealed"] += 1
    propagate(sim, narrate=False)
    return {"found": sim.get(item_id).meters["found"] >= THRESHOLD}


def start(world: World, child: Entity, place: Place, item: MysteryItem) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a quiet evening, {child.id} stepped into {place.scene}. "
        f"{place.clues} The room felt like it was holding its breath."
    )
    world.say(
        f"{child.id} noticed a strange uniform and whispered, "
        f"'"That does not belong here."'
    )


def missing(world: World, child: Entity, item: MysteryItem) -> None:
    item.meters["missing"] += 1
    child.memes["worry"] += 1
    world.say(
        f"The {item.label} was gone. Its {item.missing_text}, and that made "
        f"{child.id} look again at every corner."
    )


def track(world: World, child: Entity, item: MysteryItem, place: Place) -> None:
    world.say(
        f"{child.id} followed tiny signs in the dust. {place.shadows} hid the "
        f"answer for a moment, but the clue was plain enough to notice."
    )
    world.say(
        f"The uniform looked important, yet it also looked too neat to be a bad "
        f"sign. That was the first surprise."
    )


def warn(world: World, child: Entity, helper: Entity, item: MysteryItem) -> None:
    pred = predict(world, item.id, helper.id)
    world.facts["predicted_found"] = pred["found"]
    world.say(
        f"{child.id} guessed someone might be close by. {child.pronoun('possessive').capitalize()} "
        f"guess was that the uniform had to mean help, not trouble."
    )


def reveal(world: World, helper: Entity, item: MysteryItem, fix: SurpriseFix) -> None:
    helper.meters["revealed"] += 1
    helper.meters["helped"] += 1
    world.say(
        f"Then the surprise arrived: {helper.id} stepped out in the uniform and "
        f"{fix.reveal_text}"
    )
    world.say(item.surprise_text)
    propagate(world, narrate=True)


def resolve(world: World, child: Entity, item: MysteryItem, fix: SurpriseFix, place: Place) -> None:
    item.meters["found"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{fix.ending_text} {child.id} smiled at last, because the mystery was "
        f"not a mean trick at all."
    )
    world.say(
        f"The uniform belonged to a helper, and the missing {item.label} was "
        f"back where it should be."
    )
    world.say(
        f"At the end, {place.surprising} made the whole story feel like a warm "
        f"secret instead of a scary one."
    )


def tell(place: Place, item: MysteryItem, fix: SurpriseFix,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Officer Lee", helper_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="item", type="thing", label=item.label, tags=set(item.tags)))
    world.add(Entity(id="helper_obj", type="thing", label="uniform", tags={"uniform"}))
    world.facts["place"] = place
    world.facts["item_cfg"] = item
    world.facts["fix"] = fix
    world.facts["child"] = child
    world.facts["helper"] = helper

    start(world, child, place, item)
    world.para()
    missing(world, child, item)
    track(world, child, item, place)
    warn(world, child, helper, item)
    world.para()
    reveal(world, helper, item, fix)
    resolve(world, child, item, fix, place)
    world.facts["outcome"] = "resolved"
    return world


PLACES = {
    "station": Place(
        id="station",
        scene="the old train station",
        shadows="Long shadows stretched across the benches.",
        clues="A muddy footprint and a silver button were near the door.",
        surprising="the station had been quiet only because everyone was waiting",
        tags={"mystery", "quiet"},
    ),
    "museum": Place(
        id="museum",
        scene="the tiny museum hallway",
        shadows="Soft shadows waited under the picture frames.",
        clues="A note, a key, and a careful footprint pointed down the hall.",
        surprising="the museum guard had been watching kindly all along",
        tags={"mystery", "quiet"},
    ),
    "library": Place(
        id="library",
        scene="the dim library corner",
        shadows="Shelves cast long, whispery shadows.",
        clues="A bookmark, a bent paperclip, and a soft thump pointed to a desk.",
        surprising="the library helper had hidden the answer in plain sight",
        tags={"mystery", "quiet"},
    ),
}

ITEMS = {
    "bell": MysteryItem(
        id="bell",
        label="little bell",
        phrase="a little bell with a blue ribbon",
        missing_text="small ribbon was still tied to the hook",
        found_text="the bell had been found",
        secret_text="a clue rested beside the shelf",
        surprise_text="The bell's sound answered from the back room.",
        tags={"uniform", "mystery"},
    ),
    "map": MysteryItem(
        id="map",
        label="folded map",
        phrase="a folded map with a red mark",
        missing_text="edges were still warm from being held",
        found_text="the map had been found",
        secret_text="the red mark had led the way",
        surprise_text="The map had not vanished; it had been borrowed for a reason.",
        tags={"uniform", "mystery"},
    ),
    "badge": MysteryItem(
        id="badge",
        label="shiny badge",
        phrase="a shiny badge in a pocket",
        missing_text="clip was gone from the wall",
        found_text="the badge had been found",
        secret_text="the shine was easy to miss in the dark",
        surprise_text="The badge was safe inside the helper's pocket the whole time.",
        tags={"uniform", "mystery"},
    ),
}

FIXES = {
    "gentle_reveal": SurpriseFix(
        id="gentle_reveal",
        power=1,
        text="peeked out and smiled",
        reveal_text="smiled and pointed to the missing thing",
        ending_text="Then the helper laughed softly and opened the door.",
        tags={"surprise"},
    ),
    "quiet_note": SurpriseFix(
        id="quiet_note",
        power=1,
        text="held up a note with a tiny clue",
        reveal_text="held up a note and said the missing thing was safe",
        ending_text="Then the helper tapped the note twice and stepped aside.",
        tags={"surprise"},
    ),
    "kind_return": SurpriseFix(
        id="kind_return",
        power=2,
        text="held out the missing thing at once",
        reveal_text="opened a hand and showed the missing thing",
        ending_text="Then the helper gave a tiny bow and offered it back.",
        tags={"surprise"},
    ),
}

NAMES = ["Mina", "Luca", "Nora", "Theo", "Ivy", "Noah", "Ada", "Finn"]


@dataclass
class StoryParams:
    place: str
    item: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, item = f["place"], f["item_cfg"]
    return [
        f'Write a mystery story for a 3-to-5-year-old that includes the word "uniform" and ends with a surprise reveal.',
        f"Tell a gentle mystery where {f['child'].id} notices a uniform in {place.scene} and discovers why the {item.label} is missing.",
        f"Write a child-friendly surprise mystery with clues, a uniform, and a friendly ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, item, place = f["child"], f["helper"], f["item_cfg"], f["place"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, who notices a mystery, and the friendly helper in a uniform.",
        ),
        QAItem(
            question="What clue made the story feel mysterious?",
            answer=f"A clue in {place.clues.lower()} made the room feel secret and quiet. That clue pointed {child.id} toward the missing {item.label}.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was that the uniform belonged to {helper.id}, who was helping all along. The missing {item.label} was not lost for good.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a uniform?",
            answer="A uniform is special clothes that show someone has a job, team, or role. It can help people know who is there to help.",
        ),
        QAItem(
            question="Why do mysteries use clues?",
            answer="Clues help you think about what happened before the answer is told. They make the story feel puzzly and interesting.",
        ),
        QAItem(
            question="What does a surprise do in a story?",
            answer="A surprise changes what you expected. It can make the answer feel exciting, kind, or a little bit funny.",
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="station", item="bell", fix="gentle_reveal", child_name="Mina", child_gender="girl", helper_name="Officer Lee", helper_gender="man"),
    StoryParams(place="museum", item="map", fix="quiet_note", child_name="Theo", child_gender="boy", helper_name="Guard Mara", helper_gender="woman"),
    StoryParams(place="library", item="badge", fix="kind_return", child_name="Nora", child_gender="girl", helper_name="Helper Jun", helper_gender="man"),
]


def valid_param_combo(place: Place, item: MysteryItem, fix: SurpriseFix) -> bool:
    return surprise_is_reasonable(place, item, fix)


def valid_combos_by_python() -> list[tuple[str, str, str]]:
    return [(pid, iid, fid) for pid, place in PLACES.items() for iid, item in ITEMS.items() for fid, fix in FIXES.items() if valid_param_combo(place, item, fix)]


def explain_rejection(place: Place, item: MysteryItem, fix: SurpriseFix) -> str:
    if "uniform" not in item.tags:
        return "(No story: this world wants a mystery with a uniform clue, so choose an item tagged uniform.)"
    if "mystery" not in place.tags:
        return "(No story: the place must feel like a mystery setting.)"
    if fix.power < 1:
        return "(No story: the surprise fix is too weak to resolve the mystery.)"
    return "(No story: this combination does not fit the mystery-surprise setup.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.fix:
        if not valid_param_combo(PLACES[args.place], ITEMS[args.item], FIXES[args.fix]):
            raise StoryError(explain_rejection(PLACES[args.place], ITEMS[args.item], FIXES[args.fix]))
    combos = [c for c in valid_combos_by_python()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, fix = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["woman", "man"])
    return StoryParams(
        place=place,
        item=item,
        fix=fix,
        child_name=args.name or rng.choice(NAMES),
        child_gender=child_gender,
        helper_name=args.helper or rng.choice(["Officer Lee", "Guard Mara", "Helper Jun", "Librarian Sol"]),
        helper_gender=helper_gender,
    )


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES or params.item not in ITEMS or params.fix not in FIXES:
        raise StoryError("(Invalid parameters.)")
    return tell(PLACES[params.place], ITEMS[params.item], FIXES[params.fix],
                child_name=params.child_name, child_gender=params.child_gender,
                helper_name=params.helper_name, helper_gender=params.helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a uniform, clues, and a surprise reveal.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if "uniform" in item.tags:
            lines.append(asp.fact("uniform_item", iid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("surprise_min", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,F) :- place(P), item(I), fix(F), uniform_item(I), place(P), fix(F).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos_by_python())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if a - b:
            print("  only in ASP:", sorted(a - b))
        if b - a:
            print("  only in Python:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, fix) combos:\n")
        for row in combos:
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place} / {p.item} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
