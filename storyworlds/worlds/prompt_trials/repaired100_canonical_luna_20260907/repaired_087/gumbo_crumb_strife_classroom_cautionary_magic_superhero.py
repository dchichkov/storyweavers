#!/usr/bin/env python3
"""
A tiny classroom superhero world about gumbo, a crumb, and a cautionary bit of magic.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_here = os.path.dirname(os.path.abspath(__file__))
_root = _here
while _root and not os.path.exists(os.path.join(_root, "results.py")):
    parent = os.path.dirname(_root)
    if parent == _root:
        break
    _root = parent
sys.path.insert(0, _root)

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    affords: set[str]


@dataclass(frozen=True)
class Power:
    id: str
    name: str
    danger: str
    safe_use: str


@dataclass(frozen=True)
class Relic:
    id: str
    label: str
    magic: str


@dataclass
class Hero:
    name: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    hero: Hero
    power: Power
    relic: Relic
    crumb: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom",
        affords={"magic", "gumbo"},
    ),
}

POWERS = {
    "crumb_shield": Power(
        id="crumb_shield",
        name="Crumb Shield",
        danger="a hidden crumb can make a spell sputter and send a surprise puff across the room",
        safe_use="clear the desk, name the spell aloud, and point the wand away from classmates",
    ),
    "gumbo_glow": Power(
        id="gumbo_glow",
        name="Gumbo Glow",
        danger="a hungry glow can warm a bowl too quickly and splash the gumbo",
        safe_use="place the bowl on the tray and use one small glow at a time",
    ),
}

RELICS = {
    "blue_wand": Relic(
        id="blue_wand",
        label="the blue star wand",
        magic="a careful blue spark",
    ),
    "brass_badge": Relic(
        id="brass_badge",
        label="the brass hero badge",
        magic="a steady golden beam",
    ),
}

HERO_NAMES = ["Luna", "Mira", "Theo", "Jax"]
MENTOR_NAMES = ["Captain Vale", "Ms. Ember", "Professor Kite"]
CRUMBS = ["a cracker crumb", "a corn crumb", "a tiny bread crumb"]

INCIDENTS = [
    {
        "title": "the gumbo crumb",
        "setup": "At lunchtime, a single cracker crumb hid beside a bowl of warm gumbo on the demonstration table.",
        "clue": "When Luna tapped the desk, the crumb trembled and made a faint blue spark.",
        "strife": "The crumb was small, but it could turn a magic lesson into a sticky, startling mess.",
        "mentor": "A hero checks the little dangers before showing off the big power.",
        "resolution": "Luna swept the crumb into a bin, moved the gumbo onto a tray, and practiced with the wand aimed at the empty chalkboard.",
        "ending": "The gumbo stayed in its bowl, and the cleaned desk shone like a quiet shield.",
        "lesson": "Small problems deserve brave attention before they become large trouble.",
    },
    {
        "title": "the bubbling gumbo",
        "setup": "A pot of gumbo bubbled beside the class's magic supplies while everyone prepared a pretend rescue.",
        "clue": "A spoon rattled whenever the wand came too close to the pot.",
        "strife": "One careless spark could make the gumbo leap over the table and spoil the lesson.",
        "mentor": "Magic is not a shortcut around ordinary care.",
        "resolution": "Luna turned off the practice spell, asked for a cloth, and carried the pot to the marked food table before trying again.",
        "ending": "The final golden spark rested on the chalkboard while the gumbo cooled safely under its lid.",
        "lesson": "A true superhero protects people and their surroundings, not just the applause.",
    },
    {
        "title": "the crumb-sized warning",
        "setup": "A crumb lay under Luna's workbook, exactly where her magic notes said to draw a glowing circle.",
        "clue": "The circle broke whenever the chalk touched the crumb's edge.",
        "strife": "The broken circle made the spell wobble, and the class began to argue about whose fault it was.",
        "mentor": "Strife grows when nobody pauses to inspect the simple cause.",
        "resolution": "Luna stopped the argument, lifted the workbook, removed the crumb, and invited each classmate to check the circle together.",
        "ending": "The circle became smooth, and the whole class cheered when its gentle light filled the room.",
        "lesson": "Careful noticing can turn quarrelsome strife into teamwork.",
    },
]

OPENINGS = [
    "Luna wore her paper cape on the day the classroom needed a superhero.",
    "The classroom bell rang, and Luna's blue star wand began to hum.",
    "Everyone expected a simple gumbo science lesson until Luna spotted something tiny.",
    "Luna had promised to show one safe magic trick before lunch.",
]


@dataclass
class StoryParams:
    setting: str = "classroom"
    power: str = "crumb_shield"
    relic: str = "blue_wand"
    name: str = "Luna"
    mentor: str = "Captain Vale"
    crumb: str = "a cracker crumb"
    seed: Optional[int] = None


def reasonability_gate(setting: Setting, power: Power, relic: Relic) -> bool:
    if setting.id != "classroom":
        return False
    if "magic" not in setting.affords:
        return False
    if not power.id or not relic.id:
        return False
    return True


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.power not in POWERS:
        raise StoryError(f"Unknown power: {params.power}")
    if params.relic not in RELICS:
        raise StoryError(f"Unknown relic: {params.relic}")
    if not params.name.strip():
        raise StoryError("Hero name must not be empty")

    setting = SETTINGS[params.setting]
    power = POWERS[params.power]
    relic = RELICS[params.relic]
    if not reasonability_gate(setting, power, relic):
        raise StoryError("That classroom magic combination is not reasonable")

    hero = Hero(params.name)
    world = World(setting, hero, power, relic, params.crumb)
    number = params.seed if params.seed is not None else 0
    incident = INCIDENTS[number % len(INCIDENTS)]
    opening = OPENINGS[(number // len(INCIDENTS)) % len(OPENINGS)]

    world.say(opening)
    world.say(
        f"{hero.name}, the classroom's newest superhero, carried {relic.label} "
        f"while {params.mentor} prepared a bowl of gumbo for the magic lesson."
    )
    world.say(
        f"The plan was simple: use {power.name} to make {relic.magic} glow above the chalkboard."
    )
    world.say(f"Then came {incident['title']}. {incident['setup']}")

    world.para()
    world.say(f"{incident['strife']} {power.danger.capitalize()}.")
    world.say(f'"I can fix this with one fast spell," Luna said.')
    world.say(
        f'"First tell us what you see," {params.mentor} replied. '
        f'"A superhero uses courage and caution together."'
    )
    world.say(f"{incident['clue']}")
    world.say(f'"The {params.crumb} is part of the trouble," {hero.name} said.')
    world.say(f'"And the strife will stop if we solve the cause, not blame a person," {params.mentor} said.')

    world.para()
    world.say(f"{hero.name} followed the safe plan: {power.safe_use}.")
    world.say(incident["resolution"])
    world.say(
        f"Only then did {hero.name} lift {relic.label}, breathe slowly, and send "
        f"{relic.magic} toward the chalkboard."
    )

    world.para()
    world.say(
        f"The spell worked. The class watched the light curl into a bright superhero star, "
        f"while the gumbo stayed safely on its tray."
    )
    world.say(incident["ending"])
    world.say(f"The cautionary magic lesson was clear: {incident['lesson']}")

    hero.meters["mess_risk"] = 0.0
    hero.meters["attention"] = 1.0
    hero.memes["courage"] = 1.0
    hero.memes["cooperation"] = 1.0
    world.facts.update(
        hero=hero,
        mentor=params.mentor,
        incident=incident,
        setting=setting,
        power=power,
        relic=relic,
        crumb=params.crumb,
        resolved=True,
        gumbo_safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a cautionary superhero story set in {f['setting'].place} about {f['hero'].name}, gumbo, and {f['crumb']}.",
        f"Show how {f['hero'].name} uses {f['power'].name} safely after noticing this clue: {f['incident']['clue']}",
        f"Tell a magic classroom story where strife changes into teamwork and ends with: {f['incident']['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    incident = f["incident"]
    return [
        QAItem(
            "Who was the classroom superhero?",
            f"{hero.name} was the classroom superhero who carried {f['relic'].label}.",
        ),
        QAItem(
            "What caused the trouble?",
            f"The trouble began when {f['crumb']} interfered with the gumbo lesson and the magic practice.",
        ),
        QAItem(
            "What clue did the hero notice?",
            incident["clue"],
        ),
        QAItem(
            "How did the hero resolve the strife?",
            incident["resolution"],
        ),
        QAItem(
            "What did the cautionary magic lesson teach?",
            f"It taught that {incident['lesson'].lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gumbo?",
            "Gumbo is a hearty stew, often made with vegetables and other ingredients, served warm in a bowl.",
        ),
        QAItem(
            "Why can a crumb matter in a classroom?",
            "A crumb can attract pests, make a desk dirty, or interfere with an activity, so cleaning it helps keep the room ready.",
        ),
        QAItem(
            "What does strife mean?",
            "Strife means angry disagreement or struggle between people, and careful listening can help turn it into cooperation.",
        ),
        QAItem(
            "What makes magic cautionary in a story?",
            "Cautionary magic has consequences when it is used carelessly, so characters must think, check risks, and act responsibly.",
        ),
    ]


ASP_RULES = r"""
safe_combo(S,P,R) :- setting(S), affords(S,magic), power(P), relic(R), compatible(P,R).
classroom_ready(S,P,R) :- safe_combo(S,P,R), clear_before_magic, gumbo_present.
#show classroom_ready/3.
"""


def asp_facts() -> str:
    from asp import fact

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(fact("setting", sid))
        for affordance in sorted(setting.affords):
            lines.append(fact("affords", sid, affordance))
    for pid in POWERS:
        lines.append(fact("power", pid))
    for rid in RELICS:
        lines.append(fact("relic", rid))
    for pid, rid in [
        ("crumb_shield", "blue_wand"),
        ("gumbo_glow", "brass_badge"),
    ]:
        lines.append(fact("compatible", pid, rid))
    lines.extend(["clear_before_magic.", "gumbo_present."])
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def valid_combos() -> set[tuple[str, str, str]]:
    return {
        (setting_id, power_id, relic_id)
        for setting_id, setting in SETTINGS.items()
        for power_id, power in POWERS.items()
        for relic_id, relic in RELICS.items()
        if reasonability_gate(setting, power, relic)
        and (power_id, relic_id)
        in {("crumb_shield", "blue_wand"), ("gumbo_glow", "brass_badge")}
    }


def asp_valid_combos() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "classroom_ready"))


def asp_verify() -> int:
    try:
        actual = asp_valid_combos()
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    expected = valid_combos()
    if actual != expected:
        print("MISMATCH between Python and ASP gates")
        print("python only:", sorted(expected - actual))
        print("ASP only:", sorted(actual - expected))
        return 1
    print(f"OK: ASP/Python parity holds for {len(expected)} combo(s).")
    for params in curated_params():
        tell(params)
    print("OK: generated stories exercised.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(seed=0),
        StoryParams(power="gumbo_glow", relic="brass_badge", name="Mira", mentor="Ms. Ember", seed=1),
        StoryParams(power="crumb_shield", relic="blue_wand", name="Theo", mentor="Professor Kite", seed=2),
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    power = args.power or rng.choice(list(POWERS))
    relic = args.relic or ("blue_wand" if power == "crumb_shield" else "brass_badge")
    if args.relic and (power, relic) not in {
        ("crumb_shield", "blue_wand"),
        ("gumbo_glow", "brass_badge"),
    }:
        raise StoryError("That relic cannot safely channel the selected classroom power")
    return StoryParams(
        setting=args.setting or "classroom",
        power=power,
        relic=relic,
        name=args.name or rng.choice(HERO_NAMES),
        mentor=args.mentor or rng.choice(MENTOR_NAMES),
        crumb=args.crumb or rng.choice(CRUMBS),
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"  setting: {world.setting.place}",
            f"  hero: {world.hero.name}",
            f"  power: {world.power.name}",
            f"  relic: {world.relic.label}",
            f"  crumb: {world.crumb}",
            f"  meters: {world.hero.meters}",
            f"  memes: {world.hero.memes}",
            "  gumbo_safe: True",
            "  resolved: True",
        ]
    )


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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary magic superhero storyworld about gumbo, crumbs, and classroom strife."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--relic", choices=RELICS)
    parser.add_argument("--name", choices=HERO_NAMES)
    parser.add_argument("--mentor", choices=MENTOR_NAMES)
    parser.add_argument("--crumb", choices=CRUMBS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp

            model = asp.one_model(asp_program())
            for combo in sorted(asp.atoms(model, "classroom_ready")):
                print(combo)
        except ImportError:
            raise StoryError("ASP mode requires clingo to be installed")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []

    if args.all:
        samples = [generate(p) for p in curated_params()]
    else:
        for offset in range(max(args.n, 1)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
