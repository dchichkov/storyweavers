#!/usr/bin/env python3
"""
A heartwarming story world about a small misunderstanding around saying thank you.

Seed premise:
- A child wants to thank someone.
- A misunderstanding leads to the wrong conclusion.
- Kind clarification turns the moment warm and happy.

The simulated world tracks both physical objects and feelings:
- meters: paper, ink, crumbs, dust, flowers, polish, etc.
- memes: gratitude, confusion, worry, relief, warmth, pride
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    misunderstanding: str
    thank_item: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_spill(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    note = world.entities.get("note")
    if not hero or not note:
        return out
    if hero.memes.get("rush", 0) < THRESHOLD:
        return out
    sig = ("spill", note.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    note.meters["ink"] = note.meters.get("ink", 0) + 1
    note.meters["smudged"] = note.meters.get("smudged", 0) + 1
    out.append("The note got a little smudged.")
    return out


def _r_confusion(world: World) -> list[str]:
    hero = world.facts.get("hero")
    if not hero or hero.memes.get("confused", 0) < THRESHOLD:
        return []
    sig = ("confusion", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    return ["__confusion__"]


def _r_relief(world: World) -> list[str]:
    helper = world.facts.get("helper")
    hero = world.facts.get("hero")
    if not helper or not hero:
        return []
    if hero.memes.get("relief", 0) < THRESHOLD:
        return []
    sig = ("relief", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["warmth"] = helper.memes.get("warmth", 0) + 1
    return ["__relief__"]


RULES = [Rule("spill", _r_spill), Rule("confusion", _r_confusion), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend(x for x in res if x not in {"__confusion__", "__relief__"})
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTING = Setting(place="the kitchen table", indoor=True)

HERO_NAMES = ["Maya", "Nora", "Ivy", "Lina", "Owen", "Theo", "Sam", "Ben"]
HELPER_NAMES = ["Mrs. Reed", "Grandma", "Mr. Cole", "Aunt June", "Papa", "Mama"]
MISUNDERSTANDINGS = {
    "late": "thought the helper was upset because the helper had not arrived yet",
    "broken": "thought the helper did not want the gift because the helper had looked at the torn ribbon",
    "wrong": "thought the thank-you card was meant for the wrong person",
}

THANK_ITEMS = {
    "card": ("a handmade thank-you card", "card"),
    "cookies": ("a small plate of cookies", "cookies"),
    "flowers": ("a tiny bouquet of flowers", "flowers"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming misunderstanding story about saying thank you.")
    ap.add_argument("--place", choices=["kitchen", "porch", "bedroom", "hall"], default="kitchen")
    ap.add_argument("--misunderstanding", choices=sorted(MISUNDERSTANDINGS), default=None)
    ap.add_argument("--thank-item", choices=sorted(THANK_ITEMS), default=None)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle", "neighbor"], default=None)
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
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    thank_item = args.thank_item or rng.choice(list(THANK_ITEMS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES[:4] if hero_gender == "girl" else HERO_NAMES[4:])
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt", "uncle", "neighbor"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=args.place,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        misunderstanding=misunderstanding,
        thank_item=thank_item,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING if params.place == "kitchen" else Setting(place=f"the {params.place}", indoor=True))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    item_phrase, item_label = THANK_ITEMS[params.thank_item]
    note = world.add(Entity(id="note", type=params.thank_item, label=item_label, phrase=item_phrase, owner=hero.id, caretaker=hero.id))
    world.facts.update(hero=hero, helper=helper, note=note, params=params)

    hero.memes["gratitude"] = 1
    hero.memes["rush"] = 1
    world.say(f"{hero.label} was thinking about how kind {helper.label} had been.")
    world.say(f"{hero.label} wanted to say thank you in a special way, so {hero.pronoun('subject')} made {item_phrase}.")
    world.say(f"On the table in {world.setting.place}, the little gift waited beside a bright smile.")

    world.para()
    if params.misunderstanding == "late":
        hero.memes["confused"] = 1
        world.say(f"When {helper.label} was not there yet, {hero.label} felt a tight little worry.")
        world.say(f"{hero.label} thought {helper.label} might be upset, because {MISUNDERSTANDINGS[params.misunderstanding]}.")
    elif params.misunderstanding == "broken":
        hero.memes["confused"] = 1
        note.meters["ribbon"] = 1
        world.say(f"{hero.label} noticed the ribbon had slipped loose and frowned.")
        world.say(f"{hero.label} {MISUNDERSTANDINGS[params.misunderstanding]}, so the thank-you felt smaller for a moment.")
    else:
        hero.memes["confused"] = 1
        world.say(f"{hero.label} held the card very still and {MISUNDERSTANDINGS[params.misunderstanding]}.")
        world.say(f"That made the room feel a little lopsided until someone explained it kindly.")
    propagate(world)

    world.para()
    helper.memes["warmth"] = 1
    world.say(f"Then {helper.label} came in, saw the gift, and smiled with soft eyes.")
    world.say(f"\"Oh, sweet one, this is for me?\" {helper.label} asked.")
    world.say(f"{hero.label} blinked, then nodded. \"I wanted to thank you,\" {hero.label} said.")
    hero.memes["relief"] = 1
    helper.memes["pride"] = 1
    helper.memes["love"] = 1
    world.say(f"{helper.label} bent down and gave {hero.label} a gentle hug.")
    world.say(f"\"That is the nicest thank you,\" {helper.label} said, \"and I love it because you made it yourself.\"")
    world.say(f"{hero.label}'s face turned bright and happy, and the room felt warm again.")
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short heartwarming story about {p.hero_name} trying to thank {p.helper_name}.",
        f"Tell a gentle story where a child makes {p.thank_item} and a misunderstanding makes the child worry for a moment.",
        f"Write a simple story in {p.place} that ends with kindness, relief, and a thank-you hug.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    note = world.facts["note"]
    return [
        QAItem(
            question=f"Why did {p.hero_name} make {note.phrase}?",
            answer=f"{p.hero_name} made {note.phrase} because {hero.pronoun('subject')} wanted to thank {helper.label} for being kind.",
        ),
        QAItem(
            question=f"What misunderstanding made {p.hero_name} worry for a moment?",
            answer=f"{p.hero_name} thought something was wrong because {MISUNDERSTANDINGS[p.misunderstanding]}.",
        ),
        QAItem(
            question=f"What happened when {p.helper_name} saw the thank-you gift?",
            answer=f"{p.helper_name} smiled, asked kindly about the gift, and then gave {p.hero_name} a gentle hug.",
        ),
        QAItem(
            question=f"How did {p.hero_name} feel at the end?",
            answer=f"{p.hero_name} felt relieved and happy after the misunderstanding was explained and the thank-you was received with love.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to thank someone?",
            answer="To thank someone means to show that you appreciate what they did for you.",
        ),
        QAItem(
            question="Why can a misunderstanding feel upsetting?",
            answer="A misunderstanding can feel upsetting because people think something different from what is really happening.",
        ),
        QAItem(
            question="What usually helps after a misunderstanding?",
            answer="Kind words and clear explanation usually help after a misunderstanding.",
        ),
    ]


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


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("misunderstanding", k) for k in MISUNDERSTANDINGS
        ] + [
            asp.fact("thank_item", k) for k in THANK_ITEMS
        ]
    )


ASP_RULES = r"""
misunderstanding(M) :- misunderstanding(M).
thank_item(T) :- thank_item(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


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


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    out = []
    rng = random.Random(args.seed or 1)
    for place in ["kitchen", "porch", "bedroom", "hall"]:
        for misunderstanding in sorted(MISUNDERSTANDINGS):
            for thank_item in sorted(THANK_ITEMS):
                out.append(StoryParams(
                    place=place,
                    hero_name=rng.choice(HERO_NAMES),
                    hero_gender=rng.choice(["girl", "boy"]),
                    helper_name=rng.choice(HELPER_NAMES),
                    helper_type=rng.choice(["mother", "father", "grandmother", "grandfather", "aunt", "uncle", "neighbor"]),
                    misunderstanding=misunderstanding,
                    thank_item=thank_item,
                ))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show misunderstanding/1.\n#show thank_item/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in resolve_all(args)]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
