#!/usr/bin/env python3
"""
A gentle cautionary fairy tale about hardening a stale, unsafe rule.

The word "sexual" appears only as an adult-facing domain label in the
parameters and world model; the child-facing tale uses clear, age-appropriate
language about safety, consent, and asking a trusted adult for help.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    location: str = ""


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    companion: str
    setting: str = "the moonlit village"
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Tavi", "Nell", "Pip", "Orin", "Suri", "Bram"]
SETTINGS = [
    "the moonlit village",
    "the silverwood edge",
    "the old hill kingdom",
]


@dataclass(frozen=True)
class Caution:
    title: str
    stale_rule: str
    danger: str
    companion_line: str
    safe_action: str
    lesson: str
    ending: str


CAUTIONS = (
    Caution(
        "the locked gate",
        "The gatekeeper followed a stale rule: a visitor must never question the iron gate.",
        "But the lock had rusted shut, and a frightened child was calling from the other side.",
        '"A rule should protect people, not silence them," {companion} said.',
        "{name} found the village bell, called the trusted keeper, and waited safely in the open square while the gate was repaired.",
        "Old rules deserve careful checking when the world has changed.",
        "By dawn, the gate carried a new sign: Ask, listen, and make the safe way clear.",
    ),
    Caution(
        "the whispering well",
        "The palace rule said that anyone who heard the well whisper must keep the secret forever.",
        "One evening, the well whispered that its stones were loose beneath a little bridge.",
        '"A secret about danger must be shared with a trusted grown-up," {companion} said.',
        "{name} stepped back, warned the miller, and helped place bright lanterns around the well until masons made it firm.",
        "Keeping people safe matters more than obeying a secret rule.",
        "The well sang clean water again, while a lantern shone beside a fresh sign: Tell someone when danger whispers.",
    ),
    Caution(
        "the thorn crown",
        "A stale court custom claimed that every royal crown must be worn whenever the bell rang.",
        "The thorn crown had grown sharp, and the bell began ringing during a storm.",
        '"No crown is worth a hurt head," {companion} said. "We can ask the queen for a safer custom."',
        "{name} set the crown on a velvet cushion, moved away from the thorns, and called the queen before the ceremony.",
        "A custom should bend when it causes harm, especially when a safer choice is plain.",
        "The queen replaced the thorn crown with a soft wreath, and the bells rang for kindness instead of danger.",
    ),
    Caution(
        "the dragon door",
        "The castle door bore a stale command: Never say no to a dragon who asks for entry.",
        "A hungry dragon arrived and demanded to enter the nursery, though nobody knew it.",
        '"Everyone may say no to an unsafe request," {companion} said firmly.',
        "{name} closed the inner door, spoke through the window with a trusted guard nearby, and invited the dragon to the warm stable instead.",
        "A clear no is a strong shield, and asking for help makes the shield stronger.",
        "The nursery stayed safe, while the dragon slept peacefully in the stable beneath a friendly lantern.",
    ),
)


OPENINGS = (
    "Once, beneath a pale moon, {name} lived in {setting}.",
    "In the oldest corner of {setting}, {name} kept a little silver lantern.",
    "Long ago, when the stars wore bright crowns, {name} walked carefully through {setting}.",
    "At the edge of {setting}, {name} listened to every bell, bird, and broom.",
)

REALIZATIONS = (
    "{name} had thought a rule was strong because it was old, but now understood that safety needed thought as well as courage.",
    "The lesson glittered like a coin in the moonlight: rules should guard the living, not trap them in yesterday.",
    "{name} saw that hardening a stale rule would only make a bad path harder to leave.",
)

THANKS = (
    '"Thank you for speaking clearly," {name} said. "I will ask for help and choose the safe path."',
    '"You helped me notice what the old rule missed," {name} said. "Thank you for staying beside me."',
    '"I am glad you told me," {name} said. "No one should face a danger alone."',
)


def _choose(params: StoryParams) -> tuple[Caution, str, str, str]:
    seed = params.seed or 0
    count = len(CAUTIONS)
    caution = CAUTIONS[seed % count]
    opening = OPENINGS[(seed // count) % len(OPENINGS)]
    realization = REALIZATIONS[(seed // (count * len(OPENINGS))) % len(REALIZATIONS)]
    thanks = THANKS[(seed // (count * len(OPENINGS) * len(REALIZATIONS))) % len(THANKS)]
    return caution, opening, realization, thanks


def build_world(params: StoryParams) -> World:
    if params.name == params.companion:
        raise StoryError("The hero and companion must have different names.")
    if not params.setting:
        raise StoryError("A fairy tale needs a setting.")

    world = World()
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="child",
            label="careful traveler",
            traits=["curious", "brave"],
            meters={"alertness": 1.0, "safety": 0.5},
            memes={"worry": 0.2, "courage": 0.8},
            location=params.setting,
        )
    )
    companion = world.add(
        Entity(
            id=params.companion,
            kind="character",
            type="companion",
            label="trusted companion",
            traits=["honest", "kind"],
            meters={"alertness": 1.0, "safety": 0.8},
            memes={"care": 1.0, "trust": 1.0},
            location=params.setting,
        )
    )
    rule = world.add(
        Entity(
            id="stale_rule",
            kind="thing",
            type="rule",
            label="stale rule",
            traits=["old", "unexamined", "unsafe"],
            meters={"freshness": 0.1, "flexibility": 0.1},
            memes={"authority": 1.0},
            location=params.setting,
        )
    )
    world.facts["sexual_domain_label"] = "sexual safety"
    world.facts["harden_word"] = "harden"
    world.facts["stale_word"] = "stale"
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["rule"] = rule

    caution, opening, realization, thanks = _choose(params)
    values = {
        "name": params.name,
        "companion": params.companion,
        "setting": params.setting,
    }

    world.say(opening.format(**values))
    world.say(
        f"{params.name} was careful with every promise, but even a careful heart can meet a stale rule."
    )
    world.para()
    world.say(caution.stale_rule)
    world.say(caution.danger)
    hero.memes["worry"] += 0.8
    rule.meters["freshness"] = 0.0
    world.say(caution.companion_line.format(**values))
    world.para()
    world.say(realization)
    world.say(thanks.format(**values))
    world.say(caution.safe_action.format(**values))
    hero.memes["courage"] += 0.8
    hero.memes["trust"] = 1.0
    hero.meters["safety"] = 1.0
    rule.meters["flexibility"] = 1.0
    world.para()
    world.say(caution.lesson)
    world.say(
        "In the kingdom's book of protections, the wise elders wrote that every person may set a boundary, say no, and tell a trusted adult when something feels unsafe."
    )
    world.say(caution.ending.format(**values))

    world.facts.update(
        caution=caution,
        danger=caution.danger,
        companion_line=caution.companion_line.format(**values),
        safe_action=caution.safe_action.format(**values),
        lesson=caution.lesson,
        ending=caution.ending.format(**values),
        setting=params.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    caution: Caution = world.facts["caution"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly cautionary fairy tale about {hero.id} and {companion.id} questioning a stale rule.",
        f"Tell a gentle story in {world.facts['setting']} where a character learns not to harden an unsafe rule.",
        f"Create a fairy tale about safety, clear boundaries, trusted help, and the lesson in {caution.title}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {hero.id}, a careful traveler, and {companion.id}, a trusted companion who speaks honestly about safety.",
        ),
        QAItem(
            question="What was wrong with the old rule?",
            answer=str(world.facts["danger"]),
        ),
        QAItem(
            question=f"How did {companion.id} help?",
            answer=f"{companion.id} explained that an old rule should not silence questions about danger. {world.facts['companion_line']}",
        ),
        QAItem(
            question="What did the characters do to become safe?",
            answer=f"They did not harden the stale rule. They stepped away from danger, asked a trusted helper for support, and followed a safer plan. {world.facts['safe_action']}",
        ),
        QAItem(
            question="What lesson did the fairy tale teach?",
            answer=str(world.facts["lesson"]),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boundary?",
            answer="A boundary is a clear limit about what feels safe and acceptable to a person. Everyone may set a boundary and ask others to respect it.",
        ),
        QAItem(
            question="What should someone do when a situation feels unsafe?",
            answer="They should move away if they can, say no clearly, and tell a trusted adult or helper. They do not have to keep an unsafe secret.",
        ),
        QAItem(
            question="Why should old rules be checked?",
            answer="Old rules may have been made for a different situation. Checking them helps people keep the useful parts and change anything that could cause harm.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fairy tale about questioning stale rules.")
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--setting", choices=SETTINGS)
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
    name = args.name or rng.choice(NAMES)
    choices = [n for n in NAMES if n != name]
    companion = args.companion or rng.choice(choices)
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(name=name, companion=companion, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:14} ({entity.type:10}) "
            f"location={entity.location!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  domain_label   {world.facts.get('sexual_domain_label')!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
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


ASP_RULES = r"""
setting(moonlit_village).
setting(silverwood_edge).
setting(old_hill_kingdom).

