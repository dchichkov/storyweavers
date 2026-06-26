#!/usr/bin/env python3
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

THEMES = ("transmission", "mushroom")
SFX = {
    "radio": "bzzzt",
    "walkie": "krrt",
    "door": "tap-tap",
    "leaves": "swish",
    "footsteps": "pat-pat",
    "basket": "clink",
    "flask": "glug",
}
PLACES = {
    "lantern street": {"setting": "the lantern street", "inside": False, "has_radio": True, "has_mushroom": True},
    "brick market": {"setting": "the brick market", "inside": False, "has_radio": True, "has_mushroom": True},
    "quiet station": {"setting": "the quiet station", "inside": True, "has_radio": True, "has_mushroom": False},
    "old garden": {"setting": "the old garden", "inside": False, "has_radio": False, "has_mushroom": True},
}
CHAR_NAMES = ["Nina", "Milo", "Iris", "Pip", "Jasper", "Luna", "Toby", "Mara"]
JOB_TITLES = ["detective", "inspector", "helper", "spotter"]
MOODS = ["careful", "curious", "brave", "patient"]
OBJECTS = {
    "transmission": "a crackly transmission",
    "mushroom": "a spotted mushroom",
    "radio": "a little radio",
}

ASP_RULES = r"""
kind(transmission).
kind(mushroom).
kind(sound_effects).
kind(misunderstanding).
kind(lesson_learned).

feature(transmission) :- kind(transmission).
feature(mushroom) :- kind(mushroom).
feature(sound_effects) :- kind(sound_effects).
feature(misunderstanding) :- kind(misunderstanding).
feature(lesson_learned) :- kind(lesson_learned).

compatible(place, transmission) :- setting(place), radio_ok(place).
compatible(place, mushroom) :- setting(place), mushroom_ok(place).
compatible_story(place) :- compatible(place, transmission), compatible(place, mushroom).

setting("lantern_street").
setting("brick_market").
setting("quiet_station").
setting("old_garden").

radio_ok("lantern_street").
radio_ok("brick_market").
radio_ok("quiet_station").
mushroom_ok("lantern_street").
mushroom_ok("brick_market").
mushroom_ok("old_garden").

#show compatible/2.
#show compatible_story/1.
"""

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    location: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about a transmission and a mushroom.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_facts() -> str:
    import asp
    lines = []
    for p, meta in PLACES.items():
        lines.append(asp.fact("setting", p.replace(" ", "_")))
        if meta["has_radio"]:
            lines.append(asp.fact("radio_ok", p.replace(" ", "_")))
        if meta["has_mushroom"]:
            lines.append(asp.fact("mushroom_ok", p.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibilities() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = {(p, "transmission") for p, m in PLACES.items() if m["has_radio"]}
    python_set |= {(p, "mushroom") for p, m in PLACES.items() if m["has_mushroom"]}
    clingo_set = set(asp_compatibilities())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo_set)} facts).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice([p for p in PLACES if PLACES[p]["has_radio"] and PLACES[p]["has_mushroom"]])
    if not (PLACES[place]["has_radio"] and PLACES[place]["has_mushroom"]):
        raise StoryError("This story needs both a radio transmission and a mushroom clue in the same place.")
    hero = rng.choice(CHAR_NAMES)
    sidekick = rng.choice([n for n in CHAR_NAMES if n != hero])
    mood = rng.choice(MOODS)
    return StoryParams(place=place, hero=hero, sidekick=sidekick, mood=mood)


def _sfx(key: str) -> str:
    return SFX[key]


