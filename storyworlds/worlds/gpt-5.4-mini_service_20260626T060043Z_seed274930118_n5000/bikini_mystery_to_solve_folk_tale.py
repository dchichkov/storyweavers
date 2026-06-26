#!/usr/bin/env python3
"""
Story world: a folk-tale mystery about a missing bikini.

A small child-sized domain:
- a curious seeker notices the beloved bikini is gone
- clues are followed through a village, garden, and riverside
- a helpful truth reveals where the bikini went
- the ending image proves the mystery was solved

The story keeps a folk-tale voice: simple, rhythmic, concrete, and a little
old-fashioned.
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
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    scent: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    place: str
    hint: str
    points_to: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
        self.facts: dict = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.clues = _copy.deepcopy(self.clues)
        w.facts = dict(self.facts)
        w.lines = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village_green": Place("village_green", "the village green", "warm bread", {"search", "talk"}),
    "laundry_yard": Place("laundry_yard", "the laundry yard", "soap and sun", {"search", "talk"}),
    "riverbank": Place("riverbank", "the riverbank", "cool reeds", {"search", "talk"}),
    "orchard": Place("orchard", "the orchard", "apple blossoms", {"search", "talk"}),
}

HEROES = {
    "mira": {"name": "Mira", "type": "girl"},
    "lena": {"name": "Lena", "type": "girl"},
    "tomas": {"name": "Tomas", "type": "boy"},
    "petr": {"name": "Petr", "type": "boy"},
}

HELPERS = {
    "grandmother": {"type": "grandmother", "label": "Grandmother"},
    "mother": {"type": "mother", "label": "Mother"},
    "old_fisher": {"type": "man", "label": "the old fisher"},
    "hedge_witch": {"type": "woman", "label": "the hedge-witch"},
}

BATHING_WEAR = {
    "bikini": {
        "label": "bikini",
        "phrase": "a bright little bikini with blue flowers",
        "region": "body",
        "genders": {"girl"},
    }
}

MYSTERIES = {
    "missing_bikini": {
        "id": "missing_bikini",
        "item": "bikini",
        "question": "Where did the bikini go?",
        "theme": "mystery",
    }
}

CLUES = {
    "line": Clue("line", "line", "laundry_yard", "a fluttering blue ribbon on the washline", "riverbank"),
    "sand": Clue("sand", "sand", "riverbank", "small wet footprints near the stones", "orchard"),
    "petal": Clue("petal", "petal", "orchard", "a flower petal snagged on a thorn", "village_green"),
}

TRAITS = ["curious", "gentle", "brave", "patient", "bright"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    hero_gender: str
    helper: str
    mystery: str = "missing_bikini"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    if params.mystery not in MYSTERIES:
        return False
    if params.hero not in HEROES:
        return False
    if params.helper not in HELPERS:
        return False
    if params.hero_gender not in {"girl", "boy"}:
        return False
    if params.hero_gender not in BATHING_WEAR["bikini"]["genders"]:
        return False
    if params.place not in PLACES:
        return False
    if params.place != "village_green":
        return False
    return True


def explain_invalid(params: StoryParams) -> str:
    return "This tale only fits a girl heroine in the village green, because the bikini and the folk-tale search are built around that setting."


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def _do_search(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"At dawn, {hero.id} found that {hero.pronoun('possessive')} bikini was gone, "
        f"and {helper.label} came with a calm step and said they would look for the truth."
    )


def _add_clue(world: World, clue_id: str) -> None:
    clue = CLUES[clue_id]
    world.clues.append(clue)
    world.say(f"At {PLACES[clue.place].label}, they found {clue.hint}.")


def _solve(world: World, hero: Entity, helper: Entity, bikini: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    hero.memes["worry"] = 0.0
    bikini.hidden = False
    bikini.location = hero.id
    world.say(
        f"The old trail led them back to the laundry yard, where the bikini had been caught in a sheet and carried by the wind from the line."
    )
    world.say(
        f"{helper.label} reached up, freed {bikini.item_pronoun()}, and {hero.id} laughed because the missing thing had not been stolen at all."
    )
    world.say(
        f"Before the sun climbed high, {hero.id} wore {bikini.item_pronoun()} again, and the village green shone bright and safe."
    )


def tell(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError(explain_invalid(params))

    world = World(PLACES[params.place])

    hero_cfg = HEROES[params.hero]
    helper_cfg = HELPERS[params.helper]

    hero = world.add(Entity(
        id=hero_cfg["name"],
        kind="character",
        type=hero_cfg["type"],
        meters={"step": 0.0},
        memes={"worry": 0.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_cfg["label"],
        kind="character",
        type=helper_cfg["type"],
        label=helper_cfg["label"],
        meters={"step": 0.0},
        memes={"calm": 1.0},
    ))
    bikini = world.add(Entity(
        id="bikini",
        type="bikini",
        label="bikini",
        phrase=BATHING_WEAR["bikini"]["phrase"],
        owner=hero.id,
        caretaker=helper.id,
        location="laundry_yard",
        hidden=True,
        meters={"clean": 1.0},
    ))

    world.say(
        f"Once in a village scented with {world.place.scent}, there lived {hero.id}, "
        f"a {random.choice(TRAITS)} child who loved summer water and bright cloth."
    )
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {bikini.label}, for it was {bikini.phrase}."
    )
    world.para()

    _do_search(world, hero, helper)
    world.say(
        f"They first asked in {PLACES['village_green'].label}, then at {PLACES['riverbank'].label}, "
        f"for folk in the old village knew that a lost thing often left a trail."
    )
    world.para()

    _add_clue(world, "line")
    _add_clue(world, "sand")
    _add_clue(world, "petal")
    world.say("Each sign pointed onward, and the helper's eyes grew wise with every step.")
    world.para()

    _solve(world, hero, helper, bikini)

    world.facts.update(
        hero=hero,
        helper=helper,
        bikini=bikini,
        place=params.place,
        mystery=params.mystery,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f"Write a short folk tale mystery about {hero.id} and a missing bikini.",
        f"Tell a gentle story where a child named {hero.id} loses a bikini and follows clues to solve the mystery.",
        "Write a simple village tale that begins with a lost bikini and ends with the truth revealed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    bikini = world.facts["bikini"]
    return [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer=f"{hero.id}'s bikini was missing at the start, which made the child worried.",
        ),
        QAItem(
            question=f"Who helped {hero.id} search for the missing bikini?",
            answer=f"{helper.label} helped {hero.id} search and stayed calm while the clues were followed.",
        ),
        QAItem(
            question="What did the clues show in the end?",
            answer=f"The clues showed that the bikini had caught on a washline and drifted from the laundry yard, so it was not stolen.",
        ),
        QAItem(
            question=f"Where did {hero.id} wear the bikini again at the end?",
            answer=f"{hero.id} wore the bikini again by the village green after the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bikini?",
            answer="A bikini is a small swimsuit with two pieces, often worn for swimming or playing near water.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small sign or hint that helps someone figure out a mystery.",
        ),
        QAItem(
            question="Why do people follow clues?",
            answer="People follow clues because clues can lead them to the truth when something is missing or puzzling.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} hidden={e.hidden} location={e.location} "
            f"meters={e.meters} memes={e.memes}"
        )
    if world.clues:
        lines.append("clues:")
        for c in world.clues:
            lines.append(f"  {c.id}: {c.hint} -> {c.points_to}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(village_green).
place(laundry_yard).
place(riverbank).
place(orchard).

hero(mira).
hero(lena).
hero(tomas).
hero(petr).

gender(mira,girl).
gender(lena,girl).
gender(tomas,boy).
gender(petr,boy).

helper(grandmother).
helper(mother).
helper(old_fisher).
helper(hedge_witch).

item(bikini).
genders(bikini,girl).

valid_story(Place,Hero,Helper) :- place(Place), hero(Hero), helper(Helper), gender(Hero,girl), Place = village_green.
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
        lines.append(asp.fact("gender", hid, HEROES[hid]["type"]))
    for kid in HELPERS:
        lines.append(asp.fact("helper", kid))
    lines.append(asp.fact("item", "bikini"))
    lines.append(asp.fact("genders", "bikini", "girl"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {
        (p, h, k)
        for p in PLACES
        for h in HEROES
        for k in HELPERS
        if valid_story(StoryParams(place=p, hero=h, hero_gender="girl" if HEROES[h]["type"] == "girl" else "boy", helper=k))
    }
    cl = set(asp_valid_stories())
    if cl == py:
        print(f"OK: ASP matches Python ({len(cl)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale mystery about a missing bikini.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--hero", choices=list(HEROES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--mystery", choices=list(MYSTERIES), default="missing_bikini")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender
    if args.hero and not gender:
        gender = "girl" if HEROES[args.hero]["type"] == "girl" else "boy"
    if gender and gender != "girl":
        raise StoryError("This folk tale is built around a bikini, so the heroine must be a girl.")
    place = args.place or "village_green"
    hero = args.hero or rng.choice([k for k, v in HEROES.items() if v["type"] == "girl"])
    helper = args.helper or rng.choice(list(HELPERS))
    params = StoryParams(place=place, hero=hero, hero_gender="girl", helper=helper, mystery=args.mystery)
    if not valid_story(params):
        raise StoryError(explain_invalid(params))
    return params


def generate(params: StoryParams) -> StorySample:
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="village_green", hero="mira", hero_gender="girl", helper="grandmother"),
    StoryParams(place="village_green", hero="lena", hero_gender="girl", helper="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
