#!/usr/bin/env python3
"""
A small suspense-mystery storyworld about a child trying to make something,
while a missing piece, a trail of clues, and a final reveal create the tension.

The generated stories are constrained, state-driven, and child-facing.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

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
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Project:
    id: str
    verb: str
    gerund: str
    object_label: str
    missing_piece: str
    clue: str
    suspense: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    clue_mark: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trail: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.trail = list(self.trail)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.facts.get("hero")
    proj: Project = world.facts.get("project")
    if not child or not proj:
        return out
    hero = child
    if hero.memes.get("worry", 0.0) >= THRESHOLD and ("worry", hero.id) not in world.fired:
        world.fired.add(("worry", hero.id))
        out.append(f"{hero.id} kept looking at the empty spot and felt a small knot of worry.")
    return out


def _r_clue(world: World) -> list[str]:
    out = []
    proj: Project = world.facts.get("project")
    if not proj:
        return out
    if world.trail and ("clue", len(world.trail)) not in world.fired:
        world.fired.add(("clue", len(world.trail)))
        clue = world.trail[-1]
        out.append(clue)
    return out


CAUSAL_RULES = [
    _r_worry,
    _r_clue,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def make_mystery(world: World, hero: Entity, helper: Entity, project: Project, suspect: Suspect) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    world.say(f"{hero.id} wanted to make {project.object_label} in {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} had {project.verb} everything ready, but one part was missing: {project.missing_piece}.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"That made the room feel very still, and {hero.id} listened for any tiny sound.")

    world.para()
    world.trail.append(f"Then {project.clue}")
    propagate(world)
    world.say(f"{hero.id} and {helper.id} followed the clue through {world.setting.place}.")

    world.para()
    world.trail.append(suspect.reveal_line)
    world.say(f"Behind a chair, they found {suspect.label}.")
    world.say(f"{suspect.reveal_line}")
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1

    world.para()
    world.say(f"At last, {hero.id} found the missing {project.missing_piece}.")
    world.say(f"With {project.missing_piece} back in hand, {hero.id} could {project.gerund} and finish the {project.object_label}.")
    world.say(project.finish)
    world.say(f"The finished {project.object_label} stood right on the table, and the mystery was over.")


SETTINGS = {
    "kitchen": Setting("the kitchen", indoors=True, affords={"bake", "build", "paint"}),
    "attic": Setting("the attic", indoors=True, affords={"build", "search"}),
    "garden_shed": Setting("the garden shed", indoors=False, affords={"build", "paint", "search"}),
    "library_corner": Setting("the library corner", indoors=True, affords={"build", "write"}),
}

PROJECTS = {
    "rocket": Project(
        id="rocket",
        verb="make",
        gerund="build the rocket",
        object_label="a cardboard rocket",
        missing_piece="the red button",
        clue="a soft clink came from under the old stool",
        suspense="something tiny had gone missing",
        finish="Its red nose shone like a brave little star.",
        tags={"build", "cardboard", "button"},
    ),
    "lantern": Project(
        id="lantern",
        verb="make",
        gerund="finish the lantern",
        object_label="a paper lantern",
        missing_piece="the yellow ribbon",
        clue="there were bright yellow threads caught on a shelf",
        suspense="the last piece had vanished",
        finish="The lantern glowed warm and gold in the corner.",
        tags={"build", "paper", "ribbon"},
    ),
    "cake": Project(
        id="cake",
        verb="make",
        gerund="bake the cake",
        object_label="a small birthday cake",
        missing_piece="the blue candle",
        clue="tiny blue crumbs led toward the sink",
        suspense="one last thing had slipped away",
        finish="The candle stood tall on top, and the cake was ready to share.",
        tags={"bake", "cake", "candle"},
    ),
    "poster": Project(
        id="poster",
        verb="make",
        gerund="paint the poster",
        object_label="a big poster",
        missing_piece="the green paint pot",
        clue="a green drop marked the floor near the door",
        suspense="the room had gone quiet in a suspicious way",
        finish="The poster was bright and bold, with every corner filled in.",
        tags={"paint", "poster", "paint"},
    ),
}

SUSPECTS = {
    "mouse": Suspect(
        id="mouse",
        label="a little mouse with a round nose",
        clue_mark="tiny paw prints",
        reveal_line="Its whiskers were green from the paint pot.",
        tags={"tiny", "prints", "green"},
    ),
    "cat": Suspect(
        id="cat",
        label="a sleepy cat curled on a box",
        clue_mark="small paw marks",
        reveal_line="A yellow ribbon was stuck to its tail.",
        tags={"paw", "ribbon"},
    ),
    "sparrow": Suspect(
        id="sparrow",
        label="a sparrow perched on a nail box",
        clue_mark="little feather marks",
        reveal_line="The sparrow had tucked the candle beside its nest.",
        tags={"feather", "nest", "candle"},
    ),
    "squirrel": Suspect(
        id="squirrel",
        label="a squirrel with shiny eyes",
        clue_mark="dusty tail tracks",
        reveal_line="The squirrel had hidden the red button in its nest of paper scraps.",
        tags={"tail", "nest", "button"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Finn", "Noah", "Eli"]
HELPERS = [("mother", "mother"), ("father", "father"), ("grandma", "grandma"), ("grandpa", "grandpa")]


@dataclass
class StoryParams:
    place: str
    project: str
    suspect: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, proj in PROJECTS.items():
            if proj.id in setting.affords or any(tag in setting.affords for tag in proj.tags):
                for sid in SUSPECTS:
                    combos.append((place, pid, sid))
    return combos


def choose_triple(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.project is None or c[1] == args.project)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid mystery story matches the given options.)")
    return rng.choice(sorted(combos))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful mystery storyworld about making something and solving a small clue trail.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--name")
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
    place, project, suspect = choose_triple(args, rng)
    proj = PROJECTS[project]
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([h for h, _ in HELPERS])
    return StoryParams(place=place, project=project, suspect=suspect, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    proj = PROJECTS[params.project]
    suspect = SUSPECTS[params.suspect]
    world = World(setting)
    hero_type = params.gender
    helper_type = params.helper if params.helper in {"mother", "father"} else "woman"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type, traits=["little", "curious"]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=params.helper))
    project_piece = world.add(Entity(id="piece", type="thing", label=proj.missing_piece))
    world.facts.update(hero=hero, helper=helper, project=proj, suspect=suspect, piece=project_piece)

    world.say(f"{hero.id} was in {setting.place} to make {proj.object_label}.")
    world.say(f"{hero.pronoun().capitalize()} liked how careful work could turn plain bits into something wonderful.")
    world.say(f"Today, {hero.id} and {helper.id} had nearly everything ready.")

    world.para()
    world.say(f"Then {proj.suspense}. {proj.missing_piece.capitalize()} was gone.")
    world.say(f"{hero.id} looked under the table, then inside a basket, but the piece was not there.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1

    world.para()
    world.say(f"A clue appeared: {proj.clue}.")
    world.say(f"{hero.id} and {helper.id} followed it slowly, because a mystery was now underway.")
    world.say(f"The search felt suspenseful, like the room was holding its breath.")

    world.para()
    world.say(f"At the end of the trail, they found {suspect.label}.")
    world.say(suspect.reveal_line)
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1

    world.para()
    world.say(f"The missing {proj.missing_piece} was there after all, and {hero.id} could pick it up with a grin.")
    world.say(f"With that small piece back in place, {hero.id} could {proj.gerund} and finish the project.")
    world.say(proj.finish)
    world.say(f"That was the answer to the mystery, and the finished {proj.object_label} made the whole room feel bright.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    proj: Project = f["project"]
    return [
        f'Write a short suspense story for a young child that includes the word "make" and a missing piece.',
        f"Tell a gentle mystery where {f['hero'].id} tries to make {proj.object_label} but one part is gone.",
        f"Write a child-facing story about a clue trail, a small reveal, and finishing a thing that was being made.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    proj: Project = f["project"]
    suspect: Suspect = f["suspect"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to make?",
            answer=f"{hero.id} was trying to make {proj.object_label}.",
        ),
        QAItem(
            question=f"What was missing during the story?",
            answer=f"The missing piece was {proj.missing_piece}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} follow the clue?",
            answer=f"{helper.id} helped {hero.id} follow the clue through {world.setting.place}.",
        ),
        QAItem(
            question=f"What was found at the end of the mystery?",
            answer=f"At the end, they found {suspect.label}, and that showed what had happened to the missing piece.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the finished {proj.object_label} standing in the room after the missing piece came back.",
        ),
    ]


WORLD_QA = {
    "make": [
        QAItem(
            question="What does it mean to make something?",
            answer="To make something means to create it, put pieces together, or turn materials into a new thing.",
        ),
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or problem where something is not known at first, so people look for clues to find the answer.",
        ),
    ],
    "suspense": [
        QAItem(
            question="What does suspense feel like in a story?",
            answer="Suspense feels like a waiting moment when something important may happen soon, so you want to know what comes next.",
        ),
    ],
    "clue": [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small sign or hint that helps someone figure out what happened.",
        ),
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_QA["make"])
    out.extend(WORLD_QA["mystery"])
    out.extend(WORLD_QA["suspense"])
    out.extend(WORLD_QA["clue"])
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", project="cake", suspect="mouse", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="attic", project="rocket", suspect="squirrel", name="Leo", gender="boy", helper="grandpa"),
    StoryParams(place="garden_shed", project="poster", suspect="cat", name="Ava", gender="girl", helper="father"),
    StoryParams(place="library_corner", project="lantern", suspect="sparrow", name="Noah", gender="boy", helper="grandma"),
]


ASP_RULES = r"""
valid_story(P, J, S) :- place(P), project(J), suspect(S), affords(P, J), clue_fit(J, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for jid, j in PROJECTS.items():
        lines.append(asp.fact("project", jid))
        lines.append(asp.fact("clue_fit", jid, jid if jid in SUSPECTS else jid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    # Explicit clue-fit registry: one project can pair with any suspect in this tiny world.
    for jid in PROJECTS:
        for sid in SUSPECTS:
            lines.append(asp.fact("clue_fit", jid, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set((p, j, s) for p, j, s in valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful mystery storyworld about making something and following clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h for h, _ in HELPERS])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid mystery stories:\n")
        for p, j, s in stories:
            print(f"  {p:14} {j:10} {s}")
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
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
