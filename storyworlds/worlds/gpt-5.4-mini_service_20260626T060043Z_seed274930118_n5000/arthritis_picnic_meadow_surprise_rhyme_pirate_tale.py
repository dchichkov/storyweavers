#!/usr/bin/env python3
"""
Standalone storyworld: Arthritis Picnic Meadow Surprise Rhyme Pirate Tale

A small classical simulation in a pirate-tale style, set in a picnic meadow.
The story premise is a pirate crew planning a cheerful picnic surprise, until
the captain's arthritis in a hand and knee makes the simple trip hard. A rhyme
and a surprise help the crew adapt, turning the outing into a gentler shared
celebration.
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

PAIN_THRESHOLD = 1.0
JOY_THRESHOLD = 1.0
HURT_THRESHOLD = 1.0
FIX_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"weight": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        gender = self.id_gender if hasattr(self, "id_gender") else "neutral"
        if gender == "female":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "male":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the picnic meadow"
    flowers: str = "small flowers"
    grass: str = "soft grass"
    near_water: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    captain_title: str
    helper_title: str
    surprise: str
    rhyme: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACE = Place()

SURPRISES = {
    "lantern": {"label": "a bright lantern", "verb": "light", "effect": "warmth"},
    "banner": {"label": "a colorful banner", "verb": "hang", "effect": "cheer"},
    "cake": {"label": "a berry cake", "verb": "share", "effect": "sweetness"},
}

RHYMES = {
    "footstep": {
        "label": "a little sea rhyme",
        "lines": [
            "Step by step and slow, me hearties,",
            "Gentle hands make merry parties.",
        ],
    },
    "knee": {
        "label": "a knee-calm rhyme",
        "lines": [
            "Easy now, and easy tread,",
            "Soft grass keeps the ache from dread.",
        ],
    },
    "sail": {
        "label": "a sailing rhyme",
        "lines": [
            "Hoist the laugh and lower the speed,",
            "A kinder pace is what we need.",
        ],
    },
}

GOODIES = {
    "blanket": {"label": "a thick picnic blanket", "kind": "thing"},
    "teacup": {"label": "a small warm cup of tea", "kind": "thing"},
    "stick": {"label": "a smooth walking stick", "kind": "thing"},
}

CAPTAIN_TITLES = ["Captain", "First Mate", "Old Salt"]
HELPER_TITLES = ["mate", "deckhand", "shipmate"]
NAMES = ["Mira", "Nell", "Jo", "Tessa", "Rina", "Mara", "Lina", "Kia"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a surprise exists and a rhyme can calm arthritis.
valid_story(Surprise, Rhyme) :- surprise(Surprise), rhyme(Rhyme), calmable(Surprise, Rhyme).

% A rhyme is calmable when it helps the captain slow down and the surprise can be shared.
calmable(Surprise, Rhyme) :- surprise(Surprise), rhyme(Rhyme), shared(Surprise), gentle(Rhyme).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        if sid != "cake":
            lines.append(asp.fact("shared", sid))
    for rid, _ in RHYMES.items():
        lines.append(asp.fact("rhyme", rid))
        lines.append(asp.fact("gentle", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(s, r) for s in SURPRISES for r in RHYMES if s in {"lantern", "banner"}}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: clingo gate matches Python gate ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in clingo:", sorted(got - expected))
    print("only in python:", sorted(expected - got))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def python_reasonable(surprise: str, rhyme: str) -> bool:
    return surprise in {"lantern", "banner"} and rhyme in RHYMES


def build_story_state(params: StoryParams) -> World:
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    if params.rhyme not in RHYMES:
        raise StoryError("Unknown rhyme.")
    if not python_reasonable(params.surprise, params.rhyme):
        raise StoryError("That surprise and rhyme do not make a reasonable gentle pirate tale.")

    world = World(PLACE)
    captain = world.add(Entity(id=params.name, kind="character", label=f"Captain {params.name}"))
    captain.id_gender = "female" if params.gender == "girl" else "male"
    helper = world.add(Entity(id="helper", kind="character", label=f"the {params.helper_title}"))
    helper.id_gender = "neutral"
    surprise = world.add(Entity(id="surprise", kind="thing", label=SURPRISES[params.surprise]["label"]))
    rhyme = world.add(Entity(id="rhyme", kind="thing", label=RHYMES[params.rhyme]["label"]))
    blanket = world.add(Entity(id="blanket", kind="thing", label=GOODIES["blanket"]["label"], worn_by=helper.id))
    stick = world.add(Entity(id="stick", kind="thing", label=GOODIES["stick"]["label"], carried_by=helper.id))
    world.facts.update(
        captain=captain,
        helper=helper,
        surprise=surprise,
        rhyme=rhyme,
        blanket=blanket,
        stick=stick,
        params=params,
    )
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    c: Entity = f["captain"]
    h: Entity = f["helper"]
    s: Entity = f["surprise"]
    world.say(
        f"Captain {c.id} was a merry pirate who loved the wind, the grass, and a good tale."
    )
    world.say(
        f"{h.label.capitalize()} had prepared {s.label} for a picnic surprise in the meadow."
    )
    world.say(
        f"Their crew had come to the picnic meadow, where the grass was soft and the flowers leaned close like tiny lanterns."
    )


def arthritis_bites(world: World) -> None:
    c: Entity = world.facts["captain"]
    c.meters["arthritis"] = 2.0
    c.memes["worry"] = 1.0
    world.say(
        f"But Captain {c.id}'s arthritis was acting up, and one hand and knee felt stiff as a locked chest."
    )
    world.say(
        f"{c.pronoun('subject').capitalize()} tried to walk straight to the blanket, but each step felt slow."
    )


def surprise_turn(world: World) -> None:
    f = world.facts
    c: Entity = f["captain"]
    h: Entity = f["helper"]
    s: Entity = f["surprise"]
    r: Entity = f["rhyme"]
    c.memes["surprised"] = 1.0
    h.memes["hope"] = 1.0
    world.para()
    world.say(
        f"Then {h.label} gave a surprise: {s.label}, set beside the blanket like treasure on a friendly shore."
    )
    world.say(
        f"{h.pronoun('subject').capitalize()} also began a rhyme, and the words were as soft as the meadow breeze."
    )
    for line in RHYMES[world.facts["params"].rhyme]["lines"]:
        world.say(line)


def apply_rhyme(world: World) -> None:
    c: Entity = world.facts["captain"]
    c.memes["calmed"] = 1.0
    c.meters["pace"] = 0.0
    world.say(
        f"The rhyme slowed the day down. Captain {c.id} breathed easier and let the stiff hand rest."
    )


def resolution(world: World) -> None:
    f = world.facts
    c: Entity = f["captain"]
    h: Entity = f["helper"]
    s: Entity = f["surprise"]
    c.memes["joy"] = 2.0
    c.memes["worry"] = 0.0
    world.para()
    if f["params"].surprise == "cake":
        world.say(
            f"At last the crew shared the berry cake in small bites, so nobody had to rush."
        )
    elif f["params"].surprise == "lantern":
        world.say(
            f"The bright lantern glowed over the blanket, and the meadow looked like a tiny harbor at dusk."
        )
    else:
        world.say(
            f"The colorful banner fluttered above the picnic blanket, and the crew cheered like they had found a new island."
        )
    world.say(
        f"Captain {c.id} sat easy on the blanket, smiling at the surprise and the rhyme."
    )
    world.say(
        f"The pirate picnic stayed gentle, and the whole meadow felt warmer for it."
    )


def tell_story(params: StoryParams) -> World:
    world = build_story_state(params)
    narrate_setup(world)
    arthritis_bites(world)
    surprise_turn(world)
    apply_rhyme(world)
    resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a short pirate tale for a young child set in a picnic meadow, where Captain {p.name} has arthritis and a surprise helps the day go well.",
        f"Tell a gentle story with a rhyme, a surprise, and a stiff pirate captain at a picnic meadow.",
        f"Write a child-friendly pirate story that includes arthritis, a meadow picnic, and a comforting rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    c: Entity = f["captain"]
    s: Entity = f["surprise"]
    r: Entity = f["rhyme"]
    return [
        QAItem(
            question=f"Who was hurting in the picnic meadow story?",
            answer=f"Captain {c.id} was hurting because arthritis made a hand and knee stiff.",
        ),
        QAItem(
            question=f"What surprise had the helper prepared?",
            answer=f"The helper had prepared {s.label} for the picnic surprise.",
        ),
        QAItem(
            question=f"What helped the captain feel better during the picnic?",
            answer=f"The gentle rhyme helped Captain {c.id} slow down, breathe easier, and enjoy the surprise.",
        ),
        QAItem(
            question=f"Where did the pirate crew meet for the story?",
            answer=f"They met in the picnic meadow, where the grass was soft and the flowers were close by.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"Captain {c.id} sat on the blanket smiling, and the pirate picnic stayed gentle and cheerful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is arthritis?",
            answer="Arthritis is a condition that can make joints hurt, swell, or feel stiff when someone moves.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little poem or chant where some of the words sound alike, like the ends of two lines.",
        ),
        QAItem(
            question="Why might a surprise make a picnic fun?",
            answer="A surprise can make a picnic fun because it gives everyone something new and joyful to notice together.",
        ),
        QAItem(
            question="What is a meadow?",
            answer="A meadow is a wide open field with grass and often wild flowers growing in it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: arthritis, surprise, rhyme, picnic meadow.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain-title", choices=CAPTAIN_TITLES)
    ap.add_argument("--helper-title", choices=HELPER_TITLES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--rhyme", choices=RHYMES)
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
    surprise = args.surprise or rng.choice(["lantern", "banner"])
    rhyme = args.rhyme or rng.choice(list(RHYMES))
    if not python_reasonable(surprise, rhyme):
        raise StoryError("This tale needs a shared surprise and a gentle rhyme.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    captain_title = args.captain_title or rng.choice(CAPTAIN_TITLES)
    helper_title = args.helper_title or rng.choice(HELPER_TITLES)
    return StoryParams(
        name=name,
        gender=gender,
        captain_title=captain_title,
        helper_title=helper_title,
        surprise=surprise,
        rhyme=rhyme,
    )


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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


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
        print(f"{len(combos)} compatible surprise/rhyme combinations:")
        for s, r in combos:
            print(f"  {s:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for surprise in ["lantern", "banner"]:
            for rhyme in RHYMES:
                params = StoryParams(
                    name=args.name or "Mira",
                    gender=args.gender or "girl",
                    captain_title=args.captain_title or "Captain",
                    helper_title=args.helper_title or "shipmate",
                    surprise=surprise,
                    rhyme=rhyme,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        if len(samples) > 1:
            print(f"### story {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
