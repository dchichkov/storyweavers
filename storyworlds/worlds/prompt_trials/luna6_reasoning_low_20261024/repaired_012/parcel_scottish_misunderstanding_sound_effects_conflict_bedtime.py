#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
for _parent in _HERE.parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    child_name: str
    granny_name: str
    parcel: str
    setting: str
    seed: Optional[int] = None


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


CHILD_NAMES = ["Mairi", "Rowan", "Skye", "Ewan", "Isla", "Callum"]
GRANNY_NAMES = ["Morag", "Iona", "Fiona", "Ailsa", "Nessa", "Elspeth"]
PARCELS = ["a parcel of warm wool socks", "a parcel of shortbread", "a parcel of bedtime books"]
SETTINGS = ["a snug stone cottage in the Highlands", "a little house beside a loch", "a cottage under a quiet Scottish hill"]

ARCS = [
    {
        "problem": "A soft thump came from the parcel, then three tiny scrapes. {child} thought it was a wee creature trying to escape and grew worried.",
        "turn": "Granny {granny} listened closely. \"That is no creature,\" she said. \"It sounds like the wooden toy inside is bumping against the box.\"",
        "action": "\"I thought it was scratching,\" {child} whispered. \"And I thought you were afraid of opening it,\" said Granny. They smiled, then carefully untied the parcel together.",
        "resolution": "Inside lay a little wooden sheep, its loose wheel making the scrapes. The parcel was safe, and the misunderstanding melted away.",
        "ending": "They set the sheep by the window, where moonlight silvered its wool while the last soft tap faded into the night.",
        "problem_fact": "the parcel's bumps and scrapes sounded like a creature inside",
        "clue_fact": "Granny listened and recognized the sound of a loose wooden wheel",
        "action_fact": "the child and Granny explained their worries and opened the parcel carefully",
        "outcome_fact": "they found a wooden sheep and cleared up their misunderstanding",
    },
    {
        "problem": "The parcel made a long, low \"whooo\" whenever the wind crossed the window. {child} thought someone outside was calling for help and would not settle.",
        "turn": "Granny {granny} held a candle near the window. Its flame leaned toward a tiny gap in the parcel's wrapping, and the whoosh came again.",
        "action": "\"I heard a voice,\" {child} said. \"I heard the wind,\" Granny replied. Together they loosened the ribbon and let the folded paper breathe.",
        "resolution": "The sound stopped. The parcel held a knitted scarf, and its paper sleeve had been whistling in the draft. Neither had meant to frighten the other.",
        "ending": "Granny tucked the scarf around {child}'s shoulders, and the candle flame stood still beside the quiet parcel.",
        "problem_fact": "wind whistling through the parcel sounded like a voice",
        "clue_fact": "the candle flame showed a draft passing through a gap in the wrapping",
        "action_fact": "they talked about what they heard and loosened the parcel's ribbon",
        "outcome_fact": "they found a scarf and understood the strange sound",
    },
    {
        "problem": "A bright rattle came from the parcel beneath the table. {child} thought Granny {granny} had hidden a noisy alarm in it, while Granny worried that {child} had shaken her carefully wrapped gift.",
        "turn": "Granny lifted the parcel gently. The rattle came only when it tipped, and a small bell shape pressed against the paper.",
        "action": "\"I wasn't trying to spoil your surprise,\" {child} said. \"And I wasn't trying to startle you,\" Granny answered. They agreed to open it slowly, together.",
        "resolution": "A tiny brass bell rolled into Granny's palm. The two had guessed wrong about each other, but now the mystery had a friendly answer.",
        "ending": "Granny rang the bell once, very softly, and its warm little note floated across the room toward bedtime.",
        "problem_fact": "a parcel's rattle made the child and Granny suspect each other",
        "clue_fact": "the rattle changed when the parcel tipped and came from a small bell",
        "action_fact": "they explained themselves and opened the parcel together",
        "outcome_fact": "they found a brass bell and resolved their misunderstanding",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.child_name, params.granny_name, params.parcel, params.setting))
    seed = int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")
    return random.Random(seed)


