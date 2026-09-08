#!/usr/bin/env python3
"""
A cautionary pirate tale about Luna, a freckled deckhand, asterisk-marked
technology, and the magic of reading instructions before sailing.

The story uses a small simulated world: a brass tide compass, an asterisk
warning, a flashback to an old lesson, and a safe magical resolution.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    id: str
    place: str
    detail: str


@dataclass
class StoryParams:
    name: str = "Luna"
    title: str = "freckled deckhand"
    seed: Optional[int] = None
    voyage: str = "reef"
    setting: str = "moonlit_bay"
    flashback: int = 0
    magic: int = 0
    caution: int = 0
    ending: int = 0


@dataclass(frozen=True)
class Voyage:
    id: str
    cargo: str
    danger: str
    warning: str
    faulty_action: str
    clue: str
    cause: str
    repair: str
    safe_result: str
    ending_images: tuple[str, ...]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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


SETTINGS = {
    "moonlit_bay": Setting(
        "moonlit_bay",
        "Moonlit Bay",
        "silver waves, sleeping gulls, and a black-rock reef",
    ),
    "whispering_cove": Setting(
        "whispering_cove",
        "Whispering Cove",
        "green cliffs, rope bridges, and a bell buoy",
    ),
    "starboard_isle": Setting(
        "starboard_isle",
        "Starboard Isle",
        "bright sand, palm trees, and a lighthouse hill",
    ),
}

VOYAGES = {
    "reef": Voyage(
        id="reef",
        cargo="a chest of blue lanterns",
        danger="the ship could scrape the reef and spill the lanterns into the sea",
        warning="Never trust the glowing arrow when the asterisk is blinking",
        faulty_action="follow the glowing arrow without checking the little asterisk",
        clue="the asterisk blinking twice beside the word DEPTH",
        cause="the compass had entered its shallow-water mode, but the warning line had been covered by salt",
        repair="wipe the salt away, read the warning aloud, and switch the compass to reef mode",
        safe_result="the Sea Sparrow curved around the reef, and the blue lanterns reached the dark lighthouse",
        ending_images=(
            "That night, the blue lanterns shone along the lighthouse steps like tiny moons.",
            "The repaired compass rested beside the wheel, its asterisk glowing quietly.",
            "Captain Brine hung one blue lantern above the cabin door to remember the careful voyage.",
            "Luna's freckles glittered in the lantern light as the safe ship rocked in the bay.",
        ),
    ),
    "storm": Voyage(
        id="storm",
        cargo="a basket of warm bread",
        danger="the ship could turn broadside to the waves and lose its supper",
        warning="Never use storm magic while the asterisk is red",
        faulty_action="tap the storm button before reading the asterisk",
        clue="a red asterisk pulsing beside the word WIND",
        cause="the weather tablet was still set to calm-air magic instead of storm steering",
        repair="hold the tablet flat, read the red warning, and choose storm steering",
        safe_result="the Sea Sparrow faced the waves, and the warm bread arrived before sunset",
        ending_images=(
            "The crew shared warm bread while the storm softened beyond the rail.",
            "The red asterisk faded to gold on the safely reset tablet.",
            "Captain Brine placed a bread crumb beside the warning as a reminder.",
            "Rain beaded on Luna's freckles while the ship sailed steadily home.",
        ),
    ),
    "isle": Voyage(
        id="isle",
        cargo="a box of pearl buttons",
        danger="the tide could carry the buttons away from the island children",
        warning="An asterisk means the tide gate is not ready",
        faulty_action="open the tide gate as soon as the magic screen sparkled",
        clue="a bright asterisk shining beside the word WAIT",
        cause="the tide gate's little moonstone had not finished charging",
        repair="wait for the moonstone to glow blue, then turn the brass handle slowly",
        safe_result="the tide gate opened gently, and the pearl buttons crossed the channel dry",
        ending_images=(
            "Island children sorted the pearl buttons beneath the lighthouse sun.",
            "The moonstone glowed blue while the tide gate clicked shut.",
            "Luna pinned one pearl button beside the asterisk on the ship's chart.",
            "The Sea Sparrow left a smooth silver wake behind it.",
        ),
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary pirate story about technology, an asterisk, and a freckled deckhand."
    )
    parser.add_argument("--name", choices=["Luna", "Luna Freckle"], default="Luna")
    parser.add_argument("--voyage", choices=VOYAGES, default=None)
    parser.add_argument("--setting", choices=SETTINGS, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--flashback", type=int, choices=range(4), default=None)
    parser.add_argument("--magic", type=int, choices=range(4), default=None)
    parser.add_argument("--caution", type=int, choices=range(4), default=None)
    parser.add_argument("--ending", type=int, choices=range(4), default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    voyage = args.voyage or rng.choice(list(VOYAGES))
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(
        name=args.name,
        title="freckled deckhand",
        seed=args.seed,
        voyage=voyage,
        setting=setting,
        flashback=args.flashback if args.flashback is not None else rng.randrange(4),
        magic=args.magic if args.magic is not None else rng.randrange(4),
        caution=args.caution if args.caution is not None else rng.randrange(4),
        ending=args.ending if args.ending is not None else rng.randrange(4),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.name not in {"Luna", "Luna Freckle"}:
        raise StoryError("This pirate tale needs Luna, the freckled deckhand.")
    if params.voyage not in VOYAGES:
        raise StoryError("Unknown voyage.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    for field_name in ("flashback", "magic", "caution", "ending"):
        value = getattr(params, field_name)
        if not 0 <= value < 4:
            raise StoryError(f"{field_name} must be between 0 and 3.")


ASP_RULES = r"""
character(luna).
technology(compass).
technology(tablet).
technology(tide_gate).
symbol(asterisk).
trait(freckle).
feature(flashback).
feature(magic).
feature(cautionary).
voyage(reef).
voyage(storm).
voyage(isle).

