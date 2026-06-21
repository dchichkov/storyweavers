#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py
=================================================================

A standalone storyworld for a tiny fable-like domain: small animals plan a
village junket, one friend clings to a shiny doodad instead of helping, and a
problem around a cookie cart can only be solved through teamwork.

The world model tracks simple physical meters and social memes. The rendered
story comes from simulated state rather than slot-swapping. A reasonableness
gate keeps the domain narrow: the helper team must be large enough for the
chosen task, and the doodad temptation must plausibly interfere with helping.

Run it
------
    python storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py
    python storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py --animal mouse --task stuck_cart
    python storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py --task fallen_banner
    python storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py --all
    python storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/cookie_doodad_junket_teamwork_fable.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
STORYWORLDS_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
sys.path.insert(0, STORYWORLDS_DIR)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "ewe", "girl", "mother", "aunt"}
        male = {"mouse", "crow", "fox", "boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def cap_label(self) -> str:
        return self.label[:1].upper() + self.label[1:] if self.label else self.id


@dataclass
class AnimalCfg:
    id: str
    trait: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DoodadCfg:
    id: str
    label: str
    shine: str
    misuse: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TaskCfg:
    id: str
    label: str
    scene: str
    problem: str
    need: int
    method: str
    solved: str
    ending: str
    knowledge_tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TreatCfg:
    id: str
    label: str
    aroma: str
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


def task_possible(team_size: int, task: TaskCfg) -> bool:
    return team_size >= task.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal in ANIMALS:
        for doodad in DOODADS:
            for task_id, task in TASKS.items():
                for team_size in TEAM_SIZES:
                    if task_possible(team_size, task):
                        combos.append((animal, doodad, task_id))
                        break
    return sorted(set(combos))


def explain_task(task: TaskCfg, team_size: int) -> str:
    return (
        f"(No story: {task.label} needs at least {task.need} helpers, but this story "
        f"only has {team_size}. A teamwork fable needs a task that the team can "
        f"reasonably solve together.)"
    )


def introduce(world: World, hero: Entity, partner: Entity, elder: Entity, treat: TreatCfg, task: TaskCfg) -> None:
    world.say(
        f"In Clover Hollow, {hero.id} the {hero.type} and {partner.id} the {partner.type} "
        f"were getting ready for the village junket."
    )
    world.say(
        f"The square smelled of {treat.aroma}, and {elder.id} had promised that anyone "
        f"who helped could share a warm {treat.label} when the work was done."
    )
    world.say(
        f"But first there was one important job: {task.scene}."
    )


def tempt(world: World, hero: Entity, doodad: DoodadCfg) -> None:
    hero.memes["tempted"] += 1
    world.say(
        f"On the path, {hero.id} spotted {doodad.label}, {doodad.shine}. "
        f"{hero.pronoun().capitalize()} turned it in {hero.pronoun('possessive')} paws and "
        f"thought it looked finer than any plain old tool."
    )


def ask_help(world: World, partner: Entity, elder: Entity, task: TaskCfg) -> None:
    partner.memes["duty"] += 1
    world.say(
        f'"Please do not dawdle," said {elder.id}. "{task.problem}"'
    )
    world.say(
        f'{partner.id} nodded and called, "Come help. We can fix it if we work together."'
    )


def dawdle(world: World, hero: Entity, doodad: DoodadCfg) -> None:
    hero.memes["pride"] += 1
    hero.meters["delay"] += 1
    world.say(
        f"But {hero.id} tapped and twirled the doodad instead. "
        f"{hero.pronoun().capitalize()} even tried {doodad.misuse}, which did not help at all."
    )


def escalate(world: World, task: TaskCfg, elder: Entity) -> None:
    place = world.get("square")
    place.meters["trouble"] += 1
    elder.memes["worry"] += 1
    world.say(task.problem)


def realize(world: World, hero: Entity, partner: Entity, doodad: DoodadCfg, task: TaskCfg) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"Then {hero.id} saw {partner.id} straining alone and heard the worried rustle all around. "
        f"The doodad was bright, but it could not {task.method}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tucked {doodad.label} away and felt a hot pinch of shame. "
        f'"A shiny thing is not the same as a useful paw," {hero.pronoun()} said.'
    )


def help_together(world: World, hero: Entity, partner: Entity, extras: list[Entity], task: TaskCfg, treat: TreatCfg) -> None:
    team = [hero, partner] + extras
    for ent in team:
        ent.memes["cooperation"] += 1
        ent.meters["effort"] += 1
    place = world.get("square")
    place.meters["trouble"] = 0.0
    place.meters["order"] += 1
    world.say(
        f"At once {hero.id} hurried back. {task.method}"
    )
    world.say(task.solved)
    world.say(
        f"Soon the village junket could begin, and the tray of {treat.label}s came out at last."
    )


