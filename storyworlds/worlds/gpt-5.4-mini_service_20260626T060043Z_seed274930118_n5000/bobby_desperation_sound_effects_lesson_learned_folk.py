#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bobby_desperation_sound_effects_lesson_learned_folk.py
============================================================================================================

A small folk-tale storyworld about Bobby, a noisy problem, and a lesson learned.

Premise:
- Bobby is a young villager who loves sound effects: tap-tap, thump, whoosh, and clang.
- One day, a useful village bell goes missing from the square.
- Bobby grows desperate to make a big sound and prove he can help.
- He searches with noisy, clumsy ideas, making the trouble worse at first.
- In the end, he learns that the best sound is often the quiet one that helps somebody.

This world keeps the story grounded in simulated state:
- Bobby has emotional meters like hope, pride, worry, and desperation.
- Objects have physical meters like carried, hidden, noisy, and found.
- The narration changes depending on what actually happened in the simulation.

The world is intentionally small and constraint-based:
- A story only exists when Bobby truly has a reason to be desperate.
- The solution must be believable: a sound-made clue, a helper, and a lesson learned.
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
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["found", "noisy", "lost", "carried", "heard", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "pride", "worry", "desperation", "relief", "kindness", "lesson"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    features: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    lost_thing: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "village_green": Place("village_green", "the village green", ["grass", "paths", "bench", "well"]),
    "market_square": Place("market_square", "the market square", ["stalls", "stones", "steps", "clock"]),
    "river_bridge": Place("river_bridge", "the river bridge", ["water", "planks", "rails", "echo"]),
}

LOST_THINGS = {
    "bell": {"label": "bell", "type": "thing", "plural": False},
    "drum": {"label": "drum", "type": "thing", "plural": False},
    "lantern": {"label": "lantern", "type": "thing", "plural": False},
}

HELPERS = {
    "grandmother": {"label": "Grandmother Miri", "type": "mother"},
    "ferryman": {"label": "Old Toma", "type": "man"},
    "bakery_child": {"label": "Pip", "type": "boy"},
}

