#!/usr/bin/env python3
"""
Standalone story world: a tiny chickadee tale with tall-tale flavor.

The domain is deliberately small:
- a chickadee has a nest and a prized shiny berry
- winter wind, a hollow log, and a tall pine can complicate the day
- the story can resolve as a happy ending, suspenseful pause, or bad ending

This script follows the Storyweavers storyworld contract.
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
# Domain registries
# ---------------------------------------------------------------------------

OUTCOMES = ("happy", "suspense", "bad")
WEATHERS = ("calm", "windy", "snowy")
PLACES = ("pine", "hollow_log", "berry_bush", "fence_post")
TREASURES = ("berry", "seed", "shiny_bell")
HELPERS = ("mouse", "squirrel", "rabbit")


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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chickadee"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"mouse", "squirrel", "rabbit"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the winter woods"
    weather: str = "windy"


@dataclass
class StoryParams:
    weather: str
    place: str
    treasure: str
    outcome: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def story_text(world: World) -> str:
    return world.render()


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def describe_weather(weather: str) -> str:
    return {
        "calm": "The morning was so calm that even the pine needles seemed to hold their breath.",
        "windy": "The wind blew so hard it made the branches sing like fiddle strings.",
        "snowy": "Snow drifted down in soft little feathers, pale as a dream.",
    }[weather]


def tall_tale_flavor(place: str) -> str:
    return {
        "pine": "The pine stood tall as a church steeple and wide as a barn door in a thunderstorm.",
        "hollow_log": "The hollow log was big enough to hide a lunch, a lantern, and three surprised mice.",
        "berry_bush": "The berry bush bristled with red fruit like a crown of tiny rubies.",
        "fence_post": "The fence post leaned just enough to look like it had a secret to tell.",
    }[place]


def intro(world: World, chick: Entity, treasure: Entity) -> None:
    world.say(
        f"Chickadee was a bright little bird with a brave heart and a quick wing."
    )
    world.say(
        f"{chick.pronoun('possessive').capitalize()} favorite treasure was {treasure.phrase}, and {chick.pronoun()} kept it tucked safe near the nest."
    )


def setup(world: World) -> None:
    world.say(describe_weather(world.setting.weather))
    world.say(tall_tale_flavor(world.setting.place))


def suspense_turn(world: World, chick: Entity, treasure: Entity, helper: Entity) -> None:
    chick.memes["worry"] = chick.memes.get("worry", 0) + 1
    world.say(
        f"Then a gust whooshed by and sent {treasure.phrase} rolling right toward the edge of the {world.setting.place.replace('_', ' ')}."
    )
    world.say(
        f"Chickadee fluttered after it, but the gust was so bold it nearly lifted {chick.pronoun('object')} off {chick.pronoun('possessive')} tiny toes."
    )
    world.say(
        f"Just then, {helper.id} peeped from behind a twig and pointed with a paw, as if {helper.pronoun('subject')} knew where the treasure had gone."
    )


def happy_ending(world: World, chick: Entity, treasure: Entity, helper: Entity) -> None:
    chick.memes["joy"] = chick.memes.get("joy", 0) + 2
    treasure.meters["safe"] = treasure.meters.get("safe", 0) + 1
    world.say(
        f"Together they found {treasure.phrase} resting in a soft bed of moss, not even scratched by the wind."
    )
    world.say(
        f"Chickadee chirped so bright that the whole woods seemed to shine, and {helper.id} laughed like a bell in a bakery window."
    )
    world.say(
        f"By sunset, {chick.pronoun()} was back at the nest, snug and warm, with {treasure.phrase} tucked safely beside {chick.pronoun('possessive')} feathers."
    )


def bad_ending(world: World, chick: Entity, treasure: Entity, helper: Entity) -> None:
    chick.memes["sadness"] = chick.memes.get("sadness", 0) + 2
    treasure.meters["lost"] = treasure.meters.get("lost", 0) + 1
    world.say(
        f"The wind snatched {treasure.phrase} up and whisked it over the hill before anyone could catch it."
    )
    world.say(
        f"Chickadee searched behind every fern and stump, but the treasure was gone, and even {helper.id} could only shake {helper.pronoun('possessive')} head."
    )
    world.say(
        f"At last {chick.pronoun()} perched in the nest with an empty space where the treasure had been, listening to the wind sing its faraway song."
    )


def suspense_ending(world: World, chick: Entity, treasure: Entity, helper: Entity) -> None:
    chick.memes["worry"] = chick.memes.get("worry", 0) + 2
    world.say(
        f"They found a trail of tiny prints leading into the hollow, but the last print stopped right at the shadowy edge."
    )
    world.say(
        f"Chickadee leaned in, {helper.id} leaned in, and the dark hollow seemed to hold its breath right back."
    )
    world.say(
        f"The two friends waited there together, peering into the dimness, and nobody in the woods knew yet whether the treasure was safe or lost."
    )


# ---------------------------------------------------------------------------
# World construction and generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(Setting(place=params.place, weather=params.weather))
    chick = world.add(Entity(
        id="Chickadee",
        kind="character",
        type="chickadee",
        label="Chickadee",
        phrase="a bright chickadee",
    ))
    treasure = world.add(Entity(
        id="Treasure",
        type=params.treasure,
        label=params.treasure,
        phrase={
            "berry": "a ruby-red berry",
            "seed": "a golden seed",
            "shiny_bell": "a shiny little bell",
        }[params.treasure],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="mouse",
        label="mouse helper",
        phrase="a careful mouse friend",
    ))

    world.facts.update(
        chick=chick,
        treasure=treasure,
        helper=helper,
        params=params,
        setting=world.setting,
    )

    intro(world, chick, treasure)
    world.say("")
    setup(world)
    world.say(
        f"Chickadee wanted to carry {treasure.phrase} to the safest branch in the whole woods."
    )
    suspense_turn(world, chick, treasure, helper)
    world.say("")

    if params.outcome == "happy":
        happy_ending(world, chick, treasure, helper)
    elif params.outcome == "suspense":
        suspense_ending(world, chick, treasure, helper)
    elif params.outcome == "bad":
        bad_ending(world, chick, treasure, helper)
    else:
        raise StoryError("unknown outcome")
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------

def reasonable_combo(weather: str, place: str, treasure: str, outcome: str) -> bool:
    if weather not in WEATHERS or place not in PLACES or treasure not in TREASURES or outcome not in OUTCOMES:
        return False
    if outcome == "bad" and weather == "calm":
        return False
    if outcome == "happy" and weather == "calm" and place == "fence_post":
        return True
    return True


ASP_RULES = r"""
weather(calm; windy; snowy).
place(pine; hollow_log; berry_bush; fence_post).
treasure(berry; seed; shiny_bell).
outcome(happy; suspense; bad).

