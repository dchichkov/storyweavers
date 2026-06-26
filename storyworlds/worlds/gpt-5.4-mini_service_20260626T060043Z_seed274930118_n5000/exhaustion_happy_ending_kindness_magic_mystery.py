#!/usr/bin/env python3
"""
A small story world about a mysterious tired-out day, where kindness and a tiny
bit of magic lead to a happy ending.

Premise:
- A child notices something strange: the town's lanterns are dim, the helper
  birds are sleepy, and everyone feels worn out.
- The child follows clues through a cozy setting.
- A kind act reveals a magical cause: a moonstone music box is draining energy
  because it has been wound too tightly.
- The child and a helper solve the mystery gently, restoring warmth and ending
  the day with relief, kindness, and a happy ending.

The world uses meters for physical states and memes for emotional states.
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

SETTING_CHOICES = {
    "library": "the little library",
    "garden": "the moonlit garden",
    "village": "the sleepy village",
    "attic": "the dusty attic",
}

HERO_NAMES = ["Mina", "Eli", "Nora", "Toby", "Iris", "Leo", "Asha", "Pip"]
HELPER_NAMES = ["Grandma", "Mr. Finch", "Aunt Lila", "Mrs. Moon", "Papa", "Mama"]
TONE_WORDS = ["quiet", "careful", "gentle", "soft", "curious"]
MAGIC_ITEMS = {
    "music_box": {
        "label": "moonstone music box",
        "clue": "a silver tune",
        "effect": "hum",
        "cause": "it had been wound too tightly",
    },
    "lantern": {
        "label": "glow lantern",
        "clue": "a pale spark",
        "effect": "shine",
        "cause": "its light had been used up by a spell",
    },
    "teacup": {
        "label": "starry teacup",
        "clue": "a tiny twinkle",
        "effect": "warmth",
        "cause": "it had been shared with too many sleepy guests",
    },
}

MAGIC_AIDS = {
    "song": {
        "label": "a humming song",
        "kindness": "shared a humming song",
        "fix": "the tune eased the tired magic",
    },
    "blanket": {
        "label": "a soft blanket",
        "kindness": "wrapped the helper in a soft blanket",
        "fix": "rest helped the magic settle down",
    },
    "tea": {
        "label": "warm tea",
        "kindness": "poured warm tea for everyone",
        "fix": "the warmth brought the room back to life",
    },
}

CLUES = [
    "dim lanterns",
    "sleepy footsteps",
    "a faint silver sound",
    "a trail of glitter on the floor",
    "a yawn from the hallway",
]

WORLD_KNOWLEDGE = {
    "exhaustion": [
        QAItem(
            question="What is exhaustion?",
            answer="Exhaustion is when someone feels so tired that they need rest, water, and a quiet break."
        )
    ],
    "kindness": [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward other people."
        )
    ],
    "magic": [
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something impossible in real life, like a glowing spell or a talking object."
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a problem or secret that people solve by looking for clues."
        )
    ],
}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    key: str
    name: str
    mood: str
    hiding_place: str


@dataclass
class MagicItem:
    key: str
    label: str
    clue: str
    effect: str
    cause: str


@dataclass
class Aid:
    key: str
    label: str
    kindness_line: str
    fix_line: str


@dataclass
class StoryParams:
    setting: str
    item: str
    aid: str
    name: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery story world about exhaustion, kindness, magic, and a happy ending.")
    ap.add_argument("--setting", choices=SETTING_CHOICES)
    ap.add_argument("--item", choices=MAGIC_ITEMS)
    ap.add_argument("--aid", choices=MAGIC_AIDS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    setting = args.setting or rng.choice(list(SETTING_CHOICES))
    item = args.item or rng.choice(list(MAGIC_ITEMS))
    aid = args.aid or rng.choice(list(MAGIC_AIDS))
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if setting == "attic" and item == "lantern" and aid == "blanket":
        pass
    return StoryParams(setting=setting, item=item, aid=aid, name=name, helper=helper)


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTING_CHOICES:
        lines.append(asp.fact("setting", k))
    for k in MAGIC_ITEMS:
        lines.append(asp.fact("item", k))
    for k in MAGIC_AIDS:
        lines.append(asp.fact("aid", k))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, I, A) :- setting(S), item(I), aid(A).
#show valid_story/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, i, a) for s in SETTING_CHOICES for i in MAGIC_ITEMS for a in MAGIC_AIDS}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python registries.")
    print("Only in ASP:", sorted(cl - py))
    print("Only in Python:", sorted(py - cl))
    return 1


def choose(setting_key: str, item_key: str, aid_key: str) -> tuple[Setting, MagicItem, Aid]:
    return (
        Setting(setting_key, SETTING_CHOICES[setting_key], "quiet and a little dim", "behind a loose floorboard"),
        MagicItem(item_key, **MAGIC_ITEMS[item_key]),
        Aid(aid_key, MAGIC_AIDS[aid_key]["label"], MAGIC_AIDS[aid_key]["kindness"], MAGIC_AIDS[aid_key]["fix"]),
    )


def generate(params: StoryParams) -> StorySample:
    setting, item_cfg, aid_cfg = choose(params.setting, params.item, params.aid)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Nora", "Iris", "Asha"} else "boy",
        label=params.name,
        meters={"exhaustion": 0.0, "courage": 0.0},
        memes={"worry": 0.0, "kindness": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="mother" if params.helper in {"Mama"} else "grandmother" if params.helper in {"Grandma"} else "man",
        label=params.helper,
        meters={"exhaustion": 0.0, "care": 0.0},
        memes={"kindness": 0.0, "relief": 0.0},
    ))
    magic_item = world.add(Entity(
        id="mystery_item",
        type=item_cfg.key,
        label=item_cfg.label,
        phrase=item_cfg.label,
        owner=helper.id,
        caretaker=helper.id,
        meters={"magic": 1.0, "drain": 0.0},
        memes={"mystery": 1.0},
    ))

    hero.meters["exhaustion"] += 1.0
    helper.meters["exhaustion"] += 1.0
    world.facts.update(setting=setting, item=item_cfg, aid=aid_cfg, hero=hero, helper=helper, magic_item=magic_item)

    world.say(
        f"On a quiet evening, {hero.id} wandered through {setting.name} and noticed that something felt off."
    )
    world.say(
        f"The lamps were dim, the air was still, and one little clue kept turning up: {random.choice(CLUES)}."
    )
    world.say(
        f"{hero.id} felt the heavy kind of exhaustion that makes even small steps seem slow, so {hero.pronoun()} walked carefully."
    )
    world.para()
    world.say(
        f"At {setting.hiding_place}, {hero.id} found {helper.label} sitting beside a {item_cfg.label} that gave off {item_cfg.clue}."
    )
    world.say(
        f"{helper.label} explained that the charm had been too busy all night; {item_cfg.cause}, and its magic had started to drain the room."
    )
    world.say(
        f"{hero.id} did not scold anyone. Instead, {hero.pronoun()} showed kindness and offered to help solve the mystery."
    )
    hero.memes["kindness"] += 1.0
    helper.memes["kindness"] += 1.0
    world.para()
    world.say(
        f"{hero.id} and {helper.label} chose {aid_cfg.label}: {aid_cfg.kindness_line}."
    )
    if params.aid == "song":
        world.say("The humming note floated through the room like a warm little key.")
    elif params.aid == "blanket":
        world.say("Under the blanket, the tired magic softened and stopped tugging so hard.")
    else:
        world.say("The tea steamed up in tiny curls, and the whole place seemed to breathe again.")
    world.say(f"{aid_cfg.fix_line.capitalize()}, and the mystery began to loosen its grip.")
    magic_item.meters["drain"] = 0.0
    hero.meters["exhaustion"] = max(0.0, hero.meters["exhaustion"] - 1.0)
    helper.meters["exhaustion"] = max(0.0, helper.meters["exhaustion"] - 1.0)
    hero.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    world.para()
    world.say(
        f"In the end, the {magic_item.label} gave one last soft glow, then settled down where it belonged."
    )
    world.say(
        f"{hero.id} yawned, smiled, and found that the kind little fix had turned the strange evening into a happy ending."
    )
    world.say(
        f"The lamps shone again, {helper.label} looked rested, and {hero.id} went home with the calm feeling of a solved mystery."
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    return [
        f"Write a short mystery story for young children about {hero.id} and the {item.label}, with kindness and a happy ending.",
        f"Tell a gentle story where exhaustion is caused by a magical problem, and a child solves it by helping someone kindly.",
        f"Create a cozy story in {world.setting.name} that includes clues, magic, and a soothing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item_cfg = f["item"]
    aid_cfg = f["aid"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Why did {hero.id} think something was wrong in {setting.name}?",
            answer=f"{hero.id} noticed dim lamps, quiet air, and odd clues, so the place felt like a mystery instead of a normal evening.",
        ),
        QAItem(
            question=f"What was causing the strange tired feeling in the story?",
            answer=f"The {item_cfg.label} was the cause, because it had been wound too tightly and its magic started draining the room.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} solve the problem?",
            answer=f"They used {aid_cfg.label} and worked gently together, which helped the magic settle and brought the happy ending.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of getting angry?",
            answer=f"{hero.id} showed kindness, listened carefully, and helped solve the mystery in a calm way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["exhaustion"])
    out.extend(WORLD_KNOWLEDGE["kindness"])
    out.extend(WORLD_KNOWLEDGE["magic"])
    out.extend(WORLD_KNOWLEDGE["mystery"])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.type:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combinations")
        for c in combos[:20]:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("library", "music_box", "song", "Mina", "Grandma"),
            StoryParams("garden", "lantern", "blanket", "Eli", "Papa"),
            StoryParams("village", "teacup", "tea", "Nora", "Aunt Lila"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            samples.append(generate(p))

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
