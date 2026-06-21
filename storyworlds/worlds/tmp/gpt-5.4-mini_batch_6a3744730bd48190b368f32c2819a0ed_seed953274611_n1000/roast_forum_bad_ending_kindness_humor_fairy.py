#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/roast_forum_bad_ending_kindness_humor_fairy.py
==============================================================================

A tiny fairy-tale storyworld about a village forum, a roasted supper, a kindly
attempt at humor, and a bad ending when the joke lands wrong.

The world is built from a small causal simulation: a messenger brings a roast to
the forum, a performer tries to lighten the mood with humor, kindness may soften
or fail to soften the crowd, and the final state determines whether the forum
ends in a shared supper or a sour, lonely departure.

Seed words: roast, forum
Style: fairy tale
Features: kindness, humor, bad ending
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    aroma: str
    shared: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Humor:
    id: str
    line: str
    kind: str
    charm: int
    sting: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Kindness:
    id: str
    act: str
    effect: str
    calm: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    food: str
    humor: str
    kindness: str
    teller: str
    listener: str
    ruler: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "forum": Place(id="forum", label="the village forum", tags={"forum", "crowd"}),
    "green": Place(id="green", label="the moonlit green", tags={"forum", "crowd", "outdoors"}),
    "hall": Place(id="hall", label="the old hall", indoors=True, tags={"forum", "crowd", "indoor"}),
}

FOODS = {
    "roast": Food(id="roast", label="a roast on a wooden tray", aroma="smelled rich and warm", tags={"roast", "supper"}),
    "turnips": Food(id="turnips", label="a pan of roast turnips", aroma="smelled sweet and brown", tags={"roast", "supper"}),
    "apples": Food(id="apples", label="warm roast apples", aroma="smelled like honey and smoke", tags={"roast", "supper"}),
}

HUMORS = {
    "goose": Humor(
        id="goose",
        line="A goose once tried to run a council by hissing at every hat in the room.",
        kind="animal",
        charm=3,
        sting=2,
        tags={"humor", "goose"},
    ),
    "crown": Humor(
        id="crown",
        line="The king wore a crown so big it needed its own pillow and its own apology.",
        kind="self",
        charm=2,
        sting=4,
        tags={"humor", "crown"},
    ),
    "boots": Humor(
        id="boots",
        line="Even the knight's boots looked tired enough to ask for porridge.",
        kind="gentle",
        charm=4,
        sting=1,
        tags={"humor", "boots"},
    ),
}

KINDNESSES = {
    "share": Kindness(
        id="share",
        act="offer to share the roast with everyone",
        effect="let the children and elders eat together",
        calm=3,
        tags={"kindness", "share"},
    ),
    "soft_word": Kindness(
        id="soft_word",
        act="speak softly to the crowd",
        effect="keep the voices from growing sharp",
        calm=2,
        tags={"kindness", "soft"},
    ),
    "bow": Kindness(
        id="bow",
        act="bow to the baker and thank the helpers",
        effect="make the helpers smile for a moment",
        calm=1,
        tags={"kindness", "bow"},
    ),
}