reasonable(W,P,T,O) :- weather(W), place(P), treasure(T), outcome(O), not blocked(W,P,T,O).

blocked(calm,fence_post,_,bad).
blocked(calm,_,_,bad).

#show reasonable/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for w in WEATHERS:
        lines.append(asp.fact("weather", w))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TREASURES:
        lines.append(asp.fact("treasure", t))
    for o in OUTCOMES:
        lines.append(asp.fact("outcome", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple[str, str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/4."))
    return sorted(set(asp.atoms(model, "reasonable")))


def verify_asp() -> int:
    py = {(w, p, t, o) for w in WEATHERS for p in PLACES for t in TREASURES for o in OUTCOMES if reasonable_combo(w, p, t, o)}
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Prompts and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    return [
        f'Write a short tall-tale-style story about a chickadee and a {params.treasure}.',
        f"Tell a suspenseful bird story where Chickadee crosses {params.place.replace('_', ' ')} in {params.weather} weather.",
        f"Write a child-friendly story that can end in a happy ending, suspense, or a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    chick: Entity = f["chick"]  # type: ignore[assignment]
    treasure: Entity = f["treasure"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    ending = params.outcome.replace("_", " ")
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Chickadee, a bright little chickadee with a brave heart.",
        ),
        QAItem(
            question=f"What did Chickadee want to do with {treasure.phrase}?",
            answer=f"Chickadee wanted to carry {treasure.phrase} to the safest branch in the woods.",
        ),
        QAItem(
            question=f"Who helped Chickadee?",
            answer=f"A careful mouse friend named {helper.id} helped watch the trail and point the way.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer={
                "happy": "It ended happily, with the treasure safe and Chickadee snug back at the nest.",
                "suspense": "It ended in suspense, with everyone peering into the dark hollow and waiting to see.",
                "bad": "It ended badly, because the wind carried the treasure away and Chickadee could not get it back.",
            }[params.outcome],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chickadee?",
            answer="A chickadee is a small songbird with a lively voice and quick movements.",
        ),
        QAItem(
            question="What is winter wind like in a tall tale?",
            answer="Winter wind in a tall tale can feel huge and powerful, as if it has a mind of its own.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when the trouble does not get fixed and the hero does not get what was hoped for.",
        ),
        QAItem(
            question="What is a happy ending in a story?",
            answer="A happy ending is when the trouble gets solved and the characters finish in a safe, glad place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(weather="windy", place="pine", treasure="berry", outcome="happy"),
    StoryParams(weather="snowy", place="hollow_log", treasure="seed", outcome="suspense"),
    StoryParams(weather="windy", place="fence_post", treasure="shiny_bell", outcome="bad"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale chickadee story world.")
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--outcome", choices=OUTCOMES)
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
    if args.weather and args.place and args.treasure and args.outcome:
        if not reasonable_combo(args.weather, args.place, args.treasure, args.outcome):
            raise StoryError("The chosen combination is not a reasonable story.")
    choices = [
        (w, p, t, o)
        for w in WEATHERS
        for p in PLACES
        for t in TREASURES
        for o in OUTCOMES
        if reasonable_combo(w, p, t, o)
        and (args.weather is None or args.weather == w)
        and (args.place is None or args.place == p)
        and (args.treasure is None or args.treasure == t)
        and (args.outcome is None or args.outcome == o)
    ]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    weather, place, treasure, outcome = rng.choice(sorted(choices))
    return StoryParams(weather=weather, place=place, treasure=treasure, outcome=outcome)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/4."))
        return
    if args.verify:
        sys.exit(verify_asp())
    if args.asp:
        combos = asp_reasonable()
        print(f"{len(combos)} reasonable combos:")
        for row in combos:
            print(" ", row)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.weather} / {p.place} / {p.treasure} / {p.outcome}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