def ending(world: World, hero: Entity, partner: Entity, elder: Entity, treat: TreatCfg, task: TaskCfg) -> None:
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{elder.id} broke the first {treat.label} in two and gave a share to {hero.id} "
        f"and a share to {partner.id}."
    )
    world.say(
        f'"Remember this," said {elder.id}. "A fair junket is built by many willing hands, '
        f'not by one little doodad."'
    )
    world.say(task.ending)


def tell(animal: AnimalCfg, doodad: DoodadCfg, task: TaskCfg, treat: TreatCfg, team_size: int,
         hero_name: str = "Pip", partner_name: str = "Mara", elder_name: str = "Aunt Hazel") -> World:
    if not task_possible(team_size, task):
        raise StoryError(explain_task(task, team_size))

    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=animal.id, label=animal.id, role="hero",
                            traits=[animal.trait]))
    partner_type = PARTNER_TYPES[animal.id]
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type, label=partner_type, role="partner"))
    elder = world.add(Entity(id=elder_name, kind="character", type="aunt", label="Aunt Hazel", role="elder"))
    world.add(Entity(id="square", kind="place", type="square", label="village square"))
    doodad_ent = world.add(Entity(id="doodad", kind="thing", type="doodad", label=doodad.label, tags=set(doodad.tags)))
    treat_ent = world.add(Entity(id="cookie", kind="thing", type="cookie", label=treat.label, tags=set(treat.tags), plural=True))
    extras: list[Entity] = []
    for i in range(max(0, team_size - 2)):
        extra_type = EXTRA_TYPES[i % len(EXTRA_TYPES)]
        extras.append(world.add(Entity(
            id=f"Helper{i+1}",
            kind="character",
            type=extra_type,
            label=extra_type,
            role="helper",
        )))

    introduce(world, hero, partner, elder, treat, task)
    world.para()
    tempt(world, hero, doodad)
    ask_help(world, partner, elder, task)
    dawdle(world, hero, doodad)
    escalate(world, task, elder)
    world.para()
    realize(world, hero, partner, doodad, task)
    help_together(world, hero, partner, extras, task, treat)
    world.para()
    ending(world, hero, partner, elder, treat, task)

    world.facts.update(
        hero=hero,
        partner=partner,
        elder=elder,
        doodad=doodad_ent,
        doodad_cfg=doodad,
        task=task,
        treat=treat_ent,
        treat_cfg=treat,
        team_size=team_size,
        helpers=extras,
        solved=world.get("square").meters["order"] >= THRESHOLD,
        trouble=world.get("square").meters["trouble"],
        used_team=len(extras) + 2,
    )
    return world


ANIMALS = {
    "mouse": AnimalCfg(
        id="mouse",
        trait="quick",
        style="small and nimble",
        tags={"mouse", "teamwork"},
    ),
    "crow": AnimalCfg(
        id="crow",
        trait="clever",
        style="sharp-eyed",
        tags={"crow", "teamwork"},
    ),
    "hen": AnimalCfg(
        id="hen",
        trait="busy",
        style="steady and warm",
        tags={"hen", "teamwork"},
    ),
    "fox": AnimalCfg(
        id="fox",
        trait="nimble",
        style="bright and eager",
        tags={"fox", "teamwork"},
    ),
}

PARTNER_TYPES = {
    "mouse": "hen",
    "crow": "mouse",
    "hen": "crow",
    "fox": "mouse",
}

EXTRA_TYPES = ["goose", "mole", "squirrel"]

DOODADS = {
    "spinner": DoodadCfg(
        id="spinner",
        label="a brass doodad",
        shine="with a tiny wheel that flashed in the sun",
        misuse="to hook it onto the cart rope like a magic lever",
        tags={"doodad"},
    ),
    "whirler": DoodadCfg(
        id="whirler",
        label="a silver doodad",
        shine="all twinkles and tiny clicks",
        misuse="to wave it at the problem as if cleverness alone would do the lifting",
        tags={"doodad"},
    ),
    "bobbler": DoodadCfg(
        id="bobbler",
        label="a painted doodad",
        shine="with red beads that danced when it shook",
        misuse="to tie it to the banner cord as though decoration were the same as help",
        tags={"doodad"},
    ),
}

