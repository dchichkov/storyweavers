#!/usr/bin/env python3
"""
storyworlds/worlds/strengthen_food_dim_misunderstanding_friendship_tall_tale.py
===============================================================================

A small standalone storyworld about a tall-tale misunderstanding that is
resolved by friendship. The seed words are woven into the premise:
"strengthen" appears as the way a helper strengthens a weak idea or a snack,
and "food-dim" becomes a nickname for a dim little lantern used during a picnic
and map-search misunderstanding.

The world follows a classical tiny-story arc:
- friends build a tall tale,
- one child misunderstands the other,
- a shared meal and a clearer look at the evidence repair the friendship,
- the ending image proves what changed.

This file is self-contained and uses only stdlib plus the shared result
containers from storyworlds/results.py. ASP support is included inline for
parity checks.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    bright: bool = True
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Food:
    id: str
    label: str
    size: str
    flavor: str
    strength: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lantern:
    id: str
    label: str
    glow: str
    food_dim: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    trigger: str
    line: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    place: Optional[Place] = None
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


def _girl_name_pool() -> list[str]:
    return ["Mabel", "Ruby", "Ivy", "Nell", "Ada", "June", "Clara", "Wren"]


def _boy_name_pool() -> list[str]:
    return ["Bert", "Otis", "Finn", "Earl", "Jasper", "Theo", "Milo", "Gus"]


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    snack: str
    snack_size: str
    snack_flavor: str
    snack_strength: str
    lantern: str
    misunderstanding: str
    seed: Optional[int] = None


SETTINGS = {
    "meadow": "a big windy meadow",
    "riverbank": "a sunny riverbank",
    "orchard": "an apple orchard on a gold afternoon",
}

FOODS = {
    "sandwich": Food("sandwich", "sandwich", "tall", "jammy", "strengthen"),
    "pie": Food("pie", "pie", "round", "berry-sweet", "strengthen"),
    "loaf": Food("loaf", "bread loaf", "long", "buttery", "strengthen"),
}

LANTERNS = {
    "food-dim": Lantern("food-dim", "food-dim lantern", "glowed like a sleepy star", True, {"food-dim"}),
    "dim-lantern": Lantern("dim-lantern", "dim lantern", "shone soft and low", True, {"food-dim"}),
}

MISUNDERSTANDINGS = {
    "giant": Misunderstanding(
        "giant",
        "thought the snack was a giant clue",
        '"That clue is so tall it must point to treasure!"',
        "It was only a snack stacked high for lunch, not a map sign.",
        {"misunderstanding", "friendship"},
    ),
    "echo": Misunderstanding(
        "echo",
        "heard a shout and thought it was a warning",
        '"Did you say go home?"',
        "It was only an echo bouncing off the hill.",
        {"misunderstanding", "friendship"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale friendship storyworld about a misunderstanding and a shared snack."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=FOODS)
    ap.add_argument("--lantern", choices=LANTERNS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    snack = args.snack or rng.choice(list(FOODS))
    lantern = args.lantern or rng.choice(list(LANTERNS))
    misunderstanding = args.misunderstanding or rng.choice(list(MISUNDERSTANDINGS))
    hg = args.hero_gender or rng.choice(["girl", "boy"])
    fg = args.friend_gender or ("boy" if hg == "girl" else "girl")
    hero = args.hero or rng.choice(_girl_name_pool() if hg == "girl" else _boy_name_pool())
    friend = args.friend or rng.choice([n for n in (_boy_name_pool() + _girl_name_pool()) if n != hero])
    return StoryParams(
        setting=setting,
        hero=hero,
        hero_gender=hg,
        friend=friend,
        friend_gender=fg,
        snack=snack,
        snack_size=FOODS[snack].size,
        snack_flavor=FOODS[snack].flavor,
        snack_strength=FOODS[snack].strength,
        lantern=lantern,
        misunderstanding=misunderstanding,
    )


def tell(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(params.hero, "character", params.hero_gender, role="hero"))
    friend = w.add(Entity(params.friend, "character", params.friend_gender, role="friend"))
    place = Place("place", SETTINGS[params.setting])
    w.place = place
    snack = Food(params.snack, params.snack, params.snack_size, params.snack_flavor, params.snack_strength)
    lan = Lantern(params.lantern, params.lantern, LANTERNS[params.lantern].glow, True)
    m = MISUNDERSTANDINGS[params.misunderstanding]

    hero.memes["pride"] = 1
    friend.memes["curiosity"] = 1
    hero.memes["hurt"] = 0
    friend.memes["worry"] = 0

    w.say(
        f"On a day so bright it seemed to whistle, {hero.id} and {friend.id} set out into {place.label}. "
        f"They carried a {snack.size} {snack.label} and a {lan.label} that {lan.glow}."
    )
    w.say(
        f"{hero.id} held up the snack like a flag and tried to {snack.strength} their picnic into a grand tall tale."
    )
    w.para()
    w.say(
        f"Then came the misunderstanding: {friend.id} {m.trigger}. {friend.id} blinked, then said, {m.line}"
    )
    friend.memes["worry"] += 1
    hero.memes["hurt"] += 1
    w.say(
        f"{hero.id} frowned, because it sounded as if {friend.id} did not trust the story at all."
    )
    w.para()
    w.say(
        f"But {friend.id} looked again at the snack, laughed at the mistake, and said, "
        f'"Oh! {m.fix}"'
    )
    hero.memes["hurt"] = 0
    hero.memes["friendship"] = 1
    friend.memes["friendship"] = 1
    w.say(
        f"To make things right, {friend.id} cut the {snack.label} in two, shared the biggest piece, "
        f"and set the {lan.label} between them like a tiny moon."
    )
    w.say(
        f"That little light made the whole picnic seem taller than a fence and kinder than a song."
    )
    w.para()
    w.say(
        f"In the end, {hero.id} and {friend.id} ate side by side, laughing at the wrong guess and cheering the right one. "
        f"Their friendship was stronger than the misunderstanding, and the {lan.label} kept glowing like it knew the secret."
    )

    w.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        snack=snack,
        lantern=lan,
        misunderstanding=m,
        resolved=True,
    )
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    return [
        f"Write a tall-tale friendship story where {f['hero'].id} and {f['friend'].id} share a {f['snack'].label} in {f['place'].label}. Include a misunderstanding that gets fixed kindly.",
        f"Tell a child-friendly story in a tall-tale voice where the food-dim lantern glows during a picnic and a mistaken guess strains the friendship before it is repaired.",
        f"Write a short story using the words strengthen and food-dim, ending with two friends closer than before.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    return [
        QAItem(
            question=f"What did {f['hero'].id} and {f['friend'].id} carry on their picnic?",
            answer=f"They carried a {f['snack'].size} {f['snack'].label} and a {f['lantern'].label} that glowed softly.",
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{f['friend'].id} took one look and {f['misunderstanding'].trigger}, which made the moment feel sour until it was cleared up.",
        ),
        QAItem(
            question="How did they fix it?",
            answer=f"They talked it through, shared the snack, and let friendship strengthen the day again.",
        ),
    ]


def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does strengthen mean in this story?",
            answer="It means to make something stronger, like a friendship, a plan, or even a snack made sturdy for a picnic tale.",
        ),
        QAItem(
            question="What does food-dim mean?",
            answer="Food-dim is the story's name for a lantern that glows softly during a picnic, dim enough to feel cozy instead of bright.",
        ),
        QAItem(
            question="What should friends do after a misunderstanding?",
            answer="They should listen, explain kindly, and share what they know so the friendship can stay strong.",
        ),
    ]


def dump_trace(w: World) -> str:
    bits = []
    for e in w.entities.values():
        bits.append(f"{e.id}: memes={dict(e.memes)}")
    return "--- trace ---\n" + "\n".join(bits)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
story_ok.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("feature", "misunderstanding"),
            asp.fact("feature", "friendship"),
            asp.fact("seedword", "strengthen"),
            asp.fact("seedword", "food-dim"),
        ]
    )


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def build_sample(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _pick_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []
    if args.all:
        for i, setting in enumerate(SETTINGS):
            p = resolve_params(argparse.Namespace(
                setting=setting, snack="sandwich", lantern="food-dim", misunderstanding="giant",
                hero="Mabel", hero_gender="girl", friend="Bert", friend_gender="boy"
            ), random.Random(base_seed + i))
            samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    return samples


def verify() -> int:
    sample = build_sample(resolve_params(argparse.Namespace(
        setting="meadow", snack="sandwich", lantern="food-dim", misunderstanding="giant",
        hero="Mabel", hero_gender="girl", friend="Bert", friend_gender="boy"
    ), random.Random(0)))
    if "friendship" not in sample.story.lower():
        print("verification failed: story missing friendship")
        return 1
    print("OK: sample story generated.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        raise SystemExit(verify())
    if args.show_asp:
        print(asp_program("", "#show story_ok/0."))
        return
    if args.asp:
        import storyworlds.asp as asp
        print(asp.one_model(asp_program("", "#show story_ok/0.")))
        return
    samples = _pick_samples(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