def generate(params: StoryParams) -> StorySample:
    meta = PLACES[params.place]
    world = World(place=meta["setting"])
    detective = Entity(id=params.hero, kind="character", label="detective", type="detective", meters={"alert": 1.0}, memes={"curious": 1.0})
    helper = Entity(id=params.sidekick, kind="character", label="helper", type="helper", meters={"alert": 0.5}, memes={"curious": 0.5})
    radio = Entity(id="radio", label=OBJECTS["radio"], type="radio", location=params.place, carried_by=detective.id)
    mushroom = Entity(id="mushroom", label=OBJECTS["mushroom"], type="mushroom", location=params.place)
    world.entities = {e.id: e for e in [detective, helper, radio, mushroom]}

    world.say(f"{detective.id} was a {params.mood} little detective who liked to solve small mysteries in {world.place}.")
    world.say(f"{helper.id} stayed close by, listening for clues and for little sound effects like “{_sfx('footsteps')}” and “{_sfx('radio')}.”")
    world.say(f"One evening, a crackly transmission came from the radio: “{_sfx('radio')} ... follow the mushroom ...”")

    world.para()
    world.say(f"{detective.id} and {helper.id} hurried through {world.place}, where the path went “{_sfx('footsteps')} { _sfx('footsteps') }” under their shoes.")
    world.say(f"Near a flower box, they found a spotted mushroom beside the bricks.")
    world.say(f"{helper.id} frowned and said, “Maybe the mushroom is making the transmission!”")

    world.para()
    world.say(f"{detective.id} shook {detective.pronoun('possessive')} head. “No, listen carefully,” {detective.id} said.")
    world.say(f"They turned the radio again, and it answered with “{_sfx('radio')} ... station garden ... behind the fountain.”")
    world.say(f"Then the misunderstanding cleared up: the mushroom was not sending the message; it was hiding the place name in the garden clue.")

    world.para()
    world.say(f"{detective.id} lifted the flower pot, and there behind it was the missing note from the station map.")
    world.say(f"The lesson learned was simple: a clue can look strange at first, but listening twice can solve the mystery.")
    world.say(f"By the end, the radio was quiet, the mushroom stayed in the soil, and {helper.id} smiled because the case made sense at last.")

    world.facts = {
        "hero": detective,
        "helper": helper,
        "radio": radio,
        "mushroom": mushroom,
        "place": params.place,
        "setting": meta["setting"],
    }

    prompts = [
        f"Write a child-friendly detective story set in {meta['setting']} that includes a transmission and a mushroom clue.",
        f"Tell a short mystery where {params.hero} and {params.sidekick} misread a mushroom, then learn what the radio transmission meant.",
        "Write a gentle detective story with sound effects, a misunderstanding, and a lesson learned at the end.",
    ]

    story_qa = [
        QAItem(
            question=f"Who solved the mystery in {meta['setting']}?",
            answer=f"The little detective {params.hero} solved it with help from {params.sidekick}.",
        ),
        QAItem(
            question="What did the radio transmission say to follow?",
            answer="It said to follow the mushroom, which turned out to be a clue, not the sender.",
        ),
        QAItem(
            question="What was the misunderstanding?",
            answer=f"{params.sidekick} thought the mushroom was making the transmission, but it was only hiding a clue.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The story learned that clues can look strange at first, so it helps to listen carefully before guessing.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a transmission?",
            answer="A transmission is a message sent through a radio or another signal so someone can hear it somewhere else.",
        ),
        QAItem(
            question="What is a mushroom?",
            answer="A mushroom is a kind of fungus that can grow in soil, near trees, or beside damp places.",
        ),
        QAItem(
            question="Why do detectives listen carefully?",
            answer="Detectives listen carefully because small sounds can carry important clues.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            bits = []
            if e.label:
                bits.append(f"label={e.label}")
            if e.location:
                bits.append(f"location={e.location}")
            if e.carried_by:
                bits.append(f"carried_by={e.carried_by}")
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            print(f"  {e.id}: {e.kind} {(' '.join(bits))}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="lantern street", hero="Nina", sidekick="Milo", mood="curious"),
    StoryParams(place="brick market", hero="Iris", sidekick="Toby", mood="careful"),
    StoryParams(place="quiet station", hero="Mara", sidekick="Pip", mood="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp.one_model(asp_program("#show compatible/2.\n#show compatible_story/1."))
        print(asp.atoms(models, "compatible"))
        print(asp.atoms(models, "compatible_story"))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