safe(reef) :- voyage(reef), technology(compass), symbol(asterisk), feature(cautionary).
safe(storm) :- voyage(storm), technology(tablet), symbol(asterisk), feature(cautionary).
safe(isle) :- voyage(isle), technology(tide_gate), symbol(asterisk), feature(cautionary).

valid_tale(V) :- voyage(V), safe(V), character(luna), trait(freckle),
                 feature(flashback), feature(magic).
#show valid_tale/1.
#show safe/1.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("character", "luna"),
        asp.fact("technology", "compass"),
        asp.fact("technology", "tablet"),
        asp.fact("technology", "tide_gate"),
        asp.fact("symbol", "asterisk"),
        asp.fact("trait", "freckle"),
        asp.fact("feature", "flashback"),
        asp.fact("feature", "magic"),
        asp.fact("feature", "cautionary"),
    ]
    facts.extend(asp.fact("voyage", voyage_id) for voyage_id in VOYAGES)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_tale/1."))
    found = set(asp.atoms(model, "valid_tale"))
    expected = set(VOYAGES)
    if found == {(item,) for item in expected}:
        print(f"OK: clingo matches Python tale registry ({len(expected)} voyages).")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(found))
    print("python:", sorted((item,) for item in expected))
    return 1


def build_world(params: StoryParams, voyage: Voyage, setting: Setting) -> World:
    world = World(setting)
    luna = world.add(
        Entity(
            "luna",
            kind="character",
            label=params.name,
            type="deckhand",
            meters={"safety": 0.5, "danger": 0.0},
            memes={"curiosity": 1.0, "worry": 0.0, "courage": 0.5, "relief": 0.0},
        )
    )
    device = world.add(
        Entity(
            "device",
            label="the marked sea device",
            type="technology",
            meters={"charge": 0.8, "accuracy": 0.5, "warning_visible": 0.0},
            memes={"mystery": 1.0},
        )
    )
    ship = world.add(
        Entity(
            "ship",
            label="the Sea Sparrow",
            type="ship",
            meters={"hull_safety": 0.8, "course_safety": 0.4},
            memes={"crew_trust": 0.6},
        )
    )
    setting_entity = world.add(
        Entity(
            "setting",
            label=setting.place,
            type="place",
            meters={"calm": 0.5, "danger": 0.2},
            memes={"wonder": 0.8},
        )
    )

    openings = (
        f"{params.name} was the youngest deckhand on the Sea Sparrow, and a spray of freckles crossed her nose.",
        f"Every sailor on the Sea Sparrow knew {params.name} by her bright freckles and quicker questions.",
        f"{params.name}, the freckled deckhand, loved both old sea songs and new technology.",
        f"At dawn, {params.name} polished the brass buttons of her coat and counted every freckle she could see in the cabin mirror.",
    )
    world.say(f"Captain Brine sailed toward {setting.place}, where {setting.detail}.")
    world.say(openings[params.flashback])
    world.say(f"The crew carried {voyage.cargo}, and the marked technology was meant to guide them.")
    world.para()

    world.say(f"At the wheel sat a brass device with a glowing asterisk.")
    world.say(f"The asterisk meant, '{voyage.warning}.'")
    world.say(f"But the screen shimmered like a little piece of magic, and {params.name} wanted to make the ship hurry.")
    world.say(f'"We can trust the sparkle, can\'t we?" {params.name} asked.')
    world.say(f'Captain Brine shook his head. "A bright screen is not the same as a safe answer."')
    world.say(f'"Then what should I check?" {params.name} asked.')
    world.say(f'"Read every mark," said the captain. "Especially the small one."')
    world.para()

    world.say(f"{params.name} forgot the warning and tried to {voyage.faulty_action}.")
    world.say(f"The Sea Sparrow lurched. {voyage.danger.capitalize()}.")
    ship.meters["course_safety"] = 0.1
    ship.meters["hull_safety"] = 0.5
    setting_entity.meters["danger"] = 1.0
    luna.meters["danger"] = 1.0
    luna.memes["worry"] = 1.0

    flashbacks = (
        f"Then {params.name} remembered a flashback from her first day aboard: Captain Brine had covered a chart and asked her to find the smallest mark.",
        f"A flashback swept through {params.name}'s mind. She saw an older Luna ignoring a tiny warning and nearly dropping a whole coil of rope.",
        f"In a flashback, the captain's lantern had shone on an asterisk while he said, 'Small marks can carry large truths.'",
        f"{params.name} remembered a flashback of the ship's bell ringing after a careless sailor had skipped one line of instructions.",
    )
    world.say(flashbacks[params.flashback])
    world.say(f"She looked again and found {voyage.clue}.")
    device.meters["warning_visible"] = 1.0
    luna.memes["curiosity"] += 1.0
    world.para()

    world.say(f"The magic was not a shortcut. It was a clue.")
    world.say(f"{params.name} read the entire warning to the crew, then discovered that {voyage.cause}.")
    world.say(f'Captain Brine said, "Now choose: hurry blindly, or repair the mistake."')
    world.say(f'"Repair it," said {params.name}. "I want every sailor and every parcel safe."')
    world.say(f"Together they worked to {voyage.repair}.")
    device.meters["accuracy"] = 1.0
    device.meters["charge"] = 1.0
    ship.meters["course_safety"] = 1.0
    ship.meters["hull_safety"] = 1.0
    setting_entity.meters["danger"] = 0.0
    luna.meters["danger"] = 0.0
    luna.meters["safety"] = 1.0
    luna.memes["worry"] = 0.0
    luna.memes["courage"] = 1.0
    luna.memes["relief"] = 1.0
    world.para()

    world.say(f"At last, {voyage.safe_result.capitalize()}.")
    world.say(f'Captain Brine smiled. "That asterisk did not spoil the magic, Luna. It protected it."')
    world.say(voyage.ending_images[params.ending])
    world.say(f"From then on, the freckled deckhand read every warning before trusting any new technology.")

    world.facts.update(
        luna=luna,
        device=device,
        ship=ship,
        setting_entity=setting_entity,
        voyage=voyage,
        setting=setting,
        flashback=flashbacks[params.flashback],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    voyage: Voyage = world.facts["voyage"]
    setting: Setting = world.facts["setting"]
    return [
        f"Write a cautionary pirate tale about a freckled deckhand using technology near {setting.place}.",
        f"Include an asterisk warning, a flashback, a little magic, and the lesson that the crew should read instructions.",
        f"Tell how Luna learns that {voyage.warning.lower()}",
    ]


def story_qa(world: World) -> list[QAItem]:
    voyage: Voyage = world.facts["voyage"]
    luna: Entity = world.facts["luna"]
    setting: Setting = world.facts["setting"]
    return [
        QAItem(
            question="Who was the main character?",
            answer=f"The main character was {luna.label}, a freckled deckhand on the Sea Sparrow.",
        ),
        QAItem(
            question="What warning did the asterisk give?",
            answer=f"It warned, '{voyage.warning}.' The asterisk showed that the shining technology needed careful attention.",
        ),
        QAItem(
            question="What did Luna remember in the flashback?",
            answer=f"She remembered that small marks and skipped instructions could cause large trouble, so she looked closely at the device.",
        ),
        QAItem(
            question="What was the real problem?",
            answer=f"The real problem was that {voyage.cause}. Luna and Captain Brine corrected it instead of trusting a glittering screen.",
        ),
        QAItem(
            question="What lesson did the pirate crew learn?",
            answer=f"They learned to read every warning before using technology. After the repair, {voyage.safe_result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an asterisk?",
            answer="An asterisk is a small star-shaped mark that often points to an important note or warning.",
        ),
        QAItem(
            question="Why can technology need instructions?",
            answer="Technology can have special settings and risks, so instructions help people use it safely and correctly.",
        ),
        QAItem(
            question="What makes a story cautionary?",
            answer="A cautionary story shows a danger caused by carelessness and ends with a lesson about making a wiser choice.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that briefly shows something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        parts = []
        if entity.meters:
            parts.append(f"meters={entity.meters}")
        if entity.memes:
            parts.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) {' '.join(parts)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params, VOYAGES[params.voyage], SETTINGS[params.setting])
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
        print(asp_program("#show valid_tale/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_tale/1."))
        print(asp.atoms(model, "valid_tale"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        index = 0
        for voyage_id in VOYAGES:
            for setting_id in SETTINGS:
                rng = random.Random(base_seed + index)
                params = StoryParams(
                    name="Luna",
                    title="freckled deckhand",
                    seed=base_seed + index,
                    voyage=voyage_id,
                    setting=setting_id,
                    flashback=rng.randrange(4),
                    magic=rng.randrange(4),
                    caution=rng.randrange(4),
                    ending=rng.randrange(4),
                )
                samples.append(generate(params))
                index += 1
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