NAMES = ["Mira", "Tobin", "Elsa", "Pip", "Nell", "Bram", "Lina", "Oren"]
RULERS = ["queen", "king"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for f in FOODS:
            for h in HUMORS:
                for k in KINDNESSES:
                    combos.append((p, f, h, k))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.food not in FOODS:
        raise StoryError("Unknown food choice.")
    if params.place not in PLACES:
        raise StoryError("Unknown place choice.")
    if params.humor not in HUMORS:
        raise StoryError("Unknown humor choice.")
    if params.kindness not in KINDNESSES:
        raise StoryError("Unknown kindness choice.")
    if params.teller == params.listener:
        raise StoryError("The teller and listener must be different people.")
    if params.ruler not in RULERS:
        raise StoryError("Unknown ruler choice.")


def story_outcome(params: StoryParams) -> str:
    hum = HUMORS[params.humor]
    kind = KINDNESSES[params.kindness]
    if hum.sting > kind.calm + 1:
        return "bad"
    return "still_bad" if hum.sting >= kind.calm else "bad"


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    food = FOODS[params.food]
    hum = HUMORS[params.humor]
    kind = KINDNESSES[params.kindness]
    teller = world.add(Entity(id=params.teller, kind="character", type="person", role="teller"))
    listener = world.add(Entity(id=params.listener, kind="character", type="person", role="listener"))
    ruler = world.add(Entity(id=params.ruler.capitalize(), kind="character", type=params.ruler, role="ruler"))

    teller.memes["hope"] += 1
    listener.memes["care"] += 1
    ruler.memes["pride"] += 1

    world.say(
        f"Once upon a market dusk, {teller.id} and {listener.id} came to {place.label}. "
        f"On the stone bench sat {food.label}, and it {food.aroma}."
    )
    world.say(
        f"The village had gathered in a ring, for this was the night of the open forum, "
        f"when every voice could speak beneath the lanterns."
    )

    world.para()
    world.say(
        f"{teller.id} lifted a hand and tried a bit of humor. "
        f'"{hum.line}"'
    )
    teller.memes["boldness"] += hum.charm
    listener.memes["worry"] += hum.sting

    if hum.sting > 0:
        world.say(
            f"Some folk laughed softly, but the ruler's mouth turned thin, and the circle went quiet."
        )

    world.para()
    world.say(
        f"{listener.id} answered with kindness. {listener.id} chose to {kind.act}, "
        f"hoping to {kind.effect}."
    )
    listener.memes["kindness"] += kind.calm
    ruler.memes["softened"] += max(0, kind.calm - 1)

    if kind.calm <= hum.sting:
        world.say(
            f"It was a gentle thing, but the joke had already nicked the air. "
            f"The kindness reached the crowd like a small candle in wind."
        )
    else:
        world.say(
            f"For a breath, the words almost mended the room."
        )

    world.para()
    if hum.sting > kind.calm:
        world.say(
            f"But the ruler thought the humor had mocked the throne. "
            f"{ruler.id} rose, took the roast from the bench, and ordered the forum closed."
        )
        ruler.meters["anger"] += 2
        world.say(
            f"The people went home hungry. The roast grew cold on the tray, untouched, "
            f"and the lanterns were blown out one by one."
        )
        teller.memes["shame"] += 2
        listener.memes["sadness"] += 2
    else:
        world.say(
            f"The ruler accepted the apology, and the roast was shared by all."
        )

    world.facts.update(
        place=place,
        food=food,
        humor=hum,
        kindness=kind,
        teller=teller,
        listener=listener,
        ruler=ruler,
        outcome="bad",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that includes the words "{f["food"].id}" and "{f["place"].id}" and ends badly, but with a kind act and a funny line.',
        f"Tell a fairy tale about a forum where someone tries humor, someone answers with kindness, and the ending is still a bad one.",
        f"Write a short story for children in a fairy-tale style where {f['teller'].id} speaks at the {f['place'].label} and the roast goes cold.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teller = f["teller"]
    listener = f["listener"]
    ruler = f["ruler"]
    hum = f["humor"]
    kind = f["kindness"]
    food = f["food"]
    place = f["place"]

    return [
        QAItem(
            question="Who came to the forum?",
            answer=f"{teller.id} and {listener.id} came to {place.label} with the village gathered around them."
        ),
        QAItem(
            question="What joke did the teller tell?",
            answer=f"{hum.line} It was meant to be funny, but it made the room feel tense instead of merry."
        ),
        QAItem(
            question="How did the listener try to help?",
            answer=f"{listener.id} answered with kindness by choosing to {kind.act}. It was a gentle effort, but it could not fully fix the hurt feeling."
        ),
        QAItem(
            question="Why did the ending go badly?",
            answer=f"The ruler believed the humor mocked the throne and closed the forum. The roast stayed on the tray and the people went home hungry."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a forum?",
            answer="A forum is a place where people gather to speak, listen, and decide things together."
        ),
        QAItem(
            question="What is roast?",
            answer="A roast is food cooked by dry heat until it turns brown and smells rich."
        ),
        QAItem(
            question="Why can humor be risky?",
            answer="Humor can make people laugh, but if a joke sounds rude, it can also hurt feelings."
        ),
        QAItem(
            question="What does kindness do in a crowd?",
            answer="Kindness can calm voices, make people feel seen, and give a tense moment a softer shape."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
    for hid, h in HUMORS.items():
        lines.append(asp.fact("humor", hid))
        lines.append(asp.fact("charm", hid, h.charm))
        lines.append(asp.fact("sting", hid, h.sting))
    for kid, k in KINDNESSES.items():
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("calm", kid, k.calm))
    return "\n".join(lines)


ASP_RULES = r"""
bad_end(H, K) :- sting(H, S), calm(K, C), S > C.
gentle(H, K) :- sting(H, S), calm(K, C), S =< C.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_bad_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bad_end/2."))
    return sorted(set(asp.atoms(model, "bad_end")))


def asp_verify() -> int:
    py = {(h, k) for h in HUMORS for k in KINDNESSES if HUMORS[h].sting > KINDNESSES[k].calm}
    cl = set(asp_bad_pairs())
    rc = 0
    if py != cl:
        rc = 1
        print("MISMATCH in ASP parity.")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    else:
        print(f"OK: ASP parity on {len(py)} bad-ending pairs.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, food=None, humor=None, kindness=None, teller=None, listener=None, ruler=None), random.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a forum, a roast, kindness, humor, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--humor", choices=HUMORS)
    ap.add_argument("--kindness", choices=KINDNESSES)
    ap.add_argument("--teller")
    ap.add_argument("--listener")
    ap.add_argument("--ruler", choices=RULERS)
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
    place = args.place or rng.choice(list(PLACES))
    food = args.food or rng.choice(list(FOODS))
    humor = args.humor or rng.choice(list(HUMORS))
    kindness = args.kindness or rng.choice(list(KINDNESSES))
    teller = args.teller or rng.choice(NAMES)
    listener = args.listener or rng.choice([n for n in NAMES if n != teller])
    ruler = args.ruler or rng.choice(RULERS)
    params = StoryParams(
        place=place,
        food=food,
        humor=humor,
        kindness=kindness,
        teller=teller,
        listener=listener,
        ruler=ruler,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
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
        print("--- world model ---")
        for e in sample.world.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
            if e.memes:
                bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
            print(f"{e.id}: {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="forum", food="roast", humor="boots", kindness="soft_word", teller="Mira", listener="Tobin", ruler="queen"),
    StoryParams(place="hall", food="turnips", humor="goose", kindness="bow", teller="Elsa", listener="Bram", ruler="king"),
    StoryParams(place="green", food="apples", humor="crown", kindness="share", teller="Pip", listener="Nell", ruler="queen"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bad_end/2.\n#show gentle/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_end/2."))
        pairs = asp.atoms(model, "bad_end")
        print(f"{len(pairs)} bad-ending humor/kindness pairs:")
        for h, k in pairs:
            print(f"  {h} + {k}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
