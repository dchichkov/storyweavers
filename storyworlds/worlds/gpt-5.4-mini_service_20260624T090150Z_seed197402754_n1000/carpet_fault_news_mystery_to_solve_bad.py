#!/usr/bin/env python3
"""
A fairy-tale storyworld about carpet, fault, and news: a small mystery that can
be solved, but not happily.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def title(self) -> str:
        return self.label or self.type


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    carpet: str
    news: str
    hero_name: str
    hero_type: str
    fault: str
    seed: Optional[int] = None


@dataclass
class Carpet:
    id: str
    label: str
    phrase: str
    color: str
    pattern: str
    place: str


@dataclass
class News:
    id: str
    label: str
    phrase: str
    cause: str
    clue: str


@dataclass
class Fault:
    id: str
    label: str
    phrase: str
    truth: str
    transformation: str
    bad_ending: str


PLACES = {
    "castle_hall": "the castle hall",
    "cottage": "the cottage",
    "great_room": "the great room",
}

CARPETS = {
    "red_rug": Carpet(
        id="red_rug",
        label="red carpet",
        phrase="a red carpet woven with gold thread",
        color="red",
        pattern="gold thread",
        place="castle_hall",
    ),
    "blue_rug": Carpet(
        id="blue_rug",
        label="blue carpet",
        phrase="a blue carpet with tiny silver stars",
        color="blue",
        pattern="silver stars",
        place="great_room",
    ),
    "wool_rug": Carpet(
        id="wool_rug",
        label="wool carpet",
        phrase="a warm wool carpet by the hearth",
        color="brown",
        pattern="soft curls",
        place="cottage",
    ),
}

NEWS = {
    "bird_news": News(
        id="bird_news",
        label="bird news",
        phrase="news from a sparrow on the windowsill",
        cause="a small bird had seen the truth",
        clue="a feather stuck to the fringe",
    ),
    "bell_news": News(
        id="bell_news",
        label="bell news",
        phrase="news from the bell-tower",
        cause="the bell had rung to tell everyone",
        clue="the bell sounded three quick rings",
    ),
    "brook_news": News(
        id="brook_news",
        label="brook news",
        phrase="news from the brook",
        cause="the water had carried the story along",
        clue="a wet footprint near the door",
    ),
}

FAULTS = {
    "ink_spill": Fault(
        id="ink_spill",
        label="fault",
        phrase="the fault of spilled ink",
        truth="the ink had spilled from the owl's quill",
        transformation="the carpet would turn spotted and gray",
        bad_ending="the stain would never leave the weave",
    ),
    "ash_blame": Fault(
        id="ash_blame",
        label="fault",
        phrase="the fault of ash from the hearth",
        truth="the ash had floated down when the wind opened the chimney door",
        transformation="the carpet would grow pale as winter",
        bad_ending="the old rug would keep its smoky mark",
    ),
    "mud_blame": Fault(
        id="fault",
        label="fault",
        phrase="the fault of muddy boots",
        truth="the muddy boots belonged to the messenger, who forgot to wipe them",
        transformation="the carpet would darken into a forest shadow",
        bad_ending="the carpet would stay marked like a bruise",
    ),
}


GIRL_NAMES = ["Lina", "Mira", "Sila", "Nora", "Pia"]
BOY_NAMES = ["Oren", "Tovi", "Bram", "Leif", "Ilan"]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mystery about a carpet, a fault, and a piece of news.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--carpet", choices=CARPETS)
    ap.add_argument("--news", choices=NEWS)
    ap.add_argument("--fault", choices=FAULTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def reasonableness_gate(place: str, carpet_id: str, news_id: str, fault_id: str) -> None:
    carpet = CARPETS[carpet_id]
    news = NEWS[news_id]
    fault = FAULTS[fault_id]
    if carpet.place != place:
        raise StoryError(f"(No story: {carpet.label} belongs in {PLACES[carpet.place]}, not {PLACES[place]}.)")
    if not news.clue:
        raise StoryError("(No story: this news has no clue to begin the mystery.)")
    if not fault.truth:
        raise StoryError("(No story: this fault has no real truth behind it.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for place in PLACES:
        for carpet_id, carpet in CARPETS.items():
            if carpet.place != place:
                continue
            for news_id in NEWS:
                for fault_id in FAULTS:
                    choices.append((place, carpet_id, news_id, fault_id))
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.carpet:
        choices = [c for c in choices if c[1] == args.carpet]
    if args.news:
        choices = [c for c in choices if c[2] == args.news]
    if args.fault:
        choices = [c for c in choices if c[3] == args.fault]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")

    place, carpet_id, news_id, fault_id = rng.choice(sorted(choices))
    if args.place and args.carpet:
        reasonableness_gate(place, carpet_id, news_id, fault_id)

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, carpet=carpet_id, news=news_id, hero_name=name, hero_type=gender, fault=fault_id)


def generate(params: StoryParams) -> StorySample:
    world = World(place=PLACES[params.place])

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    carpet = CARPETS[params.carpet]
    news = NEWS[params.news]
    fault = FAULTS[params.fault]

    rug = world.add(Entity(
        id="carpet",
        kind="thing",
        type="carpet",
        label=carpet.label,
        phrase=carpet.phrase,
        place=PLACES[params.place],
        meters={"clean": 1.0, "dull": 0.0},
        memes={"mystery": 1.0},
    ))

    messenger = world.add(Entity(
        id="messenger",
        kind="character",
        type="bird",
        label="a sparrow messenger",
        phrase=news.phrase,
        meters={"tired": 0.0},
        memes={"urgent": 1.0},
    ))

    stain = world.add(Entity(
        id="stain",
        kind="thing",
        type="stain",
        label="the stain",
        phrase=fault.phrase,
        place=PLACES[params.place],
        meters={"hidden": 1.0},
        memes={"secret": 1.0},
    ))

    curse = world.add(Entity(
        id="curse",
        kind="thing",
        type="curse",
        label="the change",
        phrase=fault.transformation,
        meters={"sleeping": 1.0},
        memes={"waiting": 1.0},
    ))

    # Act I: a fairy tale setting and a mystery seed.
    world.say(f"Once in {world.place}, there was a {carpet.color} carpet with {carpet.pattern} shining in its weave.")
    world.say(f"{hero.label} loved to walk there in soft slippers and listen to the hush under {hero.pronoun('possessive')} feet.")
    world.para()

    # Act II: news arrives and a fault is suspected.
    world.say(f"One evening, {news.phrase} came to {hero.label}, and {news.cause}.")
    world.say(f"The little messenger pecked the fringe and left behind {news.clue}.")
    world.say(f"{hero.label} frowned, because everyone said the {fault.label} was somebody's blame, but no one knew whose.")
    world.para()

    # Mystery-solving beats.
    world.say(f"{hero.label} lifted the hem, looked under the chair, and found {fault.truth}.")
    world.say(f"That was the clue: the fault did not begin with the carpet at all.")
    world.say(f"{hero.label} told the truth aloud, and the room grew still.")
    world.para()

    # Bad ending + transformation.
    rug.memes["mystery"] = 0.0
    rug.meters["clean"] = 0.0
    rug.meters["marked"] = 1.0
    stain.meters["hidden"] = 0.0
    curse.meters["sleeping"] = 0.0
    curse.meters["awake"] = 1.0

    world.say(f"But the tale did not end sweetly.")
    world.say(f"As soon as the truth was known, {fault.bad_ending}.")
    world.say(f"The carpet shivered and changed: {fault.transformation}.")
    world.say(f"In the end, {hero.label} could prove the fault, yet the carpet kept its mark, and the room learned to remember.")

    world.facts.update(
        hero=hero,
        carpet=rug,
        messenger=messenger,
        stain=stain,
        curse=curse,
        news=news,
        fault=fault,
        place=params.place,
    )

    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a fairy-tale mystery about a carpet, a fault, and a piece of news.",
        f"Tell a short story where {hero.label} finds the cause of a bad mark on the carpet.",
        "Write a gentle but sad tale in which a clue is solved, yet the ending stays unhappy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    carpet = f["carpet"]
    news = f["news"]
    fault = f["fault"]
    return [
        QAItem(
            question="What kind of carpet was in the room?",
            answer=f"It was {carpet.phrase}, and it lay quietly in {world.place}.",
        ),
        QAItem(
            question="What news started the mystery?",
            answer=f"The mystery began with {news.phrase}, which brought a clue to {hero.label}.",
        ),
        QAItem(
            question="What did the hero learn was the fault?",
            answer=f"{hero.label} learned that {fault.truth}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The mystery was solved, but the ending was bad because the carpet stayed marked and changed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carpet?",
            answer="A carpet is a soft covering for a floor, often woven from wool or fabric.",
        ),
        QAItem(
            question="What is news?",
            answer="News is information that tells people something new that has happened or been found out.",
        ),
        QAItem(
            question="What does fault mean?",
            answer="A fault is something wrong that causes trouble, or the blame for that trouble.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling thing that needs clues before it can be understood.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change, when something becomes different from what it was before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.place:
            bits.append(f"place={e.place!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/4.

valid(Place, Carpet, News, Fault) :-
    place(Place),
    carpet(Carpet),
    carpet_in(Carpet, Place),
    news(News),
    fault(Fault).

bad_story(Place, Carpet, News, Fault) :-
    valid(Place, Carpet, News, Fault),
    carpet_in(Carpet, Place),
    clue(News, _),
    truth(Fault, _).

transforms(Carpet, Fault) :-
    carpet(Carpet),
    fault(Fault),
    change(Fault, _),
    carpet_in(Carpet, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid, c in CARPETS.items():
        lines.append(asp.fact("carpet", cid))
        lines.append(asp.fact("carpet_in", cid, c.place))
    for nid, n in NEWS.items():
        lines.append(asp.fact("news", nid))
        lines.append(asp.fact("clue", nid, n.clue))
    for fid, f in FAULTS.items():
        lines.append(asp.fact("fault", fid))
        lines.append(asp.fact("truth", fid, f.truth))
        lines.append(asp.fact("change", fid, f.transformation))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, c, n, f) for p in PLACES for c in CARPETS if CARPETS[c].place == p for n in NEWS for f in FAULTS)
    clingo_set = set(asp_valid_combos())
    python_set = set(py)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python registry:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="castle_hall", carpet="red_rug", news="bird_news", hero_name="Lina", hero_type="girl", fault="ink_spill"),
    StoryParams(place="great_room", carpet="blue_rug", news="bell_news", hero_name="Oren", hero_type="boy", fault="ash_blame"),
    StoryParams(place="cottage", carpet="wool_rug", news="brook_news", hero_name="Mira", hero_type="girl", fault="mud_blame"),
]


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print("  ", combo)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.carpet} / {p.news} / {p.fault}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for place in PLACES:
        for carpet_id, carpet in CARPETS.items():
            if carpet.place != place:
                continue
            for news_id in NEWS:
                for fault_id in FAULTS:
                    choices.append((place, carpet_id, news_id, fault_id))
    if args.place:
        choices = [c for c in choices if c[0] == args.place]
    if args.carpet:
        choices = [c for c in choices if c[1] == args.carpet]
    if args.news:
        choices = [c for c in choices if c[2] == args.news]
    if args.fault:
        choices = [c for c in choices if c[3] == args.fault]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")

    place, carpet, news, fault = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, carpet=carpet, news=news, hero_name=name, hero_type=gender, fault=fault)


if __name__ == "__main__":
    main()
