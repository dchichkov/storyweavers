#!/usr/bin/env python3
"""
A tiny superhero storyworld about Harry, Blob, and Sixer.

The world models a misunderstanding, a lesson learned, and a reconciliation.
Harry is brave but hasty, Blob is a gentle shape-shifting helper, and Sixer is
a small rescue robot whose numbered signals are easy to misread.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    danger: str
    landmark: str


@dataclass(frozen=True)
class Power:
    id: str
    label: str
    method: str
    limit: str


@dataclass(frozen=True)
class Mission:
    id: str
    title: str
    threat: str
    clue: str
    safe_plan: str
    ending: str


@dataclass
class Hero:
    id: str
    label: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: Setting
    hero: Hero
    blob: Hero
    sixer: Hero
    power: Power
    mission: Mission
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
    "skybridge": Setting(
        "skybridge",
        "the Skybridge",
        "a storm of loose signs and flashing wires",
        "the silver bell tower",
    ),
    "moonpark": Setting(
        "moonpark",
        "Moon Park",
        "a runaway moon-balloon",
        "the old observatory",
    ),
    "harbor": Setting(
        "harbor",
        "Star Harbor",
        "a rising tide around the rescue docks",
        "the lighthouse",
    ),
}

POWERS = {
    "shield": Power(
        "shield",
        "a bright shield",
        "raising a careful wall of light",
        "the shield becomes weak when Harry acts without listening",
    ),
    "leap": Power(
        "leap",
        "a sky-leap",
        "springing over danger in one shining bound",
        "the leap cannot carry someone safely through a blocked path",
    ),
}

MISSIONS = {
    "signals": Mission(
        "signals",
        "The Six Signal",
        "Sixer's red number six began blinking beside a trapped delivery cart.",
        "Sixer pointed at the cart, then blinked six times to show how many wheels were caught.",
        "Harry would listen to Sixer's full signal, Blob would cushion the cart, and Harry would lift the loose signs away.",
        "The cart rolled free, and Sixer's red light changed to a calm blue six.",
    ),
    "balloon": Mission(
        "balloon",
        "The Moon-Balloon Mix-Up",
        "A moon-balloon tugged at its rope while Sixer flashed a warning from below.",
        "Sixer's arrows pointed toward the knot, not toward the balloon's basket.",
        "Blob would hold the rope, Harry would make a shield from the wind, and the team would untie the knot together.",
        "The balloon floated gently above the park, tied to a safe post.",
    ),
    "tide": Mission(
        "tide",
        "The Rising Dock",
        "Water curled around a crate while Sixer sent a rapid rescue signal.",
        "The fastest blinking light marked the crate, while the slower light marked a safe walkway.",
        "Harry would follow the walkway signal, Blob would become a bridge, and Sixer would guide the workers.",
        "The crate reached dry ground, and the lighthouse beam swept over the quiet dock.",
    ),
}

HARRY_NAMES = ["Harry", "Harry Blaze", "Harry Star"]
BLOB_NAMES = ["Blob", "Blue Blob", "Blob Bright"]
SIXER_NAMES = ["Sixer", "Sixer Six", "Little Sixer"]

CURATED = [
    ("skybridge", "shield", "signals", "Harry", "Blob", "Sixer"),
    ("moonpark", "leap", "balloon", "Harry Blaze", "Blue Blob", "Sixer Six"),
    ("harbor", "shield", "tide", "Harry Star", "Blob Bright", "Little Sixer"),
]


@dataclass
class StoryParams:
    setting: str
    power: str
    mission: str
    harry: str
    blob: str
    sixer: str
    seed: Optional[int] = None


def reasonability_gate(setting: Setting, power: Power, mission: Mission) -> bool:
    return bool(setting.place and power.method and mission.safe_plan)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    power = POWERS[params.power]
    mission = MISSIONS[params.mission]
    if not reasonability_gate(setting, power, mission):
        raise StoryError("The selected setting, power, and mission do not form a workable superhero story.")

    harry = Hero(params.harry, params.harry, "hero", memes={"courage": 1.0, "patience": 0.0})
    blob = Hero(params.blob, params.blob, "helper", memes={"kindness": 1.0, "trust": 1.0})
    sixer = Hero(params.sixer, params.sixer, "signal robot", meters={"signals": 6.0})

    world = World(setting, harry, blob, sixer, power, mission)

    world.say(
        f"On {setting.place}, {harry.label} watched over the city with {blob.label} and {sixer.label}."
    )
    world.say(
        f"{harry.label} wore a red cape and carried {power.label}; {blob.label} could soften any fall, "
        f"and {sixer.label} could speak with numbered lights."
    )
    world.say(
        f"Then {mission.threat} appeared near {setting.landmark}. "
        f"{sixer.label} flashed a warning, but {harry.label} misunderstood the signal."
    )

    world.para()
    world.say(
        f'"Six means move now!" shouted {harry.label}, racing toward the danger.'
    )
    world.say(
        f'"Wait, Harry!" called {blob.label}. "Sixer may be telling us what to check, not telling us to rush."'
    )
    world.say(
        f'"Blink, blink, blink," answered {sixer.label}. The signal pointed to {mission.clue.lower()}'
    )
    world.say(
        f"{harry.label} lifted the shield too soon, and the rushing air pushed {blob.label} away from the rescue path."
    )
    world.say(
        f'"You made the danger bigger because you did not listen," said {blob.label}.'
    )
    world.say(
        f'"I thought I was protecting everyone," {harry.label} replied. "I am sorry."'
    )

    world.para()
    world.say(
        f"{harry.label} took a breath and studied {sixer.label}'s lights again. "
        f"{mission.clue} The misunderstanding became clear."
    )
    world.say(
        f'"Tell me the whole plan," said {harry.label}.'
    )
    world.say(
        f'"I will show the signal, Blob will help, and you will wait for the right moment," answered {sixer.label}.'
    )
    world.say(
        f'"That is a plan I can trust," said {harry.label}.'
    )
    world.say(
        f"{mission.safe_plan}. {blob.label} returned to {harry.label}'s side, and the three friends worked as one team."
    )

    world.para()
    world.say(mission.ending)
    world.say(
        f"{harry.label} lowered the shield and held out a hand. "
        f'"I learned that being brave is not the same as being hurried," {harry.label} said.'
    )
    world.say(
        f'"And I learned that an apology can open a stuck door," said {blob.label}.'
    )
    world.say(
        f"{blob.label} hugged {harry.label}, while {sixer.label} blinked six cheerful blue lights."
    )
    world.say(
        f"The lesson learned was simple: heroes listen before they leap, and friends can repair a misunderstanding with honesty."
    )

    harry.memes["courage"] = 2.0
    harry.memes["patience"] = 1.0
    blob.memes["trust"] = 2.0
    sixer.meters["signals"] = 0.0
    sixer.memes["teamwork"] = 1.0

    world.facts.update(
        setting=setting,
        power=power,
        mission=mission,
        harry=harry,
        blob=blob,
        sixer=sixer,
        misunderstanding=True,
        reconciliation=True,
        lesson_learned=True,
        clue=mission.clue,
        safe_plan=mission.safe_plan,
        ending=mission.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['harry'].label}, {f['blob'].label}, and {f['sixer'].label} solving {f['mission'].title}.",
        f"Show a misunderstanding caused by {f['sixer'].label}'s signal and a reconciliation between {f['harry'].label} and {f['blob'].label}.",
        f"End with a lesson learned about listening before using {f['power'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    harry = f["harry"].label
    blob = f["blob"].label
    sixer = f["sixer"].label
    mission = f["mission"]
    return [
        QAItem(
            f"Who were the three heroes at {f['setting'].place}?",
            f"{harry}, {blob}, and {sixer} were the three heroes at {f['setting'].place}.",
        ),
        QAItem(
            f"What misunderstanding did {harry} have?",
            f"{harry} thought {sixer}'s signal meant to rush immediately, but the signal was giving the team a clue about what to check.",
        ),
        QAItem(
            "How did the heroes solve the problem?",
            mission.safe_plan,
        ),
        QAItem(
            f"How did {harry} and {blob} reconcile?",
            f"{harry} apologized for rushing, {blob} accepted the apology, and they returned to the rescue path as trusted teammates.",
        ),
        QAItem(
            "What lesson was learned?",
            "The heroes learned that real courage includes listening carefully, waiting for a safe plan, and repairing misunderstandings honestly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a superhero?",
            "A superhero is a character who uses courage, helpful abilities, and good choices to protect others.",
        ),
        QAItem(
            "What is a misunderstanding?",
            "A misunderstanding happens when someone interprets words or signals incorrectly and believes something different from what was meant.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a problem by speaking honestly, apologizing when needed, and rebuilding trust.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for person in (world.hero, world.blob, world.sixer):
        lines.append(
            f"  {person.id}: role={person.role} meters={person.meters} memes={person.memes}"
        )
    lines.append(
        f"  flags: misunderstanding={world.facts['misunderstanding']} "
        f"reconciliation={world.facts['reconciliation']} "
        f"lesson_learned={world.facts['lesson_learned']}"
    )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
signal_conflict :- misunderstanding.
fixed :- reconciliation, lesson_learned.
valid(S, P, M) :- setting(S), power(P), mission(M), safe_plan(M), fixed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in POWERS:
        lines.append(asp.fact("power", key))
    for key, mission in MISSIONS.items():
        lines.append(asp.fact("mission", key))
        lines.append(asp.fact("safe_plan", key))
    lines.extend(
        [
            asp.fact("misunderstanding"),
            asp.fact("reconciliation"),
            asp.fact("lesson_learned"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (setting, power, mission)
        for setting in SETTINGS
        for power in POWERS
        for mission in MISSIONS
        if reasonability_gate(SETTINGS[setting], POWERS[power], MISSIONS[mission])
    ]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_values = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 0
    if py != clingo_values:
        print("MISMATCH between Python and ASP gates.")
        print("python only:", sorted(py - clingo_values))
        print("clingo only:", sorted(clingo_values - py))
        return 1
    for setting, power, mission in valid_combos():
        sample = generate(
            StoryParams(setting, power, mission, "Harry", "Blob", "Sixer", seed=1)
        )
        if not sample.story or "Harry" not in sample.story or "Blob" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP gate matches Python gate ({len(py)} combos), and stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero storyworld about Harry, Blob, Sixer, and a lesson learned."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--power", choices=POWERS)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--harry", choices=HARRY_NAMES)
    parser.add_argument("--blob", choices=BLOB_NAMES)
    parser.add_argument("--sixer", choices=SIXER_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if not args.setting or combo[0] == args.setting
        if not args.power or combo[1] == args.power
        if not args.mission or combo[2] == args.mission
    ]
    if not choices:
        raise StoryError("No valid setting, power, and mission combination matches the requested fields.")
    setting, power, mission = rng.choice(choices)
    return StoryParams(
        setting=setting,
        power=power,
        mission=mission,
        harry=args.harry or rng.choice(HARRY_NAMES),
        blob=args.blob or rng.choice(BLOB_NAMES),
        sixer=args.sixer or rng.choice(SIXER_NAMES),
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
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        for value in sorted(set(asp.atoms(model, "valid"))):
            print(value)
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [
            generate(
                StoryParams(
                    setting=s,
                    power=p,
                    mission=m,
                    harry=h,
                    blob=b,
                    sixer=x,
                    seed=base_seed + i,
                )
            )
            for i, (s, p, m, h, b, x) in enumerate(CURATED)
        ]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for i in range(args.n):
            seed = base_seed + i
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
