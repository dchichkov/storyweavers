#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hostile_swat_foreshadowing_sound_effects_kindness_slice.py
==============================================================================================================================

A small slice-of-life storyworld about a tense little moment, a warning sign,
a noisy swat, and a kinder way through.

Premise:
- A child notices a hostile stray cat near the porch.
- Something in the scene foreshadows that the cat is scared: the tail flicks,
  the whiskers go stiff, and the sound effects make the tension easy to hear.
- The child first reaches too fast, the cat swats, and then a kinder choice
  changes the moment: space, soft words, and a bowl of water.

This world is intentionally small and grounded. It simulates a few physical and
emotional state changes, then renders them into a complete child-facing story.
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

FORESHADOW_THRESHOLD = 1.0
HOSTILE_THRESHOLD = 1.0
KIND_THRESHOLD = 1.0
SWAT_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoor: bool = False
    vibe: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


PLACES = {
    "porch": Place(name="the porch", indoor=False, vibe="quiet", affords={"bowl", "space"}),
    "kitchen": Place(name="the kitchen", indoor=True, vibe="warm", affords={"bowl", "space"}),
    "hall": Place(name="the hall", indoor=True, vibe="narrow", affords={"space"}),
    "garden_gate": Place(name="the garden gate", indoor=False, vibe="breezy", affords={"space", "bowl"}),
}

SOUNDS = {
    "cat": "mrrp",
    "swat": "whap",
    "bowl": "clink",
    "tiny_step": "tap-tap",
    "soft_voice": "shh",
}

NAMES_GIRL = ["Mina", "Ava", "Lily", "Maya", "Zoe", "Nora"]
NAMES_BOY = ["Noah", "Eli", "Theo", "Leo", "Ben", "Sam"]
TRAITS = ["gentle", "curious", "patient", "quiet", "helpful"]


def valid_places() -> list[str]:
    return list(PLACES)


def _setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    w = World(place)
    child = w.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little"],
        memes={"curiosity": 0.0, "kindness": 0.0, "worry": 0.0, "fear": 0.0, "calm": 0.0, "shame": 0.0},
    ))
    parent = w.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        memes={"care": 0.0, "worry": 0.0, "calm": 0.0},
    ))
    cat = w.add(Entity(
        id="cat",
        kind="character",
        type="cat",
        label="a stray cat",
        phrase="a small striped stray cat",
        memes={"hostility": 0.0, "fear": 0.0, "trust": 0.0, "calm": 0.0},
    ))
    bowl = w.add(Entity(
        id="bowl",
        kind="thing",
        type="bowl",
        label="a little bowl",
        phrase="a little bowl of water",
        owner=params.name,
        meters={"fullness": 0.0},
    ))
    w.facts.update(child=child, parent=parent, cat=cat, bowl=bowl)
    return w


def _foreshadow(world: World) -> None:
    cat = world.get("cat")
    cat.memes["hostility"] += 1.0
    cat.memes["fear"] += 1.0
    world.say(
        f"At {world.place.name}, {cat.phrase} sat near the step, "
        f"its tail twitching and its whiskers stiff."
    )
    world.say(
        f"The porch was so still that even {SOUNDS['tiny_step']} sounded loud."
    )


def _approach(world: World) -> None:
    child = world.get(next(k for k in world.entities if k not in {"parent", "cat", "bowl"}))
    cat = world.get("cat")
    child.memes["curiosity"] += 1.0
    world.say(
        f"{child.id} noticed the cat and wanted to help, but {child.pronoun()} "
        f"reached a little too fast."
    )
    cat.memes["fear"] += 1.0


def _swat(world: World) -> None:
    child = world.get(next(k for k in world.entities if k not in {"parent", "cat", "bowl"}))
    cat = world.get("cat")
    if ("swat", child.id) in world.fired:
        return
    world.fired.add(("swat", child.id))
    cat.meters["swat"] = cat.meters.get("swat", 0.0) + 1.0
    child.memes["startle"] = child.memes.get("startle", 0.0) + 1.0
    world.say(f"{cat.id} gave a quick {SOUNDS['swat']} and swatted the air.")
    world.say(f"{child.id} froze for a second, then took a careful step back.")


