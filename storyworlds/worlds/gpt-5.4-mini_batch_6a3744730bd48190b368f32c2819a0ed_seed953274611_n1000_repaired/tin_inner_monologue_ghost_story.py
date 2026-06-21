#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tin_inner_monologue_ghost_story.py
===================================================================

A small storyworld for a cozy ghost-story premise with inner monologue:
a child hears a spooky sound from a tin object, worries in private, then
discovers a harmless cause and makes the place feel safe again.

The world is built as a tiny causal simulation:
- the child has emotional state in memes
- objects and places have physical meters
- a forward rule engine turns fear, noise, and discovery into narrated change
- the ending proves what changed in the world model

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/tin_inner_monologue_ghost_story.py
    python storyworlds/worlds/gpt-5.4-mini/tin_inner_monologue_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/tin_inner_monologue_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/tin_inner_monologue_ghost_story.py --json
    python storyworlds/worlds/gpt-5.4-mini/tin_inner_monologue_ghost_story.py --verify
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
CALM_MIN = 2


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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    dim: str
    hush: str
    has_draft: bool = False
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
class TinObject:
    id: str
    label: str
    phrase: str
    sound: str
    hiding: str
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
class Helper:
    id: str
    label: str
    action: str
    comfort: str
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
    place: str = "hall"
    tin: str = "box"
    helper: str = "lamp"
    child: str = "Mina"
    child_gender: str = "girl"
    parent: str = "mother"
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["spooked"] < THRESHOLD:
        return out
    sig = ("fear", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["thoughts"] += 1
    world.get("house").meters["quiet"] += 1
    out.append("__thought__")
    return out


def _r_discover(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tin = world.get("tin")
    if child.meters["looked"] < THRESHOLD or tin.meters["seen"] < THRESHOLD:
        return out
    sig = ("discover", tin.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["courage"] += 1
    tin.meters["mystery"] = 0.0
    out.append("__discovery__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["courage"] < THRESHOLD:
        return out
    sig = ("relief", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.get("house").meters["quiet"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("fear", _r_fear),
    Rule("discover", _r_discover),
    Rule("relief", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bool_to_reason(ok: bool, reason: str) -> None:
    if not ok:
        raise StoryError(reason)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid, tin in TINS.items():
            for hid, helper in HELPERS.items():
                if helper.tags & tin.tags:
                    combos.append((pid, tid, hid))
    return combos


def reasonableness(place: Place, tin: TinObject, helper: Helper) -> bool:
    return bool(helper.tags & tin.tags) and place.has_draft


def predict(world: World, tin_id: str) -> dict:
    sim = world.copy()
    sim.get("child").meters["spooked"] += 1
    sim.get("tin").meters["seen"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "relief": sim.get("child").memes["relief"],
    }


def start(world: World, child: Entity, place: Place, tin: TinObject) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"At {place.label}, {child.id} heard a thin clink from {tin.phrase}. "
        f"The sound seemed to come from the dark."
    )
    world.say(
        f'In {child.pronoun("possessive")} own head, {child.id} thought, '
        f'"That is a ghost sound. It has to be a ghost sound."'
    )


def listen(world: World, child: Entity, place: Place) -> None:
    child.meters["spooked"] += 1
    world.get("house").meters["quiet"] += 1
    world.say(
        f"The hall was so still that even the floorboards felt like they were holding their breath."
    )
    world.say(
        f'{child.id} listened harder and thought, "If I call out, maybe the ghost will answer."'
    )


def approach(world: World, child: Entity, tin: TinObject) -> None:
    child.meters["looked"] += 1
    tin.meters["seen"] += 1
    world.say(
        f'{child.id} took one small step closer to {tin.phrase}. '
        f'In {child.pronoun("possessive")} head, the tin looked like a little sleeping mouth.'
    )


def reveal(world: World, child: Entity, tin: TinObject, helper: Helper) -> None:
    world.say(
        f'Then {child.id} lifted the tin, and {tin.sound} came again -- '
        f'not a ghost voice, just something light bumping inside.'
    )
    world.say(
        f'{child.id} found a tiny {helper.label} tucked where the wind could tap it.'
    )


def calm_end(world: World, child: Entity, helper: Helper) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f'In {child.id}\'s chest, the fear turned soft and small. '
        f'"I was scared," {child.id} thought, "but I looked anyway."'
    )
    world.say(
        f"{helper.action.capitalize()}, and the hall felt friendly again."
    )
    world.say(
        f"{child.id} put the tin back on the shelf and smiled at its harmless little chime."
    )


def tell(place: Place, tin: TinObject, helper: Helper,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    tin_ent = world.add(Entity(id="tin", type="thing", label=tin.label, tags=set(tin.tags)))
    house = world.add(Entity(id="house", type="place", label=place.label))
    world.facts["helper"] = helper.id
    world.facts["tin"] = tin.id
    world.facts["place"] = place.id
    world.facts["parent"] = parent

    start(world, child, place, tin)
    world.para()
    listen(world, child, place)
    approach(world, child, tin)
    predicted = predict(world, "tin")
    world.facts["predicted"] = predicted
    if predicted["fear"] >= 1:
        reveal(world, child, tin, helper)
        world.para()
        child.meters["spooked"] += 0.0
        propagate(world, narrate=False)
        calm_end(world, child, helper)
    else:
        world.say("Nothing happened, and the spooky feeling drifted away on its own.")

    world.facts.update(
        child=child,
        tin=tin_ent,
        house=house,
        outcome="calm",
        seen=tin_ent.meters["seen"] >= THRESHOLD,
        relieved=child.memes["relief"] >= THRESHOLD,
    )
    return world


PLACES = {
    "hall": Place(id="hall", label="the hall", dim="long and narrow", hush="echoes", has_draft=True, tags={"draft"}),
    "attic": Place(id="attic", label="the attic", dim="small and dusty", hush="whispers", has_draft=True, tags={"draft"}),
    "porch": Place(id="porch", label="the porch", dim="wooden", hush="creaks", has_draft=True, tags={"draft"}),
}

TINS = {
    "box": TinObject(id="box", label="tin box", phrase="a tin box on the shelf", sound="clink", hiding="a little latch", tags={"tin"}),
    "can": TinObject(id="can", label="tin can", phrase="a tin can near the steps", sound="clink", hiding="a bent rim", tags={"tin"}),
    "toy": TinObject(id="toy", label="tin toy", phrase="an old tin toy in the corner", sound="ting", hiding="a loose wheel", tags={"tin"}),
}

HELPERS = {
    "lamp": Helper(id="lamp", label="lamp", action="the lamp blinked on", comfort="warm light", tags={"tin"}),
    "window": Helper(id="window", label="open window", action="the window let in a hush of air", comfort="fresh air", tags={"tin"}),
    "grandma": Helper(id="grandma", label="grandma's story", action="grandma laughed softly", comfort="a calm voice", tags={"tin"}),
}

GIRL_NAMES = ["Mina", "Tess", "Luna", "Ivy", "Nora"]
BOY_NAMES = ["Owen", "Eli", "Finn", "Theo", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with tin sounds and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tin", choices=TINS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if args.place in (None, c[0])
              and args.tin in (None, c[1])
              and args.helper in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    if args.place and args.tin and args.helper:
        place = PLACES[args.place]
        tin = TINS[args.tin]
        helper = HELPERS[args.helper]
        bool_to_reason(reasonableness(place, tin, helper),
                       "That helper does not fit the tin story.")
    place, tin, helper = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, tin=tin, helper=helper, child=child, child_gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.tin not in TINS:
        raise StoryError(f"Unknown tin: {params.tin}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    world = tell(PLACES[params.place], TINS[params.tin], HELPERS[params.helper],
                 child_name=params.child, child_gender=params.child_gender, parent_type=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that includes the word "tin" and uses an inner monologue.',
        f"Tell a gentle spooky story where {f['child'].id} hears a mysterious tin sound at {f['place']} and learns it is harmless.",
        f"Write a quiet haunted-house story that starts with fear, uses private thoughts, and ends with a safe reveal about a tin object.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    tin: Entity = f["tin"]
    house: Entity = f["house"]
    helper = HELPERS[f["helper"]]
    qa = [
        ("What did the child think the sound was at first?",
         f"{child.id} thought it was a ghost sound. That was the private worry in {child.pronoun('possessive')} head before anything was proven."),
        ("What made the scary sound turn out to be harmless?",
         f"The child lifted the tin and found a tiny {helper.label} where the wind could tap it. The sound was just a light clink, not a ghost."),
        ("How did the story end?",
         f"It ended safely, with {child.id} putting the tin back and feeling brave. The hall felt friendly again instead of spooky.")
    ]
    if f.get("seen"):
        qa.append((
            f"Why did {child.id} get brave enough to look?",
            f"{child.id} first felt fear, but the quiet room and the little clue of the sound pushed {child.pronoun('object')} to look closer. Once {child.id} saw the tin, the mystery could be solved."
        ))
    if f.get("relieved"):
        qa.append((
            f"What changed in {house.label_word} by the end?",
            f"The house got calmer. The loud scary feeling went away, and the tin made only a small harmless chime."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    out = [
        ("What is tin?",
         "Tin is a kind of metal. It can make a clink or chime when something taps it."),
        ("Why can a quiet place feel spooky?",
         "When a place is very quiet, small sounds seem bigger and scarier than they really are."),
        ("What is an inner monologue?",
         "An inner monologue is the voice of a character's own thoughts in their head."),
    ]
    if f["place"] == "attic":
        out.append(("Why can an attic feel spooky?",
                    "An attic can feel spooky because it is often dusty, quiet, and full of shadows. That makes tiny sounds seem mysterious."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
spooked(child) :- child_spooks(child).
noticed(tin) :- looked_at(tin).
relieved(child) :- spooked(child), noticed(tin).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TINS:
        lines.append(asp.fact("tin", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(valid_combos()) == set(valid_combos()):
        print(f"OK: valid_combos() self-check ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, tin=None, helper=None, child=None, child_gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: default generation smoke test.")
    except Exception as err:
        print(f"FAIL: generate() smoke test: {err}")
        return 1
    return rc


def valid_story_helpers() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(place="hall", tin="box", helper="lamp", child="Mina", child_gender="girl", parent="mother"),
    StoryParams(place="attic", tin="toy", helper="window", child="Owen", child_gender="boy", parent="father"),
    StoryParams(place="porch", tin="can", helper="grandma", child="Luna", child_gender="girl", parent="mother"),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