TASKS = {
    "stuck_cart": TaskCfg(
        id="stuck_cart",
        label="a stuck cookie cart",
        scene="the cookie cart had sunk into a soft patch of mud by the well",
        problem="The cookie cart is stuck fast, and the junket cannot begin while the treats are trapped by the well.",
        need=3,
        method="They leaned shoulder, wing, and paw against the handles together and pushed in one long heave.",
        solved="With a wet squelch the cart rolled free, and the round cookie tins rattled merrily inside.",
        ending="From that day on, Pip looked first for friends before fussing over trinkets.",
        knowledge_tag="cart",
        tags={"cart", "teamwork", "cookie", "junket"},
    ),
    "fallen_banner": TaskCfg(
        id="fallen_banner",
        label="a fallen junket banner",
        scene="the bright banner for the junket had slipped from the arbor and tangled in the branches",
        problem="The junket banner has fallen and tangled high above the table, so no one knows where to gather.",
        need=2,
        method="One held the ladder steady, one climbed, and together they straightened the cloth and tied the knots snug.",
        solved="The banner floated up again, bright above the square, and every little guest could see where to go.",
        ending="After that, Pip remembered that even a high knot comes loose faster with a friend below.",
        knowledge_tag="banner",
        tags={"banner", "teamwork", "junket"},
    ),
    "jammed_gate": TaskCfg(
        id="jammed_gate",
        label="a jammed orchard gate",
        scene="the orchard gate had jammed, keeping the tables, drums, and cookie baskets locked inside",
        problem="The orchard gate is jammed shut, and the junket cannot open while the baskets stay inside.",
        need=3,
        method="One lifted the latch, another pulled the gate, and the others braced the post until the wood gave a soft groan.",
        solved="The gate swung wide, and the baskets of cookie treats were carried out into the sunlight.",
        ending="Pip never again mistook fussing with a trifle for doing a neighborly deed.",
        knowledge_tag="gate",
        tags={"gate", "teamwork", "cookie", "junket"},
    ),
}

TREATS = {
    "honey_cookie": TreatCfg(
        id="honey_cookie",
        label="honey cookie",
        aroma="warm honey and butter",
        tags={"cookie"},
    ),
    "oat_cookie": TreatCfg(
        id="oat_cookie",
        label="oat cookie",
        aroma="toasted oats and cinnamon",
        tags={"cookie"},
    ),
    "berry_cookie": TreatCfg(
        id="berry_cookie",
        label="berry cookie",
        aroma="sweet berries and sugar",
        tags={"cookie"},
    ),
}

TEAM_SIZES = [2, 3, 4]


@dataclass
class StoryParams:
    animal: str
    doodad: str
    task: str
    treat: str
    team_size: int
    hero_name: str
    partner_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        animal="mouse",
        doodad="spinner",
        task="stuck_cart",
        treat="honey_cookie",
        team_size=3,
        hero_name="Pip",
        partner_name="Mara",
        seed=1,
    ),
    StoryParams(
        animal="crow",
        doodad="whirler",
        task="fallen_banner",
        treat="berry_cookie",
        team_size=2,
        hero_name="Rook",
        partner_name="Pia",
        seed=2,
    ),
    StoryParams(
        animal="hen",
        doodad="bobbler",
        task="jammed_gate",
        treat="oat_cookie",
        team_size=4,
        hero_name="Tilly",
        partner_name="Corin",
        seed=3,
    ),
]

KNOWLEDGE = {
    "cookie": [
        (
            "What is a cookie?",
            "A cookie is a small sweet baked treat. It is often crisp on the outside and soft inside."
        )
    ],
    "doodad": [
        (
            "What is a doodad?",
            "A doodad is a little object or gadget, often something small and curious. It may look interesting even when it is not very useful."
        )
    ],
    "junket": [
        (
            "What is a junket?",
            "A junket is a little outing or cheerful gathering. In this story, it means a village celebration."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people helping one another on the same task. They do better by sharing effort instead of each working alone."
        )
    ],
    "cart": [
        (
            "Why might a heavy cart need several helpers?",
            "A heavy cart can be hard to push because its weight presses down on the wheels. Several helpers can add their strength together."
        )
    ],
    "banner": [
        (
            "Why is it easier to hang a banner with two helpers?",
            "One helper can steady things while the other reaches up and ties the cloth. That makes the job safer and neater."
        )
    ],
    "gate": [
        (
            "Why can a wooden gate get stuck?",
            "A wooden gate can swell, lean, or catch on the ground. Then it may need lifting, pulling, and bracing to open."
        )
    ],
}

