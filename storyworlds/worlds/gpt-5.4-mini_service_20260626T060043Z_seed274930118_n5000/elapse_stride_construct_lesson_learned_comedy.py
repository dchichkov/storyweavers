#!/usr/bin/env python3
"""
storyworlds/worlds/elapse_stride_construct_lesson_learned_comedy.py
====================================================================

A standalone story world about comedy, a little rush of time, and a lesson
learned while building something silly and useful.

Premise:
- A playful character wants to construct a funny prop or contraption.
- Time elapses, the character strides ahead too fast, and the build gets wobbly.
- A helper suggests a calmer method.
- The character learns the lesson: slow down, follow steps, and laugh at the
  mess while fixing it.

The domain is small, child-facing, and constraint-checked. Prose is driven by
world state, not a frozen template swap.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Project:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.elapsed: int = 0

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.facts = dict(self.facts)
        c.elapsed = self.elapsed
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    builder = world.facts.get("builder")
    project = world.facts.get("project")
    if not builder or not project:
        return out
    actor = world.get(builder.id)
    proj = world.get(project.id)
    if actor.meters.get("rush", 0.0) < THRESHOLD:
        return out
    if proj.meters.get("built", 0.0) >= THRESHOLD:
        return out
    sig = ("wobble", actor.id, proj.id, world.elapsed)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    proj.meters["wobble"] = proj.meters.get("wobble", 0.0) + 1
    actor.memes["embarrassed"] = actor.memes.get("embarrassed", 0.0) + 1
    out.append(f"The {project.label} wobbled like a jelly on a spoon.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    builder = world.facts.get("builder")
    helper = world.facts.get("helper")
    project = world.facts.get("project")
    if not builder or not helper or not project:
        return out
    a = world.get(builder.id)
    h = world.get(helper.id)
    p = world.get(project.id)
    if a.memes.get("embarrassed", 0.0) < THRESHOLD:
        return out
    if p.meters.get("fixed", 0.0) >= THRESHOLD:
        return out
    sig = ("lesson", a.id, p.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["lesson_learned"] = a.memes.get("lesson_learned", 0.0) + 1
    h.memes["encouraging"] = h.memes.get("encouraging", 0.0) + 1
    p.meters["fixed"] = p.meters.get("fixed", 0.0) + 1
    p.meters["built"] = p.meters.get("built", 0.0) + 1
    out.append("They slowed down, laughed, and built it the careful way.")
    return out


CAUSAL_RULES = [
    Rule("wobble", _r_wobble),
    Rule("lesson", _r_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def tell(setting: Setting, activity: Activity, project_cfg: Project,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", trait],
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=parent_type, label="the helper",
        traits=["patient", "silly"],
    ))
    project = world.add(Entity(
        id="project", type=project_cfg.type, label=project_cfg.label,
        phrase=project_cfg.phrase, owner=hero.id, caretaker=helper.id,
        plural=project_cfg.plural,
    ))

    world.facts.update(hero=hero, helper=helper, project=project, activity=activity, setting=setting)

    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved making funny things that could make a room giggle."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, and that made {hero.pronoun('possessive')} whole day feel bright."
    )
    world.say(
        f"That morning, {helper.label} brought {hero.pronoun('object')} {project.phrase} to {setting.place}."
    )

    world.para()
    world.say(
        f"As the time began to elapse, {hero.id} tried to {activity.rush} with a big grin."
    )
    world.zone = set(activity.zone)
    hero.meters["rush"] = hero.meters.get("rush", 0.0) + 1
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1
    world.elapsed += 1
    world.say(f"{hero.id} had to stride around the table, but the {project.label} still needed careful hands.")
    propagate(world, narrate=True)

    world.para()
    if project.meters.get("fixed", 0.0) >= THRESHOLD:
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        world.say(
            f"{hero.id} laughed at the wobble, then learned the lesson: a slower stride can save a silly construct."
        )
        world.say(
            f"In the end, {hero.id} and {helper.label} admired the finished {project.label}, and the room felt cheerful again."
        )
    else:
        world.say(
            f"{hero.id} paused, took a breath, and realized that a funny build works best when no one rushes it."
        )

    world.facts["resolved"] = project.meters.get("fixed", 0.0) >= THRESHOLD
    return world


SETTINGS = {
    "workshop": Setting(place="the workshop", indoor=True, affords={"construct"}),
    "garage": Setting(place="the garage", indoor=True, affords={"construct"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"construct"}),
}

ACTIVITIES = {
    "construct": Activity(
        id="construct",
        verb="construct a funny prop",
        gerund="constructing a funny prop",
        rush="stride to the bench",
        mess="tangled",
        soil="all tangled",
        zone={"hands"},
        keyword="construct",
        tags={"construct", "comedy"},
    ),
    "stride": Activity(
        id="stride",
        verb="stride across the floor",
        gerund="striding across the floor",
        rush="stride too quickly",
        mess="wobbly",
        soil="wobbly",
        zone={"feet"},
        keyword="stride",
        tags={"stride", "comedy"},
    ),
    "elapse": Activity(
        id="elapse",
        verb="let the afternoon elapse while thinking",
        gerund="letting the afternoon elapse",
        rush="sit still too long",
        mess="late",
        soil="late",
        zone=set(),
        keyword="elapse",
        tags={"elapse", "comedy"},
    ),
}

PROJECTS = {
    "hat": Project(
        label="silly hat",
        phrase="a striped silly hat",
        type="hat",
        region="head",
    ),
    "cart": Project(
        label="cardboard cart",
        phrase="a cardboard cart with a squeaky wheel",
        type="cart",
        region="hands",
    ),
    "mask": Project(
        label="comic mask",
        phrase="a comic mask with a lopsided grin",
        type="mask",
        region="face",
    ),
}

FIXES = [
    Fix(
        id="slow_steps",
        label="slow steps",
        covers={"hands"},
        guards={"tangled", "wobbly"},
        prep="slow down and use small careful steps",
        tail="took small careful steps",
    ),
    Fix(
        id="tap_measure",
        label="a measuring tape",
        covers={"hands"},
        guards={"tangled"},
        prep="measure twice and smile once",
        tail="used the measuring tape",
    ),
    Fix(
        id="steady_feet",
        label="steady feet",
        covers={"feet"},
        guards={"wobbly"},
        prep="plant both feet and build from the bottom up",
        tail="planted both feet",
    ),
]

TRAITS = ["curious", "goofy", "brave", "cheerful", "silly"]
GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ivy"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Max", "Owen"]


def prize_at_risk(activity: Activity, project: Project) -> bool:
    return project.region in activity.zone or activity.id == "construct"


def select_fix(activity: Activity, project: Project) -> Optional[Fix]:
    for fx in FIXES:
        if activity.mess in fx.guards or (activity.id == "construct" and fx.id == "slow_steps"):
            return fx
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for a in setting.affords:
            for p in PROJECTS:
                act = ACTIVITIES[a]
                proj = PROJECTS[p]
                if prize_at_risk(act, proj) and select_fix(act, proj):
                    out.append((s, a, p))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    project: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy for a child about how time can elapse while someone tries to {f["activity"].verb}.',
        f"Tell a funny story where {f['hero'].id} learns a lesson after trying to {f['activity'].verb} at {f['setting'].place}.",
        f'Write a playful story using the words "elapse", "stride", and "construct" that ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    activity = f["activity"]
    project = f["project"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {activity.verb}. That was the funny thing {hero.pronoun('possessive')} day kept circling around.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to construct?",
            answer=f"{hero.id} was trying to construct {project.phrase}. It was meant to be funny, not fancy.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the build got tricky?",
            answer=f"{helper.label} helped {hero.id}. Together they slowed down and fixed the project.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when time elapses?",
            answer="When time elapses, it passes by little by little, like the clock moving from one moment to the next.",
        ),
        QAItem(
            question="What does it mean to stride?",
            answer="To stride means to walk with long steps, often quickly and with purpose.",
        ),
        QAItem(
            question="What does construct mean?",
            answer="To construct means to build something by putting pieces together.",
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  elapsed={world.elapsed}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, project: Project) -> str:
    return (
        f"(No story: {activity.gerund} and {project.phrase} do not make a reasonable comedy setup here. "
        f"Try a combination where the project can actually be disrupted and then repaired.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("verb", aid, a.verb))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("project_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
prize_at_risk(A, P) :- activity(A), project(P), A = construct.

has_fix(A, P) :- prize_at_risk(A, P), fix(F), activity(A), project(P), compatible(F, A, P).

compatible(F, A, P) :- guards(F, M), mess_of(A, M), prize_at_risk(A, P).
compatible(slow_steps, A, P) :- A = construct, prize_at_risk(A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world: elapse, stride, construct, and learn a lesson.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.project:
        act, proj = ACTIVITIES[args.activity], PROJECTS[args.project]
        if not (prize_at_risk(act, proj) and select_fix(act, proj)):
            raise StoryError(explain_rejection(act, proj))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.project is None or c[2] == args.project)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, project = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, project=project, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PROJECTS[params.project], params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="workshop", activity="construct", project="cart", name="Mia", gender="girl", parent="mother", trait="goofy"),
    StoryParams(place="garage", activity="construct", project="mask", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="backyard", activity="construct", project="hat", name="Nora", gender="girl", parent="mother", trait="silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, project) combos ({len(stories)} with gender):\n")
        for place, act, proj in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, proj))
            print(f"  {place:10} {act:10} {proj:10}  [{', '.join(genders)}]")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (project: {p.project})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
