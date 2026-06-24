#!/usr/bin/env python3
"""
A small storyworld: a space-adventure tale about coke, a shower, dialogue, and conflict.

The world premise:
A young shipmate wants to bring a can of coke into a cramped spaceship shower booth.
A careful crewmate warns that sticky fizz in a shower would make a slippery, messy job.
They argue, then talk it through, and choose a safer drink spot instead.

This script models:
- physical meters: sticky, wet, slippery, dirty
- emotional memes: desire, worry, conflict, relief, joy
- a simple dialogue-and-compromise turn

The story is deliberately classical:
setup -> warning/conflict -> dialogue -> resolution.
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
# Data model
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the spaceship"
    shower_booth: str = "the ship shower"
    deck: str = "the cargo deck"


@dataclass
class Prop:
    label: str
    phrase: str
    mess_kind: str
    risky_place: str
    safe_place: str


@dataclass
class StoryParams:
    name: str
    gender: str
    role: str
    helper_name: str
    helper_gender: str
    helper_role: str
    prop: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
SETTINGS = {
    "default": Setting(),
}

PROPS = {
    "coke": Prop(
        label="coke",
        phrase="a cold can of coke",
        mess_kind="sticky",
        risky_place="shower",
        safe_place="mess table",
    ),
}

NAMES_GIRL = ["Mina", "Rae", "Nova", "Luna", "Iris"]
NAMES_BOY = ["Kai", "Jett", "Orion", "Pax", "Taro"]
ROLES = ["cadet", "pilot", "engineer", "navigator", "shipmate"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def prop_at_risk(prop: Prop, place: str) -> bool:
    return place == prop.risky_place


def select_safe_spot(prop: Prop) -> Optional[str]:
    return prop.safe_place if prop.label == "coke" else None


def explain_rejection(prop: Prop) -> str:
    return (
        f"(No story: this setup only works when the {prop.label} is headed toward "
        f"the shower, where sticky fizz would make a real problem.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS["default"])
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.role,
            memes={"desire": 0.0, "joy": 0.0, "conflict": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper_name,
            kind="character",
            type=params.helper_gender,
            label=params.helper_role,
            memes={"worry": 0.0, "relief": 0.0, "conflict": 0.0},
        )
    )
    prop = world.add(
        Entity(
            id=params.prop,
            kind="thing",
            type=params.prop,
            label=params.prop,
            phrase=PROPS[params.prop].phrase,
            owner=hero.id,
            caretaker=helper.id,
            meters={"sticky": 0.0, "wet": 0.0, "dirty": 0.0, "slippery": 0.0},
        )
    )

    # Act 1: setup
    world.say(
        f"{hero.id} was a little {hero.label} aboard a silver spaceship, and "
        f"{hero.pronoun('subject')} loved tiny adventures between the engine hum and the stars."
    )
    world.say(
        f"One day, {hero.id} found {prop.phrase} and grinned as if it were treasure."
    )
    world.say(
        f"{helper.id}, the ship's {helper.label}, watched {hero.id} carry it toward {world.setting.shower_booth}."
    )

    # Act 2: conflict
    world.para()
    hero.memes["desire"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'"I want to take my coke into the shower," {hero.id} said. '
        f'"It will be fun to sip while I wash up."'
    )
    world.say(
        f'"Not in the shower," {helper.id} said. "If that can tips over, the floor will get sticky and slippery."'
    )
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    world.say(
        f"{hero.id} folded {hero.pronoun('possessive')} arms. "
        f'"But I want it now," {hero.id} muttered.'
    )
    world.say(
        f'{helper.id} pointed at the shower tile. "Look how small this booth is. '
        f"One splash could make a big mess."'
    )

    # World-state consequence if the prop goes into the shower: narrated as a foreseen risk, not a frozen log.
    if prop_at_risk(PROPS[params.prop], "shower"):
        prop.meters["sticky"] += 1
        prop.meters["slippery"] += 1
        world.facts["risk"] = "sticky and slippery"
        world.facts["reason"] = "the shower would make the coke spill into a messy patch"
        world.say(
            f"{hero.id} looked at the narrow booth and finally saw it too: "
            f"the shower would turn the drink into a sticky spill."
        )

    # Act 3: dialogue and resolution
    world.para()
    safe_spot = select_safe_spot(PROPS[params.prop])
    if safe_spot is None:
        raise StoryError("No safe compromise exists for this prop.")
    world.say(
        f'"Then where can I have it?" {hero.id} asked, a little softer now.'
    )
    world.say(
        f'"Right here on the mess table," {helper.id} said. '
        f'"You can drink your coke first, and then shower without any sticky floor."'
    )
    hero.memes["desire"] += 0.5
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    helper.memes["relief"] += 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.id} nodded. {hero.pronoun('subject').capitalize()} took the coke to the mess table, "
        f"where {helper.id} opened a towel and set it beside a clean cup."
    )
    world.say(
        f"After that, {hero.id} drank the coke safely, then took a real shower while {helper.id} "
        f"smiled at the clean floor. The ship stayed neat, and the stars still shone outside."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prop=prop,
        safe_spot=safe_spot,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prop: Entity = f["prop"]
    return [
        f'Write a short space-adventure story for a young child about {hero.id}, {prop.label}, and a shower on a spaceship.',
        f'Write a gentle story where {hero.id} wants to bring {prop.phrase} into {world.setting.shower_booth}, but {helper.id} helps find a safer plan.',
        f'Create a child-friendly dialogue story about a small conflict in space that ends with a clean, safe choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    prop: Entity = f["prop"]
    return [
        QAItem(
            question=f"What did {hero.id} want to bring into the shower?",
            answer=f"{hero.id} wanted to bring {prop.phrase} into the shower.",
        ),
        QAItem(
            question=f"Why did {helper.id} say no to the shower idea?",
            answer=(
                f"{helper.id} said no because the shower was too small, and a spilled coke would "
                f"make the floor sticky and slippery."
            ),
        ),
        QAItem(
            question=f"What safe choice did they make instead?",
            answer=(
                f"They put the coke on the mess table first, let {hero.id} drink it safely, and then "
                f"{hero.id} took a shower without making a mess."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is coke?",
            answer="Coke is a fizzy soda drink with bubbles. If it spills, it can leave sticky spots.",
        ),
        QAItem(
            question="Why can a shower be a problem for a spilled drink?",
            answer="A shower has wet floor surfaces, so a spilled drink can mix with water and make the floor slippery.",
        ),
        QAItem(
            question="What is a good way to solve a small argument?",
            answer="A good way is to talk calmly, listen to each other, and find a safer choice that works for everyone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.kind:9}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show risky/2.
#show resolved/1.

risky(coke, shower) :- prop(coke), place(shower).

resolved(coke) :- prop(coke), safe_place(mess_table).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    lines.append(asp.fact("prop", "coke"))
    lines.append(asp.fact("place", "shower"))
    lines.append(asp.fact("safe_place", "mess_table"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show risky/2.\n#show resolved/1."))
    atoms = set(asp.atoms(model, "risky")) | set(asp.atoms(model, "resolved"))
    expected = {("coke", "shower"), ("coke",)}
    if atoms == expected:
        print("OK: ASP rules match the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP rules do not match expected facts.")
    print(sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prop and args.prop not in PROPS:
        raise StoryError("Unknown prop.")
    prop = args.prop or "coke"
    if not prop_at_risk(PROPS[prop], "shower"):
        raise StoryError(explain_rejection(PROPS[prop]))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = "boy" if gender == "girl" else "girl"
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_name = args.helper_name or rng.choice(NAMES_BOY if helper_gender == "boy" else NAMES_GIRL)
    role = args.role or rng.choice(ROLES)
    helper_role = args.helper_role or rng.choice(ROLES)
    return StoryParams(
        name=name,
        gender=gender,
        role=role,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_role=helper_role,
        prop=prop,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world: coke, shower, dialogue, and conflict.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-role", choices=ROLES)
    ap.add_argument("--prop", choices=PROPS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show risky/2.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(
                name="Nova",
                gender="girl",
                role="cadet",
                helper_name="Pax",
                helper_gender="boy",
                helper_role="engineer",
                prop="coke",
            )
        ]
    else:
        params_list = []
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(p) for p in params_list]

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
