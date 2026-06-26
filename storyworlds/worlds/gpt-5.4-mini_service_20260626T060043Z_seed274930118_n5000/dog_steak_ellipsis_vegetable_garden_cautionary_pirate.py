#!/usr/bin/env python3
"""
A cautionary pirate tale in a vegetable garden: a hungry dog, a tempting steak,
and a little ellipsis of hesitation that keeps the garden safe.

The story world is small and classical:
- A dog wants steak.
- The vegetable garden belongs to a careful gardener.
- The dog is warned not to rush in and disturb the beds.
- A pirate-style cautionary turn ends with a safe choice and a calmer ending.

This script is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PEOPLE = {
    "captain": "Captain Moss",
    "gardener": "Old Mara",
    "dog": "Brindle",
}

SETTINGS = {
    "vegetable_garden": {
        "place": "the vegetable garden",
        "detail": "rows of peas, carrots, and tomatoes",
    }
}

TREATS = {
    "steak": {
        "label": "steak",
        "phrase": "a juicy steak",
        "risk": "tempting",
    }
}

WARNING_STYLES = {
    "cautionary": "cautionary",
}

# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = None
    memes: dict[str, float] = None

    def __post_init__(self) -> None:
        if self.meters is None:
            self.meters = {"mess": 0.0, "damage": 0.0}
        if self.memes is None:
            self.memes = {"hunger": 0.0, "caution": 0.0, "relief": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]


@dataclass
class World:
    place: str
    detail: str
    entities: dict[str, Entity]
    paragraphs: list[list[str]]
    facts: dict

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def copy(self) -> "World":
        import copy
        return World(
            place=self.place,
            detail=self.detail,
            entities=copy.deepcopy(self.entities),
            paragraphs=[[]],
            facts=dict(self.facts),
        )


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "vegetable_garden"
    treat: str = "steak"
    caution: str = "cautionary"
    dog_name: str = "Brindle"
    gardener_name: str = "Old Mara"
    captain_name: str = "Captain Moss"
    seed: Optional[int] = None


SETTINGS_REGISTRY = SETTINGS
TREAT_REGISTRY = TREATS
CAUTION_REGISTRY = WARNING_STYLES


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treat is tempting when it is present in the story.
tempting(T) :- treat(T).

% A story is valid if a dog, a steak, and a vegetable garden are all present.
valid_story(S, T, C) :- setting(S), treat(T), caution(C),
                        setting_name(S, "vegetable_garden"),
                        treat_name(T, "steak"),
                        caution_name(C, "cautionary").

% The story is cautionary if the dog is warned before charging into the beds.
cautionary_story :- dog(_, _), warning_said, safe_choice.
#show valid_story/3.
#show cautionary_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_name", sid, "vegetable_garden"))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("treat_name", tid, "steak"))
    for cid, c in WARNING_STYLES.items():
        lines.append(asp.fact("caution", cid))
        lines.append(asp.fact("caution_name", cid, "cautionary"))
    lines.append(asp.fact("dog", "brindle", "dog"))
    lines.append(asp.fact("garden", "vegetable_garden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = bool(valid_combos())
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness gates match.")
        return 0
    print("MISMATCH: ASP and Python reasonableness gates differ.")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [("vegetable_garden", "steak", "cautionary")]


def explain_rejection(setting: str, treat: str, caution: str) -> str:
    return (
        f"(No story: only the careful pirate tale in the vegetable garden works "
        f"here. Got setting={setting}, treat={treat}, caution={caution}, but the "
        f"world only supports a dog, a steak, and a warning before the garden is disturbed.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(
        place=setting["place"],
        detail=setting["detail"],
        entities={},
        paragraphs=[[]],
        facts={},
    )
    dog = Entity(id="dog", kind="character", type="dog", label=params.dog_name)
    gardener = Entity(id="gardener", kind="character", type="human", label=params.gardener_name)
    captain = Entity(id="captain", kind="character", type="human", label=params.captain_name)
    steak = Entity(id="steak", kind="thing", type="food", label="steak", phrase="a juicy steak", owner="gardener")
    world.entities = {"dog": dog, "gardener": gardener, "captain": captain, "steak": steak}
    return world


def predict_trouble(world: World) -> bool:
    dog = world.get("dog")
    return dog.memes["hunger"] >= 1.0


def tell_story(world: World) -> None:
    dog = world.get("dog")
    gardener = world.get("gardener")
    captain = world.get("captain")
    steak = world.get("steak")

    world.say(
        f"On a blustery day, {dog.label} the dog skulked by {world.place}, "
        f"where {world.detail} grew under the sun."
    )
    world.say(
        f"Far off, {gardener.label} guarded {steak.phrase}, and the smell drifted across the fence like a siren song."
    )
    world.para()
    dog.memes["hunger"] += 1.0
    world.say(
        f"{dog.label} licked {dog.pronoun('possessive')} chops and stared at the yard. "
        f"\"Steak...\" {dog.pronoun()} whispered, with a hungry little ellipsis."
    )
    world.say(
        f"{captain.label} the pirate came tapping along the path and frowned. "
        f"\"Arrr, no snatching from a vegetable garden,\" {captain.pronoun()} warned. "
        f"\"That way lies trouble...\""
    )
    world.facts["warning_said"] = True

    world.para()
    if predict_trouble(world):
        dog.memes["caution"] += 1.0
        world.say(
            f"{dog.label} took one step forward, then stopped. "
            f"The warning hung in the air, and the dog remembered the carrots, the beans, and the patient hands that watered them."
        )
        world.say(
            f"Instead of barrelling in, {dog.label} sat beside the gate and waited. "
            f"{gardener.label} noticed the good choice, smiled, and cut a small piece from the steak bowl for later."
        )
        world.facts["safe_choice"] = True
        dog.memes["relief"] += 1.0
    else:
        world.say(
            f"{dog.label} was not tempted enough to make a fuss, and the garden stayed neat."
        )
        world.facts["safe_choice"] = True

    world.say(
        f"In the end, {dog.label} left the garden beds untrampled, "
        f"and the little pirate warning had done its job."
    )


def generate_world(params: StoryParams) -> World:
    if (params.setting, params.treat, params.caution) not in valid_combos():
        raise StoryError(explain_rejection(params.setting, params.treat, params.caution))
    world = build_world(params)
    tell_story(world)
    world.facts.update(
        setting=params.setting,
        treat=params.treat,
        caution=params.caution,
        dog=world.get("dog"),
        gardener=world.get("gardener"),
        captain=world.get("captain"),
        steak=world.get("steak"),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short cautionary pirate tale about a dog, a steak, and a vegetable garden.',
        'Tell a simple story where a hungry dog almost rushes toward a steak but stops after a warning.',
        'Create a child-friendly pirate warning story that includes the word "ellipsis" and ends safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    dog = world.get("dog")
    gardener = world.get("gardener")
    captain = world.get("captain")
    return [
        QAItem(
            question="Who wanted the steak in the vegetable garden?",
            answer=f"{dog.label} the dog wanted the steak, but the garden was not a place for snatching things.",
        ),
        QAItem(
            question="Who gave the cautionary warning?",
            answer=f"{captain.label} the pirate gave the warning and told the dog not to disturb the garden beds.",
        ),
        QAItem(
            question="What choice kept the garden safe?",
            answer=f"{dog.label} stopped at the gate and waited, which kept {gardener.label}'s vegetable garden neat and safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vegetable garden?",
            answer="A vegetable garden is a place where people grow foods like peas, carrots, beans, and tomatoes in tidy beds.",
        ),
        QAItem(
            question="What does a cautionary warning do?",
            answer="A cautionary warning tries to stop a risky choice before it causes trouble.",
        ),
        QAItem(
            question="What is an ellipsis?",
            answer="An ellipsis is a little trail of dots that can show a pause, hesitation, or a thought that is not finished yet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary pirate tale in a vegetable garden.")
    ap.add_argument("--setting", choices=SETTINGS_REGISTRY, default="vegetable_garden")
    ap.add_argument("--treat", choices=TREAT_REGISTRY, default="steak")
    ap.add_argument("--caution", choices=CAUTION_REGISTRY, default="cautionary")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if (args.setting, args.treat, args.caution) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.treat, args.caution))
    return StoryParams(
        setting=args.setting,
        treat=args.treat,
        caution=args.caution,
        dog_name=PEOPLE["dog"],
        gardener_name=PEOPLE["gardener"],
        captain_name=PEOPLE["captain"],
        seed=args.seed if args.seed is not None else rng.randrange(1 << 30),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type}, label={e.label}, meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}}, "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"facts: {world.facts}")
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
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show cautionary_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        atoms = asp.atoms(model, "valid_story")
        print(f"{len(atoms)} valid story combination(s):")
        for a in atoms:
            print("  ", a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(1 << 30)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(seed=base_seed)
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 10):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### sample {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
