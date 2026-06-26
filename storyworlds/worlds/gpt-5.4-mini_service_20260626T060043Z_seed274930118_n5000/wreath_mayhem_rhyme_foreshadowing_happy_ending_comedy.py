#!/usr/bin/env python3
"""
A small storyworld about wreath-making mayhem, built as a playful comedy.

Premise:
A child wants to make a bright wreath for a door or wall. The project is a
little silly, a little messy, and full of tiny accidents. The adult worries that
the room will become a mayhem zone, but the pair uses a clever fix and ends with
a cheerful, decorated wreath and a tidy room.

Narrative instruments:
- Rhyme: the story includes light, child-friendly rhyming lines.
- Foreshadowing: the world model can predict the coming mess before it happens.
- Happy Ending: the final state proves the trouble got resolved.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["mess", "dirty", "scattered", "decorated", "steady", "tidy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "delight", "pride", "mayhem", "surprise", "relief", "humor"]:
            self.memes.setdefault(k, 0.0)

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
class Setting:
    place: str = "the kitchen table"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)
    rhyme1: str = ""
    rhyme2: str = ""


@dataclass
class WreathMaterial:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class HelperGear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for thing in world.entities.values():
            if thing.kind != "thing" or thing.worn_by != actor.id:
                continue
            if thing.protective:
                continue
            sig = ("mess", actor.id, thing.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            thing.meters["mess"] += 1
            thing.meters["dirty"] += 1
            thing.memes["surprise"] += 1
            out.append(f"{thing.label.capitalize()} got messy in the bustle.")
    return out


def _r_mayhem(world: World) -> list[str]:
    out: list[str] = []
    if sum(e.meters["mess"] for e in world.entities.values()) >= 2:
        if ("mayhem",) not in world.fired:
            world.fired.add(("mayhem",))
            for e in world.characters():
                e.memes["mayhem"] += 1
                e.memes["humor"] += 1
            out.append("The room turned into mayhem for a minute.")
    return out


def _r_cleanup(world: World) -> list[str]:
    out: list[str] = []
    if any(e.meters["dirty"] >= THRESHOLD for e in world.entities.values() if e.kind == "thing"):
        if ("cleanup",) not in world.fired:
            world.fired.add(("cleanup",))
            for e in world.characters():
                e.memes["relief"] += 1
            out.append("Then the room got a quick cleanup.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("mayhem", _r_mayhem), Rule("cleanup", _r_cleanup)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"decorate"}),
    "porch": Setting(place="the porch", indoors=False, affords={"decorate"}),
    "craftroom": Setting(place="the craft room", indoors=True, affords={"decorate"}),
}

PROJECTS = {
    "wreath": Project(
        id="wreath",
        verb="make a wreath",
        gerund="making a wreath",
        rush="grab the ribbon and hurry to finish",
        mess="mess",
        soil="a little tangled",
        tags={"wreath", "craft", "greenery"},
        rhyme1="Sprigs and strings and shiny bows",
        rhyme2="made the wreath where laughter grows",
    ),
}

MATERIALS = {
    "pine": WreathMaterial(
        id="pine",
        label="pine sprigs",
        phrase="fresh pine sprigs",
        region="hands",
        plural=True,
    ),
    "ribbon": WreathMaterial(
        id="ribbon",
        label="ribbons",
        phrase="bright ribbons",
        region="hands",
        plural=True,
    ),
    "bells": WreathMaterial(
        id="bells",
        label="little bells",
        phrase="tiny jingling bells",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    HelperGear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"mess"},
        prep="put on an apron first",
        tail="put on the apron and went back to work",
    ),
    HelperGear(
        id="tray",
        label="a tray",
        covers={"table"},
        guards={"mess"},
        prep="move the supplies onto a tray",
        tail="moved the supplies onto the tray and laughed",
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Noah", "Theo"]
TRAITS = ["cheerful", "curious", "playful", "silly", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    project: str
    material: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness checks and foreshadowing
# ---------------------------------------------------------------------------
def project_at_risk(project: Project, material: WreathMaterial) -> bool:
    return True


def select_gear(project: Project, material: WreathMaterial) -> Optional[HelperGear]:
    for gear in GEAR:
        if "mess" in gear.guards:
            return gear
    return None


def predict_mayhem(world: World, actor: Entity, project: Project, material: WreathMaterial) -> dict:
    sim = world.copy()
    _do_project(sim, sim.get(actor.id), project, material, narrate=False)
    total_dirty = sum(e.meters["dirty"] for e in sim.entities.values())
    return {
        "mayhem": any(e.memes["mayhem"] >= THRESHOLD for e in sim.characters()),
        "dirty": total_dirty,
    }


def explain_rejection(project: Project, material: WreathMaterial) -> str:
    return f"(No story: this combination never becomes funny mayhem in a natural way.)"


# ---------------------------------------------------------------------------
# Verbs and narration
# ---------------------------------------------------------------------------
def _do_project(world: World, actor: Entity, project: Project, material: WreathMaterial, narrate: bool = True) -> None:
    world.facts["project"] = project
    world.facts["material"] = material
    actor.meters["mess"] += 1
    actor.memes["joy"] += 1
    if narrate:
        propagate(world, narrate=True)
    else:
        propagate(world, narrate=False)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.keys() if False), '')}"
    )


def opening(world: World, hero: Entity, parent: Entity, project: Project, material: WreathMaterial) -> None:
    world.say(
        f"{hero.id} loved {project.gerund} with {material.phrase}."
    )
    world.say(
        f"{project.rhyme1}. {project.rhyme2}."
    )
    world.say(
        f"{hero.id} and {parent.label} planned to {project.verb} at {world.setting.place}."
    )


def foreshadow(world: World, hero: Entity, parent: Entity, project: Project, material: WreathMaterial) -> bool:
    pred = predict_mayhem(world, hero, project, material)
    if not pred["mayhem"]:
        return False
    world.facts["predicted_mayhem"] = True
    world.say(
        f"{parent.label.capitalize()} peeked at the ribbons and said, "
        f'"This could get a bit silly."'
    )
    return True


def start_making(world: World, hero: Entity, project: Project, material: WreathMaterial) -> None:
    world.say(
        f"{hero.id} wanted to {project.verb}, so {hero.pronoun('subject')} reached for the {material.label}."
    )
    world.say(
        f"First came one loop, then two loops, and the whole table began to wobble."
    )


def spill_line(world: World, hero: Entity, project: Project) -> None:
    world.say(
        f"{hero.id} tried to {project.rush}, but the ribbon slipped and twirled."
    )
    world.say(
        f"\"A wreath can wibble, a wreath can wobble,\" {hero.pronoun('subject')} giggled, "
        f"\"but it still can look lovely and possible.\""
    )


def offer_fix(world: World, parent: Entity, hero: Entity, project: Project, material: WreathMaterial) -> Optional[HelperGear]:
    gear = select_gear(project, material)
    if gear is None:
        return None
    world.say(
        f"{parent.label.capitalize()} smiled and said, "
        f'"How about we {gear.prep}?"'
    )
    return gear


def accept_fix(world: World, hero: Entity, parent: Entity, project: Project, gear: HelperGear, material: WreathMaterial) -> None:
    hero.memes["worry"] = 0
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} nodded, put on {gear.label}, and kept going."
    )
    world.say(
        f"They {gear.tail}. Soon the wreath stayed neat while the room calmed down."
    )


def ending(world: World, hero: Entity, parent: Entity, project: Project, material: WreathMaterial) -> None:
    world.say(
        f"In the end, the wreath hung straight, bright, and a tiny bit lopsided in a charming way."
    )
    world.say(
        f"{hero.id} laughed, {parent.label} laughed, and the little accident turned into a happy ending."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, project: Project, material: WreathMaterial,
         hero_name: str = "Mia", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    wreath = world.add(Entity(
        id="wreath", type="wreath", label="wreath", phrase=material.phrase,
        owner=hero.id, caretaker=parent.id,
    ))
    material_ent = world.add(Entity(
        id=material.id, type=material.id, label=material.label, phrase=material.phrase,
        owner=hero.id, caretaker=parent.id, plural=material.plural, region=material.region
    ))
    material_ent.worn_by = hero.id

    world.facts.update(hero=hero, parent=parent, wreath=wreath, material=material_ent, project=project)

    opening(world, hero, parent, project, material)
    world.para()
    foreshadow(world, hero, parent, project, material)
    start_making(world, hero, project, material)
    spill_line(world, hero, project)
    _do_project(world, hero, project, material, narrate=True)
    world.para()
    gear = offer_fix(world, parent, hero, project, material)
    if gear:
        world.facts["gear"] = gear
        accept_fix(world, hero, parent, project, gear, material)
    ending(world, hero, parent, project, material)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    project: Project = f["project"]
    material: WreathMaterial = f["material"]
    return [
        f'Write a short comedy story for a child about {hero.id} making a wreath with {material.label}.',
        f'Tell a story with rhyme, foreshadowing, and a happy ending about a child and a parent making a wreath.',
        f'Write a funny story where {hero.id} wants to {project.verb} but the project becomes a little mayhem before it gets fixed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    project: Project = f["project"]
    material: WreathMaterial = f["material"]
    gear: Optional[HelperGear] = f.get("gear")
    out = [
        QAItem(
            question=f"What did {hero.id} want to make?",
            answer=f"{hero.id} wanted to make a wreath.",
        ),
        QAItem(
            question=f"What made the craft a little funny and messy?",
            answer=f"The ribbons and sprigs made the project turn into a little mayhem.",
        ),
        QAItem(
            question=f"Who helped solve the problem?",
            answer=f"{parent.label.capitalize()} helped by suggesting a simple fix.",
        ),
    ]
    if gear:
        out.append(QAItem(
            question=f"What did they use to keep the craft steadier?",
            answer=f"They used {gear.label} so the wreath-making could stay calmer and cleaner.",
        ))
    out.append(QAItem(
        question=f"How did the story end?",
        answer="It ended with the wreath finished, the room tidied, and everyone laughing.",
    ))
    return out


WORLD_KNOWLEDGE = {
    "wreath": [
        ("What is a wreath?",
         "A wreath is a круг-shaped decoration, often made from leaves, flowers, ribbons, or other festive things, and it can hang on a door or wall.")
    ],
    "mess": [
        ("What does mayhem mean?",
         "Mayhem means a lot of silly, busy chaos where things get a bit out of order.")
    ],
    "ribbon": [
        ("Why are ribbons fun in crafts?",
         "Ribbons are fun because they can curl, loop, and add bright color to a project.")
    ],
    "apron": [
        ("What is an apron for?",
         "An apron helps keep clothes cleaner when you are doing a messy job like cooking or crafting.")
    ],
    "greenery": [
        ("What is greenery?",
         "Greenery means green leaves, sprigs, or plants used for decoration.")
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["wreath", "mess", "ribbon", "apron", "greenery"]:
        if key == "apron" and "gear" not in world.facts:
            continue
        if key in WORLD_KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[key])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
project_risk(P) :- project(P).
mayhem_due_to_mess(P) :- project(P), messy(P).
resolved(P) :- project(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        for g in sorted(m.genders):
            lines.append(asp.fact("wears", g, mid))
    for gid, g in enumerate(GEAR):
        lines.append(asp.fact("gear", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show project/1."))
    return sorted(set(asp.atoms(model, "project")))


def asp_verify() -> int:
    import asp
    py = set((k,) for k in PROJECTS.keys())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} project(s).")
        return 0
    print("Mismatch between ASP and Python.")
    print("Python only:", sorted(py - cl))
    print("ASP only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about wreath-making mayhem.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    project = args.project or "wreath"
    material = args.material or rng.choice(list(MATERIALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    if project not in PROJECTS:
        raise StoryError("Unknown project.")
    if material not in MATERIALS:
        raise StoryError("Unknown material.")
    return StoryParams(place=place, project=project, material=material, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROJECTS[params.project], MATERIALS[params.material], params.name, params.gender, [params.trait], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show project/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show project/1."))
        print(sorted(set(asp.atoms(model, "project"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, mat in enumerate(MATERIALS.keys()):
            params = StoryParams(
                place="kitchen",
                project="wreath",
                material=mat,
                name=GIRL_NAMES[i % len(GIRL_NAMES)],
                gender="girl",
                parent="mother",
                trait=TRAITS[i % len(TRAITS)],
                seed=base_seed + i,
            )
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
