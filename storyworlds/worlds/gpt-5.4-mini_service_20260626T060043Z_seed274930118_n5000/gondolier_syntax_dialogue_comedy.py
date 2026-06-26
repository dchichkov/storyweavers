#!/usr/bin/env python3
"""
A tiny comedy storyworld about a gondolier who cares too much about syntax.

Seed tale premise:
A gondolier in a little canal town keeps correcting everybody's sentences, even
while steering. A passenger tries to speak plainly, but the gondolier insists on
proper syntax. Their silly argument turns into a lesson when the passenger
rephrases the request clearly, and the gondolier happily rows them where they
need to go.

The world is built around:
- a gondolier character
- a passenger with a request
- a syntax problem that causes comic confusion
- dialogue as the main instrument
- a gentle, smiling resolution
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the canal"
    mood: str = "bright"


@dataclass
class Request:
    id: str
    verb: str
    noun: str
    confusion: str
    clear_verb: str
    clear_sentence: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    type: str
    phrase: str
    goal: str
    humor: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "owner": v.owner,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        return clone


def _say(world: World, text: str) -> None:
    world.say(text)


def _laugh(world: World, person: Entity) -> None:
    person.memes["amused"] = person.memes.get("amused", 0.0) + 1.0


def _confuse(world: World, person: Entity) -> None:
    person.memes["confusion"] = person.memes.get("confusion", 0.0) + 1.0


def _clarify(world: World, person: Entity) -> None:
    person.memes["clarity"] = person.memes.get("clarity", 0.0) + 1.0


def tell(world: World, gondolier: Entity, passenger: Entity, request: Request, prop: Prop) -> World:
    intro = gondolier.traits[0] if gondolier.traits else "cheerful"
    _say(world, f"{gondolier.id} was a {intro} gondolier who loved neat syntax almost as much as rowing.")
    _say(world, f"{passenger.id} had {prop.phrase}, and {prop.goal} was all {passenger.id} wanted.")
    _say(world, f"That made for a funny pair in {world.setting.place}: one person wanted a ride, and the other wanted every sentence to sit up straight.")

    world.para()
    _say(world, f'"{request.verb}," said {passenger.id}.')
    _say(world, f'"No, no," said {gondolier.id}, tapping the oar like a teacher. "That syntax is wobbly."')
    _confuse(world, passenger)
    _laugh(world, gondolier)
    _say(world, f'"Wobbly?" said {passenger.id}. "It is a perfectly good boat request in my heart."')
    _say(world, f'"A heart can be good," said {gondolier.id}, "but the grammar is doing a little dance on the table."')

    world.para()
    _say(world, f"{passenger.id} tried again, slower this time.")
    _say(world, f'"{request.confusion}"')
    _say(world, f'{gondolier.id} blinked, then grinned. "Ah! That sentence has lost its hat, its shoes, and one important verb."')
    _clarify(world, passenger)
    _laugh(world, passenger)
    _say(world, f'"Fine," said {passenger.id}. "{request.clear_sentence}."')
    _say(world, f'"Now that," said {gondolier.id}, "is excellent syntax."')

    world.para()
    _say(world, f"So the gondolier pushed off with a flourish, and the boat slid along the water like a polite joke.")
    _say(world, f"{passenger.id} got {prop.goal}, and {gondolier.id} got to keep the sentence tidy.")
    _say(world, f'By the end, the canal was calm, the oar was steady, and everyone agreed that a little syntax could make a ride much funnier.')

    world.facts.update(gondolier=gondolier, passenger=passenger, request=request, prop=prop, setting=world.setting)
    return world


SETTINGS = {
    "canal": Setting(place="the canal", mood="bright"),
    "harbor": Setting(place="the harbor", mood="breezy"),
    "lagoon": Setting(place="the lagoon", mood="glowy"),
}

REQUESTS = {
    "dock": Request(
        id="dock",
        verb="Please take me to the dock",
        noun="dock",
        confusion="please take me to, uh, dock me to the take",
        clear_verb="take",
        clear_sentence="Please take me to the dock",
        tags={"boat", "syntax"},
    ),
    "market": Request(
        id="market",
        verb="Could you row me to the market",
        noun="market",
        confusion="could you market me to the row",
        clear_verb="row",
        clear_sentence="Could you row me to the market",
        tags={"boat", "syntax"},
    ),
    "bridge": Request(
        id="bridge",
        verb="Would you bring me under the bridge",
        noun="bridge",
        confusion="would you under me the bring bridge",
        clear_verb="bring",
        clear_sentence="Would you bring me under the bridge",
        tags={"boat", "syntax"},
    ),
}

PROPS = {
    "parcel": Prop(
        id="parcel",
        label="a parcel",
        type="parcel",
        phrase="a parcel tied up with blue string",
        goal="a parcel delivered safely",
        humor="the box looked more important than the words",
        tags={"delivery"},
    ),
    "hat": Prop(
        id="hat",
        label="a hat",
        type="hat",
        phrase="a tiny hat with a feather",
        goal="a hat carried without getting soggy",
        humor="it bobbed like a tiny captain",
        tags={"clothing"},
    ),
    "fish": Prop(
        id="fish",
        label="a fish",
        type="fish",
        phrase="a fish in a little bucket",
        goal="a fish brought home for supper",
        humor="it was having a very quiet day",
        tags={"food"},
    ),
}

GONDOLIERS = ["Marco", "Luca", "Nico", "Piero", "Gianni"]
PASSENGERS = ["Mina", "Toby", "Lia", "Sami", "Nora"]
TRAITS = ["cheerful", "serious", "playful", "fussy", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for r in REQUESTS:
            for p in PROPS:
                out.append((s, r, p))
    return out


@dataclass
class StoryParams:
    setting: str
    request: str
    prop: str
    gondolier_name: str
    passenger_name: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    g = f["gondolier"]
    p = f["passenger"]
    req = f["request"]
    prop = f["prop"]
    return [
        f'Write a short comedy for a child about a gondolier named {g.id} who keeps correcting syntax.',
        f'Tell a dialogue-driven story where {p.id} asks for {prop.goal} but says it in a funny, broken way.',
        f'Write a gentle canal story that includes the word "syntax" and ends with a correct sentence and a happy boat ride.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    g, p, req, prop = f["gondolier"], f["passenger"], f["request"], f["prop"]
    return [
        QAItem(
            question=f"Who kept correcting the syntax in the story?",
            answer=f"The gondolier named {g.id} kept correcting the syntax, but he did it in a joking, friendly way.",
        ),
        QAItem(
            question=f"What did {p.id} want to get by the end of the boat ride?",
            answer=f"{p.id} wanted {prop.goal}, and the gondolier finally rowed them there after the sentence was fixed.",
        ),
        QAItem(
            question=f"What kind of sentence made {g.id} laugh and stop the argument?",
            answer=f"The clear sentence was: '{req.clear_sentence}.' That was the one {g.id} called excellent syntax.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gondolier?",
            answer="A gondolier is a person who rows and steers a long boat, often in a city with canals.",
        ),
        QAItem(
            question="What is syntax?",
            answer="Syntax is the order of words in a sentence. Good syntax helps people understand what you mean.",
        ),
        QAItem(
            question="Why can dialogue be funny in a story?",
            answer="Dialogue can be funny when characters misunderstand each other, argue in silly ways, or say surprising things.",
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
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: str, request: str, prop: str) -> str:
    return "(No story: this tiny comedy world always supports any canal setting, request, and prop combination.)"


ASP_RULES = r"""
% Everything is compatible in this tiny comedy world.
valid(S,R,P) :- setting(S), request(R), prop(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for r in REQUESTS:
        lines.append(asp.fact("request", r))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a gondolier and syntax.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=REQUESTS)
    ap.add_argument("--prize", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--passenger")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, request, prop = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        request=request,
        prop=prop,
        gondolier_name=args.name or rng.choice(GONDOLIERS),
        passenger_name=args.passenger or rng.choice(PASSENGERS),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    g = world.add(Entity(id=params.gondolier_name, kind="character", type="man", traits=[params.trait]))
    p = world.add(Entity(id=params.passenger_name, kind="character", type="person", traits=["impatient"]))
    req = REQUESTS[params.request]
    prop = PROPS[params.prop]
    world = tell(world, g, p, req, prop)
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
    StoryParams(setting="canal", request="dock", prop="parcel", gondolier_name="Marco", passenger_name="Mina", trait="cheerful"),
    StoryParams(setting="harbor", request="market", prop="hat", gondolier_name="Luca", passenger_name="Toby", trait="playful"),
    StoryParams(setting="lagoon", request="bridge", prop="fish", gondolier_name="Nico", passenger_name="Nora", trait="fussy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, r, p in combos:
            print(f"  {s:8} {r:8} {p:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.gondolier_name}: {p.request} with {p.prop} on {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