def tell(params: StoryParams) -> World:
    if not params.child_name.strip() or not params.granny_name.strip():
        raise StoryError("Child and granny names must not be blank.")
    if params.child_name.casefold() == params.granny_name.casefold():
        raise StoryError("The child and granny must have different names.")
    if params.parcel not in PARCELS:
        raise StoryError(f"Unknown parcel; choose one of: {', '.join(PARCELS)}.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting; choose one of: {', '.join(SETTINGS)}.")

    rng = _rng_for(params)
    arc = ARCS[rng.randrange(len(ARCS))]
    child = params.child_name
    granny = params.granny_name
    parcel = params.parcel
    world = World(params)
    child_entity = world.add(Entity(child, "character", "child", "a child"))
    granny_entity = world.add(Entity(granny, "character", "grandmother", "Granny"))
    parcel_entity = world.add(Entity("gift_parcel", "thing", "parcel", parcel))
    child_entity.meters.update({"worry": 1.0, "understanding": 0.0})
    granny_entity.meters.update({"patience": 1.0, "understanding": 0.0})
    child_entity.memes["misunderstanding"] = 1.0
    granny_entity.memes["conflict"] = 1.0
    parcel_entity.meters["wrapped"] = 1.0

    world.say(
        f"In {params.setting}, {child} was getting ready for bed while Granny {granny} placed {parcel} on the little table. "
        f"\"We can open it together in the morning,\" Granny said, and the quiet house settled beneath the stars."
    )
    world.para()
    world.say(arc["problem"].format(child=child, granny=granny))
    world.say(f"\"Did you hear that?\" {child} asked. \"I did,\" Granny replied, but they each imagined a different cause.")
    world.para()
    world.say(arc["turn"].format(child=child, granny=granny))
    world.say(arc["action"].format(child=child, granny=granny))
    world.para()
    world.say(arc["resolution"].format(child=child, granny=granny))
    world.say(arc["ending"].format(child=child, granny=granny))

    child_entity.meters.update({"worry": 0.0, "understanding": 1.0})
    granny_entity.meters["understanding"] = 1.0
    child_entity.memes["misunderstanding"] = 0.0
    granny_entity.memes["conflict"] = 0.0
    parcel_entity.meters["wrapped"] = 0.0
    world.facts = {
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "parcel": parcel,
        "setting": params.setting,
        "child": child,
        "granny": granny,
    }
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle bedtime story about a parcel, a misunderstanding, and a sound that gets a friendly explanation.",
        f"Tell a Scottish bedtime tale in which {f['child']} and Granny {f['granny']} listen to a parcel and talk through their worry.",
        "End with a peaceful image that shows how the characters have changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What worried {f['child']} about the parcel?",
            answer=f["problem"],
        ),
        QAItem(
            question="What helped them understand the sound?",
            answer=f["clue"],
        ),
        QAItem(
            question=f"How did {f['child']} and Granny {f['granny']} settle their disagreement?",
            answer=f"{f['action']} {f['outcome']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=world.paragraphs[-1][-1],
        ),
    ]


def world_knowledge_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parcel?",
            answer="A parcel is something wrapped or packed to be carried or given to someone.",
        ),
        QAItem(
            question="Why can a sound be misunderstood?",
            answer="A sound can be hard to identify when we cannot see what made it, so listening carefully and asking questions can help.",
        ),
        QAItem(
            question="What makes a bedtime story soothing?",
            answer="A gentle problem, kind words, and a peaceful ending can help a bedtime story feel safe and calm.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  setting={world.params.setting}")
    lines.append(f"  outcome={world.facts.get('outcome', '')}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :-
    feature(misunderstanding),
    feature(sound_effects),
    feature(conflict),
    style(bedtime_story),
    has(parcel),
    has(scottish_setting),
    resolved.
resolved :- characters_talk, sound_explained, worry_released.
characters_talk :- dialogue.
sound_explained :- clue.
worry_released :- outcome.
#show valid_story/0.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "sound_effects"),
        asp.fact("feature", "conflict"),
        asp.fact("style", "bedtime_story"),
        asp.fact("has", "parcel"),
        asp.fact("has", "scottish_setting"),
        asp.fact("dialogue"),
        asp.fact("clue"),
        asp.fact("outcome"),
    ]
    if params is not None:
        facts.extend(
            [
                asp.fact("parcel_choice", params.parcel),
                asp.fact("setting_choice", params.setting),
            ]
        )
    return "\n".join(facts)


def asp_program(params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n"


def python_reasonable(params: StoryParams) -> bool:
    try:
        tell(params)
    except StoryError:
        return False
    return True


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    cases = [
        StoryParams("Mairi", "Morag", PARCELS[0], SETTINGS[0], 0),
        StoryParams("Skye", "Iona", PARCELS[1], SETTINGS[1], 1),
    ]
    for params in cases:
        py_ok = python_reasonable(params)
        model = asp.one_model(asp_program(params))
        asp_ok = any(sym.name == "valid_story" for sym in model)
        if py_ok != asp_ok or not generate(params).story:
            print("MISMATCH: ASP and Python reasonableness checks disagree.")
            return 1

    invalid = StoryParams("Mairi", "Mairi", PARCELS[0], SETTINGS[0], 2)
    if python_reasonable(invalid):
        print("MISMATCH: Python accepted identical child and granny names.")
        return 1
    print("OK: ASP/Python parity holds and generated stories are complete.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Scottish bedtime story world about a parcel, sounds, and understanding."
    )
    parser.add_argument("--child-name")
    parser.add_argument("--granny-name")
    parser.add_argument("--parcel", choices=PARCELS)
    parser.add_argument("--setting", choices=SETTINGS)
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
    child = args.child_name or rng.choice(CHILD_NAMES)
    available = [name for name in GRANNY_NAMES if name.casefold() != child.casefold()]
    granny = args.granny_name or rng.choice(available)
    return StoryParams(
        child_name=child,
        granny_name=granny,
        parcel=args.parcel or rng.choice(PARCELS),
        setting=args.setting or rng.choice(SETTINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
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
    if args.n < 1 and not args.all:
        raise SystemExit("-n must be at least 1.")
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program())
        print("1 compatible Scottish bedtime story pattern." if model else "No compatible story.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Mairi", "Morag", parcel, setting, i)
            for i, (parcel, setting) in enumerate(
                zip(PARCELS, SETTINGS)
            )
        ]
    else:
        params_list = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            params_list.append(params)

    samples = [generate(params) for params in params_list]
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
