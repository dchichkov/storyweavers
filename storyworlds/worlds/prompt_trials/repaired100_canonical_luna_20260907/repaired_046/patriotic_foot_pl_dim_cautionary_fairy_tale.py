#!/usr/bin/env python3
"""A gentle cautionary fairy tale about patriotic feet and a very small march."""

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


SETTINGS = {
    "village": "the little hill village",
    "garden": "the royal garden",
    "square": "the old town square",
    "meadow": "the bellflower meadow",
}
HERO_NAMES = ["Luna", "Mira", "Pip", "Tessa", "Nell"]
HELPER_NAMES = ["Bram", "Ivy", "Oren", "Sela", "Wren"]
BANNERS = ["a red-and-gold banner", "a blue-and-silver banner", "a green-and-white banner"]
MARCHES = ["the morning parade", "the lantern procession", "the harvest march"]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    setting: str = SETTINGS["village"]
    hero: str = "Luna"
    helper: str = "Bram"
    banner: str = BANNERS[0]
    march: str = MARCHES[0]
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass(frozen=True)
class Incident:
    name: str
    danger: str
    tempting_choice: str
    clue: str
    careful_action: str
    helper_action: str
    result: str
    ending: str


INCIDENTS = [
    Incident(
        "the rushing drum",
        "Luna wished to beat the parade drum so loudly that the village could hear it from every hill",
        "run ahead and pound it without waiting for the march leader",
        "a loose strap dragged a bright line through the dust",
        "tighten the strap and keep the drum at a steady beat",
        "walk beside Luna and signal when the road narrowed",
        "the drum guided the march instead of frightening the birds and waking every baby",
        "the banner floated above a calm procession while the drum sounded like a friendly heart",
    ),
    Incident(
        "the proud bridge",
        "Luna wanted to plant the banner on the tallest, thinnest bridge rail",
        "climb the rail so the colors would look grand above the river",
        "the old wood creaked where three nails had lifted",
        "carry the banner across the bridge and tie it to the strong post",
        "test the post and hold the cloth away from the water",
        "the colors shone safely from the sturdy post",
        "the river mirrored the banner without carrying anyone away",
    ),
    Incident(
        "the windy ribbon",
        "Luna tried to chase a ribbon that the wind had pulled toward a steep slope",
        "run after it with eyes fixed on the fluttering cloth",
        "the ribbon's shadow crossed a patch of loose stones",
        "stop at the safe path and use a long branch to draw the ribbon back",
        "anchor the banner while Luna reached from solid ground",
        "the ribbon returned without a tumble down the slope",
        "the patriotic colors rested safely beside the path as the wind sang on",
    ),
    Incident(
        "the glittering shortcut",
        "Luna saw glitter beside the parade road and wanted to leave the group to gather it",
        "dash into the dark woods where the glitter seemed brightest",
        "the glitter was only dew on thorny brambles",
        "stay with the helpers and inspect the sparkle from the path",
        "point out the safe road and carry a lantern",
        "Luna learned that a bright prize is not always a good direction",
        "the true treasure was the banner returning safely at the head of the march",
    ),
    Incident(
        "the steep hill song",
        "Luna promised to sing the loudest song while racing up the steepest hill",
        "rush uphill while holding the banner high above her head",
        "the path turned slick beneath the morning mist",
        "fold the banner, walk slowly, and sing only after reaching level ground",
        "take the lower path and carry the flagpole carefully",
        "the march reached the hilltop with every singer safe and smiling",
        "their song rose over the meadow while the banner waved from level ground",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary patriotic fairy-tale world.")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--hero", choices=HERO_NAMES)
    parser.add_argument("--helper", choices=HELPER_NAMES)
    parser.add_argument("--banner", choices=BANNERS)
    parser.add_argument("--march", choices=MARCHES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_key = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if helper == hero:
        helper = rng.choice([x for x in HELPER_NAMES if x != hero])
    return StoryParams(
        setting=SETTINGS[setting_key],
        hero=hero,
        helper=helper,
        banner=args.banner or rng.choice(BANNERS),
        march=args.march or rng.choice(MARCHES),
    )


def tell(params: StoryParams) -> World:
    incident = INCIDENTS[(params.seed or 0) % len(INCIDENTS)]
    world = World(params)
    luna = world.add(Entity(
        "hero", "character", params.hero, "hero",
        meters={"balance": 1.0, "caution": 0.4, "energy": 1.0},
        memes={"patriotism": 1.0, "wisdom": 0.2},
        traits=["eager", "proud"],
    ))
    helper = world.add(Entity(
        "helper", "character", params.helper, "helper",
        meters={"care": 1.0, "balance": 1.0},
        memes={"friendship": 1.0, "wisdom": 1.0},
        traits=["watchful", "kind"],
    ))
    banner = world.add(Entity(
        "banner", "object", params.banner, "banner",
        meters={"safety": 1.0, "wind_resistance": 0.7},
        memes={"belonging": 1.0},
        traits=["bright", "ceremonial"],
    ))

    world.say(f"Once, in {params.setting}, a young girl named {params.hero} prepared for {params.march}.")
    world.say(f"She carried {params.banner}, and her heart felt as bright as a bell because she loved her home.")
    world.say(f"“I shall show everyone how patriotic I am!” cried {params.hero}.")
    world.say(f"“Then let your care be as strong as your pride,” said {params.helper}, who walked beside her.")
    world.para()

    world.say(f"But {incident.name} soon tested her.")
    world.say(f"{incident.danger}.")
    world.say(f"“I will {incident.tempting_choice}!” said {params.hero}.")
    world.say(f"{params.helper} shook {params.helper}'s head. “A good purpose does not make a dangerous step wise.”")
    world.say(f"Then {params.hero} noticed that {incident.clue}.")
    world.facts["danger_seen"] = True
    world.para()

    world.say(f"{params.hero} took one slow breath and chose caution. {params.hero} decided to {incident.careful_action}.")
    world.say(f"{params.helper} replied, “And I will {incident.helper_action}.”")
    world.say(f"Together they changed their plan, watched the road, and {incident.result}.")
    luna.meters["caution"] += 1.0
    luna.meters["balance"] += 1.0
    luna.memes["wisdom"] += 1.0
    helper.memes["friendship"] += 1.0
    world.facts["wise_choice"] = True
    world.para()

    world.say(f"At last, {params.hero} and {params.helper} rejoined {params.march}.")
    world.say(f"“Patriotism means caring for our people and our place,” said {params.hero}.")
    world.say(f"“And careful feet can carry a brave heart a long way,” answered {params.helper}.")
    world.say(f"{incident.ending}.")
    world.facts.update(
        hero=luna,
        helper=helper,
        banner=banner,
        incident=incident.name,
        danger=incident.danger,
        tempting_choice=incident.tempting_choice,
        clue=incident.clue,
        careful_action=incident.careful_action,
        helper_action=incident.helper_action,
        result=incident.result,
        ending=incident.ending,
        patriotic=True,
        dialogue=True,
        cautionary=True,
        foot_pl_dim=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a cautionary fairy tale about {f['hero'].label} carrying {f['banner'].label} during {world.params.march}.",
        f"Show how {f['hero'].label} notices that {f['clue']} and chooses safety.",
        "Use patriotic feeling kindly: love of home should mean caring for people and places, not showing off.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    return [
        QAItem(
            question=f"Why did {hero} want to make the parade impressive?",
            answer=f"{hero} loved the home place and wanted to show patriotic pride during {world.params.march}.",
        ),
        QAItem(
            question=f"What warning did {hero} notice?",
            answer=f"{hero} noticed that {f['clue']}, so the tempting shortcut or stunt was not safe.",
        ),
        QAItem(
            question=f"How did {helper} help {hero}?",
            answer=f"{helper} helped by deciding to {f['helper_action']}.",
        ),
        QAItem(
            question=f"What careful choice did {hero} make?",
            answer=f"{hero} chose to {f['careful_action']}, rather than taking the dangerous option to {f['tempting_choice']}.",
        ),
        QAItem(
            question="What lesson did the fairy tale teach?",
            answer=f"It taught that loving one's home is best shown through care and responsibility. {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does patriotic mean in this story?",
            answer="Patriotic means caring about one's home and community and helping keep them safe and good.",
        ),
        QAItem(
            question="Why should people be cautious near steep places or weak bridges?",
            answer="They should be cautious because a slip or broken surface can cause a serious fall.",
        ),
        QAItem(
            question="Why can a helper be important?",
            answer="A helper can notice dangers, offer another idea, and make a difficult job safer.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_setting/1.
#show safe_choice/1.
valid_setting(village).
valid_setting(garden).
valid_setting(square).
valid_setting(meadow).
safe_choice(careful).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", key) for key in SETTINGS]
    lines.extend(asp.fact("safe_choice", "careful") for _ in [0])
    return "\n".join(lines)


def asp_program(show: str = "#show valid_setting/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program())
        actual = sorted(set(asp.atoms(model, "valid_setting")))
        expected = sorted((key,) for key in SETTINGS)
        if actual != expected:
            print("MISMATCH: ASP settings do not match Python settings.")
            return 1
        for seed in range(len(INCIDENTS)):
            params = StoryParams(seed=seed)
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("MISMATCH: generated sample was incomplete.")
                return 1
        print(f"OK: ASP gate matches {len(expected)} settings and generated stories pass.")
        return 0
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0


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
    StoryParams(setting=SETTINGS["village"], hero="Luna", helper="Bram", banner=BANNERS[0], march=MARCHES[0], seed=0),
    StoryParams(setting=SETTINGS["garden"], hero="Mira", helper="Ivy", banner=BANNERS[1], march=MARCHES[1], seed=1),
    StoryParams(setting=SETTINGS["square"], hero="Pip", helper="Oren", banner=BANNERS[2], march=MARCHES[2], seed=2),
    StoryParams(setting=SETTINGS["meadow"], hero="Tessa", helper="Sela", banner=BANNERS[0], march=MARCHES[0], seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero} and {sample.params.helper} in {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
