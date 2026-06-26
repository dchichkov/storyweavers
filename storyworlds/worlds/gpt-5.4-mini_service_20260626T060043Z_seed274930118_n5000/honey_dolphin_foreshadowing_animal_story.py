#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/honey_dolphin_foreshadowing_animal_story.py
==============================================================================================================

A small animal-story world about a dolphin, a little honey, and the warning
signs that something sticky may go wrong before it does.

Seed tale inspiration:
---
A curious dolphin loved the shiny smell of honey that drifted from a beach
picnic. The dolphin wanted to carry a jar to a friend, but first a buzzing bee,
a tilting lid, and a sticky fin hinted that the honey might spill. The dolphin
listened, used a shell boat, and delivered the honey safely.

This world keeps that premise as a stateful simulation:
- a dolphin character,
- a honey object that can spill and stick,
- foreshadowing signals that build tension,
- a careful fix that avoids the mess.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

FORESHADOW_SIGNS = ["buzz", "tilt", "drip"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "dolphin":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type == "bee":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type == "seal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    smell: str
    affords: set[str] = field(default_factory=set)


@dataclass
class CarryOption:
    id: str
    label: str
    phrase: str
    guards: set[str]
    fits: set[str]
    safe_signs: set[str] = field(default_factory=set)
    tail: str = ""


@dataclass
class StoryParams:
    place: str
    carrier: str
    helper: str
    option: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.signs_seen: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def carryer(self) -> Entity:
        return next(e for e in self.entities.values() if e.kind == "character" and e.type == "dolphin")

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.signs_seen = list(self.signs_seen)
        return clone


def note_sign(world: World, sign: str) -> None:
    if sign not in world.signs_seen:
        world.signs_seen.append(sign)


def apply_foreshadowing(world: World) -> list[str]:
    out = []
    dolphin = world.carryer()
    if dolphin.memes.get("curiosity", 0) >= THRESHOLD and "buzz" not in world.signs_seen:
        note_sign(world, "buzz")
        dolphin.memes["unease"] = dolphin.memes.get("unease", 0) + 0.5
        out.append("A tiny buzz hummed near the jar, as if something was watching the honey.")
    if world.entities["honey"].meters.get("tilt", 0) >= THRESHOLD and "tilt" not in world.signs_seen:
        note_sign(world, "tilt")
        out.append("The jar gave a small tilt, and a drop slid toward the lid.")
    if world.entities["honey"].meters.get("drip", 0) >= THRESHOLD and "drip" not in world.signs_seen:
        note_sign(world, "drip")
        out.append("A sticky drip gathered at the rim, shining like a warning.")
    return out


def pour_spill(world: World) -> list[str]:
    out = []
    honey = world.entities["honey"]
    carrier = world.carryer()
    if honey.carried_by != carrier.id:
        return out
    if carrier.meters.get("safe_container", 0) >= THRESHOLD:
        return out
    if honey.meters.get("tilt", 0) >= THRESHOLD and honey.meters.get("drip", 0) >= THRESHOLD:
        sig = ("spill",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        honey.meters["spilled"] = 1
        carrier.memes["worry"] = carrier.memes.get("worry", 0) + 1
        out.append("The honey sloshed out and made a sticky puddle on the sand.")
    return out


def resolve_fix(world: World) -> list[str]:
    out = []
    carrier = world.carryer()
    option = world.facts["option"]
    if option == "shell_boat":
        sig = ("fix", option)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        carrier.meters["safe_container"] = 1
        honey = world.entities["honey"]
        honey.carried_by = carrier.id
        honey.meters["tilt"] = 0
        honey.meters["drip"] = 0
        carrier.memes["joy"] = carrier.memes.get("joy", 0) + 1
        out.append("So the dolphin tucked the honey jar into a shell boat and the lid stayed steady.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for s in apply_foreshadowing(world) + pour_spill(world) + resolve_fix(world):
            if s not in produced:
                produced.append(s)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, option: CarryOption, name: str = "Dory", trait: str = "curious") -> World:
    world = World(setting)
    dolphin = world.add(Entity(id=name, kind="character", type="dolphin", traits=["little", trait]))
    bee = world.add(Entity(id="bee", kind="character", type="bee", label="a busy bee"))
    seal = world.add(Entity(id="seal", kind="character", type="seal", label="a seal friend"))
    honey = world.add(Entity(
        id="honey", type="honey", label="honey", phrase="a small jar of honey",
        owner=dolphin.id, caretaker=seal.id, carried_by=dolphin.id
    ))
    world.facts.update(hero=dolphin, bee=bee, seal=seal, honey=honey, option=option, setting=setting)

    dolphin.memes["curiosity"] = 1
    dolphin.memes["love"] = 1
    honey.meters["tilt"] = 0
    honey.meters["drip"] = 0

    world.say(f"{dolphin.id} was a little {trait} dolphin who loved sweet smells and bright chances.")
    world.say(f"At {setting.place}, the air smelled like salt and warm honey, and {dolphin.id} carried a small jar along the shore.")
    world.say(f"{dolphin.id} wanted to bring {honey.phrase} to the {bee.label if bee.label else 'bee'} near the flowers.")
    world.para()
    world.say("First came the signs.")
    # Foreshadowing beats
    world.entities["honey"].meters["tilt"] = 1
    propagate(world)
    world.say(f"{seal.label.capitalize()} noticed the wobble and called, \"Careful, {dolphin.id}! That jar is tipping.\"")
    world.say(f"{dolphin.id} slowed down, and the little warning made {dolphin.pronoun('possessive')} ears feel warm.")
    world.para()

    world.say(f"{dolphin.id} looked around and saw a {option.label} nearby.")
    if option.id == "shell_boat":
        world.say("It was just wide enough to hold the jar without letting it roll.")
    propagate(world)
    world.say(f"{dolphin.id} nodded and chose the safer way.")
    world.say(f"They placed the honey in the shell boat and carried it over the wet sand.")
    world.say(f"The bee got a sweet taste, the seal smiled, and the honey stayed where it belonged.")
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "beach": Setting(place="the beach", smell="salt and honey", affords={"carry"}),
    "harbor": Setting(place="the harbor", smell="salt and fish", affords={"carry"}),
    "reef": Setting(place="the reef", smell="seaweed and sun", affords={"carry"}),
}

OPTIONS = {
    "shell_boat": CarryOption(
        id="shell_boat",
        label="shell boat",
        phrase="a wide shell boat",
        guards={"spill"},
        fits={"honey"},
        safe_signs={"tilt", "drip"},
        tail="the shell boat held the jar steady",
    ),
    "leaf_basket": CarryOption(
        id="leaf_basket",
        label="leaf basket",
        phrase="a woven leaf basket",
        guards={"spill"},
        fits={"honey"},
        safe_signs={"tilt"},
        tail="the leaf basket stayed snug",
    ),
}

TRAITS = ["curious", "gentle", "bright-eyed", "hopeful", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, "carry") for place in SETTINGS]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for oid, opt in OPTIONS.items():
        lines.append(asp.fact("option", oid))
        for g in sorted(opt.guards):
            lines.append(asp.fact("guards", oid, g))
        for f in sorted(opt.fits):
            lines.append(asp.fact("fits", oid, f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place) :- setting(Place), affords(Place, carry).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    place: str
    carrier: str
    helper: str
    option: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about honey, a dolphin, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--carrier", choices=["dolphin"])
    ap.add_argument("--helper", choices=["bee", "seal"])
    ap.add_argument("--option", choices=OPTIONS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(SETTINGS))
    option = args.option or rng.choice(list(OPTIONS))
    if args.helper and args.helper not in {"bee", "seal"}:
        raise StoryError("helper must be bee or seal")
    return StoryParams(
        place=place,
        carrier="dolphin",
        helper=args.helper or rng.choice(["bee", "seal"]),
        option=option,
        name=args.name or rng.choice(["Dory", "Mina", "Lumi", "Nori", "Tide"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short animal story about a dolphin, honey, and a warning that comes true unless the dolphin listens.",
        f"Tell a gentle story where {hero.id} the dolphin notices signs that {f['honey'].label} might spill, then finds a safer way.",
        "Write an Animal Story with foreshadowing, a sticky problem, and a happy ending by the sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["seal"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.trait if hasattr(hero, 'trait') else 'curious'} dolphin who carries honey by the sea.",
        ),
        QAItem(
            question=f"What early signs warned that the honey might spill?",
            answer="A tiny buzz, a tilting jar, and a sticky drip all hinted that the honey could make a mess.",
        ),
        QAItem(
            question=f"How did {hero.id} keep the honey safe?",
            answer=f"{hero.id} put the jar into a shell boat so the lid stayed steady and the honey reached the friends without spilling.",
        ),
        QAItem(
            question=f"Who helped notice the danger?",
            answer=f"{helper.label.capitalize()} noticed the wobble and called out a warning before the honey could slip.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is honey?",
            answer="Honey is a sweet, sticky food made by bees from flower nectar.",
        ),
        QAItem(
            question="Why does honey drip slowly?",
            answer="Honey drips slowly because it is thick and sticky, so it moves more slowly than water.",
        ),
        QAItem(
            question="What is a dolphin?",
            answer="A dolphin is a smart sea animal that swims quickly and uses sound to notice things around it.",
        ),
    ]


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
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  signs seen: {world.signs_seen}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    option = OPTIONS[params.option]
    world = tell(SETTINGS[params.place], option, params.name, params.trait)
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


def asp_verify() -> int:
    import asp
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible settings:")
        for c in combos:
            print(" ", c[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, carrier="dolphin", helper="seal", option="shell_boat", name="Dory", trait="curious")
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
