#!/usr/bin/env python3
"""A heartwarming parade story about a sailor, infantry friends, and a kind twist."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Parade:
    name: str
    route: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Twist:
    hidden_plan: str
    reveal: str
    kindness: str
    resolved: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    parade_name: str = "the Harbor Lights Parade"
    sailor_name: str = "Mara"
    sailor_species: str = "sailor"
    infantry_name: str = "Jonah"
    infantry_species: str = "infantry drummer"
    route: str = "harbor"
    twist: str = "lantern_surprise"
    opening: str = "morning"


@dataclass(frozen=True)
class TwistCase:
    worry: str
    first_plan: str
    obstacle: str
    clue: str
    reveal: str
    action: str
    kindness: str
    lesson: str
    ending: str


@dataclass
class World:
    parade: Parade
    sailor: Person
    infantry: Person
    twist: Twist
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PARADES = {
    "the Harbor Lights Parade": Parade(
        name="the Harbor Lights Parade",
        route="from the pier to the old clock tower",
    ),
    "the River Ribbon Parade": Parade(
        name="the River Ribbon Parade",
        route="from the ferry steps to the riverside square",
    ),
    "the Sunrise Parade": Parade(
        name="the Sunrise Parade",
        route="from the market gate to the hilltop garden",
    ),
}

SAILORS = [
    ("Mara", "sailor"),
    ("Tessa", "sailor"),
    ("Niko", "sailor"),
]

INFANTRY = [
    ("Jonah", "infantry drummer"),
    ("Amir", "infantry guide"),
    ("Lena", "infantry flag bearer"),
]

TWISTS = {
    "lantern_surprise": TwistCase(
        "the parade's smallest lanterns had not arrived",
        "borrowed lanterns from the harbor office",
        "a crate marked for the children's rest tent had been set aside",
        "a blue ribbon tied to the missing crate matched the rest tent's banner",
        "the lanterns were being saved for a quiet surprise at the rest tent",
        "followed the safe route with the infantry while checking each crate label",
        "helped carry the lanterns to children who could not walk the whole parade route",
        "a celebration shines brightest when it includes people who cannot reach the loudest street",
        "little lanterns glowed around the rest tent while the parade waved from the road",
    ),
    "silent_drum": TwistCase(
        "the infantry drum had gone quiet before the parade",
        "tightened every drum cord in a hurry",
        "one cord kept slipping because it had been tied around a wet handle",
        "a row of dry salt marks led from the drum to the harbor awning",
        "the drum had been sheltered from rain by a child who feared its skin would tear",
        "thanked the child and dried the handle before retuning the drum",
        "invited the child to tap the opening beat with a small practice drum",
        "care can look like a delay until its loving reason is heard",
        "the first drumbeat welcomed the child who had protected it",
    ),
    "lost_flag": TwistCase(
        "the infantry flag was missing from its polished pole",
        "searched the parade square and the band cart",
        "the pole's empty clasp still held a thread of gold cloth",
        "gold threads circled the door of the nearby community kitchen",
        "the flag had been used as a warm cover for a tired cook's sleeping baby",
        "asked permission before lifting the cloth and carried the baby inside",
        "made a new flag from spare sailcloth and stitched the gold thread into its edge",
        "a symbol of welcome should first welcome the person who needs shelter",
        "the new sailcloth flag flew beside the kitchen while the baby slept safely inside",
    ),
    "rainy_route": TwistCase(
        "rain threatened to wash out the parade route",
        "planned to hurry the march beneath the gray clouds",
        "the harbor stones grew too slick for a safe turn",
        "chalk arrows pointed toward a covered ferry shed",
        "the dock workers had prepared the shed as a dry parade lane",
        "moved the marchers slowly and checked the floor with the infantry",
        "turned the shed into a close, gentle parade for families waiting out the rain",
        "changing the route can preserve the joy instead of ending it",
        "rain drummed overhead while bright flags curled through the warm ferry shed",
    ),
    "empty_chair": TwistCase(
        "one decorated chair at the parade front was empty",
        "left it as a sad reminder of an absent guest",
        "a folded map beneath the chair named the harbor clinic",
        "the chair belonged to an injured bridge worker who was watching from a window",
        "the guest could not reach the parade, so the parade needed to reach the guest",
        "walked the sailor and infantry banners to the clinic courtyard",
        "let the worker lead the final salute from the window",
        "honor is an action, not only a place saved in a row",
        "the empty chair held a folded flag while its honored guest smiled from above",
    ),
}

ROUTES = ("harbor", "river", "market")
OPENINGS = ("morning", "before_music", "after_rain", "quiet_start", "question")


ASP_RULES = r"""
ready(P) :- parade(P), sailor(S), infantry(I), safe_route(P), includes(S,P), includes(I,P).
kind_twist(T) :- twist(T), helps_people(T), shared_joy(T).
valid_story(P,T) :- parade(P), twist(T), ready(P), kind_twist(T).
"""


def twist_id(name: str) -> str:
    return "twist_" + "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("parade", "parade"),
        asp.fact("sailor", "sailor"),
        asp.fact("infantry", "infantry"),
        asp.fact("safe_route", "parade"),
        asp.fact("includes", "sailor", "parade"),
        asp.fact("includes", "infantry", "parade"),
    ]
    for name, case in TWISTS.items():
        tid = twist_id(name)
        lines.extend((
            asp.fact("twist", tid),
            asp.fact("helps_people", tid),
            asp.fact("shared_joy", tid),
        ))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show kind_twist/1."))
    actual = set(asp.atoms(model, "kind_twist"))
    expected = {(twist_id(name),) for name in TWISTS}
    if actual == expected:
        print(f"OK: clingo gate matches python reasoning ({len(expected)} twists).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(actual))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.parade_name, params.sailor_name, params.sailor_species,
        params.infantry_name, params.infantry_species, params.route,
        params.twist, params.opening,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.parade_name not in PARADES:
        raise StoryError(f"Unknown parade: {params.parade_name}")
    if params.twist not in TWISTS:
        raise StoryError(f"Unknown twist: {params.twist}")
    parade = PARADES[params.parade_name]
    case = TWISTS[params.twist]
    return World(
        parade=Parade(name=parade.name, route=parade.route),
        sailor=Person(name=params.sailor_name, role=params.sailor_species),
        infantry=Person(name=params.infantry_name, role=params.infantry_species),
        twist=Twist(
            hidden_plan=case.reveal,
            reveal=case.reveal,
            kindness=case.kindness,
        ),
    )


def tell_story(world: World, params: StoryParams) -> None:
    sailor = world.sailor
    infantry = world.infantry
    parade = world.parade
    case = TWISTS[params.twist]
    rng = story_rng(params)

    sailor.memes.update(courage=0.0, care=1.0)
    infantry.memes.update(patience=1.0, welcome=1.0)
    parade.meters["route_length"] = float(len(parade.route))
    parade.meters["people_included"] = 0.0

    openings = {
        "morning": (
            f"At morning light, {sailor.name} the sailor polished a lantern beside "
            f"{parade.name}. The march would travel {parade.route}, but {case.worry}."
        ),
        "before_music": (
            f"Before the music began, {infantry.name}, the infantry drummer, checked "
            f"the flags at {parade.name}. Then everyone discovered that {case.worry}."
        ),
        "after_rain": (
            f"After a night of rain, {parade.name} smelled of wet rope and clean stone. "
            f"{sailor.name} saw that {case.worry}."
        ),
        "quiet_start": (
            f"The harbor was unusually quiet before {parade.name}. {infantry.name} "
            f"held the first flag and whispered that {case.worry}."
        ),
        "question": (
            f'"How can our parade welcome everyone if {case.worry}?" asked '
            f"{sailor.name} beside the waiting flags."
        ),
    }
    world.say(openings[params.opening])
    world.say(rng.choice([
        f'"We can hurry and pretend nothing is wrong," {infantry.name} said.',
        f'"Let us check before we choose," {infantry.name} replied.',
        f'{infantry.name} touched the drum gently. "A parade is for people, not just for perfect plans."',
    ]))
    world.say(
        f'"Then we will look carefully," {sailor.name} answered. '
        f'"We are sailors and infantry, but today we are also neighbors."'
    )

    world.para()
    world.say(f"First, they {case.first_plan}.")
    world.say(rng.choice([
        f"It seemed sensible, but it met a problem: {case.obstacle}.",
        f"The plan did not work because {case.obstacle}.",
        f"Then their careful check showed that {case.obstacle}.",
    ]))
    world.say(
        f"Instead of blaming anyone, {sailor.name} followed a small clue: {case.clue}."
    )
    world.say(
        f'The twist warmed the whole plan. {case.reveal.capitalize()}. '
        f'"We thought we were preparing a parade," {infantry.name} said. '
        f'"Perhaps the parade is preparing us to notice someone."'
    )

    world.para()
    world.say(f"{sailor.name} {case.action}.")
    sailor.memes["courage"] = 1.0
    world.say(
        f"The sailor and the infantry worked together. {case.kindness.capitalize()}."
    )
    world.say(
        rng.choice([
            f'"May we join you?" {sailor.name} asked.',
            f'"Will you lead the welcome?" {infantry.name} asked.',
            f'"No one should watch alone," they promised.',
        ])
    )
    world.say(
        f'"Yes," came the happy answer. "Now the parade feels like ours, too."'
    )
    world.twist.resolved = True
    infantry.memes["joy"] = 1.0
    parade.meters["people_included"] = 1.0

    world.para()
    world.say(
        rng.choice([
            f"They remembered the lesson: {case.lesson}.",
            f"{infantry.name} wrote the lesson on the parade board: {case.lesson.capitalize()}.",
            f'"What changed?" asked {sailor.name}. {infantry.name} smiled. '
            f'"{case.lesson.capitalize()}."',
        ])
    )
    world.say(
        f"At last, {case.ending.capitalize()}. The parade moved on, slower than planned "
        f"and warmer than anyone had expected."
    )

    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        twist=world.twist,
        case=case,
        reveal=case.reveal,
        action=case.action,
        kindness=case.kindness,
        lesson=case.lesson,
        ending=case.ending,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    return [
        f"Write a heartwarming parade story about {f['sailor'].name}, a sailor, and {f['infantry'].name}, an infantry drummer.",
        f"Build a gentle twist in which {case.reveal}.",
        f"End with this image: {case.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case = f["case"]
    sailor = f["sailor"]
    infantry = f["infantry"]
    parade = f["parade"]
    return [
        QAItem(
            question=f"What problem did {sailor.name} and {infantry.name} face before {parade.name}?",
            answer=f"They faced this problem: {case.worry.capitalize()}.",
        ),
        QAItem(
            question="What did their first plan teach them?",
            answer=f"The first plan met an obstacle because {case.obstacle}. That made them check the situation instead of rushing.",
        ),
        QAItem(
            question="What was the surprising twist?",
            answer=f"The twist was that {case.reveal}. The missing or changed parade piece had a caring purpose.",
        ),
        QAItem(
            question=f"How did the sailor and infantry make the celebration kinder?",
            answer=f"They {case.action} Then they {case.kindness}.",
        ),
        QAItem(
            question="What lesson did the parade teach?",
            answer=f"It taught that {case.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or around boats and learns to care for people, equipment, and the water.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are people who travel and work together on foot as part of a ground unit.",
        ),
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized celebration in which people move together while sharing music, colors, or symbols.",
        ),
        QAItem(
            question="Why can changing a parade plan be kind?",
            answer="Changing the plan can make room for safety, accessibility, or people who need the celebration to come closer to them.",
        ),
        QAItem(
            question="What makes a twist heartwarming?",
            answer="A heartwarming twist reveals that an unexpected problem was connected to care, generosity, or a thoughtful welcome.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming parade story with a sailor, infantry, and a kind twist."
    )
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--parade", choices=sorted(PARADES))
    ap.add_argument("--sailor-name")
    ap.add_argument("--infantry-name")
    ap.add_argument("--twist", choices=sorted(TWISTS))
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    parade_name = args.parade or rng.choice(sorted(PARADES))
    sailor_name, sailor_species = rng.choice(SAILORS)
    infantry_name, infantry_species = rng.choice(INFANTRY)
    twist = args.twist or rng.choice(sorted(TWISTS))
    return StoryParams(
        seed=args.seed,
        parade_name=parade_name,
        sailor_name=args.sailor_name or sailor_name,
        sailor_species=sailor_species,
        infantry_name=args.infantry_name or infantry_name,
        infantry_species=infantry_species,
        route=rng.choice(ROUTES),
        twist=twist,
        opening=rng.choice(OPENINGS),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for person in (world.sailor, world.infantry):
        lines.append(
            f"{person.name}: role={person.role!r} meters={person.meters} memes={person.memes}"
        )
    lines.append(
        f"parade: name={world.parade.name!r} route={world.parade.route!r} "
        f"meters={world.parade.meters}"
    )
    lines.append(
        f"twist: reveal={world.twist.reveal!r} kindness={world.twist.kindness!r} "
        f"resolved={world.twist.resolved}"
    )
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show kind_twist/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show kind_twist/1."))
        print(sorted(set(asp.atoms(model, "kind_twist"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
