#!/usr/bin/env python3
"""
Standalone storyworld: a heartwarming moral-value tale about a sergeant,
a swoop, and a glottal surprise.

Premise:
- A small child or animal is trying to do a kind deed.
- A sergeant notices a risky swoop of action and gently redirects it.
- A glottal little troublemaking sound or hiccup can make the moment tense.
- The ending should prove a moral value: kindness, honesty, patience, or courage.

The world is intentionally compact: a single scene, a few typed entities, and
a state-driven resolution that changes both physical and emotional meters.
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

MORAL_VALUES = {
    "kindness": "kindness",
    "honesty": "honesty",
    "patience": "patience",
    "courage": "courage",
}

PLACES = {
    "garden": {"label": "the garden", "kind": "outdoor"},
    "market": {"label": "the market", "kind": "outdoor"},
    "porch": {"label": "the porch", "kind": "outdoor"},
    "kitchen": {"label": "the kitchen", "kind": "indoor"},
    "station": {"label": "the little station", "kind": "indoor"},
}

ACTIVITIES = {
    "swoop": {
        "verb": "swoop in too fast",
        "gerund": "swooping in too fast",
        "risk": "a spill",
        "damage": "spill",
        "motion": "swoop",
    },
    "glottal": {
        "verb": "make a glottal hiccup",
        "gerund": "making a glottal hiccup",
        "risk": "a shaky voice",
        "damage": "shiver",
        "motion": "glottal",
    },
}

GIFTS = {
    "bread": {
        "label": "a warm loaf of bread",
        "kind": "bread",
        "care": "wrap it in a cloth",
    },
    "tea": {
        "label": "a cup of tea",
        "kind": "tea",
        "care": "carry it carefully",
    },
    "flowers": {
        "label": "a little bunch of flowers",
        "kind": "flowers",
        "care": "keep them upright",
    },
    "toy": {
        "label": "a small wooden toy",
        "kind": "toy",
        "care": "hold it with two hands",
    },
}

CHARACTER_KINDS = {
    "child": {"subject": "they", "object": "them", "possessive": "their"},
    "girl": {"subject": "she", "object": "her", "possessive": "her"},
    "boy": {"subject": "he", "object": "him", "possessive": "his"},
    "fox": {"subject": "it", "object": "it", "possessive": "its"},
    "mouse": {"subject": "it", "object": "it", "possessive": "its"},
}

NAMES = {
    "child": ["Mina", "Pip", "Jory", "Nia", "Owen"],
    "girl": ["Ava", "Lina", "Maya", "Rose", "Ivy"],
    "boy": ["Theo", "Milo", "Ben", "Noah", "Finn"],
    "fox": ["Rusty", "Moss", "Juniper"],
    "mouse": ["Pebble", "Nib", "Tally"],
}

TRAITS = ["gentle", "brave", "careful", "patient", "warmhearted"]


# ---------------------------------------------------------------------------
# Core entities / world
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        forms = CHARACTER_KINDS.get(self.type, CHARACTER_KINDS["child"])
        return forms[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class World:
    place: str
    place_label: str
    moral: str
    activity: str
    gift: str
    hero_kind: str
    hero_name: str
    sergeant_name: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy
        clone = World(
            place=self.place,
            place_label=self.place_label,
            moral=self.moral,
            activity=self.activity,
            gift=self.gift,
            hero_kind=self.hero_kind,
            hero_name=self.hero_name,
            sergeant_name=self.sergeant_name,
        )
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0


def setup_world(params: "StoryParams") -> World:
    w = World(
        place=params.place,
        place_label=PLACES[params.place]["label"],
        moral=params.moral,
        activity=params.activity,
        gift=params.gift,
        hero_kind=params.hero_kind,
        hero_name=params.hero_name,
        sergeant_name=params.sergeant_name,
    )
    hero = w.add(Entity(id="hero", kind="character", type=params.hero_kind, label=params.hero_name))
    sergeant = w.add(Entity(id="sergeant", kind="character", type="sergeant", label=params.sergeant_name))
    gift = w.add(Entity(
        id="gift",
        kind="thing",
        type=params.gift,
        label=GIFTS[params.gift]["label"],
        phrase=GIFTS[params.gift]["label"],
        owner=hero.id,
        caretaker=sergeant.id,
    ))
    helper = w.add(Entity(id="helper", kind="thing", type="cloth", label="a soft cloth", protective=True))
    helper.worn_by = hero.id
    w.facts.update(hero=hero, sergeant=sergeant, gift=gift, helper=helper)
    return w


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def hero_pronouns(hero: Entity) -> tuple[str, str, str]:
    return hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")


def predict_outcome(world: World, risky: bool = True) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    sergeant = sim.get("sergeant")
    gift = sim.get("gift")
    if risky:
        hero.meters[sim.activity] = 1.0
        if sim.activity == "swoop":
            gift.meters["spill"] = 1.0
        else:
            hero.meters["voice"] = 1.0
    return {
        "gift_spilled": gift.meters.get("spill", 0.0) >= THRESHOLD,
        "voice_shaky": hero.meters.get("voice", 0.0) >= THRESHOLD,
        "sergeant_warmth": sergeant.memes.get("warmth", 0.0),
    }


def intro(world: World) -> None:
    hero = world.get("hero")
    sergeant = world.get("sergeant")
    world.say(
        f"{hero.label} was a {random.choice(['small', 'little'])} {world.hero_kind} with a "
        f"{random.choice(TRAITS)} heart."
    )
    world.say(
        f"{sergeant.label} was a sergeant who noticed things quickly, but spoke softly."
    )


def value_beat(world: World) -> None:
    hero = world.get("hero")
    world.say(
        f"{hero.label} loved the value of {world.moral}; it made {hero.pronoun('object')} "
        f"want to help in a careful way."
    )


def setup_scene(world: World) -> None:
    gift = world.get("gift")
    world.say(
        f"One afternoon at {world.place_label}, {gift.label} waited on a small table."
    )
    world.say(
        f"{gift.label.capitalize()} looked ready for someone kind to carry it home."
    )


def tension(world: World) -> None:
    hero = world.get("hero")
    sergeant = world.get("sergeant")
    gift = world.get("gift")
    subj, obj, poss = hero_pronouns(hero)
    if world.activity == "swoop":
        world.say(
            f"{hero.label} wanted to swoop in and take {gift.label} at once, "
            f"but {sergeant.label} lifted a hand."
        )
        world.say(
            f'"Careful," {sergeant.label} said. "A fast swoop could make {gift.label} spill."'
        )
        hero.memes["eager"] = hero.memes.get("eager", 0.0) + 1.0
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    else:
        world.say(
            f"{hero.label} tried to speak, but a tiny glottal hiccup caught in {poss} throat."
        )
        world.say(
            f"{sergeant.label} waited kindly, because a patient listener makes room for brave words."
        )
        hero.memes["nervous"] = hero.memes.get("nervous", 0.0) + 1.0


def resolve(world: World) -> None:
    hero = world.get("hero")
    sergeant = world.get("sergeant")
    gift = world.get("gift")
    subj, obj, poss = hero_pronouns(hero)
    world.para()
    if world.activity == "swoop":
        world.say(
            f"{sergeant.label} showed {hero.label} how to {GIFTS[world.gift]['care']} first."
        )
        world.say(
            f"{hero.label} nodded, slowed down, and carried {gift.label} with both hands."
        )
        world.say(
            f"In the end, {gift.label} made it home safely, and {world.moral} felt even warmer."
        )
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
        hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
        sergeant.memes["warmth"] = sergeant.memes.get("warmth", 0.0) + 1.0
    else:
        world.say(
            f"{sergeant.label} smiled and said, 'Take your time. I'm listening.'"
        )
        world.say(
            f"That gentle patience helped {hero.label} speak again, and the glottal catch slipped away."
        )
        world.say(
            f"{hero.label} said the whole message clearly, and {sergeant.label} answered with a proud nod."
        )
        hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0
        hero.memes["courage"] = hero.memes.get("courage", 0.0) + 1.0
        sergeant.memes["warmth"] = sergeant.memes.get("warmth", 0.0) + 1.0


def tell_story(world: World) -> World:
    intro(world)
    value_beat(world)
    world.para()
    setup_scene(world)
    tension(world)
    resolve(world)
    world.facts.update(
        moral=world.moral,
        activity=world.activity,
        place=world.place,
        place_label=world.place_label,
    )
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    gift: str
    hero_kind: str
    hero_name: str
    sergeant_name: str
    moral: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a heartwarming story for a child about {world.hero_name}, a sergeant, and {world.moral}.",
        f"Tell a gentle tale set at {world.place_label} that includes a {world.activity} moment and a sergeant.",
        f"Write a short story where a {world.hero_kind} learns {world.moral} with help from a sergeant.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    sergeant = world.get("sergeant")
    gift = world.get("gift")
    subj, obj, poss = hero_pronouns(hero)
    items = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a {world.hero_kind} with a kind heart, and {sergeant.label}, the sergeant who helped."
        ),
        QAItem(
            question=f"What was happening at {world.place_label}?",
            answer=f"{gift.label.capitalize()} was waiting there while {hero.label} and {sergeant.label} faced a small problem and solved it gently."
        ),
        QAItem(
            question=f"What did {hero.label} learn?",
            answer=f"{hero.label} learned about {world.moral} and how to slow down, listen, and choose the careful way."
        ),
    ]
    if world.activity == "swoop":
        items.append(
            QAItem(
                question=f"Why did {sergeant.label} warn {hero.label} about the swoop?",
                answer=f"{sergeant.label} worried that a fast swoop would make {gift.label} spill, so {sergeant.label} suggested carrying it carefully."
            )
        )
    else:
        items.append(
            QAItem(
                question=f"Why did {sergeant.label} stay patient when {hero.label} had a glottal hiccup?",
                answer=f"{sergeant.label} knew that patience helps when someone is trying to speak bravely, so {sergeant.label} waited kindly."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    if world.activity == "swoop":
        return [
            QAItem(
                question="What does swoop mean?",
                answer="To swoop is to move quickly and suddenly, like a fast little dive or grab."
            ),
            QAItem(
                question="Why should you carry fragile things carefully?",
                answer="Fragile things can spill or break if they are moved too fast, so careful hands help keep them safe."
            ),
        ]
    return [
        QAItem(
            question="What is a glottal hiccup?",
            answer="A glottal hiccup is a tiny catch in the throat that can make a voice sound bumpy for a moment."
        ),
        QAItem(
            question="Why is patience helpful when someone is speaking?",
            answer="Patience gives the speaker time to finish, and it helps them feel safe and heard."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- motion(A).
gift(G) :- gift_item(G).
moral(M) :- moral_value(M).

compatible(P, A, G, M) :- place(P), activity(A), gift(G), moral(M).

% The ASP twin is intentionally simple: every registered moral tale is valid.
valid_story(P, A, G, M) :- compatible(P, A, G, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("motion", aid))
    for gid in GIFTS:
        lines.append(asp.fact("gift_item", gid))
    for mid in MORAL_VALUES:
        lines.append(asp.fact("moral_value", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, a, g, m) for p in PLACES for a in ACTIVITIES for g in GIFTS for m in MORAL_VALUES)
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - asp_set))
    print("only in asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, a, g, m) for p in PLACES for a in ACTIVITIES for g in GIFTS for m in MORAL_VALUES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.gift and args.gift not in GIFTS:
        raise StoryError("Unknown gift.")
    if args.moral and args.moral not in MORAL_VALUES:
        raise StoryError("Unknown moral value.")

    place = args.place or rng.choice(list(PLACES))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    gift = args.gift or rng.choice(list(GIFTS))
    moral = args.moral or rng.choice(list(MORAL_VALUES))

    hero_kind = args.hero_kind or rng.choice(["child", "girl", "boy", "fox", "mouse"])
    hero_name = args.hero_name or rng.choice(NAMES[hero_kind])
    sergeant_name = args.sergeant_name or rng.choice(["Sergeant Bell", "Sergeant Reed", "Sergeant Vale"])

    return StoryParams(
        place=place,
        activity=activity,
        gift=gift,
        hero_kind=hero_kind,
        hero_name=hero_name,
        sergeant_name=sergeant_name,
        moral=moral,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="garden", activity="swoop", gift="bread", hero_kind="child", hero_name="Mina", sergeant_name="Sergeant Bell", moral="kindness"),
    StoryParams(place="porch", activity="glottal", gift="flowers", hero_kind="girl", hero_name="Ava", sergeant_name="Sergeant Reed", moral="patience"),
    StoryParams(place="market", activity="swoop", gift="tea", hero_kind="boy", hero_name="Theo", sergeant_name="Sergeant Vale", moral="honesty"),
    StoryParams(place="station", activity="glottal", gift="toy", hero_kind="mouse", hero_name="Pebble", sergeant_name="Sergeant Bell", moral="courage"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming moral-value story world with swoop, glottal, and sergeant.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--hero-kind", choices=sorted(CHARACTER_KINDS))
    ap.add_argument("--hero-name")
    ap.add_argument("--sergeant-name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story tuples:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} / {p.activity} / {p.moral}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
