#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/millennium_dense_purl_curiosity_heartwarming.py
===============================================================================

A small heartwarming storyworld about a curious child, a very dense old place,
and a simple knitting lesson that turns into a keepsake for the new millennium.

Seed words: millennium, dense, purl
Feature: Curiosity
Style: Heartwarming

This world tells close variations of the same tiny premise:
a child wanders into a dense, old storage room with a patient elder, discovers
a half-finished scarf for a millennium celebration, makes a mistake while
knitting, then learns the purl stitch and finishes a warm gift together.

The world model tracks physical meters and emotional memes, and the prose is
rendered from state changes rather than from a frozen template.
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
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    density: str
    light: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Yarn:
    id: str
    label: str
    color: str
    texture: str
    warmth: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    label: str
    purpose: str
    gift_for: str
    words: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    stitch: str
    clue: str
    success: str
    mistake: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_warm(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    scarf = world.entities.get("scarf")
    if room and scarf and scarf.meters["finished"] >= THRESHOLD and "warmth" not in world.fired:
        world.fired.add(("warmth",))
        room.meters["warmth"] += 1
        out.append("__warm__")
    return out


def _r_curiosity(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.memes["curiosity"] >= THRESHOLD and ("curiosity",) not in world.fired:
        world.fired.add(("curiosity",))
        child.memes["boldness"] += 1
        out.append("__curious__")
    return out


CAUSAL_RULES = [Rule("curiosity", _r_curiosity), Rule("warm", _r_warm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def _knit(world: World, yarn: Entity, lesson: Lesson, success: bool, narrate: bool = True) -> None:
    yarn.meters["rows"] += 1
    if success:
        yarn.meters["finished"] += 1
        yarn.memes["pride"] += 1
    else:
        yarn.meters["tangles"] += 1
        yarn.memes["confusion"] += 1
    propagate(world, narrate=narrate)


def predict_finish(world: World, lesson: Lesson) -> dict:
    sim = world.copy()
    _knit(sim, sim.get("scarf"), lesson, success=False, narrate=False)
    _knit(sim, sim.get("scarf"), lesson, success=True, narrate=False)
    return {"rows": sim.get("scarf").meters["rows"], "finished": sim.get("scarf").meters["finished"]}


def setup(world: World, child: Entity, elder: Entity, place: Place, project: Project, yarn: Yarn) -> None:
    child.memes["curiosity"] += 2
    elder.memes["patience"] += 2
    world.say(
        f"On a quiet afternoon, {child.id} wandered into {place.name}, a {place.density} old room full of boxes, baskets, and whispers from long ago."
    )
    world.say(
        f"{child.id} had been wondering about the word millennium, and {elder.id} smiled when {child.id} asked what it meant."
    )
    world.say(
        f"On a shelf, {child.id} spotted {project.label} and {yarn.label}, with {yarn.texture} yarn tucked beside a note for the coming millennium celebration."
    )


def wonder(world: World, child: Entity, elder: Entity, project: Project) -> None:
    world.say(
        f'"Why is it for the millennium?" {child.id} asked. {elder.id} patted the chair and said it was a gift to welcome the new year with something warm.'
    )
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1


def try_wrong_way(world: World, child: Entity, yarn: Yarn, lesson: Lesson) -> None:
    world.say(
        f'{child.id} tried to copy the stitches alone at first, but the yarn slipped the wrong way and made a small knot.'
    )
    _knit(world, yarn, lesson, success=False)
    world.say(
        f'"That is close," {elder_id(world)} said kindly, "but the purl stitch turns the loop around so the cloth stays soft."'
    )


def elder_id(world: World) -> str:
    return world.facts["elder"].id


def teach_purl(world: World, elder: Entity, child: Entity, yarn: Yarn, lesson: Lesson) -> None:
    world.say(
        f'{elder.id} lifted the needles and showed {child.id} the purl stitch. "{lesson.clue}," {elder.id} said, slow enough to follow.'
    )
    child.memes["confidence"] += 1
    yarn.memes["understanding"] += 1
    _knit(world, yarn, lesson, success=True)
    world.say(f'{child.id} copied the motion, and the yarn began to look neat and even.')


def finish_gift(world: World, elder: Entity, child: Entity, project: Project, yarn: Yarn) -> None:
    child.memes["love"] += 1
    elder.memes["love"] += 1
    world.say(
        f'By evening, {project.label} was finished: a soft scarf for the millennium, made of {yarn.color} yarn and warm hands working together.'
    )
    world.say(
        f'{child.id} held it up, grinning, and {elder.id} wrapped it around {child.id}\'s shoulders so they could feel how gentle it was.'
    )
    world.say(
        f'"Now I know purl," {child.id} said, and {elder.id} laughed because some lessons are small, but they last a very long time.'
    )


def tell(place: Place, yarn: Yarn, project: Project, lesson: Lesson,
         child_name: str = "Mina", child_gender: str = "girl",
         elder_name: str = "Grandma", elder_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder"))
    room = world.add(Entity(id="room", type="room", label=place.name))
    scarf = world.add(Entity(id="scarf", type="thing", label=project.label))
    wool = world.add(Entity(id="yarn", type="thing", label=yarn.label))
    world.facts.update(child=child, elder=elder, place=place, project=project, lesson=lesson, yarn=yarn, room=room, scarf=scarf, wool=wool)

    setup(world, child, elder, place, project, yarn)
    world.para()
    wonder(world, child, elder, project)
    try_wrong_way(world, child, scarf, lesson)
    world.para()
    teach_purl(world, elder, child, scarf, lesson)
    finish_gift(world, elder, child, project, yarn)
    world.facts["done"] = True
    return world


PLACES = {
    "attic": Place(id="attic", name="the attic", density="dense", light="thin", tags={"dense"}),
    "closet": Place(id="closet", name="the old closet", density="dense", light="soft", tags={"dense"}),
    "library": Place(id="library", name="the little library nook", density="dense", light="golden", tags={"dense"}),
}

YARNS = {
    "blue": Yarn(id="blue", label="blue yarn", color="blue", texture="soft", warmth="gentle", tags={"purl"}),
    "red": Yarn(id="red", label="red yarn", color="red", texture="smooth", warmth="cozy", tags={"purl"}),
    "gold": Yarn(id="gold", label="gold yarn", color="gold", texture="bright", warmth="warm", tags={"purl", "millennium"}),
}

PROJECTS = {
    "scarf": Project(id="scarf", label="a long scarf", purpose="gift", gift_for="millennium", words=["millennium", "purl"], tags={"millennium", "purl"}),
    "blanket": Project(id="blanket", label="a small blanket", purpose="gift", gift_for="new year", words=["millennium", "purl"], tags={"millennium", "purl"}),
}

LESSONS = {
    "purl": Lesson(id="purl", stitch="purl", clue="Put the needle in, wrap the yarn, and pull it back through", success="the loop came out neat", mistake="the loop twisted into a knot", tags={"purl"}),
}


@dataclass
class StoryParams:
    place: str
    yarn: str
    project: str
    lesson: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    elder_name: str = "Grandma"
    elder_gender: str = "grandmother"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for yarn in YARNS:
            for project in PROJECTS:
                if "purl" in PROJECTS[project].tags and "millennium" in PROJECTS[project].tags:
                    combos.append((place, yarn, project))
    return combos


def explain_rejection(params: StoryParams | None = None) -> str:
    return "(No story: this world expects a dense place, purling yarn, and a millennium gift.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming curiosity storyworld about knitting a millennium gift.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--yarn", choices=YARNS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--elder")
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
              and (args.yarn is None or c[1] == args.yarn)
              and (args.project is None or c[2] == args.project)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, yarn, project = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        yarn=yarn,
        project=project,
        lesson=args.lesson or "purl",
        child_name=args.name or rng.choice(["Mina", "Lena", "Ivy", "Nora"]),
        child_gender="girl",
        elder_name=args.elder or rng.choice(["Grandma", "Auntie", "Nana"]),
        elder_gender="grandmother",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.yarn not in YARNS or params.project not in PROJECTS or params.lesson not in LESSONS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], YARNS[params.yarn], PROJECTS[params.project], LESSONS[params.lesson], params.child_name, params.child_gender, params.elder_name, params.elder_gender)
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
        f'Write a heartwarming story for a child who is curious about the word "millennium" and learns the purl stitch.',
        f"Tell a gentle story in a dense old place where {f['child'].id} asks about a millennium gift and learns to purl.",
        f'Write a cozy story that includes the words "millennium", "dense", and "purl" and ends with a handmade present.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {elder.id}, who spend time together in a quiet, dense old place."),
        ("What word was the child curious about?", "The child was curious about the word millennium, and that curiosity led to a knitting lesson."),
        ("What did the elder teach?", f"{elder.id} taught the purl stitch, showing how to turn the loop so the knitting becomes smooth and soft."),
        ("How did the story end?", f"They finished a warm gift together for the millennium, and the child felt proud and close to {elder.id}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a millennium?", "A millennium is a very long time: one thousand years."),
        ("What does dense mean?", "Dense can mean packed tightly together, with very little empty space."),
        ("What is purl in knitting?", "Purl is a knitting stitch that makes a soft, bumpy texture when you turn the yarn in a certain way."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="attic", yarn="gold", project="scarf", lesson="purl", child_name="Mina", elder_name="Grandma"),
    StoryParams(place="closet", yarn="blue", project="blanket", lesson="purl", child_name="Ivy", elder_name="Auntie"),
]


ASP_RULES = r"""
valid(P, Y, G) :- place(P), yarn(Y), project(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for y in YARNS:
        lines.append(asp.fact("yarn", y))
    for g in PROJECTS:
        lines.append(asp.fact("project", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        print(f"MISMATCH: generate smoke test failed: {e}")
        return 1
    print("OK: generate smoke test passed.")
    return 0


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
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a child who is curious about the word "millennium" and learns the purl stitch.',
        f"Tell a gentle story in a dense old place where {f['child'].id} asks about a millennium gift and learns to purl.",
        f'Write a cozy story that includes the words "millennium", "dense", and "purl" and ends with a handmade present.',
    ]


if __name__ == "__main__":
    main()
