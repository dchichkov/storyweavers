#!/usr/bin/env python3
"""
A small animal-story world about jewelry, pride, and a funny bad ending.

Premise:
A flashy animal has a beloved piece of jewelry, wants to show off, makes a
silly choice, and ends up losing the sparkle in a mildly comic way.

The simulated world tracks:
- who owns the jewelry
- where the jewelry is worn
- how a boastful stunt can jostle it loose
- emotional beats for pride, worry, embarrassment, and amusement

The ending is intentionally a "bad ending" in the sense that the jewel is lost
or damaged, but the tone stays child-facing and humorous.
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
    worn_by: Optional[str] = None
    lost: bool = False
    broken: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"lion", "bear", "fox", "wolf", "dog", "cat", "rabbit", "monkey", "horse", "goat"}
        female = {"owl", "hen", "squirrel", "deer", "mouse", "duck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Jewelry:
    id: str
    label: str
    phrase: str
    kind: str
    worn_on: str
    shiny: bool = True
    fragile: bool = True


@dataclass
class Animal:
    kind: str
    type: str
    name: str
    trait: str
    friend_type: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    animal: str
    name: str
    friend: str
    jewelry: str
    setting: str
    seed: Optional[int] = None


ANIMALS = {
    "fox": Animal(kind="mammal", type="fox", name="Fin", trait="proud", friend_type="raccoon"),
    "bear": Animal(kind="mammal", type="bear", name="Bram", trait="showy", friend_type="otter"),
    "cat": Animal(kind="mammal", type="cat", name="Mimi", trait="sparkly", friend_type="mouse"),
    "rabbit": Animal(kind="mammal", type="rabbit", name="Pip", trait="bouncy", friend_type="duck"),
    "owl": Animal(kind="bird", type="owl", name="Oona", trait="fancy", friend_type="squirrel"),
}

JEWELRY = {
    "necklace": Jewelry(id="necklace", label="necklace", phrase="a shiny necklace with a round blue bead", kind="necklace", worn_on="neck"),
    "bracelet": Jewelry(id="bracelet", label="bracelet", phrase="a tiny bracelet with three bells", kind="bracelet", worn_on="paw"),
    "ring": Jewelry(id="ring", label="ring", phrase="a little ring with a bright red gem", kind="ring", worn_on="paw"),
    "crown": Jewelry(id="crown", label="crown", phrase="a tin crown with a wobbly star", kind="crown", worn_on="head"),
}

SETTINGS = {
    "muddy yard": {"hazard": "mud", "action": "jump in the mud puddle"},
    "apple tree": {"hazard": "branches", "action": "climb the apple tree"},
    "pond dock": {"hazard": "water", "action": "lean over the pond"},
    "berry hill": {"hazard": "roll", "action": "roll down the hill"},
}


def pick_good_combo() -> list[tuple[str, str]]:
    combos = []
    for a in SETTINGS:
        for j in JEWELRY:
            if a == "apple tree" and j == "crown":
                combos.append((a, j))
            elif a == "muddy yard" and j in {"bracelet", "ring"}:
                combos.append((a, j))
            elif a == "pond dock" and j in {"necklace", "bracelet"}:
                combos.append((a, j))
            elif a == "berry hill" and j in {"crown", "necklace"}:
                combos.append((a, j))
    return combos


def reasonableness_gate(setting: str, jewelry: str) -> bool:
    return (setting, jewelry) in pick_good_combo()


def setting_description(setting: str) -> str:
    if setting == "muddy yard":
        return "The yard was squishy and warm, with a mud puddle shining like chocolate soup."
    if setting == "apple tree":
        return "The apple tree looked brave and tall, with branches that shook like arms."
    if setting == "pond dock":
        return "The pond sparkled, and the dock squeaked every time a foot stepped on it."
    return "The hill curved down in a silly hurry, as if it wanted everybody to tumble."


def introduce(world: World, hero: Entity, friend: Entity, jewel: Entity, setting: str) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait_word']} {hero.type} who loved {jewel.label} "
        f"more than a pile of pancakes."
    )
    world.say(
        f"{friend.id}, a {friend.type}, followed along with a grin because {hero.id} always had a grand plan."
    )
    world.say(setting_description(setting))


def boast(world: World, hero: Entity, jewel: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} held up {hero.pronoun('possessive')} {jewel.label} and said, "
        f'"Look at my {jewel.label}! It is the fanciest thing in the whole field!"'
    )


def risky_action(world: World, hero: Entity, friend: Entity, setting: str, jewel: Entity) -> None:
    world.para()
    world.say(
        f"So {hero.id} decided to {SETTINGS[setting]['action']} while still wearing the {jewel.label}."
    )
    world.say(
        f"{friend.id} blinked and said, \"That sounds a little wiggly.\""
    )
    hero.memes["reckless"] += 1


def simulate_loss(world: World, hero: Entity, jewel: Entity, setting: str) -> None:
    sig = ("loss", hero.id, jewel.id, setting)
    if sig in world.fired:
        return
    world.fired.add(sig)

    if setting == "muddy yard":
        world.say(f"One big splat of mud hit {hero.pronoun('possessive')} paws.")
        world.say(f"The {jewel.label} slid off and vanished into the mud with a tiny blip.")
        jewel.lost = True
    elif setting == "apple tree":
        world.say(f"Up in the branches, {hero.id} gave a wobble and did a very ungraceful wiggle.")
        world.say(f"The {jewel.label} pinged against a twig, bent crooked, and got stuck in a fork of bark.")
        jewel.broken = True
    elif setting == "pond dock":
        world.say(f"The dock gave a squeak, the water gave a splash, and the {jewel.label} went plink into the pond.")
        jewel.lost = True
    else:
        world.say(f"The hill was so slippery that the {jewel.label} bounced away like a shiny pebble.")
        jewel.lost = True

    hero.memes["embarrassment"] += 1
    hero.memes["sad"] += 1
    hero.memes["humor"] += 1


def ending(world: World, hero: Entity, friend: Entity, jewel: Entity, setting: str) -> None:
    world.para()
    if jewel.lost:
        world.say(
            f"{hero.id} sat down and sighed, because the {jewel.label} was gone for good."
        )
    elif jewel.broken:
        world.say(
            f"{hero.id} stared at the bent {jewel.label} and made a tiny face that tried very hard not to laugh."
        )
    world.say(
        f"{friend.id} gave a polite snort and said, \"Well, that was the flashiest disaster I ever saw.\""
    )
    world.say(
        f"{hero.id} giggled too, even though {hero.pronoun('possessive')} fancy treasure was not fancy anymore."
    )
    world.say(
        f"And that was the end: the {setting} was still messy, the {jewel.label} was lost or crooked, "
        f"and {hero.id} learned that showing off can end with a splash, a clatter, and a very silly face."
    )


def tell(params: StoryParams) -> World:
    if params.animal not in ANIMALS:
        raise StoryError("Unknown animal.")
    if params.jewelry not in JEWELRY:
        raise StoryError("Unknown jewelry.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not reasonableness_gate(params.setting, params.jewelry):
        raise StoryError("This setting and jewelry do not make a good story together.")

    base = ANIMALS[params.animal]
    jewel_cfg = JEWELRY[params.jewelry]
    world = World()

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=base.type,
        memes={"trait_word": base.trait, "pride": 0.0, "reckless": 0.0, "embarrassment": 0.0, "sad": 0.0, "humor": 0.0},
    ))
    friend = world.add(Entity(
        id=base.friend_type.title(),
        kind="character",
        type=base.friend_type,
    ))
    jewel = world.add(Entity(
        id=jewel_cfg.label.title(),
        kind="thing",
        type=jewel_cfg.kind,
        label=jewel_cfg.label,
        phrase=jewel_cfg.phrase,
        owner=hero.id,
        worn_by=hero.id,
    ))

    world.say(f"{hero.id} had {jewel.phrase}.")
    world.say(f"{hero.id} wore the {jewel.label} every chance {hero.pronoun('subject')} got.")
    introduce(world, hero, friend, jewel, params.setting)
    boast(world, hero, jewel)
    risky_action(world, hero, friend, params.setting, jewel)
    simulate_loss(world, hero, jewel, params.setting)
    ending(world, hero, friend, jewel, params.setting)

    world.facts.update(
        hero=hero,
        friend=friend,
        jewel=jewel,
        setting=params.setting,
        hazard=SETTINGS[params.setting]["hazard"],
        action=SETTINGS[params.setting]["action"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    jewel: Entity = f["jewel"]
    return [
        f'Write a funny animal story for a small child about {hero.id} and a {jewel.label}.',
        f"Tell a short story where a {hero.type} wants to show off {hero.pronoun('possessive')} {jewel.label} and makes a silly mistake.",
        f'Write an animal story with a shiny {jewel.label}, a risky choice, and a bad ending that still feels playful.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    jewel: Entity = f["jewel"]
    setting = f["setting"]
    action = f["action"]
    qa = [
        QAItem(
            question=f"What did {hero.id} love to show off?",
            answer=f"{hero.id} loved showing off {hero.pronoun('possessive')} {jewel.label}, which looked very shiny at first.",
        ),
        QAItem(
            question=f"Where did {hero.id} make the silly mistake?",
            answer=f"{hero.id} made the mistake at the {setting} while trying to {action}.",
        ),
        QAItem(
            question=f"Who noticed the plan sounded wiggly?",
            answer=f"{friend.id} noticed it sounded wiggly and gave a warning before the trouble started.",
        ),
    ]
    if jewel.lost:
        qa.append(QAItem(
            question=f"What happened to the {jewel.label} at the end?",
            answer=f"The {jewel.label} slipped away and was lost, so {hero.id} could not wear it anymore.",
        ))
    elif jewel.broken:
        qa.append(QAItem(
            question=f"What happened to the {jewel.label} at the end?",
            answer=f"The {jewel.label} got bent and stuck, so it was no longer a pretty perfect jewel.",
        ))
    qa.append(QAItem(
        question=f"Why was the ending funny even though it was bad?",
        answer=f"It was funny because the whole shiny disaster was so silly, and {friend.id} said it like a joke while everyone still had to admit the jewel was ruined or gone.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jewelry?",
            answer="Jewelry is something people or animals wear to look nice, like necklaces, rings, bracelets, or crowns.",
        ),
        QAItem(
            question="Why can jewelry be easy to lose?",
            answer="Jewelry can be small and slippery, so it can slip off, fall into mud, or drop into water.",
        ),
        QAItem(
            question="What makes a story humorous?",
            answer="A humorous story has a funny moment or a silly problem that makes readers smile or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for j in JEWELRY.values():
        lines.append(asp.fact("jewelry", j.id))
        lines.append(asp.fact("worn_on", j.id, j.worn_on))
    for a in ANIMALS.values():
        lines.append(asp.fact("animal", a.type))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,J) :- setting(S), jewelry(J), good_pair(S,J).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about jewelry and a humorous bad ending.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--friend", choices=sorted({a.friend_type for a in ANIMALS.values()}))
    ap.add_argument("--jewelry", choices=sorted(JEWELRY))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
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
    combos = [(s, j) for s in SETTINGS for j in JEWELRY if reasonableness_gate(s, j)]
    if args.setting and args.jewelry and not reasonableness_gate(args.setting, args.jewelry):
        raise StoryError("That setting and jewelry combination is too unreasonable for this story.")
    valid = [(s, j) for (s, j) in combos
             if (not args.setting or s == args.setting)
             and (not args.jewelry or j == args.jewelry)]
    if not valid:
        raise StoryError("No compatible story fits those choices.")
    setting, jewelry = rng.choice(valid)
    animal = args.animal or rng.choice(sorted(ANIMALS))
    friend = args.friend or ANIMALS[animal].friend_type
    name = args.name or ANIMALS[animal].name
    return StoryParams(animal=animal, name=name, friend=friend, jewelry=jewelry, setting=setting)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.lost:
            parts.append("lost=True")
        if e.broken:
            parts.append("broken=True")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(parts)}")
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


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(animal="fox", name="Fin", friend="raccoon", jewelry="necklace", setting="pond dock"),
    StoryParams(animal="cat", name="Mimi", friend="mouse", jewelry="bracelet", setting="muddy yard"),
    StoryParams(animal="owl", name="Oona", friend="squirrel", jewelry="crown", setting="apple tree"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is not fully implemented for this compact world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
