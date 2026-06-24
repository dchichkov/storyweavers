#!/usr/bin/env python3
"""
A small fable-like storyworld about yesterday, transformation, rhyme, and magic.

Premise:
- A young animal likes to perform a little rhyme.
- A magical object or rule causes an honest transformation.
- The change creates a problem or lesson.
- A wiser helper offers a reasonable magical fix that preserves the lesson.

The world is intentionally tiny and state-driven: physical state is modeled with
meters, emotional state with memes, and the story is rendered from the changes.
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
    transformed_into: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "dog", "boy", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"crow", "owl", "girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else self.label or self.id


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    transform_to: str
    cost: str
    lift: str
    fix_label: str
    fix_phrase: str
    protects_from: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    charm: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    charm = world.facts["charm"]
    if hero.memes.get("spell", 0) < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.transformed_into = charm.transform_to
    hero.meters["changed"] = 1
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    out.append(f"A soft magic shimmered around {hero.id}, and {hero.pronoun()} became a {charm.transform_to}.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    charm = world.facts["charm"]
    if hero.transformed_into != charm.transform_to:
        return out
    if hero.meters.get("changed", 0) < THRESHOLD:
        return out
    sig = ("fix", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["helped"] = 1
    hero.transformed_into = "self"
    hero.meters["changed"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["fear"] = 0
    out.append(f"{helper.id} spoke a kinder rhyme, and the magic eased until {hero.id} was themself again.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_transformation, _r_fix):
            sent = rule(world)
            if sent:
                changed = True
                for s in sent:
                    world.say(s)


SETTINGS = {
    "meadow": Setting(place="the meadow", kind="outdoor", affords={"rhyme", "magic"}),
    "oak": Setting(place="the old oak tree", kind="outdoor", affords={"rhyme", "magic"}),
    "brook": Setting(place="the little brook", kind="outdoor", affords={"rhyme", "magic"}),
}

CHARMS = {
    "badge": Charm(
        id="badge",
        label="a moon badge",
        phrase="a moon badge that loved honest words",
        transform_to="small owl",
        cost="sparkly",
        lift="speak a true rhyme",
        fix_label="a kinder rhyme",
        fix_phrase="a kinder rhyme that praised patience",
        protects_from={"fear"},
    ),
    "ring": Charm(
        id="ring",
        label="a silver ring",
        phrase="a silver ring that heard every rhyme",
        transform_to="green frog",
        cost="glowing",
        lift="tell a careful rhyme",
        fix_label="a steady rhyme",
        fix_phrase="a steady rhyme that named the lesson",
        protects_from={"lonely"},
    ),
    "stone": Charm(
        id="stone",
        label="a bright stone",
        phrase="a bright stone with a warm magic",
        transform_to="tiny mouse",
        cost="warm",
        lift="sing a true rhyme",
        fix_label="a gentle rhyme",
        fix_phrase="a gentle rhyme that made room for change",
        protects_from={"worry"},
    ),
}

HEROES = [("Milo", "fox"), ("Pip", "crow"), ("Tessa", "girl")]
HELPERS = [("Oona", "owl"), ("Gus", "goat"), ("Nell", "crow")]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CHARMS]


@dataclass
class StoryState:
    world: World
    hero: Entity
    helper: Entity
    charm: Entity


def setup(params: StoryParams) -> StoryState:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    charm_def = CHARMS[params.charm]
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label=charm_def.label, phrase=charm_def.phrase))
    world.facts["charm"] = charm_def
    return StoryState(world=world, hero=hero, helper=helper, charm=charm)


def introduce(world: World, hero: Entity, helper: Entity, charm: Entity) -> None:
    world.say(f"Yesterday, {hero.id} lived near {world.setting.place} and loved a small rhyme more than any bright toy.")
    world.say(f"{hero.id} often kept {charm.label} close, because its magic promised a lesson if the rhyme was true.")
    world.say(f"{helper.id}, a wise friend, listened carefully and never mocked the old songs.")


def desire(world: World, hero: Entity, charm: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(f"That day, {hero.id} wished to {world.facts['charm'].lift}, just to see what wonder would come.")
    world.say(f"{hero.id} began a little rhyme, and the air around {charm.label} grew bright and still.")


def warn(world: World, helper: Entity, hero: Entity, charm: Entity) -> None:
    hero.memes["spell"] = hero.memes.get("spell", 0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.say(f"{helper.id} warned, \"Magic likes honest hearts, but it may change you for a while.\"")
    world.say(f"{hero.id} listened, yet the rhyme was already humming, and the magic began to move.")


def conflict(world: World, hero: Entity) -> None:
    propagate(world)
    if hero.transformed_into and hero.transformed_into != "self":
        world.say(f"{hero.id} blinked at the world from a new shape and felt small and strange.")
        world.say(f"The meadow looked wider, and even the grass seemed to wait for a wiser rhyme.")


def resolution(world: World, helper: Entity, hero: Entity, charm: Entity) -> None:
    if hero.transformed_into and hero.transformed_into != "self":
        world.say(f"{helper.id} smiled and sang {world.facts['charm'].fix_phrase}.")
        propagate(world)
    if hero.transformed_into == "self":
        world.say(f"{hero.id} laughed softly, because the magic had taught {hero.pronoun('object')} to choose careful words.")
        world.say(f"Afterward, {hero.id} and {helper.id} walked home at dusk, and {charm.label} shone like a patient star.")


def tell(params: StoryParams) -> World:
    state = setup(params)
    world, hero, helper, charm = state.world, state.hero, state.helper, state.charm
    introduce(world, hero, helper, charm)
    world.para()
    desire(world, hero, charm)
    warn(world, helper, hero, charm)
    conflict(world, hero)
    world.para()
    resolution(world, helper, hero, charm)
    world.facts.update(hero=hero, helper=helper, charm=CHARMS[params.charm], setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["charm"]
    return [
        f'Write a short fable about yesterday, magic, and rhyme, using the phrase "{c.phrase}".',
        f"Tell a gentle story where a small animal learns a lesson after a magical rhyme changes {c.label}.",
        f"Write a child-friendly fable set at {world.setting.place} about a wise friend and a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    charm = world.facts["charm"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who lived near {world.setting.place} and loved a little rhyme.",
        ),
        QAItem(
            question=f"What did {helper.id} do when the magic got strong?",
            answer=f"{helper.id} sang a kinder rhyme and helped {hero.id} change back to themself.",
        ),
        QAItem(
            question=f"What caused the transformation?",
            answer=f"The transformation began when {hero.id} spoke a true rhyme with {charm.label}, and its magic woke up.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, {hero.id} was back to being themself, and the lesson from the magic stayed with them.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses characters and events to teach a lesson.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the ends, like sing and ring.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something wonderful that can make impossible things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes} transformed_into={e.transformed_into}")
    return "\n".join(lines)


def explain_rejection(place: str, charm: str) -> str:
    return f"(No story: the combination {place!r} and {charm!r} does not make a reasonable fable.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("transforms_to", cid, c.transform_to))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C) :- place(P), charm(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about yesterday, rhyme, magic, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["fox", "crow", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["owl", "goat", "crow"])
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
    if args.place and args.charm:
        if (args.place, args.charm) not in combos:
            raise StoryError(explain_rejection(args.place, args.charm))
    picks = [c for c in combos if (args.place is None or c[0] == args.place) and (args.charm is None or c[1] == args.charm)]
    if not picks:
        raise StoryError("(No valid combination matches the given options.)")
    place, charm = rng.choice(sorted(picks))
    hero_name, hero_type = (args.hero, args.hero_type) if args.hero and args.hero_type else rng.choice(HEROES)
    helper_name, helper_type = (args.helper, args.helper_type) if args.helper and args.helper_type else rng.choice(HELPERS)
    if args.hero is None:
        hero_name, hero_type = rng.choice(HEROES)
    if args.helper is None:
        helper_name, helper_type = rng.choice(HELPERS)
    return StoryParams(place=place, charm=charm, hero=hero_name, hero_type=hero_type, helper=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="meadow", charm="badge", hero="Milo", hero_type="fox", helper="Oona", helper_type="owl"),
    StoryParams(place="oak", charm="ring", hero="Pip", hero_type="crow", helper="Gus", helper_type="goat"),
    StoryParams(place="brook", charm="stone", hero="Tessa", hero_type="girl", helper="Nell", helper_type="crow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:\n")
        for p, c in vals:
            print(f"  {p:8} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.charm} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
