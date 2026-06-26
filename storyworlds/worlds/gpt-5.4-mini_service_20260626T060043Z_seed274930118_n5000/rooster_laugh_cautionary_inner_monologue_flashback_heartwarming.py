#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rooster_laugh_cautionary_inner_monologue_flashback_heartwarming.py
===========================================================================================================

A tiny heartwarming storyworld about a rooster, a laugh, a cautionary memory,
an inner monologue, and a flashback that helps the day end gently.

Premise:
- A rooster loves to laugh in the early morning.
- The rooster also remembers that a very loud laugh once startled a sleeping
  chick.
- The rooster worries about repeating that mistake.
- A kind compromise lets the laugh stay warm, but soft.

The world is small on purpose:
- one hero rooster
- one sleepy chick to protect
- one caring hen
- one or two places
- one protective helper object that makes a gentle compromise possible

The simulated story is driven by state:
- sound meters rise when the rooster laughs
- sleep meters fall if the chick is startled
- cautionary inner monologue and flashback are triggered by the rooster's memory
- the ending proves the chick stayed safe and everyone feels closer
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
    protective: bool = False
    muffles: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rooster", "hen", "mother", "woman", "girl"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case] if self.type == "rooster" else {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def maybe_article(self) -> str:
        return self.phrase or self.label


@dataclass
class Setting:
    place: str
    indoors: bool = False
    quiet: bool = True


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    action: str
    muffles: bool = True


@dataclass
class StoryParams:
    place: str
    gear: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "coop": Setting(place="the warm coop", indoors=True, quiet=True),
    "yard": Setting(place="the sunny yard", indoors=False, quiet=True),
}

GEAR = {
    "feather_scarf": Gear(
        id="feather_scarf",
        label="a feather scarf",
        phrase="a soft feather scarf",
        action="laugh into the feather scarf",
        muffles=True,
    ),
    "hay_pillow": Gear(
        id="hay_pillow",
        label="a hay pillow",
        phrase="a small hay pillow",
        action="hide his laugh behind the hay pillow",
        muffles=True,
    ),
}


GENTLE_LINES = [
    "It reminded him to keep the sound kind.",
    "He wanted the morning to feel safe for everyone.",
    "He could still be joyful without making a fuss.",
]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_loud_laugh(world: World) -> list[str]:
    hero = world.get("rooster")
    chick = world.get("chick")
    if hero.meters.get("sound", 0) < THRESHOLD:
        return []
    if world.facts.get("muffled"):
        return []
    if "loud" in world.fired:
        return []
    world.fired.add("loud")
    chick.meters["sleep"] = max(0.0, chick.meters.get("sleep", 0) - 1.0)
    chick.memes["startled"] = chick.memes.get("startled", 0) + 1.0
    return ["The little chick stirred in the nest."]