def _kindness(world: World) -> None:
    child = world.get(next(k for k in world.entities if k not in {"parent", "cat", "bowl"}))
    parent = world.get("parent")
    cat = world.get("cat")
    bowl = world.get("bowl")
    if (KIND_THRESHOLD, child.id) in world.fired:
        return
    world.fired.add((KIND_THRESHOLD, child.id))
    child.memes["kindness"] += 1.0
    child.memes["calm"] += 1.0
    parent.memes["calm"] += 1.0
    cat.memes["trust"] += 1.0
    cat.memes["calm"] += 1.0
    bowl.meters["fullness"] = 1.0
    world.say(
        f"{child.id} remembered to be kind: {SOUNDS['soft_voice']}, "
        f"slow hands, and one bowl of water left just nearby."
    )
    world.say(
        f"The cat blinked, stopped being hostile, and leaned closer to sniff "
        f"the water."
    )


def _settle(world: World) -> None:
    child = world.get(next(k for k in world.entities if k not in {"parent", "cat", "bowl"}))
    cat = world.get("cat")
    bowl = world.get("bowl")
    if (1, "settled") in world.fired:
        return
    if cat.memes["trust"] < KIND_THRESHOLD or bowl.meters.get("fullness", 0.0) < 1.0:
        return
    world.fired.add((1, "settled"))
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    cat.memes["hostility"] = max(0.0, cat.memes["hostility"] - 1.0)
    world.say(
        f"After that, the cat drank with a tiny {SOUNDS['bowl']} and sat down "
        f"in the sun like it belonged there."
    )
    world.say(
        f"{child.id} smiled, because kindness had changed the whole moment."
    )


def _run_rules(world: World) -> None:
    _foreshadow(world)
    _approach(world)
    _swat(world)
    _kindness(world)
    _settle(world)


def tell(place: Place, name: str, gender: str, parent: str) -> World:
    params = StoryParams(place=place_key(place), name=name, gender=gender, parent=parent)
    world = _setup_world(params)
    _run_rules(world)
    return world


def place_key(place: Place) -> str:
    for k, v in PLACES.items():
        if v.name == place.name:
            return k
    raise KeyError(place.name)


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    place = world.place.name
    return [
        f'Write a short slice-of-life story for a small child that includes the words "hostile" and "swat".',
        f"Tell a gentle story about {child.id} at {place} where a scared cat acts hostile at first, then kindness helps.",
        f"Write a tiny realistic story with foreshadowing and sound effects about a child, a stray cat, and a kinder choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    cat = world.facts["cat"]
    bowl = world.facts["bowl"]
    return [
        QAItem(
            question=f"Who tried to help the cat at {world.place.name}?",
            answer=f"{child.id} tried to help, and {parent.label} watched closely nearby.",
        ),
        QAItem(
            question="What made it clear the cat was uneasy before the swat?",
            answer="Its tail kept twitching, its whiskers went stiff, and the little sounds made the tension easy to hear.",
        ),
        QAItem(
            question="What did the cat do when the child reached too fast?",
            answer=f"The cat gave a quick swat, which was a scared warning rather than a mean trick.",
        ),
        QAItem(
            question="How did the child show kindness after that?",
            answer=f"{child.id} stepped back, used a soft voice, and left the bowl of water nearby so the cat could choose to come closer.",
        ),
        QAItem(
            question="What was the ending image in the story?",
            answer=f"The cat drank from the bowl and sat down more calmly, while {child.id} smiled because the moment had turned gentle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a cat's swat usually mean?",
            answer="A swat is often a warning or a sign that the cat feels scared or overwhelmed and wants more space.",
        ),
        QAItem(
            question="Why can a soft voice help with an upset animal?",
            answer="A soft voice can make the moment feel less scary, which gives the animal room to relax and choose to come closer.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when small details hint that something important may happen later.",
        ),
        QAItem(
            question="What are sound effects in writing?",
            answer="Sound effects are words like clink, tap-tap, or whap that help a reader hear the moment in their mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_helped(C) :- child(C), kindness(C).
cat_swatted(C) :- child(C), swat_event(C).
calmed(C) :- child(C), kindness(C), cat_trust(C).
valid_story(P) :- place(P), affords(P, swat), affords(P, kindness).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k, p in PLACES.items():
        lines.append(asp.fact("place", k))
        if p.indoor:
            lines.append(asp.fact("indoor", k))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", k, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        combos.append((place, "any"))
    return combos


def asp_verify() -> int:
    clingo_set = set(asp_valid_places())
    python_set = {(k,) for k in PLACES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid places ({len(clingo_set)} places).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life storyworld: foreshadowing, sound effects, and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    _run_rules(world)
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
    StoryParams(place="porch", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="kitchen", name="Noah", gender="boy", parent="father"),
    StoryParams(place="garden_gate", name="Lily", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(f"{len(asp.atoms(model, 'valid_story'))} valid places:")
        for (place,) in sorted(set(asp.atoms(model, "valid_story"))):
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
            header = f"### {p.name} at {p.place} ({p.gender})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
