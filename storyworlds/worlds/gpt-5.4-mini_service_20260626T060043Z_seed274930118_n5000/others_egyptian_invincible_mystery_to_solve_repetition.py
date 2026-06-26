#!/usr/bin/env python3
"""
A standalone storyworld for a small space-adventure mystery with repetition,
others, and an Egyptian-inspired invincible relic.

The core premise is a child-facing crew aboard a ship who keep hearing the same
strange message from an invincible tablet. They must solve the mystery by
following repeated clues across the ship, the dunes, and a quiet chamber.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Person:
    id: str
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "fear": 0.0, "joy": 0.0})

    def pronoun(self) -> str:
        return "they"

    def poss(self) -> str:
        return "their"


@dataclass
class Thing:
    id: str
    name: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = "ship"

    def it(self) -> str:
        return "it"


@dataclass
class Location:
    id: str
    name: str
    tag: str
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    crew: list[Person]
    relic: Thing
    clue_book: Thing
    locations: dict[str, Location]
    trail: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            crew=dataclasses.deepcopy(self.crew),
            relic=dataclasses.deepcopy(self.relic),
            clue_book=dataclasses.deepcopy(self.clue_book),
            locations=dataclasses.deepcopy(self.locations),
            trail=list(self.trail),
            paragraphs=[[]],
            facts=dataclasses.deepcopy(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    other_name: str
    seed: Optional[int] = None


SETTINGS = {
    "ship": Location(id="ship", name="the starship", tag="ship"),
    "dunes": Location(id="dunes", name="the red dunes", tag="desert"),
    "chamber": Location(id="chamber", name="a hidden chamber", tag="ruins"),
}

MYSTERIES = {
    "repetition": {
        "title": "the repeating signal",
        "clue": "the same small tune again and again",
        "message": "It repeats because the tablet is trying to point to the hidden chamber.",
        "turn": "Each repeat is a clue, not a mistake.",
    },
    "lost_map": {
        "title": "the missing map",
        "clue": "a map mark that appears twice",
        "message": "It repeats because the crew copied the wrong trail and the real path is under the dunes.",
        "turn": "The doubled mark is the answer.",
    },
}

EGYPTIAN_WORDS = ["Egyptian", "golden", "hieroglyph", "scarab", "obelisk", "pyramid"]
SEED_WORDS = ["others", "egyptian", "invincible"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
loc(ship).
loc(dunes).
loc(chamber).

mystery(repetition).
mystery(lost_map).

valid_story(S, M) :- loc(S), mystery(M).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("loc", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid_stories() -> list[tuple]:
    return sorted((sid, mid) for sid in SETTINGS for mid in MYSTERIES)


def asp_verify() -> int:
    a = set(asp_valid_stories())
    p = set(python_valid_stories())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - p:
        print("only in ASP:", sorted(a - p))
    if p - a:
        print("only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")

    hero = Person(id=params.name.lower(), name=params.name, role="captain")
    other = Person(id=params.other_name.lower(), name=params.other_name, role="navigator")
    relic = Thing(
        id="relic",
        name="an Egyptian invincible tablet",
        owner=hero.id,
        location=params.setting,
        memes={"invincible": 1.0},
    )
    clue_book = Thing(
        id="clue_book",
        name="a little notebook of repeats",
        owner=hero.id,
        location=params.setting,
    )
    world = World(
        crew=[hero, other],
        relic=relic,
        clue_book=clue_book,
        locations=SETTINGS,
    )
    world.facts.update(params=params, hero=hero, other=other, mystery=MYSTERIES[params.mystery])
    return world


def _distance(world: World, loc_id: str) -> None:
    for p in world.crew:
        p.meters["distance"] += 1
    world.trail.append(loc_id)


def _repeat_signal(world: World, mystery_id: str) -> None:
    key = f"signal:{mystery_id}"
    if key in world.fired:
        return
    world.fired.add(key)
    world.say("Again and again, the little signal hummed through the ship.")
    world.say("Again and again, the same clue returned, as if it did not want to be missed.")


def generate_story(world: World) -> None:
    params: StoryParams = world.facts["params"]
    mystery = world.facts["mystery"]
    hero, other = world.crew
    setting = world.locations[params.setting]

    world.say(f"On the starship, {hero.name} and {other.name} noticed an Egyptian invincible tablet.")
    world.say(f"It was not just shiny; it seemed invincible, as if nothing could scratch its surface.")
    world.say(f"Then the tablet sent {mystery['clue']}.")

    world.para()
    if params.setting == "ship":
        world.say(f"The clue led them from {setting.name} to the red dunes outside the ship.")
    elif params.setting == "dunes":
        world.say(f"The clue led them across {setting.name} toward a hidden chamber under the sand.")
    else:
        world.say(f"The clue guided them through {setting.name}, where the walls waited in silence.")

    _distance(world, params.setting)
    _repeat_signal(world, params.mystery)
    world.say(f"{other.name} counted the repeats aloud, because sometimes others hear the pattern first.")
    world.say(f"{hero.name} wrote the same line in the notebook, hoping the repeated words would make sense.")

    world.para()
    world.say("Inside the hidden place, they finally found why the tablet kept repeating itself.")
    world.say(mystery["message"])
    world.say(f"{mystery['turn']}")

    world.para()
    world.say(f"{hero.name} touched the invincible tablet, and it glowed softly instead of breaking.")
    world.say(f"At last, the crew carried the tablet home, with the mystery solved and the repeats understood.")
    world.say("The ship flew on, and the little notebook stayed full of clues instead of worry.")


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    m = world.facts["mystery"]
    hero, other = world.facts["hero"], world.facts["other"]
    return [
        QAItem(
            question=f"What mystery did {hero.name} and {other.name} solve?",
            answer=f"They solved {m['title']}.",
        ),
        QAItem(
            question="Why did the clue keep coming back?",
            answer=m["message"],
        ),
        QAItem(
            question=f"What did the repeated clue make the crew do?",
            answer=f"It made them travel from the {p.setting} and follow the same clue until they found the answer.",
        ),
        QAItem(
            question="What made the tablet special?",
            answer="It was an Egyptian invincible tablet, so it seemed strong and impossible to damage.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means saying or showing the same thing more than once.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out.",
        ),
        QAItem(
            question="What is a tablet in a story like this?",
            answer="A tablet can be a flat object with writing or symbols on it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a space adventure mystery with repetition and the word '{p.name}'.",
        f"Tell a child-friendly story about others solving a clue on the {p.setting}.",
        "Write a short story where an Egyptian invincible relic keeps repeating the same hint.",
    ]


def build_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery with repetition.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--other-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    name = args.name or rng.choice(["Nova", "Iris", "Milo", "Aria", "Juno"])
    other_name = args.other_name or rng.choice([n for n in ["Tari", "Zed", "Lena", "Orin", "Bea"] if n != name])
    return StoryParams(setting=setting, mystery=mystery, name=name, other_name=other_name)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        print(f"trail: {sample.world.trail}")
        print(f"relic: {sample.world.relic.name}")
        print(f"crew: {[p.name for p in sample.world.crew]}")
    if qa:
        print()
        print("== prompts ==")
        for i, q in enumerate(sample.prompts, 1):
            print(f"{i}. {q}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in sorted(SETTINGS):
            for m in sorted(MYSTERIES):
                params = StoryParams(setting=s, mystery=m, name="Nova", other_name="Tari")
                samples.append(build_story(params))
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            samples.append(build_story(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### sample {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
