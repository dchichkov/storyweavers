#!/usr/bin/env python3
"""
A small bedtime-story world about a child, a treasured clutch, and a moral choice.

Seed premise:
- A child finds a little clutch of stars-and-ribbon pieces that can be used to
  decorate a bedtime craft.
- The child wants to keep the prettiest piece, but a sibling needs it for the
  shared blanket fort.
- A gentle parent helps them notice that sharing makes the night brighter.

This script models:
- physical meters: held, hidden, shared, decorated, tidy, sleepy
- emotional memes: desire, worry, kindness, pride, peace, guilt

The story always resolves with a moral-value turn: honesty, sharing, patience,
or kindness becomes the key that settles the bedtime tension.
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

MORAL_VALUES = ["sharing", "honesty", "patience", "kindness"]

PLACES = {
    "bedroom": "the bedroom",
    "nursery": "the nursery",
    "attic": "the attic play nook",
    "cabin": "the little cabin room",
}

CHARACTER_NAMES = ["Mina", "Eli", "Noor", "Iris", "Toby", "Finn", "Lia", "Sami"]
SIBLING_NAMES = ["Poppy", "Milo", "June", "Ari", "Bea", "Rowan", "Ada", "Owen"]

CLUTCH_KINDS = {
    "star_clutch": {
        "label": "a tiny star clutch",
        "phrase": "a tiny clutch stitched with gold stars",
        "detail": "golden stars",
        "use": "hold bedtime wishes",
        "value": "sharing",
    },
    "moon_clutch": {
        "label": "a moon clutch",
        "phrase": "a soft little clutch with a silver moon",
        "detail": "silver moon",
        "use": "carry sleepy treasures",
        "value": "honesty",
    },
    "flower_clutch": {
        "label": "a flower clutch",
        "phrase": "a cloth clutch with small flower buttons",
        "detail": "flower buttons",
        "use": "keep tiny bedtime things",
        "value": "kindness",
    },
}

BEDTIME_TASKS = {
    "tidy": "put away the blocks",
    "read": "choose a storybook",
    "light": "carry the night-light",
    "blanket": "set out the blanket fort",
}

ASP_RULES = r"""
% Moral choice is valid when the clutch is wanted, the sibling needs it,
% and the parent can guide a gentle solution.
valid_story(P, C, V) :- place(P), clutch(C), value(V), possible(P, C, V).
moral_turn(C, V) :- clutch(C), value(V), moral_match(C, V).
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["held", "hidden", "shared", "decorated", "tidy", "sleepy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["desire", "worry", "kindness", "pride", "peace", "guilt", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self) -> str:
        return "it" if self.kind != "character" else "they"

@dataclass
class Setting:
    place: str
    bedtime: bool = True
    cozy: bool = True

@dataclass
class ClutchSpec:
    id: str
    label: str
    phrase: str
    value: str
    detail: str

@dataclass
class StoryParams:
    place: str
    clutch: str
    hero: str
    sibling: str
    seed: Optional[int] = None

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

def _morality_for(clutch_id: str) -> str:
    return CLUTCH_KINDS[clutch_id]["value"]

def _clutch_obj(clutch_id: str) -> ClutchSpec:
    d = CLUTCH_KINDS[clutch_id]
    return ClutchSpec(id=clutch_id, label=d["label"], phrase=d["phrase"], value=d["value"], detail=d["detail"])

def build_world(params: StoryParams) -> World:
    world = World(Setting(place=PLACES[params.place]))
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="child", label=params.sibling))
    clutch = _clutch_obj(params.clutch)
    item = world.add(Entity(
        id="clutch",
        type="clutch",
        label=clutch.label,
        phrase=clutch.phrase,
        owner=hero.id,
        held_by=hero.id,
    ))
    item.meters["held"] = 1

    hero.memes["love"] += 1
    hero.memes["desire"] += 1
    hero.memes["worry"] += 0.5
    sibling.memes["desire"] += 1
    sibling.memes["worry"] += 0.5

    world.say(f"{hero.id} had {clutch.phrase} that felt warm in sleepy hands.")
    world.say(f"It was bedtime in {world.setting.place}, and the room glowed with a soft, cozy light.")
    world.say(f"{hero.id} loved the clutch because it could {clutch.value} little bedtime wishes.")

    world.para()
    task = BEDTIME_TASKS["blanket" if clutch.value == "sharing" else "read"]
    world.say(f"That night, {sibling.id} needed the clutch to {task} for the blanket fort.")
    world.say(f"{hero.id} clutched it tighter and whispered, 'I found it first.'")
    hero.memes["guilt"] += 0.5
    sibling.memes["worry"] += 1

    world.para()
    world.say(f"The parent sat beside them and spoke gently: 'A good bedtime choice can make the whole room peaceful.'")
    if clutch.value == "sharing":
        hero.memes["kindness"] += 1
        hero.memes["peace"] += 1
        sibling.memes["peace"] += 1
        item.meters["shared"] = 1
        item.held_by = sibling.id
        world.say(f"{hero.id} thought about sharing, then placed the clutch in {sibling.id}'s palm.")
        world.say(f"{sibling.id} smiled and used it to hold the fort flap closed while {hero.id} tucked in the pillows.")
    elif clutch.value == "honesty":
        hero.memes["kindness"] += 0.5
        hero.memes["peace"] += 1
        sibling.memes["peace"] += 1
        item.meters["shared"] = 1
        world.say(f"{hero.id} took a breath and told the truth: 'I wanted to keep it, but I know it belongs in our bedtime game.'")
        world.say(f"The parent smiled, and {sibling.id} thanked {hero.id} for being honest.")
    elif clutch.value == "patience":
        hero.memes["kindness"] += 0.5
        hero.memes["peace"] += 1
        sibling.memes["peace"] += 1
        world.say(f"{hero.id} waited patiently while the parent finished the storybook page.")
        world.say(f"Then {hero.id} handed over the clutch, and waiting had turned the room quiet and sweet.")
        item.meters["shared"] = 1
        item.held_by = sibling.id
    else:
        hero.memes["kindness"] += 1
        hero.memes["peace"] += 1
        sibling.memes["peace"] += 1
        item.meters["decorated"] = 1
        world.say(f"{hero.id} used kindness and offered, 'We can both use it if we take turns.'")
        world.say(f"Together they clipped the clutch onto the blanket fort, where it shone like a small moon.")
        item.meters["shared"] = 1
        item.held_by = None

    world.para()
    world.say(f"At last, the room grew very still.")
    world.say(f"{hero.id} and {sibling.id} lay beneath the blanket fort, calm and sleepy, while the little clutch helped the night feel safe and kind.")

    world.facts.update(hero=hero, sibling=sibling, clutch=item, clutch_spec=clutch, setting=world.setting)
    return world

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story for a small child about {f["hero"].id}, {f["sibling"].id}, and {f["clutch_spec"].label}.',
        f"Tell a cozy story where {f['hero'].id} learns {f['clutch_spec'].value} at bedtime in {f['setting'].place}.",
        "Write a short bedtime story about a child holding a treasured clutch and choosing a moral value.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    clutch = f["clutch"]
    value = f["clutch_spec"].value
    return [
        QAItem(
            question=f"What did {hero.id} hold tightly at bedtime?",
            answer=f"{hero.id} held a {clutch.label} that could help the bedtime moment feel special.",
        ),
        QAItem(
            question=f"Why did {hero.id} have to make a choice about the clutch?",
            answer=f"{sibling.id} needed it for the shared bedtime game, so {hero.id} had to choose whether to keep it or share it.",
        ),
        QAItem(
            question=f"What moral value helped solve the problem?",
            answer=f"{value.capitalize()} helped solve it, because {hero.id} chose a gentle bedtime way forward.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {sibling.id} calm and sleepy, with the clutch used in a kind bedtime way.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    value = f["clutch_spec"].value
    return [
        QAItem(
            question="What is a bedtime story?",
            answer="A bedtime story is a gentle story told at night to help a child feel calm, safe, and ready for sleep.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something too, so both people can enjoy it.",
        ),
        QAItem(
            question="What does a clutch mean in this story?",
            answer="A clutch is a small thing someone can hold carefully, like a tiny pouch or treasured bundle.",
        ),
        QAItem(
            question="Why are moral values important in stories?",
            answer="Moral values like kindness or honesty help characters make good choices and solve problems gently.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} meters={meters} memes={memes} held_by={e.held_by}")
    return "\n".join(lines)

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for cid, spec in CLUTCH_KINDS.items():
        lines.append(asp.fact("clutch", cid))
        lines.append(asp.fact("value", spec["value"]))
        lines.append(asp.fact("moral_match", cid, spec["value"]))
    for v in MORAL_VALUES:
        lines.append(asp.fact("possible", "bedroom", "star_clutch", v))
        lines.append(asp.fact("possible", "nursery", "moon_clutch", v))
        lines.append(asp.fact("possible", "attic", "flower_clutch", v))
        lines.append(asp.fact("possible", "cabin", "star_clutch", v))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show moral_turn/2."))
    got_valid = sorted(set(asp.atoms(model, "valid_story")))
    got_turn = sorted(set(asp.atoms(model, "moral_turn")))
    expected_valid = [(p, c, v) for p in PLACES for c in CLUTCH_KINDS for v in MORAL_VALUES if v == _moral_for(c)]
    expected_turn = [(c, _moral_for(c)) for c in CLUTCH_KINDS]
    if got_valid == expected_valid and got_turn == expected_turn:
        print(f"OK: ASP matches Python gate ({len(got_valid)} valid stories).")
        return 0
    print("MISMATCH")
    print("asp valid:", got_valid)
    print("py valid:", expected_valid)
    print("asp turn:", got_turn)
    print("py turn:", expected_turn)
    return 1

def _moral_for(clutch_id: str) -> str:
    return CLUTCH_KINDS[clutch_id]["value"]

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for c in CLUTCH_KINDS:
            v = _moral_for(c)
            out.append((p, c, v))
    return out

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about a clutch and a moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clutch", choices=CLUTCH_KINDS)
    ap.add_argument("--hero")
    ap.add_argument("--sibling")
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
    place = args.place or rng.choice(list(PLACES))
    clutch = args.clutch or rng.choice(list(CLUTCH_KINDS))
    hero = args.hero or rng.choice(CHARACTER_NAMES)
    sibling = args.sibling or rng.choice([n for n in SIBLING_NAMES if n != hero])
    if hero == sibling:
        sibling = rng.choice([n for n in SIBLING_NAMES if n != hero])
    return StoryParams(place=place, clutch=clutch, hero=hero, sibling=sibling)

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
        print(format_qa(sample))

CURATED = [
    StoryParams(place="bedroom", clutch="star_clutch", hero="Mina", sibling="Poppy"),
    StoryParams(place="nursery", clutch="moon_clutch", hero="Eli", sibling="June"),
    StoryParams(place="attic", clutch="flower_clutch", hero="Noor", sibling="Ari"),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show moral_turn/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 50):
            seed = base_seed + i
            i += 1
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
