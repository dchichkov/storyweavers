#!/usr/bin/env python3
"""
storyworlds/worlds/response_octagon_bad_ending_mystery_to_solve.py
===================================================================

A tiny story world in a tall-tale register: a child, a mysterious octagon,
and a problem that can end badly unless the missing response is found.

Premise:
- A small team waits for a "response" to arrive at an octagon-shaped place.
- The response matters because it unlocks a door, a ride, or a rescue.
- Something goes wrong: the response goes missing, and the ending would be bad
  if nobody solves the mystery in time.

World model:
- Characters have physical meters and emotional memes.
- Objects can be carried, hidden, opened, or revealed.
- The story is driven by state changes: searching, clues, discovery, relief.
- The tall-tale flavor comes from oversized details, lively comparisons, and a
  clear, concrete ending image.

The domain is intentionally small and constraint-checked so generated stories
stay plausible and complete.
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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    openable: bool = False
    open_state: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["tired", "safe", "blocked", "found", "opened"]:
            self.meters.setdefault(key, 0.0)
        for key in ["hope", "worry", "curiosity", "relief", "fear", "confusion", "courage"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    shape: str = "octagon"
    mood: str = "windy"
    affordances: set[str] = field(default_factory=set)
    clues: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.events: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.events = list(self.events)
        return clone


PLACES = {
    "fair": Place(
        name="the county fair",
        affordances={"search", "ask", "listen"},
        mood="loud",
        clues=["ticket booth", "cotton-candy cart", "octagon gate", "chalk path"],
    ),
    "station": Place(
        name="the old train station",
        affordances={"search", "ask", "listen"},
        mood="echoing",
        clues=["platform bench", "signal lamp", "octagon clock", "mail shelf"],
    ),
    "harbor": Place(
        name="the harbor square",
        affordances={"search", "ask", "listen"},
        mood="salt-bright",
        clues=["rope pile", "fish crate", "octagon kiosk", "blue sign"],
    ),
}

MYSTERIES = {
    "bell": {
        "thing": "a silver response bell",
        "missing": "the silver response bell had vanished",
        "bad_ending": "the gates would stay shut and the parade would pass them by",
        "key_clue": "a bell rope",
        "reveal": "inside the old octagon booth, hanging from a nail",
        "solve_line": "The bell rang at last, clear as a church star.",
    },
    "letter": {
        "thing": "a folded response letter",
        "missing": "the folded response letter was gone",
        "bad_ending": "the mayor would think nobody had answered, and the lamps would go dark",
        "key_clue": "a blue wax seal",
        "reveal": "under a stack of maps in the octagon desk",
        "solve_line": "The letter was opened, and the answer came out shining.",
    },
    "whistle": {
        "thing": "a brass response whistle",
        "missing": "the brass response whistle was missing",
        "bad_ending": "the rescue boat would drift away without a signal",
        "key_clue": "a brass shine",
        "reveal": "in the pocket of a raincoat on the octagon bench",
        "solve_line": "The whistle blew once, then twice, like a brave little trumpet.",
    },
}

HERO_NAMES = ["Mina", "Jasper", "Ruby", "Nell", "Toby", "Ivy", "Eli", "June"]
HELPER_NAMES = ["Uncle Bo", "Grandma Wren", "Aunt Polly", "Old Ezra", "Mister Pike"]
TRAITS = ["bold", "curious", "spirited", "patient", "bright-eyed", "stubborn"]


def reasonableness_gate(place: str, mystery: str) -> None:
    if place not in PLACES:
        raise StoryError("Unknown place.")
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if "octagon" not in PLACES[place].name and place != "fair":
        raise StoryError("This story world needs an octagon-shaped setting to feel right.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    reasonableness_gate(place, mystery)

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        mystery=mystery,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    w = World(place)

    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_type))

    response = w.add(Entity(
        id="response",
        type=params.mystery,
        label="response",
        phrase=mystery["thing"],
        owner=helper.id,
        hidden_in="octagon",
        openable=False,
    ))
    octagon = w.add(Entity(
        id="octagon",
        type="place",
        label="octagon",
        phrase=f"an octagon-shaped booth at {place.name}",
        openable=True,
        open_state=False,
    ))
    clue = w.add(Entity(
        id="clue",
        type="clue",
        label="clue",
        phrase=mystery["key_clue"],
        hidden_in="octagon",
    ))

    hero.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    w.facts.update(hero=hero, helper=helper, response=response, octagon=octagon, clue=clue, mystery=mystery)
    return w


def predict_bad_ending(world: World) -> bool:
    return True


def narrate_setup(w: World) -> None:
    f = w.facts
    hero, helper = f["hero"], f["helper"]
    mystery = f["mystery"]
    place = w.place.name

    w.say(
        f"At {place}, there stood an octagon so grand it looked as if eight windmills had agreed to hold hands."
    )
    w.say(
        f"{hero.id} was a {random.choice(TRAITS)} {hero.type} who could spot a loose nail from a mile away, "
        f"and {helper.id} had been waiting for {mystery['thing']} all morning."
    )
    w.say(
        f"But when the time came, {mystery['missing']}. That was a bad sign, because {mystery['bad_ending']}."
    )


def narrate_search(w: World) -> None:
    f = w.facts
    hero, helper, clue = f["hero"], f["helper"], f["clue"]
    mystery = f["mystery"]
    place = w.place

    w.para()
    w.say(
        f"{hero.id} did not sit still. {hero.pronoun().capitalize()} peered behind the ticket booth, "
        f"under the chalk path, and around the octagon corners."
    )
    w.say(
        f"Then {hero.id} found a clue: {clue.phrase}. "
        f"It shone like a penny in moonlight and gave {hero.pronoun('object')} a spark of courage."
    )
    hero.memes["courage"] += 1
    hero.memes["hope"] += 1
    helper.memes["worry"] += 1
    w.say(
        f"{helper.id} said, \"If we follow that clue, the mystery may still be solved before the bad ending comes knocking.\""
    )


def narrate_turn(w: World) -> None:
    f = w.facts
    hero, helper, response = f["hero"], f["helper"], f["response"]
    mystery = f["mystery"]

    w.para()
    hero.meters["found"] += 1
    w.say(
        f"So {hero.id} followed the clue right to {mystery['reveal']}."
    )
    w.say(
        f"There was {response.phrase}, neat as a button and safe as a tucked-in blanket."
    )
    response.hidden_in = None
    response.carried_by = hero.id
    w.say(
        f"{hero.id} lifted {response.it()} with both hands, and {helper.id} gave out a great breath of relief."
    )
    helper.memes["relief"] += 1
    helper.memes["worry"] = 0.0
    hero.memes["hope"] += 1


def narrate_resolution(w: World) -> None:
    f = w.facts
    hero, helper, response = f["hero"], f["helper"], f["response"]
    mystery = f["mystery"]

    w.para()
    w.say(mystery["solve_line"])
    w.say(
        f"The octagon was no longer a puzzle box with a missing tooth; it was simply the right shape for a happy answer."
    )
    w.say(
        f"{hero.id} carried the response back, and {helper.id} smiled so wide it looked like sunrise had chosen a face."
    )
    hero.memes["relief"] += 1
    hero.memes["curiosity"] += 1
    response.hidden_in = None
    response.carried_by = hero.id
    w.say(
        f"In the last image, the octagon stood bright and still, with the response back where it belonged and the bad ending left outside."
    )


def generate_story(w: World) -> None:
    narrate_setup(w)
    narrate_search(w)
    narrate_turn(w)
    narrate_resolution(w)


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    hero, helper = f["hero"], f["helper"]
    mystery = f["mystery"]
    return [
        f"Write a tall tale about {hero.id} and {helper.id} solving a missing {mystery['thing']} at an octagon-shaped place.",
        f"Tell a child-friendly mystery where a response goes missing and a brave kid follows a clue.",
        f"Write a story that begins with a bad ending looming, then turns happy when the response is found.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    hero, helper, response = f["hero"], f["helper"], f["response"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What was missing at the octagon at the start of the story?",
            answer=f"{mystery['thing'].capitalize()} was missing, which made the day feel shaky and strange.",
        ),
        QAItem(
            question=f"Who looked for the clue first?",
            answer=f"{hero.id} looked first because {hero.pronoun().capitalize()} was curious and brave.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was {mystery['key_clue']}, and it led them straight to the hiding place.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The response was found, the bad ending was avoided, and {helper.id} felt relieved.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an octagon?",
            answer="An octagon is a shape with eight sides.",
        ),
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a hint that helps someone figure out what happened or where something is hidden.",
        ),
        QAItem(
            question="Why is a bad ending something to avoid?",
            answer="A bad ending can mean someone stays stuck, sad, or unsafe, so characters work hard to find a better way.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.openable:
            bits.append(f"open_state={e.open_state}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(p).
mystery(m).

octagon_place(p) :- place(p).

clue_helpful(c) :- mystery(m), clue_of(m, c).

bad_ending_possible(p, m) :- octagon_place(p), mystery(m).
solved(p, m) :- clue_helpful(c), reveal(c, m).
avoid_bad_ending(p, m) :- solved(p, m), bad_ending_possible(p, m).

#show bad_ending_possible/2.
#show avoid_bad_ending/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("clue_of", m, MYSTERIES[m]["key_clue"].replace(" ", "_")))
        lines.append(asp.fact("reveal", MYSTERIES[m]["key_clue"].replace(" ", "_"), m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale mystery at an octagon-shaped place.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["woman", "man"])
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


def resolve_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    w = build_world(params)
    generate_story(w)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    program = asp_program("#show bad_ending_possible/2.\n#show avoid_bad_ending/2.")
    model = asp.one_model(program)
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program loaded and produced a model.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending_possible/2.\n#show avoid_bad_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show bad_ending_possible/2.\n#show avoid_bad_ending/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(PLACES):
            for mystery in sorted(MYSTERIES):
                params = StoryParams(
                    place=place,
                    mystery=mystery,
                    hero=random.choice(HERO_NAMES),
                    hero_type="girl",
                    helper=random.choice(HELPER_NAMES),
                    helper_type="woman",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params_from_args(args, random.Random(seed))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
