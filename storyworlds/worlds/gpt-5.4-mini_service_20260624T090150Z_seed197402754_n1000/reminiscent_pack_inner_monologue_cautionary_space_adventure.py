#!/usr/bin/env python3
"""
A small space-adventure storyworld about a cautious child astronaut, a pack,
and an inner monologue that helps prevent trouble.

Seed tale:
---
A young astronaut named Nova was traveling with her older brother on a tiny ship.
Nova carried a little pack that was full of snacks, a map, and a shiny charm that
reminded her of home. When the ship drifted close to a glowing comet trail, Nova
wanted to float outside to look at it more closely. But her inner monologue kept
warning her that space was big, quiet, and easy to get lost in.

Her brother pointed to the safety line and told Nova to keep the pack closed and
stay clipped in. Nova listened. She took a slow breath, held the pack close, and
watched the comet from the window instead. It still felt exciting, but now it was
safe too.

This world models a tiny space-craft scene where:
- a hero has a beloved pack,
- a risky space moment triggers inner monologue and caution,
- safe choices resolve the tension without losing the wonder of space.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    tethered: bool = False
    sealed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def subject_name(self) -> str:
        return self.label or self.id

    def obj_name(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the starship"
    view: str = "a glowing comet trail"
    space_risk: bool = True


@dataclass
class PackSpec:
    label: str = "pack"
    phrase: str = "a little pack"
    contents: tuple[str, ...] = ("snacks", "a map", "a charm")
    reminds_of: str = "home"


@dataclass
class StoryParams:
    place: str
    view: str
    name: str
    age: str
    parent: str
    pack: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


def story_setup() -> tuple[Setting, PackSpec]:
    return Setting(), PackSpec()


def danger_level(world: World, hero: Entity) -> bool:
    return bool(hero.memes.get("curious_pull", 0.0) >= THRESHOLD and not hero.meters.get("tethered", 0.0))


def inner_monologue(world: World, hero: Entity) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f'{hero.pronoun().capitalize()} thought, "Space is beautiful, but it is also huge and quiet. '
        f'I should be careful."'
    )


def introduce(world: World, hero: Entity, parent: Entity, pack: Entity, pack_spec: PackSpec) -> None:
    world.say(
        f"{hero.subject_name()} was a small {hero.type} on {world.setting.place}, and {parent.label} looked after {hero.pronoun('object')}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {pack.phrase}, and inside it were {', '.join(pack_spec.contents[:-1])}, and {pack_spec.contents[-1]}. "
        f"It felt {pack.memes.get('reminiscent', 0) and 'reminiscent of home' or 'special'}."
    )


def long_for_view(world: World, hero: Entity, view: str) -> None:
    hero.memes["curious_pull"] = hero.memes.get("curious_pull", 0.0) + 1
    world.say(
        f"{hero.subject_name()} watched {view} sliding past the window and wanted a closer look."
    )


def caution(world: World, parent: Entity, hero: Entity, pack: Entity) -> None:
    world.say(
        f"{parent.label} pointed at the safety line and said, \"Stay clipped in, keep your {pack.label} closed, and look from here.\""
    )


def resolve(world: World, hero: Entity, parent: Entity, pack: Entity) -> None:
    hero.meters["tethered"] = 1.0
    pack.sealed = True
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.subject_name()} took a slow breath, held {hero.pronoun('possessive')} {pack.label} close, and stayed clipped in."
    )
    world.say(
        f"Then {hero.pronoun()} watched {world.setting.view} from the window, and the starship stayed safe and bright."
    )


def tell(setting: Setting, pack_spec: PackSpec, name: str, age: str, parent_type: str = "father") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="girl" if age == "young" else "boy", label=name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    pack = world.add(Entity(id="pack", type="pack", label=pack_spec.label, phrase=pack_spec.phrase, owner=hero.id))
    pack.memes["reminiscent"] = 1.0

    world.say(f"{name} was a {age} astronaut.")
    world.say(f"{name} had an inner monologue that spoke up whenever space felt tricky.")

    world.para()
    introduce(world, hero, parent, pack, pack_spec)
    long_for_view(world, hero, setting.view)
    inner_monologue(world, hero)
    caution(world, parent, hero, pack)

    world.para()
    if danger_level(world, hero):
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        world.say(f"{hero.subject_name()} almost floated toward the hatch, but the warning in {hero.pronoun('possessive')} head stopped {hero.pronoun('object')}.")
    resolve(world, hero, parent, pack)

    world.facts.update(hero=hero, parent=parent, pack=pack, pack_spec=pack_spec)
    return world


SETTINGS = {
    "ship": Setting(place="the starship", view="a glowing comet trail", space_risk=True),
    "station": Setting(place="the space station", view="a silver planet", space_risk=True),
    "lunar": Setting(place="the moon base", view="Earth turning blue in the sky", space_risk=True),
}

PACKS = {
    "pack": PackSpec(label="pack", phrase="a little pack", contents=("snacks", "a map", "a charm"), reminds_of="home"),
    "satchel": PackSpec(label="satchel", phrase="a soft satchel", contents=("crackers", "a sketch card", "a tiny toy"), reminds_of="home"),
    "rucksack": PackSpec(label="rucksack", phrase="a small rucksack", contents=("dried fruit", "a route card", "a ribbon"), reminds_of="Earth"),
}

NAMES = ["Nova", "Milo", "Iris", "Kian", "Luna", "Rory", "Zia", "Orion"]
AGES = ["young", "small", "little"]


@dataclass
class StoryParamsResolved:
    place: str
    view: str
    name: str
    age: str
    parent: str
    pack: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with inner monologue and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--view")
    ap.add_argument("--name")
    ap.add_argument("--age", choices=AGES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--pack", choices=PACKS)
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
    if args.view and "space" not in args.view.lower() and "planet" not in args.view.lower() and "comet" not in args.view.lower():
        raise StoryError("The view must feel like space adventure: comet, planet, stars, or Earth from space.")

    place = args.place or rng.choice(list(SETTINGS))
    pack = args.pack or rng.choice(list(PACKS))
    name = args.name or rng.choice(NAMES)
    age = args.age or rng.choice(AGES)
    parent = args.parent or rng.choice(["mother", "father"])
    view = args.view or SETTINGS[place].view
    return StoryParams(place=place, view=view, name=name, age=age, parent=parent, pack=pack)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a child named {f["hero"].id} that includes the word "reminiscent".',
        f"Tell a gentle cautionary story where {f['hero'].id} wants to go closer to {world.setting.view} but listens to an inner monologue and stays safe.",
        f"Write a story about a pack, a safety line, and a brave choice made in space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    pack: Entity = f["pack"]
    return [
        QAItem(
            question=f"What did {hero.id} want to look at more closely?",
            answer=f"{hero.id} wanted to look more closely at {world.setting.view} outside the ship.",
        ),
        QAItem(
            question=f"What did {parent.label} tell {hero.id} to do with the {pack.label}?",
            answer=f"{parent.label} told {hero.id} to keep the {pack.label} closed and stay clipped in.",
        ),
        QAItem(
            question=f"How did {hero.id} make the safe choice at the end?",
            answer=f"{hero.id} took a slow breath, held the {pack.label} close, stayed clipped in, and watched from the window instead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a safety line in space?",
            answer="A safety line is a tether that helps keep a person from drifting away when they are floating in space.",
        ),
        QAItem(
            question="Why do astronauts stay clipped in?",
            answer="Astronauts stay clipped in so they do not drift off when there is little or no gravity to hold them down.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside a character's head that helps them think through what to do.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.tethered:
            bits.append("tethered=True")
        if e.sealed:
            bits.append("sealed=True")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
hero(X) :- hero_name(X).
pack(P) :- pack_name(P).
cautionary_story(X) :- hero(X), pack(P), inner_monologue(X), safety_line(P).
safe_end(X) :- cautionary_story(X), chooses_window_view(X).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for p in PACKS:
        lines.append(asp.fact("pack_name", p))
    for n in NAMES:
        lines.append(asp.fact("hero_name", n))
    lines.append(asp.fact("inner_monologue", "yes"))
    lines.append(asp.fact("safety_line", "yes"))
    lines.append(asp.fact("chooses_window_view", "yes"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show safe_end/1."))
    ok = bool(asp.atoms(model, "safe_end"))
    if ok:
        print("OK: ASP gate recognizes the safe ending.")
        return 0
    print("MISMATCH: ASP gate failed to derive safe_end.")
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    pack_spec = PACKS[params.pack]
    world = tell(setting, pack_spec, params.name, params.age, params.parent)
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
    StoryParams(place="ship", view=SETTINGS["ship"].view, name="Nova", age="young", parent="father", pack="pack"),
    StoryParams(place="station", view=SETTINGS["station"].view, name="Iris", age="little", parent="mother", pack="satchel"),
    StoryParams(place="lunar", view=SETTINGS["lunar"].view, name="Kian", age="small", parent="father", pack="rucksack"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_end/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available, but this world's reasoner is mainly used for verification.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place} / {p.pack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
