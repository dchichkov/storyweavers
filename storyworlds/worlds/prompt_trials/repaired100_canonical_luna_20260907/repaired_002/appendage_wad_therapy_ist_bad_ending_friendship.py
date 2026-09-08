#!/usr/bin/env python3
"""
A small space-adventure storyworld about an appendage, a wad, and a therapist,
where friendship helps repair a bad ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = "ship"

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    id: str
    label: str
    hazards: tuple[str, ...]
    affordances: tuple[str, ...]


@dataclass
class Gear:
    id: str
    label: str
    purpose: str
    guards: tuple[str, ...]


@dataclass
class StoryParams:
    setting: str = "moon_orbit"
    appendage: str = "antenna"
    wad: str = "repair_wad"
    therapist: str = "Dr. Vale"
    friend: str = "Pip"
    hazard: str = "static"
    ending: str = "friendship"
    seed: Optional[int] = None


SETTINGS = {
    "moon_orbit": Setting(
        "moon_orbit",
        "a little research ship circling the moon",
        ("static", "loose_tools"),
        ("observe_craters", "repair_signal"),
    ),
    "red_moon": Setting(
        "red_moon",
        "a red moon station above a dusty planet",
        ("dust", "solar_flare"),
        ("map_canyons", "repair_signal"),
    ),
}

APPENDAGES = {
    "antenna": {
        "label": "a silver antenna appendage",
        "region": "roof",
        "function": "carry friendly messages",
    },
    "arm": {
        "label": "a small helper-arm appendage",
        "region": "side",
        "function": "hold tools",
    },
}

WADS = {
    "repair_wad": Gear(
        "repair_wad",
        "a blue repair wad",
        "seal a cracked joint",
        ("static", "dust", "loose_tools"),
    ),
    "soft_wad": Gear(
        "soft_wad",
        "a soft comfort wad",
        "cushion a tender joint",
        ("static", "solar_flare"),
    ),
}

HAZARDS = {
    "static": {
        "warning": "a storm of space static was crackling ahead",
        "event": "A bright snap of static leaped across the cabin.",
        "clue": "the antenna trembled and stopped carrying the ship's welcome song",
        "effect": "damage",
    },
    "loose_tools": {
        "warning": "the tool locker was floating open",
        "event": "A wrench drifted loose and bumped the robot's appendage.",
        "clue": "the appendage clicked in the wrong direction",
        "effect": "damage",
    },
    "dust": {
        "warning": "red moon dust was sliding through the open hatch",
        "event": "A dusty gust curled through the station.",
        "clue": "the appendage became stiff and gray",
        "effect": "damage",
    },
    "solar_flare": {
        "warning": "a solar flare was flashing beyond the shield",
        "event": "The warning lights blinked gold as the flare touched the station.",
        "clue": "the appendage shivered beneath its heat shield",
        "effect": "damage",
    },
}

OPENERS = [
    "Far beyond Earth,",
    "At the edge of the moon's silver shadow,",
    "Inside a tiny ship among bright stars,",
    "Past the quiet rings of Saturn,",
]

SCENES = [
    "Blue planets shone in the windows while the engines hummed softly.",
    "The stars looked like pinpricks in a dark blanket, and the ship smelled of warm metal.",
    "A small moon rolled below the window like a pale marble.",
    "The navigation lights painted green circles across the cabin floor.",
]

ENDING_IMAGES = {
    "friendship": "Together, they watched the repaired antenna send a hello across the stars.",
    "lantern": "That night, Pip hung a tiny lantern beside the fixed appendage, and its warm glow filled the cabin.",
    "orbit": "The ship returned to its gentle orbit, carrying two friends and one bright new signal.",
}

KNOWLEDGE = {
    "appendage": (
        "What is an appendage?",
        "An appendage is a part that sticks out from a body or machine and helps it move, sense, or work.",
    ),
    "wad": (
        "What is a wad?",
        "A wad is a small soft or packed lump of material, such as a piece used for repair or comfort.",
    ),
    "therapist": (
        "What does a therapist do?",
        "A therapist listens carefully and helps someone understand feelings, recover, or find a useful next step.",
    ),
    "friendship": (
        "What is friendship?",
        "Friendship is a caring bond in which people help, listen to, and trust one another.",
    ),
}


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.appendage not in APPENDAGES:
        raise StoryError(f"Unknown appendage: {params.appendage}")
    if params.wad not in WADS:
        raise StoryError(f"Unknown wad: {params.wad}")
    if params.hazard not in HAZARDS:
        raise StoryError(f"Unknown hazard: {params.hazard}")
    if params.ending not in ENDING_IMAGES:
        raise StoryError(f"Unknown ending: {params.ending}")
    if not params.therapist.strip() or not params.friend.strip():
        raise StoryError("The therapist and friend need names.")
    if params.wad == "soft_wad" and params.hazard == "dust":
        raise StoryError("The soft comfort wad cannot protect the appendage from heavy moon dust.")


def build_story(params: StoryParams) -> World:
    validate(params)
    setting = SETTINGS[params.setting]
    appendage_cfg = APPENDAGES[params.appendage]
    wad = WADS[params.wad]
    hazard = HAZARDS[params.hazard]
    world = World(setting)

    luna = world.add(
        Entity(
            "Luna",
            "character",
            "a little repair robot",
            meters={"signal": 1.0, "damage": 0.0},
            memes={"hope": 1.0, "worry": 0.0},
        )
    )
    friend = world.add(
        Entity(
            "friend",
            "character",
            params.friend,
            meters={"help": 0.0},
            memes={"care": 1.0, "worry": 0.0},
        )
    )
    therapist = world.add(
        Entity(
            "therapist",
            "character",
            params.therapist,
            memes={"patience": 1.0},
        )
    )
    appendage = world.add(
        Entity(
            "appendage",
            "object",
            appendage_cfg["label"],
            meters={"strength": 1.0, "damage": 0.0},
            location=appendage_cfg["region"],
        )
    )
    world.facts.update(
        luna=luna,
        friend=friend,
        therapist=therapist,
        appendage=appendage,
        wad=wad,
        hazard=hazard,
        appendage_cfg=appendage_cfg,
        ending=ENDING_IMAGES[params.ending],
    )

    world.say(f"{random.Random(params.seed).choice(OPENERS)} Luna lived aboard {setting.label}.")
    world.say(
        f"Her {params.appendage} was {appendage_cfg['label'].removeprefix('a ')}; it helped {appendage_cfg['function']}."
    )
    world.say(SCENES[(params.seed or 0) % len(SCENES)])
    world.say(
        f"Luna wanted to {setting.affordances[0].replace('_', ' ')}, but {friend.label} noticed "
        f"that {hazard['warning']}."
    )
    world.say(f'"We can still finish the mission," Luna said. "I do not want to stop."')
    world.say(
        f'"Stopping for a moment is not giving up," {friend.label} replied. '
        f'"It helps us notice what needs care."'
    )
    world.para()

    world.say(hazard["event"])
    appendage.meters["damage"] += 1.0
    appendage.meters["strength"] -= 0.4
    luna.meters["signal"] -= 0.5
    luna.memes["worry"] += 1.0
    friend.memes["worry"] += 1.0
    world.say(f"Then {hazard['clue']}. The mission screen went dark.")
    world.say(
        f"Luna tried to force the {params.appendage}, but the attempt made the joint worse. "
        f"The ship drifted toward the silent side of the moon."
    )
    world.say(
        f'"My appendage is broken, and the mission is over," Luna whispered.'
    )
    world.say(
        f'"Tell me where it hurts," said {params.therapist}, the ship therapist. '
        f'"We will listen before we repair."'
    )
    world.say(
        f'"The joint feels frightened when I move it," Luna said. '
        f'"I also feel frightened that my friends will be disappointed."'
    )
    world.say(
        f'"Thank you for telling us," said {params.therapist}. '
        f'"A careful repair can begin with an honest feeling."'
    )
    world.para()

    world.say(
        f"{params.friend} opened the supply drawer and brought {wad.label}. "
        f"It was made to {wad.purpose}."
    )
    world.say(
        f'"Hold the light steady," {params.friend} said. '
        f'"I will not leave while you try."'
    )
    world.say(
        f"Luna breathed slowly, while {params.therapist} guided her through three gentle movements. "
        f"Then {params.friend} pressed the wad around the cracked joint."
    )
    appendage.meters["damage"] = 0.0
    appendage.meters["strength"] = 1.0
    luna.meters["signal"] = 1.0
    luna.memes["worry"] = 0.0
    luna.memes["hope"] += 1.0
    friend.memes["worry"] = 0.0
    friend.memes["care"] += 1.0
    world.say(
        f"The blue wad held firm. Luna moved the appendage once, then twice, and a clear signal shimmered across the cabin."
    )
    world.say(
        f'"I thought the bad ending had already happened," Luna said.'
    )
    world.say(
        f'"A bad moment is not the last page," {params.friend} answered. '
        f'"Friends can help turn the page."'
    )
    world.say(
        f"Together, Luna, {params.friend}, and {params.therapist} guided the ship back into its safe orbit."
    )
    world.para()
    world.say(ENDING_IMAGES[params.ending])
    world.facts["state"] = "repaired"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly space adventure about Luna's {f['appendage_cfg']['label']}, "
        f"a {f['wad'].label}, and {f['therapist'].label}.",
        f"Show how {f['friend'].label} uses friendship to help after {f['hazard']['event'].lower()}",
        f"End with this image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    appendage = f["appendage"]
    wad = f["wad"]
    therapist = f["therapist"]
    friend = f["friend"]
    hazard = f["hazard"]
    return [
        QAItem(
            "What went wrong during Luna's space mission?",
            f"{hazard['event']} Luna's appendage was damaged, so her signal faded and the ship drifted toward the silent side of the moon.",
        ),
        QAItem(
            "How did friendship help Luna?",
            f"{friend.label} stayed beside Luna, held the light steady, and helped apply {wad.label}. Their care helped Luna feel safe enough to try the repair.",
        ),
        QAItem(
            "What did the therapist teach Luna?",
            f"{therapist.label} taught Luna to describe her fear and listen to the damaged appendage before forcing it to move.",
        ),
        QAItem(
            "How was the appendage repaired?",
            f"Luna made three gentle movements while {therapist.label} guided her, and {friend.label} pressed {wad.label} around the cracked joint.",
        ),
        QAItem(
            "Why was the ending not truly bad?",
            "The frightening moment seemed like a bad ending, but Luna's friends helped repair the appendage and return the ship to a safe orbit.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE.values()]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"setting: {world.setting.label}"]
    for entity in world.entities.values():
        meters = {k: round(v, 2) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 2) for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes} location={entity.location}")
    lines.append(f"state: {world.facts.get('state', 'in progress')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


ASP_RULES = r"""
setting(moon_orbit).
setting(red_moon).
appendage(antenna).
appendage(arm).
wad(repair_wad).
wad(soft_wad).
hazard(static).
hazard(loose_tools).
hazard(dust).
hazard(solar_flare).

