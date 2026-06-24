#!/usr/bin/env python3
"""
storyworlds/worlds/rack_glory_adventurous_bravery_sound_effects_inner.py
========================================================================

A small Tall Tale storyworld built from the seed words rack, glory, and adventurous.

Premise:
- An adventurous child wants a glory token from a high rack in a frontier shop.
- A wobbly rack, a noisy spill, and a brave little rescue create the turn.
- Sound effects and inner monologue carry the tension and the fix.

The world is intentionally small and constraint-checked: one plausible problem,
one plausible brave action, and one clean ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the frontier general store"
    detail: str = "a high shelf and a shaky rack near the doorway"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    name: str = "Mabel"
    gender: str = "girl"
    helper: str = "Uncle Jed"
    seed: Optional[int] = None


GIRL_NAMES = ["Mabel", "Ivy", "June", "Ruby", "Nell", "Ada"]
BOY_NAMES = ["Tom", "Benn", "Cal", "Jasper", "Eli", "Bo"]
HELPERS = ["Uncle Jed", "Aunt May", "Old Sam", "Gramma Belle"]


def _bravery(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1


def _noise(world: World) -> None:
    bell = world.get("glory")
    bell.meters["noise"] = bell.meters.get("noise", 0.0) + 1


def _stabilize(world: World) -> None:
    rack = world.get("rack")
    if rack.meters.get("wobble", 0.0) >= THRESHOLD:
        rack.meters["wobble"] = 0.0


def propagate(world: World) -> None:
    if world.get("rack").meters.get("wobble", 0.0) >= THRESHOLD and ("ring",) not in world.fired:
        world.fired.add(("ring",))
        _noise(world)
        world.say("KLANG! went the glory bell on the rack.")
    if world.get("hero").memes.get("bravery", 0.0) >= THRESHOLD and ("steady",) not in world.fired:
        world.fired.add(("steady",))
        _stabilize(world)
        world.say("The rack steadied under brave hands.")


def predict_fall(world: World) -> bool:
    sim = world.copy()
    sim.get("rack").meters["wobble"] = 1.0
    propagate(sim)
    return sim.get("glory").meters.get("noise", 0.0) >= THRESHOLD


def tell(name: str, gender: str, helper: str) -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    helper_ent = world.add(Entity(id="helper", kind="character", type="parent", label=helper))
    rack = world.add(Entity(id="rack", type="rack", label="rack", phrase="the tall rack by the door"))
    glory = world.add(Entity(id="glory", type="bell", label="glory bell", phrase="a shining glory bell"))
    world.facts.update(hero=hero, helper=helper_ent, rack=rack, glory=glory)

    world.say(
        f"Once, in the frontier town of {world.setting.place}, there was an adventurous child named {name}."
        f" {name} liked big sky ideas, tidy boots, and the kind of glory that made a room feel wider."
    )
    world.say(
        f"Near the door stood {world.setting.detail}, and on it hung a shining glory bell."
        f" {name} watched it and thought, 'If I can reach that rack, I can fix this day proper.'"
    )

    world.para()
    world.say(
        f"{name} stepped closer. The boards said {name}'s feet, creak-creak, and the rack answered with a little shiver."
    )
    world.get("rack").meters["wobble"] = 1.0
    if predict_fall(world):
        world.say(
            f"{name} heard the warning in the wobble and swallowed a gulp."
            f" 'Brave now,' {name} told {hero.pronoun('object')}self, 'slow hands, steady heart.'"
        )

    world.para()
    _bravery(world, hero)
    world.say(
        f"{name} climbed up one careful step at a time, and the rack gave a mighty CREEK."
        f" {helper} gasped, 'Easy, kiddo!'"
    )
    propagate(world)
    world.say(
        f"Then {name} reached out, gave the glory bell a gentle lift, and set it straight again."
        f" CLINK! The bell sang clear and bright instead of tumbling to the floor."
    )

    world.para()
    world.say(
        f"At last, {name} climbed down, grinning like a possum at a picnic."
        f" The rack stayed steady, the glory bell hung proud, and the whole store seemed taller for it."
    )

    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a Tall Tale for a child named {hero.label} about bravery near a rack and a glory bell.",
        f"Tell a short story where an adventurous child uses brave thinking and sound effects to fix a wobbly rack.",
        "Write a frontier-style story with inner monologue, a noisy rack, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question="Who was the adventurous child in the story?",
            answer=f"The adventurous child was {hero.label}, a brave little kid in the frontier store.",
        ),
        QAItem(
            question="What was hanging on the rack?",
            answer="A shining glory bell was hanging on the rack near the door.",
        ),
        QAItem(
            question="What did the child tell themselves before climbing?",
            answer=f"{hero.label} told {hero.pronoun('object')}self to be brave, slow, and steady before climbing.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the rack steady, the glory bell hanging straight, and the child grinning after a brave rescue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rack for?",
            answer="A rack is something you can use to hold or hang things up off the floor.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while still trying your best.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words like clank, creak, and clang that help you hear the action in your head.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking words, like when they talk to themselves in their head.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "store"),
            asp.fact("entity", "hero"),
            asp.fact("entity", "rack"),
            asp.fact("entity", "glory"),
            asp.fact("wobbles", "rack"),
            asp.fact("hangs_on", "glory", "rack"),
            asp.fact("trait", "hero", "adventurous"),
            asp.fact("trait", "hero", "brave"),
        ]
    )


ASP_RULES = r"""
worry(glory) :- hangs_on(glory, rack), wobbles(rack).
fix(glory) :- worry(glory), brave(hero).
story_ok :- worry(glory), fix(glory), adventurous(hero).
#show worry/1.
#show fix/1.
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("Mismatch: ASP did not derive story_ok.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale storyworld with rack, glory, and adventure.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.helper)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams("Mabel", "girl", "Uncle Jed")),
            generate(StoryParams("Jasper", "boy", "Old Sam")),
            generate(StoryParams("Ruby", "girl", "Aunt May")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