rule(stale_rule).
character(hero).
character(companion).
danger(stale_rule).
trusted_help(companion).
safe_plan :- danger(stale_rule), trusted_help(companion).
protected :- safe_plan.
#show protected/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting in SETTINGS:
        constant = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", constant))
    lines.extend(
        [
            asp.fact("rule", "stale_rule"),
            asp.fact("character", "hero"),
            asp.fact("character", "companion"),
            asp.fact("danger", "stale_rule"),
            asp.fact("trusted_help", "companion"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show protected/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    try:
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1
    protected = any(symbol.name == "protected" for symbol in model)
    if not protected:
        print("ASP verification failed: protected state was not derived.")
        return 1
    for seed in range(8):
        params = StoryParams(
            name=NAMES[seed % len(NAMES)],
            companion=NAMES[(seed + 1) % len(NAMES)],
            setting=SETTINGS[seed % len(SETTINGS)],
            seed=seed,
        )
        sample = generate(params)
        if "trusted adult" not in sample.story or "unsafe" not in sample.story:
            print("Python story verification failed.")
            return 1
    print("OK: ASP/Python safety parity verified.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(CAUTIONS)):
            params = StoryParams(
                name=NAMES[index % len(NAMES)],
                companion=NAMES[(index + 1) % len(NAMES)],
                setting=SETTINGS[index % len(SETTINGS)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
