#!/usr/bin/env python3
"""
A small Storyweavers world: a child, a schnauzer, a brave gaze, and a soft
nursery-rhyme turn.

This world is intentionally tiny and classical:
- a child feels wary at dusk,
- a schnauzer notices with a steady gaze,
- bravery grows when they look together,
- the ending proves something changed in the world and in the heart.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    time: str
    path: str
    afford_gaze: bool = True


@dataclass
class Creature:
    id: str
    kind: str
    name: str
    size: str
    bravery_hint: str
    gaze_target: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    creature: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        w = World(self.setting)
        import copy as _copy
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "garden": Setting(place="the garden", time="at dusk", path="the little stone path"),
    "yard": Setting(place="the yard", time="near bedtime", path="the back path"),
    "porch": Setting(place="the porch", time="under the moon", path="the porch steps"),
}

CREATURES = {
    "schnauzer": Creature(
        id="schnauzer",
        kind="animal",
        name="a schnauzer",
        size="small",
        bravery_hint="a steady little nose and a brave beard",
        gaze_target="the dark gate",
        tags={"schnauzer", "dog", "gaze", "bravery"},
    ),
}

GENTLE_NICKNAMES = ["Milo", "Nina", "Ruby", "Theo", "Ivy", "Luna", "Eli", "Maya"]


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, creature) for setting in SETTINGS for creature in CREATURES]


def reasonableness_gate(setting: str, creature: str) -> None:
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if creature not in CREATURES:
        raise StoryError("Unknown creature.")
    if setting == "porch" and creature == "schnauzer":
        return
    if setting in SETTINGS and creature in CREATURES:
        return
    raise StoryError("That story shape is not reasonable.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny nursery-rhyme storyworld about gaze and bravery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    creature = args.creature or rng.choice(list(CREATURES))
    reasonableness_gate(setting, creature)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GENTLE_NICKNAMES)
    companion = args.companion or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, creature=creature, name=name, gender=gender, companion=companion)


def story_intro(world: World, child: Entity, carer: Entity, creature: Creature) -> None:
    world.say(
        f"Little {child.id} was a {child.type} who loved a quiet gaze, "
        f"and {carer.label} loved to walk beside {child.pronoun('object')}."
    )
    world.say(
        f"In {world.setting.place}, {world.setting.time}, there was "
        f"{creature.name} with {creature.bravery_hint}."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    creature = CREATURES[params.creature]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    carer = world.add(Entity(id=params.companion, kind="character", type="parent", label=f"the {params.companion}"))
    pup = world.add(Entity(
        id="schnauzer",
        kind="animal",
        type="schnauzer",
        label="the schnauzer",
        phrase="a small schnauzer with bright eyes",
    ))
    child.memes["unease"] = 1.0
    child.memes["bravery"] = 0.0
    pup.memes["bravery"] = 1.0
    pup.meters["attention"] = 1.0

    story_intro(world, child, carer, creature)
    world.para()
    world.say(
        f"{params.name} tiptoed by the {setting.path} and looked toward {creature.gaze_target}, "
        f"but the shadows made {child.pronoun('object')} pause."
    )
    world.say(
        f"Then the schnauzer sat right still, and with one steady gaze it looked too."
    )
    child.memes["unease"] += 0.5
    child.memes["bravery"] += 0.5
    world.trace.append("schnauzer notices the dark place and stays calm")

    world.para()
    world.say(
        f"{params.name} took a breath and copied the schnauzer's brave gaze. "
        f"One little step, then two, along the path."
    )
    child.memes["bravery"] += 1.0
    child.memes["unease"] = max(0.0, child.memes["unease"] - 1.0)
    world.trace.append("child follows the dog and courage grows")

    world.para()
    world.say(
        f"Out from the shadow rolled a lost silver ball, bright as a star. "
        f"{params.name} smiled, because the scary dark had only been hiding a toy."
    )
    world.say(
        f"So the child picked up the ball, the schnauzer wagged its tail, and bravery stayed in {params.name}'s heart."
    )
    world.trace.append("the feared dark turns out to hide something small and harmless")

    world.facts.update(
        child=child,
        carer=carer,
        creature=creature,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    carer = f["carer"]
    creature = f["creature"]
    return [
        "Write a short nursery-rhyme style story about a child, a schnauzer, and a brave gaze.",
        f"Tell a gentle story where {child.id} feels unsure, but {creature.name} helps {child.id} become brave.",
        f"Write a simple bedtime story set in {world.setting.place} with a schnauzer and a little moment of courage.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    carer = f["carer"]
    creature = f["creature"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who learned to be brave in {setting.place}?",
            answer=f"{child.id} learned to be brave in {setting.place} after watching the schnauzer's steady gaze.",
        ),
        QAItem(
            question=f"What did the schnauzer do to help {child.id}?",
            answer="The schnauzer sat still and kept a calm gaze, which helped the child copy that brave way of looking.",
        ),
        QAItem(
            question=f"What was hiding in the shadows?",
            answer="A lost silver ball was hiding in the shadows, so the dark turned out to be harmless.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a schnauzer?",
            answer="A schnauzer is a small dog with a wiry coat and bright, watchful eyes.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means being scared or unsure and still taking a careful step forward.",
        ),
        QAItem(
            question="What is a gaze?",
            answer="A gaze is a long, steady look at something.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for t in world.trace:
        lines.append(f"- {t}")
    lines.append("--- entity state ---")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_brave(C) :- child(C), feels_uneasy(C), sees_schnauzer(C), steady_gaze(schnauzer).
resolved(C) :- child_brave(C), finds_ball(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("schnauzer", "schnauzer"))
    lines.append(asp.fact("feels_uneasy", "child"))
    lines.append(asp.fact("sees_schnauzer", "child"))
    lines.append(asp.fact("steady_gaze", "schnauzer"))
    lines.append(asp.fact("finds_ball", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show child_brave/1.\n#show resolved/1."))
    atoms = set()
    for sym in model:
        if sym.name in {"child_brave", "resolved"}:
            atoms.add((sym.name, tuple(getattr(a, "name", getattr(a, "string", getattr(a, "number", None))) for a in sym.arguments)))
    if ("child_brave", ("child",)) in atoms and ("resolved", ("child",)) in atoms:
        print("OK: ASP parity looks reasonable.")
        return 0
    print("ASP parity mismatch.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show child_brave/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show child_brave/1.\n#show resolved/1."))
        print(" ".join(str(s) for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(setting=s, creature=c, name="Mia", gender="girl", companion="mother")
            for s, c in valid_combos()
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
