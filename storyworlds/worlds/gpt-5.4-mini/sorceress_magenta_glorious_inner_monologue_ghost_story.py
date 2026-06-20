#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sorceress_magenta_glorious_inner_monologue_ghost_story.py
=========================================================================================

A small standalone storyworld for a ghost-story seed with the words
"sorceress", "magenta", and "glorious", using an inner-monologue frame.

Premise:
- A child or young helper enters an old tower at dusk.
- A nervous inner monologue tries to manage fear.
- A magenta clue, a ghostly presence, and a sorceress's calm magic turn the
  scare into a glorious, safe ending.

This is a classical, state-driven TinyStories-style simulation: typed entities
have physical meters and emotional memes, causality changes world state, and the
renderer turns that state into prose.
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
FEAR_LIMIT = 2.0


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
        female = {"girl", "mother", "mom", "woman", "sorceress"}
        male = {"boy", "father", "dad", "man", "ghost"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    dark: bool = True
    eerie: bool = True
    glow: str = ""

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
class Magic:
    id: str
    label: str
    color: str
    effect: str
    safe: bool = True

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
    apply: Callable[[World], list[str]]

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


def _r_fear_spike(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["haunting"] < THRESHOLD:
            continue
        sig = ("fear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in list(world.entities.values()):
            if c.kind == "character":
                c.memes["fear"] += 1
        out.append("__shiver__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glow"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in list(world.entities.values()):
            if c.kind == "character":
                c.memes["calm"] += 1
                if c.memes["fear"] > 0:
                    c.memes["fear"] = max(0.0, c.memes["fear"] - 1)
        out.append("__warm__")
    return out


RULES = [Rule("fear", _r_fear_spike), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predictive_whisper(world: World, place: Place) -> dict:
    sim = world.copy()
    sim.get("ghost").meters["haunting"] += 1
    propagate(sim, narrate=False)
    return {"fear": sim.get("child").memes["fear"], "haunting": sim.get("ghost").meters["haunting"]}


def reasonableness_gate(magic: Magic, place: Place) -> bool:
    return magic.safe and place.dark and place.eerie


def valid_combos() -> list[tuple[str, str]]:
    return [(p.id, m.id) for p in PLACES.values() for m in MAGICS.values() if reasonableness_gate(m, p)]


@dataclass
@dataclass
class StoryParams:
    place: str
    magic: str
    child: str
    child_gender: str
    sorceress: str
    sorceress_gender: str
    ghost: str
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


def inner_thoughts(world: World, child: Entity, place: Place, ghost: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f"{child.id} stepped into {place.name} and tried to be brave. "
        f'In {child.pronoun("possessive")} head, a tiny voice whispered, "This '
        f"is scary, but I can still look for the clue."
    )


def setup(world: World, child: Entity, sorceress: Entity, ghost: Entity, place: Place) -> None:
    world.say(
        f"At dusk, {child.id} and {sorceress.id} went into {place.name}. "
        f"The windows were dim, and the hallway felt like a ghost story."
    )
    world.say(
        f"{child.id} heard a soft rustle and wondered if the {ghost.id} was real."
    )


def reveal(world: World, ghost: Entity, magic: Magic) -> None:
    ghost.meters["haunting"] += 1
    ghost.memes["lonely"] += 1
    world.say(
        f"A pale shape drifted out of the shadows, and the room went still. "
        f"The air felt cold, like a held breath."
    )
    propagate(world, narrate=True)


def use_magic(world: World, sorceress: Entity, magic: Magic, child: Entity) -> None:
    world.say(
        f'The {sorceress.label_word} lifted {sorceress.pronoun("possessive")} hands. '
        f'"Look closely," {sorceress.id} said, and cast {magic.label}.'
    )
    world.say(
        f"The magic flashed {magic.color}, and {magic.effect}."
    )


def resolution(world: World, child: Entity, sorceress: Entity, ghost: Entity, magic: Magic) -> None:
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    child.memes["wonder"] += 2
    ghost.memes["joy"] += 1
    ghost.meters["haunting"] = 0.0
    world.say(
        f"Then the ghost's face turned kind instead of grim. It was only lonely, "
        f"not mean at all."
    )
    world.say(
        f"The {sorceress.label_word} smiled and told {child.id} that some spooky "
        f"things just need a little light and a little patience."
    )
    world.say(
        f"{child.id} took a slow breath and felt the fear leave {child.pronoun('possessive')} shoulders."
    )
    world.say(
        f"By the end, the tower looked glorious: {magic.color} light on old stones, "
        f"a gentle ghost, and {child.id} standing brave beside the {sorceress.label_word}."
    )


def tell(place: Place, magic: Magic, child_name: str = "Mina", child_gender: str = "girl",
         sorceress_name: str = "Selene", sorceress_gender: str = "woman",
         ghost_name: str = "ghost") -> World:
    world = World()
    child = world.add(Entity(child_name, kind="character", type=child_gender, role="child"))
    sorceress = world.add(Entity(sorceress_name, kind="character", type=sorceress_gender, role="sorceress", label="sorceress"))
    ghost = world.add(Entity(ghost_name, kind="character", type="ghost", role="ghost", label="ghost"))
    tower = world.add(Entity("tower", type="place", label=place.name))
    spell = world.add(Entity(magic.id, type="magic", label=magic.label))
    world.facts.update(place=place, magic=magic, child=child, sorceress=sorceress, ghost=ghost, tower=tower, spell=spell)

    setup(world, child, sorceress, ghost, place)
    world.para()
    inner_thoughts(world, child, place, ghost)
    reveal(world, ghost, magic)
    world.para()
    use_magic(world, sorceress, magic, child)
    resolution(world, child, sorceress, ghost, magic)
    world.facts["ending"] = "glorious"
    world.facts["predicted_fear"] = predictive_whisper(world, place)["fear"]
    return world


PLACES = {
    "old_tower": Place("old_tower", "the old tower", dark=True, eerie=True, glow="moonlight"),
    "attic": Place("attic", "the attic", dark=True, eerie=True, glow="lantern light"),
    "chapel": Place("chapel", "the empty chapel", dark=True, eerie=True, glow="stained glass"),
}

MAGICS = {
    "magenta_glow": Magic("magenta_glow", "magenta glow", "magenta", "painted the dark edges with gentle light"),
    "magenta_lantern": Magic("magenta_lantern", "a magenta lantern spell", "magenta", "made every dusty corner bloom with color"),
}

CHILD_NAMES = ["Mina", "Lina", "Tia", "Nora", "Ivy", "Mara"]
SORCERESS_NAMES = ["Selene", "Amara", "Vera", "Lucia", "Celia"]
GHOST_NAMES = ["ghost", "little ghost", "shy ghost"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: inner-monologue ghost tale with a sorceress and magenta magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"], dest="child_gender")
    ap.add_argument("--sorceress")
    ap.add_argument("--sorceress-gender", choices=["woman", "man"], dest="sorceress_gender")
    ap.add_argument("--ghost")
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
    if args.place and args.magic and not reasonableness_gate(MAGICS[args.magic], PLACES[args.place]):
        raise StoryError("(No story: the magic or the setting does not create a useful ghost-story tension.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.magic is None or c[1] == args.magic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, magic = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    sorc_gender = args.sorceress_gender or "woman"
    child = args.child or rng.choice(CHILD_NAMES)
    sorceress = args.sorceress or rng.choice(SORCERESS_NAMES)
    ghost = args.ghost or rng.choice(GHOST_NAMES)
    return StoryParams(place, magic, child, child_gender, sorceress, sorc_gender, ghost)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story that includes the words "sorceress", "magenta", and "glorious".',
        f"Tell a story where {f['child'].id} feels scared in {f['place'].name}, hears an inner voice, and a sorceress uses {f['magic'].label} to help.",
        f"Write a gentle spooky story with a ghost, a calm sorceress, and an ending that turns glorious and safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sorc = f["sorceress"]
    magic = f["magic"]
    place = f["place"]
    ghost = f["ghost"]
    return [
        QAItem(
            question="What did the child feel at first?",
            answer=f"{child.id} felt scared when the story began. The dark place and the ghostly sound made the inner monologue sound nervous before anything got better."
        ),
        QAItem(
            question="What did the sorceress do?",
            answer=f"The sorceress cast {magic.label} and filled the room with magenta light. That calm magic changed the scene from spooky to safe."
        ),
        QAItem(
            question="What happened to the ghost at the end?",
            answer=f"The ghost stopped haunting and became gentle and lonely instead of frightening. By the end, it was calm enough to be part of the glorious ending."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended gloriously in {place.name}, with magenta light on the old stones and {sorc.id} standing beside {child.id}. The scary feeling gave way to wonder and relief."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a sorceress?", "A sorceress is a person who uses magic. In stories, a sorceress can help, protect, or transform what seems scary."),
        QAItem("What does magenta mean?", "Magenta is a bright pink-purple color. It often looks vivid, glowing, and a little magical."),
        QAItem("What is a ghost story?", "A ghost story is a tale about spooky things, haunted places, or unseen characters. A child-friendly ghost story can still end safely and kindly."),
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M) :- place(P), magic(M), safe(M), dark(P), eerie(P).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m, mm in MAGICS.items():
        lines.append(asp.fact("magic", m))
        if mm.safe:
            lines.append(asp.fact("safe", m))
    for p, pl in PLACES.items():
        if pl.dark:
            lines.append(asp.fact("dark", p))
        if pl.eerie:
            lines.append(asp.fact("eerie", p))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, magic=None, child=None, child_gender=None, sorceress=None, sorceress_gender=None, ghost=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAILED: {exc}")
        return 1
    if ok:
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
        print("OK: normal generation smoke test passed.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MAGICS[params.magic], params.child, params.child_gender, params.sorceress, params.sorceress_gender, params.ghost)
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


CURATED = [
    StoryParams("old_tower", "magenta_glow", "Mina", "girl", "Selene", "woman", "ghost"),
    StoryParams("attic", "magenta_lantern", "Nora", "girl", "Amara", "woman", "little ghost"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, m in asp_valid_combos():
            print(f"  {p:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