guards(repair_wad, static).
guards(repair_wad, loose_tools).
guards(repair_wad, dust).
guards(soft_wad, static).
guards(soft_wad, solar_flare).

works(antenna, repair_signal).
works(arm, repair_signal).

safe(A, W) :- hazard(A), wad(W), guards(W, A).
repairable(App, W, A) :- appendage(App), wad(W), hazard(A), safe(A, W).
valid_story(S, App, W, A) :- setting(S), appendage(App), wad(W), hazard(A), repairable(App, W, A).
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("setting", "moon_orbit"),
        asp.fact("setting", "red_moon"),
        asp.fact("appendage", "antenna"),
        asp.fact("appendage", "arm"),
        asp.fact("wad", "repair_wad"),
        asp.fact("wad", "soft_wad"),
        asp.fact("hazard", "static"),
        asp.fact("hazard", "loose_tools"),
        asp.fact("hazard", "dust"),
        asp.fact("hazard", "solar_flare"),
        asp.fact("guards", "repair_wad", "static"),
        asp.fact("guards", "repair_wad", "loose_tools"),
        asp.fact("guards", "repair_wad", "dust"),
        asp.fact("guards", "soft_wad", "static"),
        asp.fact("guards", "soft_wad", "solar_flare"),
        asp.fact("works", "antenna", "repair_signal"),
        asp.fact("works", "arm", "repair_signal"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show valid_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid_combos() -> set[tuple[str, str, str, str]]:
    combos = set()
    for setting in SETTINGS:
        for appendage in APPENDAGES:
            for wad, gear in WADS.items():
                for hazard in HAZARDS:
                    if hazard in gear.guards:
                        combos.add((setting, appendage, wad, hazard))
    return combos


def asp_valid_combos() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = python_valid_combos()
    actual = asp_valid_combos()
    if expected != actual:
        print("MISMATCH between Python and ASP validity gates.")
        print("Only in Python:", sorted(expected - actual))
        print("Only in ASP:", sorted(actual - expected))
        return 1
    for seed in range(5):
        params = StoryParams(seed=seed)
        sample = generate(params)
        if not sample.story or "Luna" not in sample.story:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP/Python parity holds for {len(expected)} valid combinations.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard_choices = list(HAZARDS)
    if setting == "moon_orbit":
        hazard_choices = ["static", "loose_tools"]
    else:
        hazard_choices = ["dust", "solar_flare"]
    hazard = args.hazard or rng.choice(hazard_choices)
    compatible_wads = [key for key, wad in WADS.items() if hazard in wad.guards]
    return StoryParams(
        setting=setting,
        appendage=args.appendage or rng.choice(list(APPENDAGES)),
        wad=args.wad or rng.choice(compatible_wads),
        therapist=args.therapist or rng.choice(["Dr. Vale", "Dr. Mira", "Dr. Sol"]),
        friend=args.friend or rng.choice(["Pip", "Nova", "Kiko"]),
        hazard=hazard,
        ending=args.ending or rng.choice(list(ENDING_IMAGES)),
        seed=args.seed,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A space adventure about an appendage, a wad, therapy, and friendship."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--appendage", choices=APPENDAGES)
    parser.add_argument("--wad", choices=WADS)
    parser.add_argument("--therapist")
    parser.add_argument("--friend")
    parser.add_argument("--hazard", choices=HAZARDS)
    parser.add_argument("--ending", choices=ENDING_IMAGES)
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
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(json.dumps([list(map(str, model)) for model in asp.solve(asp_program(), models=1)], indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, setting in enumerate(SETTINGS):
            params = StoryParams(setting=setting, seed=base_seed + i)
            samples.append(generate(params))
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