KNOWLEDGE_ORDER = ["cookie", "doodad", "junket", "teamwork", "cart", "banner", "gate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    task = f["task"]
    treat = f["treat_cfg"]
    doodad = f["doodad_cfg"]
    return [
        f'Write a short fable for a 3-to-5-year-old that includes the words "cookie", "doodad", and "junket".',
        f"Tell a teamwork fable where {hero.id} the {hero.type} is distracted by {doodad.label}, but learns to help solve {task.label}.",
        f"Write a gentle animal story in a fable style where a village junket is saved by cooperation, and the ending includes a {treat.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    elder = f["elder"]
    task = f["task"]
    doodad = f["doodad_cfg"]
    treat = f["treat_cfg"]
    used_team = f["used_team"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {partner.id} the {partner.type}. They were helping prepare for a village junket."
        ),
        (
            "What distracted the hero at first?",
            f"{hero.id} was distracted by {doodad.label}. It looked shiny and exciting, so {hero.pronoun()} wasted time playing with it instead of helping."
        ),
        (
            "What problem needed to be fixed?",
            f"The problem was {task.label}. Because of that trouble, the junket could not properly begin."
        ),
        (
            f"Why did {hero.id} stop playing with the doodad?",
            f"{hero.id} saw that the doodad was not solving anything and that {partner.id} was struggling. That made {hero.pronoun('object')} feel ashamed and ready to help for real."
        ),
        (
            "How was the problem solved?",
            f"It was solved by teamwork. {task.method} That shared effort is what changed the day."
        ),
        (
            "How did the story end?",
            f"The junket could begin, and {elder.id} shared a {treat.label} after the work was done. The ending proves that willing helpers mattered more than the little doodad."
        ),
    ]
    if used_team >= task.need:
        qa.append(
            (
                "Why did the helpers succeed together?",
                f"They had enough helpers for the job, with {used_team} workers for a task that needed {task.need}. Because they combined their effort in the right way, the trouble gave way."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cookie", "doodad", "junket", "teamwork", f["task"].knowledge_tag}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
possible(Task, Team) :- task(Task), team_size(Team), need(Task, Need), Team >= Need.
valid(Animal, Doodad, Task) :- animal(Animal), doodad(Doodad), task(Task), team_size(Team), possible(Task, Team).

chosen_possible :- chosen_task(T), chosen_team_size(S), need(T, N), S >= N.
outcome(solved) :- chosen_possible.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for doodad in DOODADS:
        lines.append(asp.fact("doodad", doodad))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("need", task_id, task.need))
    for size in TEAM_SIZES:
        lines.append(asp.fact("team_size", size))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_task", params.task),
        asp.fact("chosen_team_size", params.team_size),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if task_possible(params.team_size, TASKS[params.task]) else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a teamwork fable with a cookie, a doodad, and a village junket."
    )
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--doodad", choices=sorted(DOODADS))
    ap.add_argument("--task", choices=sorted(TASKS))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--team-size", type=int, choices=TEAM_SIZES)
    ap.add_argument("--hero-name")
    ap.add_argument("--partner-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


HERO_NAMES = ["Pip", "Rook", "Tilly", "Moss", "Nell", "Bram", "Saffy", "Wren"]
PARTNER_NAMES = ["Mara", "Pia", "Corin", "Lark", "Bea", "Otis", "June", "Milo"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task is not None and args.team_size is not None:
        task = TASKS[args.task]
        if not task_possible(args.team_size, task):
            raise StoryError(explain_task(task, args.team_size))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.doodad is None or combo[1] == args.doodad)
        and (args.task is None or combo[2] == args.task)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, doodad, task = rng.choice(combos)
    team_size = args.team_size if args.team_size is not None else rng.choice(
        [size for size in TEAM_SIZES if task_possible(size, TASKS[task])]
    )
    treat = args.treat or rng.choice(sorted(TREATS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    partner_name = args.partner_name or rng.choice([n for n in PARTNER_NAMES if n != hero_name])
    return StoryParams(
        animal=animal,
        doodad=doodad,
        task=task,
        treat=treat,
        team_size=team_size,
        hero_name=hero_name,
        partner_name=partner_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.doodad not in DOODADS:
        raise StoryError(f"(Unknown doodad: {params.doodad})")
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.team_size not in TEAM_SIZES:
        raise StoryError(f"(Unsupported team size: {params.team_size})")
    task = TASKS[params.task]
    if not task_possible(params.team_size, task):
        raise StoryError(explain_task(task, params.team_size))

    world = tell(
        animal=ANIMALS[params.animal],
        doodad=DOODADS[params.doodad],
        task=TASKS[params.task],
        treat=TREATS[params.treat],
        team_size=params.team_size,
        hero_name=params.hero_name,
        partner_name=params.partner_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py:
            print("  only in clingo:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))

    cases = list(CURATED)
    for seed in range(10):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Failed to resolve params for seed {seed}.")
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, doodad, task) combos:\n")
        for animal, doodad, task in combos:
            print(f"  {animal:8} {doodad:8} {task}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.task} with {p.doodad} ({p.animal}, team={p.team_size})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
