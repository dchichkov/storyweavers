#!/usr/bin/env python3
"""
Standalone storyworld: a tiny detective story about Baldy, a description, supervision,
curiosity, sharing, and a helpful flashback.

The world is small on purpose:
- A child or small person called Baldy has a problem.
- Their curiosity makes them notice clues.
- Someone supervising keeps the group calm and fair.
- Sharing descriptions helps identify the missing thing.
- A flashback reveals the key clue and resolves the case.

This script follows the Storyweavers contract:
- self-contained stdlib storyworld script
- eager import of results.py
- lazy import of asp.py only in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generated stories
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    role: str = ""
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.role in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.role in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    has_wall: bool = True
    has_table: bool = True
    has_box: bool = True


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Suspect:
    id: str
    label: str
    note: str
    color: str
    size: str


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    reveals: str


@dataclass
class Resolution:
    id: str
    method: str
    ending: str


SCENES = {
    "hall": Scene(place="the school hall", has_wall=True, has_table=True, has_box=True),
    "library": Scene(place="the little library", has_wall=True, has_table=True, has_box=True),
    "office": Scene(place="the tidy office", has_wall=True, has_table=True, has_box=True),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="striped cat", note="a soft tail brushed the chair", color="gray", size="small"),
    "dog": Suspect(id="dog", label="brown dog", note="muddy paw prints were near the door", color="brown", size="medium"),
    "moth": Suspect(id="moth", label="small moth", note="wings dusted the lamp shade", color="pale", size="tiny"),
    "teacher": Suspect(id="teacher", label="teacher", note="carried a neat folder and a chalky sleeve", color="blue", size="tall"),
}

CLUES = {
    "button": Clue(id="button", label="button", detail="a shiny button on the floor", reveals="the coat was missing a button"),
    "crumb": Clue(id="crumb", label="crumb", detail="a crumb trail by the desk", reveals="someone had been sharing crackers"),
    "ink": Clue(id="ink", label="ink spot", detail="a tiny ink spot on the page", reveals="the notes were handled by the writer"),
    "ribbon": Clue(id="ribbon", label="ribbon", detail="a blue ribbon on the chair", reveals="the lost item had been tied up"),
}

RESOLUTIONS = {
    "flashback": Resolution(id="flashback", method="a flashback", ending="the remembered moment showed what really happened"),
    "sharing": Resolution(id="sharing", method="sharing descriptions", ending="everyone compared what they had noticed"),
    "supervise": Resolution(id="supervise", method="careful supervising", ending="the calm grown-up kept the room fair and quiet"),
}

GIVEN_NAMES = ["Baldy", "Nina", "Milo", "Tess", "Otto", "June"]
SUPERVISORS = ["Ms. Fern", "Mr. Pike", "Aunt Mara", "Coach Lin"]
TRAITS = ["curious", "quiet", "brave", "careful", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scene: str
    suspect: str
    clue: str
    resolution: str
    name: str
    supervisor: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, supervisor: Entity, suspect: Suspect, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a little {hero.role} detective with a big curiosity and a neat "
        f"description book. {supervisor.label} was there to supervise the room so everyone "
        f"could share clues one at a time."
    )
    world.say(
        f"That morning, {hero.id} noticed {clue.detail}, and the strange trace pointed toward "
        f"the {suspect.label}."
    )


def tension(world: World, hero: Entity, supervisor: Entity, suspect: Suspect, clue: Clue) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} wanted to ask every question at once, but {supervisor.label} asked for "
        f"sharing instead. Each child gave a short description, and the room stayed calm."
    )
    world.say(
        f"{hero.id} listened closely because the clue did not fit the first guess. "
        f"{clue.reveals.capitalize()}, but the case was still not solved."
    )


def flashback_turn(world: World, hero: Entity, suspect: Suspect, clue: Clue, resolution: Resolution) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0) + 1
    world.say(
        f"Then came {resolution.method}. {hero.id} remembered a small flashback: earlier, "
        f"the {suspect.label} had brushed past the table after the crackers were shared."
    )
    world.say(
        f"That memory matched {clue.detail}, and the description suddenly made sense."
    )


def ending(world: World, hero: Entity, supervisor: Entity, suspect: Suspect, resolution: Resolution) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(
        f"{hero.id} pointed to the {suspect.label} and explained the case in a clear description. "
        f"{supervisor.label} smiled and praised the careful work."
    )
    world.say(
        f"In the end, the room was peaceful again, and {hero.id} felt proud that curiosity, "
        f"sharing, {resolution.id}, and supervision had solved the mystery."
    )


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", role="boy", label=params.name))
    supervisor = world.add(Entity(id="supervisor", kind="character", role="adult", label=params.supervisor))
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    resolution = RESOLUTIONS[params.resolution]

    world.facts.update(
        hero=hero,
        supervisor=supervisor,
        suspect=suspect,
        clue=clue,
        resolution=resolution,
        scene=world.scene,
    )

    intro(world, hero, supervisor, suspect, clue)
    world.para()
    tension(world, hero, supervisor, suspect, clue)
    world.para()
    flashback_turn(world, hero, suspect, clue, resolution)
    ending(world, hero, supervisor, suspect, resolution)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def reasonable(scene: Scene, suspect: Suspect, clue: Clue, resolution: Resolution) -> bool:
    # Small detective story rule: the clue must plausibly point to the suspect,
    # and the ending must fit the scene.
    if suspect.id == "moth" and clue.id in {"button", "crumb"}:
        return False
    if resolution.id == "flashback" and not scene.has_table:
        return False
    return True


def explain_rejection(scene: Scene, suspect: Suspect, clue: Clue, resolution: Resolution) -> str:
    return (
        f"(No story: in {scene.place}, the clue '{clue.label}' does not give a believable "
        f"detective path to the {suspect.label}, or the chosen ending would not fit the scene.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue can point to a suspect only when it matches that suspect's profile.
reasonable(Suspect, Clue, Resolution) :- suspect(Suspect), clue(Clue), resolution(Resolution),
                                       points_to(Clue, Suspect), fits_scene(Resolution).

valid(Scene, Suspect, Clue, Resolution) :- scene(Scene), reasonable(Suspect, Clue, Resolution).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        if scene.has_table:
            lines.append(asp.fact("fits_scene", "flashback"))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))

    # hand-built points-to registry
    lines.append(asp.fact("points_to", "button", "cat"))
    lines.append(asp.fact("points_to", "crumb", "dog"))
    lines.append(asp.fact("points_to", "ink", "teacher"))
    lines.append(asp.fact("points_to", "ribbon", "moth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Registries / combo enumeration
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for scene_id, scene in SCENES.items():
        for suspect_id, suspect in SUSPECTS.items():
            for clue_id, clue in CLUES.items():
                for res_id in RESOLUTIONS:
                    if reasonable(scene, suspect, clue, RESOLUTIONS[res_id]):
                        out.append((scene_id, suspect_id, clue_id, res_id))
    return out


CURATED = [
    StoryParams(scene="hall", suspect="cat", clue="button", resolution="flashback", name="Baldy", supervisor="Ms. Fern", trait="curious"),
    StoryParams(scene="library", suspect="dog", clue="crumb", resolution="sharing", name="Baldy", supervisor="Mr. Pike", trait="careful"),
    StoryParams(scene="office", suspect="teacher", clue="ink", resolution="supervise", name="Baldy", supervisor="Aunt Mara", trait="sharp-eyed"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a young child about {f["hero"].id}, curiosity, sharing, and a flashback.',
        f'Write a story where {f["hero"].id} and {f["supervisor"].label} supervise a clue hunt in {f["scene"].place}.',
        f'Write a gentle mystery that uses the word "description" and ends with a helpful discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    supervisor = f["supervisor"]
    suspect = f["suspect"]
    clue = f["clue"]
    resolution = f["resolution"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a curious little detective.",
        ),
        QAItem(
            question=f"Who helped supervise the clue-sharing?",
            answer=f"{supervisor.label} helped supervise the room so everyone could share clues fairly.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed {clue.detail}. It seemed to point toward the {suspect.label}.",
        ),
        QAItem(
            question=f"What helped solve the mystery?",
            answer=f"{resolution.method} helped solve the mystery, because {hero.id} remembered the important moment and explained it clearly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and thinks carefully to figure out what happened.",
        ),
        QAItem(
            question="Why is sharing descriptions helpful?",
            answer="Sharing descriptions helps because different people may notice different small details, and those details can fit together like puzzle pieces.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows or remembers something that happened earlier.",
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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} kind={e.kind} role={e.role} mem={dict(e.memes)}")
    lines.append(f"  place={world.scene.place}")
    lines.append(f"  facts={sorted(world.facts.keys())}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective storyworld about Baldy, curiosity, sharing, and a flashback.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--name", default=None)
    ap.add_argument("--supervisor", choices=SUPERVISORS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.scene:
        combos = [c for c in combos if c[0] == args.scene]
    if args.suspect:
        combos = [c for c in combos if c[1] == args.suspect]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if args.resolution:
        combos = [c for c in combos if c[3] == args.resolution]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, suspect_id, clue_id, res_id = rng.choice(sorted(combos))
    name = args.name or "Baldy"
    supervisor = args.supervisor or rng.choice(SUPERVISORS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        scene=scene_id,
        suspect=suspect_id,
        clue=clue_id,
        resolution=res_id,
        name=name,
        supervisor=supervisor,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    world = World(scene=scene)
    hero = world.add(Entity(id=params.name, kind="character", role="boy", label=params.name))
    supervisor = world.add(Entity(id="supervisor", kind="character", role="adult", label=params.supervisor))
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    resolution = RESOLUTIONS[params.resolution]

    if not reasonable(scene, suspect, clue, resolution):
        raise StoryError(explain_rejection(scene, suspect, clue, resolution))

    tell(world, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:")
        for row in asp_valid():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.scene} / {p.suspect} / {p.clue} / {p.resolution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