RULES = [Rule("loud_laugh", _r_loud_laugh)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for line in out:
            world.say(line)
    return out


def tell(setting: Setting, gear_def: Gear, name: str = "Rufus") -> World:
    world = World(setting)
    rooster = world.add(Entity(
        id="rooster",
        kind="character",
        type="rooster",
        label=name,
        phrase=f"a bright rooster named {name}",
        meters={"sound": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "memory": 0.0},
    ))
    hen = world.add(Entity(
        id="hen",
        kind="character",
        type="hen",
        label="Mabel",
        phrase="a kind hen named Mabel",
    ))
    chick = world.add(Entity(
        id="chick",
        kind="character",
        type="chick",
        label="Pip",
        phrase="a sleepy chick named Pip",
        meters={"sleep": 1.0},
        memes={"peace": 1.0},
    ))
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="helper",
        label=gear_def.label,
        phrase=gear_def.phrase,
        protective=True,
        muffles=True,
    ))

    world.say(
        f"{rooster.label} was {rooster.phrase} who loved to laugh in the morning."
    )
    world.say(
        f"{hen.label} was {hen.phrase}, and {chick.label} was {chick.phrase} tucked in the nest."
    )

    world.para()
    world.say(
        f"One morning in {setting.place}, {rooster.label} felt a chuckle bubble up in his chest."
    )
    world.say(
        "He thought, 'I want to laugh loud enough to shake the dew from the fence.'"
    )
    world.say(
        "Then another thought followed: 'But last time, my big laugh made Pip blink awake and cry.'"
    )
    rooster.memes["memory"] += 1.0
    rooster.memes["worry"] += 1.0
    world.facts["flashback"] = True
    world.facts["cautionary"] = True

    world.para()
    world.say(
        "He looked at the nest and listened to the tiny breathing there."
    )
    world.say(
        "In his head he told himself, 'A good laugh should leave the room warmer, not shakier.'"
    )
    world.say(
        random.choice(GENTLE_LINES)
    )

    if gear_def.muffles:
        world.say(
            f"{hen.label} noticed his careful face and brought over {gear_def.phrase}."
        )
        world.say(
            f'"Try to {gear_def.action}," she said softly. "That way you can laugh and still keep the morning gentle."'
        )
        world.facts["muffled"] = True
        gear.worn_by = rooster.id

    world.para()
    rooster.meters["sound"] = 0.5 if world.facts.get("muffled") else 1.2
    rooster.memes["joy"] += 1.0
    world.say(
        f"{rooster.label} smiled, tucked his beak close, and gave a small laugh that felt like a pillow of sunshine."
    )
    if world.facts.get("muffled"):
        world.say(
            f"The laugh stayed soft, so {chick.label} kept sleeping with a tiny smile on his face."
        )
    else:
        propagate(world)

    world.para()
    world.say(
        f"{rooster.label} laughed again, this time into {gear_def.label}, and the sound came out round and kind."
    )
    world.say(
        f"{hen.label} laughed too, and soon the three of them were sharing breakfast beside a nest that stayed perfectly calm."
    )
    world.say(
        f"By the end, {rooster.label} still loved to laugh, but now his laugh was a gentle one that let everyone rest."
    )

    world.facts.update(
        rooster=rooster,
        hen=hen,
        chick=chick,
        gear=gear_def,
        setting=setting,
        name=name,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a warm story about a rooster named {f["name"]} who loves to laugh, but remembers to be gentle around a sleepy chick.',
        f"Tell a heartwarming cautionary tale with an inner monologue and flashback about {f['name']} the rooster learning how to laugh softly.",
        f"Write a short, child-friendly story where laughter stays kind, a flashback helps the hero choose wisely, and everyone ends happy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rooster = f["rooster"]
    hen = f["hen"]
    chick = f["chick"]
    gear = f["gear"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who loved to laugh in the morning at {place}?",
            answer=f"{rooster.label}, the rooster, loved to laugh in the morning.",
        ),
        QAItem(
            question="Why did the rooster pause before laughing very loudly?",
            answer=f"He remembered a flashback about startling {chick.label} before, so he chose to be careful instead.",
        ),
        QAItem(
            question="What helped the rooster keep his laugh gentle?",
            answer=f"{hen.label} brought {gear.phrase}, which helped muffle the laugh so the nest stayed calm.",
        ),
        QAItem(
            question="How did the story end for the chick?",
            answer=f"{chick.label} stayed sleepy and safe, and the morning ended with everyone sharing breakfast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rooster?",
            answer="A rooster is a male chicken. Roosters often crow or make noise in the morning.",
        ),
        QAItem(
            question="Why might a loud laugh bother a sleepy baby bird?",
            answer="A loud sound can wake a sleeping bird too suddenly, which may startle it.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming rooster storyworld about a careful laugh.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    gear = args.gear or rng.choice(list(GEAR))
    name = args.name or rng.choice(["Rufus", "Coco", "Sunny", "Bram", "Toby"])
    return StoryParams(place=place, gear=gear, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], GEAR[params.gear], params.name)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
place(coop).
place(yard).
gear(feather_scarf).
gear(hay_pillow).
muffles(feather_scarf).
muffles(hay_pillow).

valid(P, G) :- place(P), gear(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for g in GEAR:
        lines.append(asp.fact("gear", g))
    for g in GEAR.values():
        if g.muffles:
            lines.append(asp.fact("muffles", g.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {(p, g) for p in SETTINGS for g in GEAR}
    clingo_set = set(asp_valid())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only python:", sorted(python_set - clingo_set))
    print("only clingo:", sorted(clingo_set - python_set))
    return 1


CURATED = [
    StoryParams(place="coop", gear="feather_scarf", name="Rufus"),
    StoryParams(place="yard", gear="hay_pillow", name="Coco"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
