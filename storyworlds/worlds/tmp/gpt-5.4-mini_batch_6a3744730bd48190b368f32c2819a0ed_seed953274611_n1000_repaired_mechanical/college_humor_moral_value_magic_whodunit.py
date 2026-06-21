#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/college_humor_moral_value_magic_whodunit.py
============================================================================

A small college whodunit with humor, a moral turn, and a little magic.

Premise:
- A college prop goes missing during a silly campus event.
- One student suspects a magical trick, but the clues point elsewhere.
- The real fix is honest, kind, and funny: the thief turns out to be trying to
  help, and the missing item is found in an unexpected place.

This is a standalone storyworld script with typed entities, physical meters and
emotional memes, a tiny causal engine, a reasonableness gate, inline ASP twins,
and three Q&A sets grounded in simulated state.
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
SENSE_MIN = 2


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
    magic: bool = False
    clue: bool = False
    missing: bool = False
    found: bool = False

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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    campus_kind: str
    noise: str
    magic_flavor: str
    clue_places: list[str]
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    missing_text: str
    clue_text: str
    magicable: bool = False
    clue_kind: str = "thing"
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
class Trick:
    id: str
    label: str
    idea: str
    effect: str
    sense: int
    power: int
    honest: bool
    funny: bool
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


def _r_magic_glow(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["magic"] < THRESHOLD:
            continue
        sig = ("magic_glow", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("campus").meters["curious"] += 1
        out.append("__magic__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    if world.get("scene").meters["absurd"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("nora", "milo"):
        world.get(eid).memes["amused"] += 1
    out.append("__laugh__")
    return out


CAUSAL_RULES = [Rule("magic_glow", "magic", _r_magic_glow), Rule("laugh", "social", _r_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(place: Place, obj: ObjectCfg, trick: Trick) -> bool:
    return place.id in PLACES and obj.id in OBJECTS and trick.id in TRICKS and trick.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for oid, obj in OBJECTS.items():
            for tid, trick in TRICKS.items():
                if reasonableness_ok(place, obj, trick):
                    combos.append((pid, oid, tid))
    return combos


def nice_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def setup_story(world: World, place: Place, obj: ObjectCfg, trick: Trick) -> None:
    campus = world.add(Entity(id="campus", kind="place", type="college", label=place.label))
    campus.meters["curious"] = 0.0
    scene = world.add(Entity(id="scene", kind="thing", type="event", label="club fair"))
    scene.meters["absurd"] = 1.0 if trick.funny else 0.0
    nora = world.add(Entity(id="nora", kind="character", type="girl", role="detective", label="Nora", traits=["sharp", "kind"]))
    milo = world.add(Entity(id="milo", kind="character", type="boy", role="helper", label="Milo", traits=["goofy", "honest"]))
    prof = world.add(Entity(id="prof", kind="character", type="adult", role="guide", label="Professor Quill", traits=["calm"]))
    missing = world.add(Entity(id="amulet", kind="thing", type=obj.clue_kind, label=obj.label, missing=True, magic=obj.magicable))
    world.facts.update(place=place, obj=obj, trick=trick, campus=campus, scene=scene, nora=nora, milo=milo, prof=prof, missing=missing)


def tell(place: Place, obj: ObjectCfg, trick: Trick, nora_name: str, milo_name: str) -> World:
    world = World()
    setup_story(world, place, obj, trick)
    nora = world.get("nora"); nora.id = nora_name; nora.label = nora_name
    milo = world.get("milo"); milo.id = milo_name; milo.label = milo_name
    prof = world.get("prof")
    campus = world.get("campus")
    scene = world.get("scene")
    missing = world.get("amulet")
    world.say(f"At {place.label} college, Nora and Milo were helping with the club fair. The hall smelled like popcorn, chalk dust, and big ideas.")
    world.say(f"Then the {obj.label} went missing. {obj.missing_text} Nora narrowed {nora.pronoun('possessive')} eyes like a tiny detective.")
    world.para()
    world.say(f'"The clue is magical," Milo whispered. "I can feel it in my noodles."')
    world.say(f"Nora found a spark of {place.magic_flavor} near {place.clue_places[0]}. {obj.clue_text}")
    world.say(f'"Whoever took it had a reason," said {prof.label_word}. "A silly one, maybe. But a reason."')
    trick_used = trick.honest
    if trick_used:
        missing.meters["magic"] += 1
        scene.meters["absurd"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(f"Milo had used a little magic trick: {trick.idea}. It made the flyer dance, the chalk wink, and three students swear the building had sneezed.")
        world.say(f"But the joke hid a clue. {trick.effect}, and that pointed to the old costume room.")
        missing.found = True
        missing.missing = False
        missing.attrs["found_in"] = "costume room"
        world.para()
        world.say(f"Nora opened the costume room and found the {obj.label} sitting on a box of fake mustaches. Nobody had stolen it for greed; Milo had moved it there to keep it safe from the punch bowl.")
        world.say(f'"I was trying to help," Milo said, sheepish. "I also may have made the hallway look haunted."')
        world.say(f'"Next time," said {prof.label_word}, smiling, "tell the truth first, and save the magic for birthday parties."')
        world.say(f"Nora laughed, because the case was solved, the {obj.label} was back, and the only thing truly enchanted was how relieved everyone felt.")
        outcome = "solved"
    else:
        missing.meters["magic"] += 0.0
        world.para()
        world.say(f"Someone had done a sneaky little spell, but it left no good clue. Nora and Milo looked under the stage, behind the banners, and even inside a trumpet case.")
        world.say(f"At last, they found the {obj.label} in the costume room, where it had been tucked away during setup. The whole mystery turned out to be less spooky than a lost sock.")
        world.say(f"Milo confessed he had moved it without asking, and Professor Quill said the right thing was to apologize and return it, not to invent a bigger lie.")
        world.say(f"The case ended with laughter, a lesson, and the {obj.label} back where it belonged.")
        outcome = "unsolved"
    world.facts["outcome"] = outcome
    return world


THEMES = {
    "campus": Place(id="campus", label="college", campus_kind="college", noise="students laughing", magic_flavor="sparkly chalk", clue_places=["the notice board", "the trophy shelf"], tags={"college"}),
    "library": Place(id="library", label="the college library", campus_kind="college", noise="pages whispering", magic_flavor="moonlit dust", clue_places=["the returns cart", "the reading nook"], tags={"college"}),
    "quad": Place(id="quad", label="the college quad", campus_kind="college", noise="bicycles ringing", magic_flavor="glitter in the grass", clue_places=["the fountain", "the band bench"], tags={"college"}),
}

PLACES = THEMES

OBJECTS = {
    "trophy": ObjectCfg(id="trophy", label="gold trophy", phrase="a gold trophy", missing_text="The trophy cabinet looked empty.", clue_text="A little patch of glitter clung to the cabinet handle.", magicable=True, clue_kind="trophy", tags={"magic", "college"}),
    "lantern": ObjectCfg(id="lantern", label="lantern", phrase="a lantern", missing_text="The lantern shelf was bare.", clue_text="A streak of wax and sparkles led toward the side door.", magicable=True, clue_kind="lantern", tags={"magic", "college"}),
    "mask": ObjectCfg(id="mask", label="theater mask", phrase="a theater mask", missing_text="The mask box had only one lonely ribbon left.", clue_text="A ribbon fluttered near the costume stairs like it was trying to be innocent.", magicable=True, clue_kind="mask", tags={"humor", "college"}),
}

TRICKS = {
    "chalk": Trick(id="chalk", label="talking chalk", idea="he tapped the chalk and made it scribble fake footprints", effect="the footprints ended at the costume room door", sense=2, power=1, honest=True, funny=True, tags={"magic", "humor"}),
    "glow": Trick(id="glow", label="glow spell", idea="he made the flyer glow like a firefly", effect="the glow reflected in a mirror facing the costume room", sense=3, power=1, honest=True, funny=True, tags={"magic", "humor"}),
    "puff": Trick(id="puff", label="puff of smoke", idea="he sneezed a puff of harmless smoke into the air", effect="the smoke curled toward the costume room vent", sense=2, power=1, honest=True, funny=True, tags={"magic", "humor"}),
}

NAMES = ["Nora", "Milo", "Ivy", "Ben", "Tara", "Eli", "June", "Owen"]


@dataclass
class StoryParams:
    place: str
    obj: str
    trick: str
    nora: str
    milo: str
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


CURATED = [
    StoryParams(place="campus", obj="mask", trick="chalk", nora="Nora", milo="Milo"),
    StoryParams(place="library", obj="trophy", trick="glow", nora="Ivy", milo="Ben"),
    StoryParams(place="quad", obj="lantern", trick="puff", nora="June", milo="Owen"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny college whodunit that includes the word "college" and a little magic, ending with a moral lesson.',
        f"Tell a story set at {f['place'].label} where Nora and Milo solve a missing-object mystery with a harmless magical clue.",
        f"Write a campus mystery where somebody is trying to help, the joke is gentle, and the truth is kinder than the rumor.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place: Place = f["place"]
    obj: ObjectCfg = f["obj"]
    trick: Trick = f["trick"]
    outcome = f["outcome"]
    qa = [
        ("Where does the story happen?",
         f"It happens at {place.label}. The whole mystery grows out of ordinary college life, which makes the magical clue feel extra surprising."),
        ("What went missing?",
         f"The {obj.label} went missing. That was the problem everyone had to solve before the club fair could feel normal again."),
        ("What magical trick was used?",
         f"{trick.idea.capitalize()}. It was funny rather than scary, and it helped point Nora toward the real answer."),
    ]
    if outcome == "solved":
        qa.append((
            "Who really moved the object?",
            "Milo moved it, but he was trying to keep it safe from a mess. He should have asked first, yet the story ends with honesty and apology instead of blame."
        ))
        qa.append((
            "What is the moral of the story?",
            "Tell the truth first and ask before you move something that belongs to someone else. A small mistake can be fixed, but honesty makes the fix kinder."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with laughter, the {obj.label} returned, and everyone relieved that the mystery was solved. The last image is a neat one: the lost thing back where it belonged."
        ))
    else:
        qa.append((
            "What did Nora learn?",
            "She learned that a mystery can look magical even when the answer is ordinary. A careful check of the real clues still matters more than guessing."
        ))
        qa.append((
            "What is the moral of the story?",
            "Apologize when you make a bad choice and return what you took. Being honest is better than inventing a bigger lie."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["obj"].tags) | set(world.facts["trick"].tags)
    bank = {
        "college": [("What is college?", "College is a place where older students study, learn new things, and work toward jobs they want to do later.")],
        "magic": [("What is magic in stories?", "In stories, magic is a special power that can make strange things happen. It is fun to imagine, but it is not real life.")],
        "humor": [("Why do stories use humor?", "Humor makes a story feel lighter and more fun. A joke can help a mystery feel friendly instead of scary.")],
        "moral": [("What is a moral?", "A moral is the lesson a story wants you to remember. It helps you know how to act kindly and wisely.")],
        "whodunit": [("What is a whodunit?", "A whodunit is a mystery story where readers try to figure out who did it before the answer is revealed.")],
    }
    order = ["college", "whodunit", "humor", "magic", "moral"]
    out = []
    for tag in order:
        if tag in tags or tag in bank:
            out.extend(bank.get(tag, []))
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
        if e.magic:
            bits.append("magic=True")
        if e.missing:
            bits.append("missing=True")
        if e.found:
            bits.append("found=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
magic_glow(E) :- entity(E), magic(E), not found(E).
laugh(scene) :- absurd(scene), not broken(scene).
valid(P,O,T) :- place(P), object(O), trick(T), sense(T,S), sense_min(M), S >= M.
outcome(solved) :- honest(T), magic(T), valid(P,O,T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.magicable:
            lines.append(asp.fact("magic", oid))
    for tid, t in TRICKS.items():
        lines.append(asp.fact("trick", tid))
        lines.append(asp.fact("sense", tid, t.sense))
        if t.honest:
            lines.append(asp.fact("honest", tid))
        if t.funny:
            lines.append(asp.fact("funny", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP vs Python gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="College whodunit with humor, moral value, and a little magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--nora")
    ap.add_argument("--milo")
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
              if (args.place is None or c[0] == args.place)
              and (args.obj is None or c[1] == args.obj)
              and (args.trick is None or c[2] == args.trick)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, trick = rng.choice(sorted(combos))
    return StoryParams(place=place, obj=obj, trick=trick,
                       nora=args.nora or nice_name(rng, ["Nora", "Ivy", "June", "Tara"]),
                       milo=args.milo or nice_name(rng, ["Milo", "Ben", "Owen", "Eli"]))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.obj not in OBJECTS or params.trick not in TRICKS:
        raise StoryError("Invalid params.")
    world = tell(PLACES[params.place], OBJECTS[params.obj], TRICKS[params.trick], params.nora, params.milo)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos:")
        for t in asp.atoms(model, "valid"):
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
