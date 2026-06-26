#!/usr/bin/env python3
"""
storyworlds/worlds/threaten_polo_middle_conflict_lesson_learned_heartwarming.py
===============================================================================

A small heartwarming storyworld about a child, a middle-of-the-game conflict,
and a gentle lesson learned around polo.

Seed prompt sketch:
---
A child wants to play polo in the middle of practice. Something goes wrong, a
threat is made, feelings flare, and a kind adult helps everyone learn a lesson.
In the end, the child understands how to play safely and the group stays close.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the middle field"
    outside: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False
    fragile: bool = False
    at_risk_from: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "field": Setting(place="the middle field", outside=True, affords={"polo"}),
    "clubyard": Setting(place="the club yard", outside=True, affords={"polo"}),
    "schoolground": Setting(place="the school ground", outside=True, affords={"polo"}),
}

ACTIVITIES = {
    "polo": Activity(
        id="polo",
        verb="play polo",
        gerund="playing polo",
        rush="dash toward the ball",
        mess="bump",
        soil="ruffled and upset",
        keyword="polo",
        tags={"polo", "game", "team"},
    )
}

ITEMS = {
    "hat": Item(
        id="hat",
        label="hat",
        phrase="a neat little hat",
        type="hat",
        fragile=False,
        at_risk_from={"bump"},
    ),
    "polo_shirt": Item(
        id="polo_shirt",
        label="polo shirt",
        phrase="a bright polo shirt",
        type="shirt",
        fragile=False,
        at_risk_from={"bump"},
    ),
    "whistle": Item(
        id="whistle",
        label="whistle",
        phrase="a shiny whistle",
        type="whistle",
        fragile=True,
        at_risk_from={"bump"},
    ),
}

REMEDIES = {
    "pause": Remedy(
        id="pause",
        label="a calm pause",
        prep="take a calm pause and check the rules",
        tail="paused, took a breath, and listened to the coach",
        helps={"bump"},
    ),
    "practice": Remedy(
        id="practice",
        label="gentle practice",
        prep="slow down and practice gentle swings first",
        tail="slowed down and practiced gentle swings together",
        helps={"bump"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Ava", "Nora", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Noah", "Max"]
TRAITS = ["curious", "careful", "brave", "lively", "sweet"]


# ---------------------------------------------------------------------------
# Storyworld parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,I) :- activity(A), item(I), causes(A,M), item_risk(I,M).
has_fix(A,I) :- at_risk(A,I), remedy(R), helps(R,M), causes(A,M), remedy_covers(R,I).
valid_story(P,A,I,G) :- setting(P), affords(P,A), at_risk(A,I), has_fix(A,I), wears(G,I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("causes", aid, a.mess))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for m in sorted(i.at_risk_from):
            lines.append(asp.fact("item_risk", iid, m))
        lines.append(asp.fact("wears", "girl", iid))
        lines.append(asp.fact("wears", "boy", iid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for m in sorted(r.helps):
            lines.append(asp.fact("helps", rid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def item_at_risk(activity: Activity, item: Item) -> bool:
    return activity.mess in item.at_risk_from


def select_remedy(activity: Activity, item: Item) -> Optional[Remedy]:
    for remedy in REMEDIES.values():
        if activity.mess in remedy.helps and item.id in {"hat", "polo_shirt", "whistle"}:
            return remedy
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for item_id, item in ITEMS.items():
                if item_at_risk(act, item) and select_remedy(act, item):
                    for gender in ("girl", "boy"):
                        if gender in {"girl", "boy"}:
                            combos.append((place, act_id, item_id, gender))
    return combos


def explain_rejection(activity: Activity, item: Item) -> str:
    return (
        f"(No story: {activity.gerund} does not create a believable middle conflict "
        f"for a {item.label}, or there is no remedy that can really help.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def predict_problem(world: World, hero: Entity, activity: Activity, item: Item) -> dict:
    sim = world.copy()
    sim.facts["event"] = "predicted"
    if item_at_risk(activity, item):
        return {"at_risk": True, "lesson": True}
    return {"at_risk": False, "lesson": False}


def introduce(world: World, hero: Entity, adult: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in [hero.type,] if t)} {hero.type} "
        f"who loved {item.label}s and bright, busy days."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} had {hero.pronoun('possessive')} "
        f"{item.label} ready, and {adult.label} always watched kindly from nearby."
    )


def setup(world: World, hero: Entity, adult: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"At the middle of practice, {hero.id} wanted to {activity.verb} with everyone else."
    )
    world.say(
        f"The ball kept rolling back to the center, and the middle field felt exciting."
    )


def conflict(world: World, hero: Entity, adult: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
    world.say(
        f"But when {hero.id} rushed to {activity.rush}, {hero.pronoun('possessive')} "
        f"{item.label} got in the way."
    )
    world.say(
        f"{hero.id} frowned and said, \"I want to keep going, even if I have to threaten to quit.\""
    )
    world.say(
        f"{adult.label} knelt down and listened, because big feelings were happening in the middle."
    )


def lesson(world: World, hero: Entity, adult: Entity, activity: Activity, item: Entity) -> Optional[Remedy]:
    remedy = select_remedy(activity, item)
    if remedy is None:
        return None
    world.say(
        f"Then {adult.label} showed a better way: {remedy.prep}."
    )
    return remedy


def resolve(world: World, hero: Entity, adult: Entity, activity: Activity, item: Entity, remedy: Remedy) -> None:
    hero.memes["conflict"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["lesson_learned"] = hero.memes.get("lesson_learned", 0) + 1
    world.say(
        f"{hero.id} took a breath, nodded, and learned that being strong meant listening too."
    )
    world.say(
        f"So {hero.id} and {adult.label} {remedy.tail}. Soon the game felt safe again."
    )
    world.say(
        f"By the end, {hero.id} was {activity.gerund}, smiling in the middle field, with everyone still together."
    )


def tell(setting: Setting, activity: Activity, item_cfg: Item, hero_name: str, hero_type: str, adult_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    adult = world.add(Entity(id="Coach", kind="character", type=adult_type, label="the coach"))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.type, label=item_cfg.label, phrase=item_cfg.phrase, owner=hero.id, worn_by=hero.id))

    world.say(
        f"{hero.id} was a {trait} little {hero.type} who loved {item.label} and the game of polo."
    )
    world.say(
        f"{hero.id} wore {item.phrase} and watched the middle field with shining eyes."
    )

    world.para()
    setup(world, hero, adult, activity, item)
    conflict(world, hero, adult, activity, item)
    remedy = lesson(world, hero, adult, activity, item)
    if remedy:
        world.para()
        resolve(world, hero, adult, activity, item, remedy)

    world.facts.update(
        hero=hero,
        adult=adult,
        item=item,
        item_cfg=item_cfg,
        activity=activity,
        setting=setting,
        remedy=remedy,
        resolved=remedy is not None,
        conflict=True,
        middle=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, adult, act, item = f["hero"], f["adult"], f["activity"], f["item_cfg"]
    return [
        f'Write a heartwarming story about {hero.id}, polo, and a lesson learned in the middle of practice.',
        f"Tell a child-friendly story where {hero.id} wants to {act.verb} but the {item.label} causes a conflict, and the coach helps.",
        f'Write a short story that includes the words "threaten", "polo", and "middle" and ends kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, act, item = f["hero"], f["adult"], f["activity"], f["item_cfg"]
    return [
        QAItem(
            question=f"Who learned a lesson in the middle of the polo practice?",
            answer=f"{hero.id} learned a lesson in the middle of practice after {hero.pronoun('subject')} got upset and then listened to {adult.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the conflict started?",
            answer=f"{hero.id} wanted to {act.verb} in the middle field.",
        ),
        QAItem(
            question=f"Why did the story get tense when {hero.id} said something about quitting?",
            answer=f"It got tense because {hero.id} felt a conflict growing in the middle of the game and threatened to quit before the coach helped.",
        ),
        QAItem(
            question=f"What helped calm things down?",
            answer=f"{adult.label} helped by showing a calmer way to keep playing, so {hero.id} could keep going safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is polo?",
            answer="Polo is a team game where players try to move a ball and work together while riding or playing with sticks, depending on the kind of polo being played.",
        ),
        QAItem(
            question="What does middle mean?",
            answer="Middle means the center place between sides or edges.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a problem where people want different things or feelings start bumping together.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something helpful after a mistake or a hard moment.",
        ),
        QAItem(
            question="What does threaten mean?",
            answer="To threaten means to say you might do something harmful or unpleasant, often to try to scare or control someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.item:
        act = ACTIVITIES[args.activity]
        item = ITEMS[args.item]
        if not (item_at_risk(act, item) and select_remedy(act, item)):
            raise StoryError(explain_rejection(act, item))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.item is None or c[2] == args.item)
        and (args.gender is None or c[3] == args.gender)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, item, gender = rng.choice(sorted(combos))
    name = args.name or rng.choice(valid_names(gender))
    adult = args.adult or "mother"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        ITEMS[params.item],
        params.name,
        params.gender,
        params.adult,
        params.trait,
    )
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="field", activity="polo", item="hat", name="Mia", gender="girl", adult="mother", trait="curious"),
    StoryParams(place="clubyard", activity="polo", item="polo_shirt", name="Leo", gender="boy", adult="father", trait="brave"),
    StoryParams(place="schoolground", activity="polo", item="whistle", name="Nora", gender="girl", adult="mother", trait="sweet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming polo storyworld with conflict and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, act, item, gender in stories:
            print(f"  {place:12} {act:8} {item:10} {gender}")
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
