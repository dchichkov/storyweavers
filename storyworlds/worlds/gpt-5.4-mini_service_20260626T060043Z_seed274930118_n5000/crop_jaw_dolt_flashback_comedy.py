#!/usr/bin/env python3
"""
storyworlds/worlds/crop_jaw_dolt_flashback_comedy.py
=====================================================

A tiny comedy storyworld about a child, a garden crop, and a silly mishap that
gets remembered in a flashback before turning into a laugh.

Premise seed:
- The family tends a crop.
- Someone gets a sore jaw from a ridiculous mistake.
- A doltish helper causes the problem.
- A flashback shows the earlier blunder.
- The ending resolves with laughter and a useful fix.

The story stays small on purpose: one domain, a few compatible variants, and a
state-driven turn from embarrassment to comedy.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class CropKind:
    id: str
    label: str
    phrase: str
    mess: str
    harvest_verb: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    label_phrase: str
    helps_with: set[str] = field(default_factory=set)
    comedic: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.flashback: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.flashback = list(self.flashback)
        return c


def _r_jaw_ache(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.meters.get("jaw_ache", 0.0) < THRESHOLD:
            continue
        sig = ("jaw_ache", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["grumpy"] = ent.memes.get("grumpy", 0.0) + 1
        out.append(f"{ent.id} rubbed {ent.pronoun('possessive')} jaw and made a tiny, dramatic face.")
    return out


def _r_crop_spill(world: World) -> list[str]:
    out = []
    for ent in world.characters():
        if ent.meters.get("crop_spilled", 0.0) < THRESHOLD:
            continue
        sig = ("crop_spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["embarrassment"] = ent.memes.get("embarrassment", 0.0) + 1
        out.append(f"That was enough to make {ent.id} blush like a beet.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_jaw_ache, _r_crop_spill):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    crop: str
    tool: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "garden": Place("the garden", False, {"tend", "harvest", "spill"}),
    "farm": Place("the farm patch", False, {"tend", "harvest", "spill"}),
    "yard": Place("the backyard", False, {"tend", "harvest", "spill"}),
}

CROPS = {
    "carrots": CropKind(
        id="carrots",
        label="carrots",
        phrase="a row of orange carrots",
        mess="muddy",
        harvest_verb="pull up",
        smell="sweet",
        tags={"crop", "orange"},
    ),
    "peas": CropKind(
        id="peas",
        label="peas",
        phrase="a patch of round green peas",
        mess="spilled",
        harvest_verb="scoop up",
        smell="fresh",
        tags={"crop", "green"},
    ),
    "corn": CropKind(
        id="corn",
        label="corn",
        phrase="a patch of tall corn",
        mess="dusty",
        harvest_verb="pick",
        smell="warm",
        tags={"crop", "yellow"},
    ),
}

TOOLS = {
    "basket": Tool("basket", "basket", "a basket", helps_with={"carrots", "peas", "corn"}),
    "tray": Tool("tray", "tray", "a wobbly tray", helps_with={"peas", "corn"}, comedic=True),
    "wheelbarrow": Tool("wheelbarrow", "wheelbarrow", "a tiny wheelbarrow", helps_with={"carrots", "corn"}, comedic=True),
}

NAMES = {
    "girl": ["Mina", "Tia", "Lily", "June", "Pia"],
    "boy": ["Owen", "Ben", "Max", "Theo", "Finn"],
}
HELPERS = ["mother", "father", "grandpa", "big sister"]
ROLES = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for crop in CROPS:
            for tool in TOOLS:
                if crop in TOOLS[tool].helps_with:
                    out.append((place, crop, tool))
    return out


def explain_rejection(crop: CropKind, tool: Tool) -> str:
    return (
        f"(No story: {tool.label_phrase} doesn't fit this crop well enough to make a funny problem. "
        f"Try a tool that can actually carry {crop.label}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy storyworld with a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=ROLES)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.crop and args.tool:
        if args.crop not in TOOLS[args.tool].helps_with:
            raise StoryError(explain_rejection(CROPS[args.crop], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.crop is None or c[1] == args.crop)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, crop, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, crop=crop, tool=tool, name=name, role=gender, helper=helper)


def _do_harvest(world: World, hero: Entity, crop: CropKind, tool: Tool, narrate: bool = True) -> None:
    hero.meters["crop_spilled"] = hero.meters.get("crop_spilled", 0.0) + (1.0 if tool.comedic else 0.0)
    hero.meters["jaw_ache"] = hero.meters.get("jaw_ache", 0.0) + 1.0
    propagate(world, narrate=narrate)


def predict(world: World, hero: Entity, crop: CropKind, tool: Tool) -> dict:
    sim = world.copy()
    _do_harvest(sim, sim.get(hero.id), crop, tool, narrate=False)
    return {
        "jaw_ache": sim.get(hero.id).meters.get("jaw_ache", 0.0) >= THRESHOLD,
        "spilled": sim.get(hero.id).meters.get("crop_spilled", 0.0) >= THRESHOLD,
    }


def tell(world: World, hero: Entity, helper: Entity, crop: CropKind, tool: Tool) -> None:
    world.say(f"{hero.id} was a {hero.type} who loved the {crop.label} patch and the smell of {crop.smell} dirt.")
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.type} went to {world.place.name} to {crop.harvest_verb} {crop.phrase}.")
    world.say(f"{hero.id} picked up {tool.label_phrase} and tried to carry the crop with a very serious face.")

    world.para()
    world.say(f"Then the silly trouble started. {hero.id} lifted too much at once, and {hero.pronoun('possessive')} jaw went clicky from the effort.")
    _do_harvest(world, hero, crop, tool, narrate=True)

    world.para()
    if hero.meters.get("jaw_ache", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} winced, and {helper.id} gave a tiny snort of laughter.")
    world.flashback.append(
        f"Earlier that morning, {helper.id} had called {tool.label_phrase} 'the mightiest machine ever made,' "
        f"and then it tipped over as soon as it touched the carrots."
    )
    world.say(f"That reminded everyone of something even funnier.")

    world.para()
    world.say(
        f"In a flashback, {helper.id} had already bragged about the plan, then promptly bounced the {tool.label} into a mud puddle."
    )
    world.say(
        f"This time, {hero.id} laughed so hard that the jaw ache turned into a smile."
    )
    world.say(
        f"{helper.id} helped sort the crop into neat piles, and {hero.id} carried the light baskets instead."
    )
    world.say(
        f"By the end, the {crop.label} were safe, the {tool.label} was clean again, and everybody was laughing at the same dumb mistake."
    )

    world.facts.update(hero=hero, helper=helper, crop=crop, tool=tool)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a funny short story for a young child about {f['hero'].id}, a {f['crop'].label} crop, and a silly helper.",
        f"Tell a comedy story where a character gets a sore jaw while helping with {f['crop'].phrase}, then remembers a flashback.",
        f"Write a gentle, humorous story that uses the words crop, jaw, and dolt without making anyone mean.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    crop = f["crop"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who helped with the {crop.label} crop at {world.place.name}.",
        ),
        QAItem(
            question=f"Why did {hero.id} rub {hero.pronoun('possessive')} jaw?",
            answer=f"{hero.id} rubbed {hero.pronoun('possessive')} jaw because the work got too silly and {hero.pronoun('possessive')} jaw felt achey after the big lift.",
        ),
        QAItem(
            question=f"What did {helper.id} do that made the story funny?",
            answer=f"{helper.id} acted like a doltish helper by bragging about {tool.label_phrase}, and then it tipped over in the mud.",
        ),
        QAItem(
            question=f"What did the flashback show?",
            answer=f"The flashback showed {helper.id} boasting about the plan earlier and then dropping the {tool.label} into a puddle.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the crop sorted safely, the joke finally understood, and everybody laughing together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a crop?",
            answer="A crop is a group of plants that people grow on purpose, often to eat later.",
        ),
        QAItem(
            question="What is a jaw?",
            answer="A jaw is the part of your face that helps you chew food and talk.",
        ),
        QAItem(
            question="What does dolt mean?",
            answer="A dolt is a silly, clumsy person who makes a foolish mistake.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part that shows something that happened earlier than the main moment.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  flashback: {world.flashback[-1] if world.flashback else 'none'}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", crop="carrots", tool="basket", name="Mina", role="girl", helper="mother"),
    StoryParams(place="farm", crop="peas", tool="tray", name="Owen", role="boy", helper="grandpa"),
    StoryParams(place="yard", crop="corn", tool="wheelbarrow", name="Tia", role="girl", helper="big sister"),
]


ASP_RULES = r"""
valid(Place,Crop,Tool) :- place(Place), crop(Crop), tool(Tool), helps(Tool,Crop).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CROPS:
        lines.append(asp.fact("crop", c))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        for c in sorted(tool.helps_with):
            lines.append(asp.fact("helps", t, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    crop = CROPS[params.crop]
    tool = TOOLS[params.tool]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.role))
    helper = world.add(Entity(id=params.helper, kind="character", type="person"))
    world.add(Entity(id="crop", type="crop", label=crop.label, phrase=crop.phrase, caretaker=helper.id))
    tell(world, hero, helper, crop, tool)
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.crop is None or c[1] == args.crop)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, crop, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(ROLES)
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, crop=crop, tool=tool, name=name, role=gender, helper=helper)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, crop, tool in combos:
            print(f"  {place:8} {crop:10} {tool}")
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
            header = f"### {p.name}: {p.crop} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