BOBBY_NAMES = ["Bobby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for thing in LOST_THINGS:
            for helper in HELPERS:
                combos.append((place, thing, helper))
    return combos


def sound_effect(action: str) -> str:
    return {
        "search": "tap-tap, tap-tap",
        "run": "pat-pat, pat-pat",
        "shake": "clang-clang",
        "wind": "whoooosh",
        "step": "thump, thump",
        "find": "ding!",
        "comfort": "soft hush-hush",
    }.get(action, "tap-tap")


def lesson_line() -> str:
    return "Bobby learned that a helpful sound is better than a loud one when somebody needs care."


def setup_story(world: World, bobby: Entity, lost: Entity, helper: Entity) -> None:
    world.say(
        f"In {world.place.label}, there lived a small boy named Bobby who loved sound effects. "
        f"He liked tap-tap feet, thump-thump doors, and the bright little clang of clean metal."
    )
    world.say(
        f"One morning, the village felt too quiet. The {lost.label} was missing, and Bobby's chest filled with desperation."
    )
    bobby.memes["desperation"] += 1
    bobby.memes["worry"] += 1
    lost.meters["lost"] += 1
    world.facts["setup_done"] = True


def search_sequence(world: World, bobby: Entity, lost: Entity) -> None:
    world.para()
    world.say(
        f"Bobby hurried across {world.place.label} making {sound_effect('run')}, looking behind the bench, the well, and the steps."
    )
    world.say(
        f"He called, 'Hello? {lost.label}, where are you?' and listened for a little {sound_effect('search')}."
    )
    bobby.memes["hope"] += 1
    bobby.memes["desperation"] += 1
    world.facts["searched"] = True


def trouble_sequence(world: World, bobby: Entity, lost: Entity) -> None:
    world.para()
    world.say(
        f"At last Bobby saw a shadow near the stones and shook a wooden crate to make {sound_effect('shake')}."
    )
    world.say(
        f"But the noise only startled a pigeon, and {sound_effect('wind')} carried the wrong clue away."
    )
    bobby.memes["pride"] += 1
    bobby.memes["worry"] += 1
    world.facts["noise_made_trouble"] = True


def helper_sequence(world: World, bobby: Entity, helper: Entity, lost: Entity) -> None:
    world.para()
    world.say(
        f"Then {helper.label} heard Bobby's hurry and came with gentle steps and a calm face."
    )
    world.say(
        f"'{bobby.id},' {helper.pronoun().capitalize()} said, 'listen for the place where the sound changes. Quiet ears can solve a noisy problem.'"
    )
    helper.memes["kindness"] += 1
    bobby.memes["hope"] += 1
    world.facts["helper_arrived"] = True


def find_sequence(world: World, bobby: Entity, lost: Entity, helper: Entity) -> None:
    world.para()
    world.say(
        f"Bobby stopped, breathed in, and listened. Near the old well he heard a tiny {sound_effect('find')} against the stones."
    )
    world.say(
        f"The {lost.label} had rolled into a crack under a loose plank. Bobby reached in, pulled it free, and the whole square seemed to smile."
    )
    lost.meters["found"] += 1
    lost.meters["lost"] = 0
    bobby.memes["relief"] += 1
    bobby.memes["desperation"] = 0
    helper.memes["relief"] += 1
    world.facts["found"] = True


def lesson_sequence(world: World, bobby: Entity, helper: Entity) -> None:
    world.para()
    world.say(
        f"Bobby wanted to bang the {world.facts['lost_label']} loud as a drum, but he remembered {helper.label}'s words."
    )
    world.say(
        f"Instead, he gave a soft {sound_effect('comfort')} so everyone could hear the good news."
    )
    bobby.memes["lesson"] += 1
    world.say(lesson_line())
    world.facts["lesson_learned"] = True


def tell_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.lost_thing not in LOST_THINGS:
        raise StoryError("Unknown lost thing.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")

    world = World(PLACES[params.place])
    bobby = world.add(Entity(id="Bobby", kind="character", label="Bobby", type="boy"))
    lost_cfg = LOST_THINGS[params.lost_thing]
    lost = world.add(Entity(id=params.lost_thing, label=lost_cfg["label"], type=lost_cfg["type"], plural=lost_cfg["plural"]))
    helper_cfg = HELPERS[params.helper]
    helper = world.add(Entity(id=params.helper, kind="character", label=helper_cfg["label"], type=helper_cfg["type"]))

    world.facts["lost_label"] = lost.label
    world.facts["helper_label"] = helper.label
    world.facts["place_label"] = world.place.label

    setup_story(world, bobby, lost, helper)
    search_sequence(world, bobby, lost)
    trouble_sequence(world, bobby, lost)
    helper_sequence(world, bobby, helper, lost)
    find_sequence(world, bobby, lost, helper)
    lesson_sequence(world, bobby, helper)

    world.facts.update(
        bobby=bobby,
        lost=lost,
        helper=helper,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale about Bobby in {f['place_label']} who grows desperate to find a lost {f['lost_label']}.",
        f"Tell a child-friendly story with sound effects, a helper, and a lesson learned, set in {f['place_label']}.",
        f"Write a gentle story where Bobby learns that quiet listening can solve a noisy problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bobby: Entity = f["bobby"]
    lost: Entity = f["lost"]
    helper: Entity = f["helper"]
    place_label = f["place_label"]
    return [
        QAItem(
            question=f"Why was Bobby desperate in the story?",
            answer=f"Bobby was desperate because the {lost.label} was missing in {place_label}, and he really wanted to help find it.",
        ),
        QAItem(
            question=f"Who helped Bobby when the noisy search did not work?",
            answer=f"{helper.label} helped Bobby. {helper.label} told him to listen carefully instead of making even more noise.",
        ),
        QAItem(
            question=f"What did Bobby learn by the end?",
            answer="He learned that a helpful sound is better than a loud one when somebody needs care.",
        ),
        QAItem(
            question=f"What sound did Bobby hear when he found the missing {lost.label}?",
            answer="He heard a tiny ding as the missing thing touched the stones under the loose plank.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is desperation?",
            answer="Desperation is a strong feeling that comes when someone is very worried and wants help right away.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a word or phrase that copies a sound, like tap-tap, clang-clang, or whoosh.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand a better way to act after something happens.",
        ),
        QAItem(
            question="Why do people listen carefully when something is lost?",
            answer="Because quiet listening can help them notice small clues that loud noise would hide.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(parts)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
% Bobby feels desperate when the thing is lost and the helper has not yet arrived.
desperate(bobby) :- lost(Thing), not found(Thing), not helper_arrived.

% A story is reasonable only if Bobby has a missing thing, a helper, and a lesson.
valid_story(Place, Thing, Helper) :-
    place(Place), lost_thing(Thing), helper(Helper),
    requires_help(Thing), has_lesson.

% Sound effects matter in this world.
has_sound_effects :- sound(tap_tap); sound(clang_clang); sound(whoosh); sound(ding).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for feature in place.features:
            lines.append(asp.fact("feature", pid, feature))
    for lid in LOST_THINGS:
        lines.append(asp.fact("lost_thing", lid))
        lines.append(asp.fact("requires_help", lid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for s in ["tap_tap", "clang_clang", "whoosh", "ding"]:
        lines.append(asp.fact("sound", s))
    lines.append("has_lesson.")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale world about Bobby, sound effects, and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--lost-thing", choices=LOST_THINGS)
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
    place = args.place or rng.choice(list(PLACES))
    lost = args.lost_thing or rng.choice(list(LOST_THINGS))
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, lost_thing=lost, helper=helper, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    program = asp_program("#show valid_story/3.\n#show desperate/1.\n#show has_sound_effects/0.")
    model = asp.one_model(program)
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program loads and solves.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [StoryParams(place=p, lost_thing=t, helper=h, seed=base_seed)
                       for p, t, h in valid_combos()]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            seed = base_seed + i
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
