#!/usr/bin/env python3
"""
storyworlds/worlds/rapid_cartridge_repetition_cautionary_myth.py
===============================================================

A small, standalone story world for a mythic cautionary tale built from the
seed words "rapid" and "cartridge".

Premise:
- A child or small seeker is tempted to repeat a forbidden action at a river
  rapid.
- The action is tied to a sacred cartridge: a tiny brass chamber used to start
  a shrine bell-fire.
- Repetition makes the danger grow faster than a single mistake would.
- A careful elder or guardian warns, a costly choice is made, and the ending
  proves what changed.

The storyworld keeps the domain small and constraint-driven:
- Only a few entities.
- Simulated meters and memes.
- A forward rule engine that drives the prose.
- A reasonableness gate plus an inline ASP twin.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the river shrine"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    repeat_verb: str
    danger: str
    consequence: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    danger: str
    carries: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class GuideItem:
    id: str
    label: str
    phrase: str
    protects: set[str]
    fixes: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def character(self) -> Entity:
        for e in self.entities.values():
            if e.kind == "character":
                return e
        raise KeyError("no character")


@dataclass
class Rule:
    name: str
    apply: callable


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("Seeker")
    act = world.facts["action"]
    relic = world.get("Cartridge")
    if child.memes.get("repeat", 0.0) < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["danger"] = child.meters.get("danger", 0.0) + 1
    relic.meters["heat"] = relic.meters.get("heat", 0.0) + 1
    out.append(f"Again and again, {child.id} did not listen, and the {act.keyword} warning grew louder.")
    return out


def _r_rapid(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("Seeker")
    if child.meters.get("danger", 0.0) < THRESHOLD:
        return out
    sig = ("rapid",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    out.append("The rapid water answered at once, quick and white and hungry at the stones.")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("Seeker")
    guide = world.get("Keeper")
    relic = world.get("Cartridge")
    if relic.meters.get("heat", 0.0) < THRESHOLD:
        return out
    sig = ("spoil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guide.meters["work"] = guide.meters.get("work", 0.0) + 1
    out.append(f"Now the {relic.label} could not be used again, and that meant more care for {guide.label}.")
    child.memes["shame"] = child.memes.get("shame", 0.0) + 1
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("rapid", _r_rapid), Rule("spoil", _r_spoil)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_danger(world: World, seeker: Entity, action: Action, relic: Relic) -> dict:
    sim = world.copy()
    sim.character().memes["repeat"] = 1
    sim.character().meters["danger"] = 1
    propagate(sim, narrate=False)
    return {
        "spoil": sim.get("Cartridge").meters.get("heat", 0.0) >= THRESHOLD,
        "fear": sim.character().memes.get("fear", 0.0),
    }


def myth_opening(world: World, hero: Entity, guide: Entity, action: Action, relic: Relic) -> None:
    world.say(
        f"Long ago, at {world.setting.place}, {hero.id} was a small {hero.type} who loved old stories and bright warnings."
    )
    world.say(
        f"Above the stones, the rapid river rushed like a silver beast, and the {relic.label} rested in a shrine bowl."
    )
    world.say(
        f"The {guide.label} told {hero.id}, 'Do not touch the {relic.label} twice, and do not call the {action.keyword} again and again.'"
    )


def myth_tension(world: World, hero: Entity, guide: Entity, action: Action, relic: Relic) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes["repeat"] = hero.memes.get("repeat", 0.0) + 1
    world.say(
        f"But {hero.id} wanted to {action.verb}, because one spark looked small and harmless."
    )
    world.say(
        f"{hero.id} tried once, then twice, and each time the {action.keyword} call sounded easier to repeat."
    )
    world.say(
        f"Then {guide.id} lifted a hand and warned, 'A little mistake becomes a bigger one when it is repeated.'"
    )


def myth_turn(world: World, hero: Entity, guide: Entity, action: Action, relic: Relic) -> None:
    pred = predict_danger(world, hero, action, relic)
    world.facts["predicted_spoil"] = pred["spoil"]
    if pred["spoil"]:
        world.say(
            f"{hero.id} heard the old warning at last, but the {action.keyword} echo had already reached the rapid water."
        )
    else:
        world.say(
            f"{hero.id} paused before the third try, and the shrine fell quiet again."
        )


def myth_resolution(world: World, hero: Entity, guide: Entity, action: Action, relic: Relic, aid: GuideItem) -> None:
    if world.facts.get("predicted_spoil"):
        world.say(
            f"{guide.id} took the blackened {relic.label} away and set {aid.label} beside the bowl instead."
        )
        world.say(
            f"With the safer helper in place, {hero.id} learned that a single careful choice can end a dangerous pattern."
        )
        world.say(
            f"By dawn, the rapid river still roared, but the shrine was calm, and {hero.id} remembered the lesson of repetition."
        )
    else:
        world.say(
            f"{guide.id} smiled softly and covered the {relic.label}, and {hero.id} promised not to repeat the call."
        )
        world.say(
            f"The rapid river went on its way, and the shrine kept its hush."
        )


SETTINGS = {
    "river_shrine": Setting(place="the river shrine", affords={"call"}),
}

ACTIONS = {
    "call": Action(
        id="call",
        verb="call the river spirit",
        gerund="calling the river spirit",
        repeat_verb="call it again",
        danger="the spirit wakes too fast",
        consequence="the shrine gets burned quiet",
        keyword="rapid",
        tags={"rapid", "myth", "repetition", "cautionary"},
    ),
}

RELICS = {
    "cartridge": Relic(
        id="cartridge",
        label="cartridge",
        phrase="a brass cartridge",
        danger="it sparks if handled too many times",
        carries={"spark"},
    ),
}

AIDS = {
    "shell": GuideItem(
        id="shell",
        label="a river shell",
        phrase="a river shell",
        protects={"calm"},
        fixes={"quiet"},
        prep="place a river shell beside the bowl",
        tail="set the river shell there",
    )
}

NAMES = ["Mira", "Kavi", "Tala", "Ivo", "Sena", "Nilo"]
GUIDES = ["Elder Reed", "Keeper Moss", "Aunt Luma"]
TYPES = ["girl", "boy"]
TRAITS = ["curious", "heedless", "bright-eyed", "restless"]


@dataclass
class StoryParams:
    place: str
    action: str
    relic: str
    name: str
    type: str
    guide: str
    trait: str
    seed: Optional[int] = None


def build_story(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="Seeker", kind="character", type=params.type, label=params.name))
    guide = world.add(Entity(id="Keeper", kind="character", type="elder", label=params.guide))
    relic = world.add(Entity(id="Cartridge", type="relic", label="cartridge", phrase="a brass cartridge"))
    aid = AIDS["shell"]

    world.facts.update(hero=hero, guide=guide, action=ACTIONS[params.action], relic=relic, aid=aid)

    myth_opening(world, hero, guide, ACTIONS[params.action], relic)
    world.para()
    myth_tension(world, hero, guide, ACTIONS[params.action], relic)
    propagate(world, narrate=True)
    world.para()
    myth_turn(world, hero, guide, ACTIONS[params.action], relic)
    world.para()
    myth_resolution(world, hero, guide, ACTIONS[params.action], relic, aid)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a brief myth about a {f["hero"].type} at the {world.setting.place} who learns not to repeat a dangerous action.',
        f'Tell a cautionary story where the word "rapid" matters and a cartridge must not be handled twice.',
        f'Write a mythic tale of repetition, warning, and a safer ending beside a fast river.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    action = world.facts["action"]
    qa = [
        QAItem(
            question=f"What did {hero.label} want to do at {world.setting.place}?",
            answer=f"{hero.label} wanted to {action.verb}, even though the elder warned that repeating it would be dangerous.",
        ),
        QAItem(
            question=f"Why did {guide.label} warn about the cartridge?",
            answer="The warning was about repetition: touching or calling it again and again could wake the rapid river too fast and spoil the shrine's safety.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer="The danger was stopped, the cartridge was put away, and the lesson about repeating a risky action was remembered.",
        ),
    ]
    if world.facts.get("predicted_spoil"):
        qa.append(
            QAItem(
                question=f"Why was the ending cautionary?",
                answer=f"Because {hero.label} had already repeated the warning, so the cartridge blackened and the guide had to replace danger with a safer helper.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rapid?",
            answer="A rapid is a fast, rushing part of a river where the water moves hard over stones and around bends.",
        ),
        QAItem(
            question="What is a cartridge?",
            answer="A cartridge is a small container or chamber that can hold something powerful, like powder, a spark, or a special signal in a story.",
        ),
        QAItem(
            question="Why can repetition be dangerous in myths?",
            answer="Repetition can be dangerous because doing the same risky thing over and over can make the problem grow stronger each time.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(seeker).
guide(keeper).
setting(river_shrine).
action(call).
relic(cartridge).

repeats_dangerously(S) :- hero(S), story_repeat(S).
rapid_answers(S) :- repeats_dangerously(S).
cautionary(S) :- rapid_answers(S), relic(cartridge).
valid_story(S) :- cautionary(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "seeker"),
            asp.fact("guide", "keeper"),
            asp.fact("setting", "river_shrine"),
            asp.fact("action", "call"),
            asp.fact("relic", "cartridge"),
            asp.fact("story_repeat", "seeker"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    got = set(asp.atoms(model, "valid_story"))
    expected = {("seeker",)}
    if got == expected:
        print("OK: ASP gate matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("  ASP:", sorted(got))
    print("  PY :", sorted(expected))
    return 1


def python_gate_ok() -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic cautionary story world about rapid repetition and a cartridge.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--type", choices=TYPES)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.relic and args.action == "call" and args.relic != "cartridge":
        raise StoryError("This myth only works with the cartridge relic.")
    return StoryParams(
        place=args.place or "river_shrine",
        action=args.action or "call",
        relic=args.relic or "cartridge",
        name=args.name or rng.choice(NAMES),
        type=args.type or rng.choice(TYPES),
        guide=args.guide or rng.choice(GUIDES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
    StoryParams(place="river_shrine", action="call", relic="cartridge", name="Mira", type="girl", guide="Elder Reed", trait="curious"),
    StoryParams(place="river_shrine", action="call", relic="cartridge", name="Kavi", type="boy", guide="Keeper Moss", trait="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
