#!/usr/bin/env python3
"""
storyworlds/worlds/lot_pedal_chapped_transformation_friendship_rhyme_fairy.py
=============================================================================

A small fairy-tale storyworld about a magical pedal, a chapped little task,
friendship, rhyme, and a gentle transformation.

Premise:
- A child in a fairy-tale village wants to pedal a wondrous little cart.
- The pedal is magical, but the child's hands are chapped and sore.
- A kind friend offers balm and a rhyme, and the two discover that sharing
  the work can change the journey.

World model:
- Physical meters: comfort, dryness, shine, magic, speed.
- Emotional memes: hope, worry, friendship, delight, patience.

The story is intentionally constrained so each generated sample reads like a
complete fairy tale with a clear setup, turn, and resolution.
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
# Shared domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

HERO_NAMES = ["Mira", "Nori", "Lina", "Tessa", "Ivo", "Perrin", "Elin", "Sora"]
FRIEND_NAMES = ["Pip", "Wren", "Bram", "Lumi", "Jory", "Mina", "Fenn", "Rae"]
HERO_TYPES = ["girl", "boy", "child"]
FRIEND_TYPES = ["girl", "boy", "child"]
TRAITS = ["brave", "gentle", "curious", "cheerful", "little", "kind"]

PLACES = {
    "meadow": {"place": "the meadow", "outdoors": True, "affords": {"pedal"}},
    "fair": {"place": "the little fair", "outdoors": True, "affords": {"pedal"}},
    "courtyard": {"place": "the castle courtyard", "outdoors": True, "affords": {"pedal"}},
    "shed": {"place": "the lantern shed", "outdoors": False, "affords": {"pedal"}},
}

ACTIVITIES = {
    "pedal": {
        "id": "pedal",
        "verb": "pedal the star-cart",
        "gerund": "pedaling the star-cart",
        "rush": "rush to the bright pedal",
        "mess": "stiff",
        "soot": "stiff and sore",
        "zone": {"hands"},
        "keyword": "pedal",
        "tags": {"pedal", "transformation"},
    }
}

ITEMS = {
    "gloves": {
        "label": "gloves",
        "phrase": "a pair of soft gloves",
        "region": "hands",
        "plural": True,
        "genders": {"girl", "boy", "child"},
    },
    "mittens": {
        "label": "mittens",
        "phrase": "a pair of wool mittens",
        "region": "hands",
        "plural": True,
        "genders": {"girl", "boy", "child"},
    },
}

HELPERS = {
    "balm": {
        "id": "balm",
        "label": "herb balm",
        "prep": "rub on herb balm and sing a rhyme",
        "tail": "rubbed on herb balm and sang a rhyme",
        "guards": {"chapped"},
    }
}

# ---------------------------------------------------------------------------
# Entities and world
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------


def _apply_chap(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("pedal", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("balmed", 0.0) >= THRESHOLD:
            continue
        sig = ("chap", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["chapped"] = actor.meters.get("chapped", 0.0) + 1.0
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
        out.append(f"{actor.pronoun('possessive').capitalize()} hands grew chapped from the bright pedal.")
    return out


def _apply_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    if not hero or not friend:
        return out
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("friendship", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    out.append(f"{friend.id} stayed close and promised to help.")
    return out


def _apply_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    if not hero or not helper:
        return out
    if hero.memes.get("friendship", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("transformed", 0.0) >= THRESHOLD:
        return out
    if hero.memes.get("rhyme", 0.0) < THRESHOLD:
        return out
    sig = ("transform", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["comfort"] = hero.meters.get("comfort", 0.0) + 1.0
    hero.meters["speed"] = hero.meters.get("speed", 0.0) + 1.0
    hero.meters["chapped"] = 0.0
    hero.memes["transformed"] = 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    out.append(f"The rhyme turned the sore little moment into a bright new ride.")
    return out


RULES = [_apply_chap, _apply_friendship, _apply_transformation]

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


def is_valid_combo(place: str, activity: str, item: str) -> bool:
    return place in PLACES and activity in ACTIVITIES and item in ITEMS


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, i) for p in PLACES for a in PLACES[p]["affords"] for i in ITEMS]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Storytelling helpers
# ---------------------------------------------------------------------------


def build_world(params: StoryParams) -> World:
    setting = Setting(**{k: v for k, v in PLACES[params.place].items() if k in {"place", "outdoors", "affords"}})
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", params.hero_trait],
        meters={"comfort": 0.0, "speed": 0.0, "chapped": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "friendship": 0.0, "rhyme": 0.0, "transformed": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        traits=["little", params.friend_trait],
        meters={"comfort": 0.0, "speed": 0.0},
        memes={"hope": 1.0, "worry": 0.0, "friendship": 0.0, "rhyme": 1.0, "joy": 0.0},
    ))
    item = world.add(Entity(
        id="item",
        type=params.item,
        label=ITEMS[params.item]["label"],
        phrase=ITEMS[params.item]["phrase"],
        owner=hero.id,
        worn_by=hero.id,
        plural=ITEMS[params.item]["plural"],
        meters={"shine": 1.0},
    ))
    balm = world.add(Entity(
        id="balm",
        type="helper",
        label=HELPERS["balm"]["label"],
        meters={"magic": 1.0},
        memes={"kindness": 1.0},
    ))

    world.facts.update(hero=hero, friend=friend, item=item, balm=balm)
    return world


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                for s in lines:
                    world.say(s)


def introduce(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    item = world.facts["item"]
    world.say(
        f"Once in {world.setting.place}, there lived a {hero.traits[1]} little {hero.type} named {hero.id}."
    )
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {item.label} and dreamed of a merry pedal ride."
    )
    world.say(
        f"Close by lived {friend.id}, a {friend.traits[1]} little {friend.type} who liked rhymes and kind deeds."
    )


def setup_conflict(world: World) -> None:
    hero = world.facts["hero"]
    item = world.facts["item"]
    world.para()
    world.say(
        f"One bright day, {hero.id} went to {world.setting.place} to pedal the star-cart."
    )
    world.say(
        f"But the wind was sharp, and {hero.pronoun('possessive')} hands grew chapped around the {item.label}."
    )
    propagate(world)


def turn_and_resolve(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    balm = world.facts["balm"]
    world.para()
    world.say(
        f"{friend.id} hurried over and said, \"A balm, a song, a rhyme can mend a worried palm.\""
    )
    hero.memes["rhyme"] = hero.memes.get("rhyme", 0.0) + 1.0
    hero.memes["balmed"] = 1.0
    hero.meters["comfort"] = hero.meters.get("comfort", 0.0) + 1.0
    world.say(
        f"So they used {balm.label} together, and {friend.id} sang a little rhyme."
    )
    world.say(
        f"With friendship warm between them, the sore feeling softened."
    )
    propagate(world)
    if hero.memes.get("transformed", 0.0) >= THRESHOLD:
        world.say(
            f"Then the old trouble changed into a new delight, and {hero.id} pedaled on with a brighter heart."
        )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    setup_conflict(world)
    turn_and_resolve(world)
    world.facts["resolved"] = world.facts["hero"].memes.get("transformed", 0.0) >= THRESHOLD
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        f'Write a fairy tale about {hero.id}, {friend.id}, and a magical {item.label} with the words "lot", "pedal", and "chapped".',
        f"Tell a short story where {hero.id} wants to pedal a star-cart, but {hero.pronoun('possessive')} hands are chapped until a friend helps.",
        f"Write a gentle fairy tale about friendship and rhyme that ends with a transformation of worry into joy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who is the fairy tale mainly about?",
            answer=f"It is mainly about {hero.id}, a little {hero.type} who loves {hero.pronoun('possessive')} {item.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s hands become chapped?",
            answer=f"{hero.id}'s hands became chapped because {hero} was pedaling the star-cart and holding the bright pedal for a lot of time.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id} feel better?",
            answer=f"{friend.id} helped by bringing herb balm, sharing a rhyme, and staying close in friendship.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pedal?",
            answer="A pedal is a part you push with your feet or hands to make a machine or cart move.",
        ),
        QAItem(
            question="What does it mean when skin is chapped?",
            answer="Chapped skin is dry, rough, and sore, often from wind or cold air.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind bond between people who help, listen, and stay close to each other.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like fair and bear.",
        ),
        QAItem(
            question="What is transformation in a fairy tale?",
            answer="Transformation means something changes into a new form or feeling, like worry turning into joy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        lines.append(f"  {e.id} ({e.type}) " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A place affords an activity.
valid_place(P, A) :- affords(P, A).

% An item is at risk when the activity touches the same body region.
item_at_risk(A, I) :- activity(A), item(I), zone(A, R), worn_on(I, R).

% A helper is suitable when it can soothe the chapped condition.
helper_suitable(H, A, I) :- helper(H), item_at_risk(A, I), soothes(H, chapped).

% A valid fairy story must have a place, an at-risk item, and a helper.
valid_story(P, A, I) :- valid_place(P, A), item_at_risk(A, I), helper_suitable(_, A, I).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p["affords"]):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a["zone"]):
            lines.append(asp.fact("zone", aid, r))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("worn_on", iid, i["region"]))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for m in sorted(h["guards"]):
            lines.append(asp.fact("soothes", hid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_place/2."))
    asp_set = set(asp.atoms(model, "valid_place"))
    py_set = {(p, a) for p, a in [(p, a) for p in PLACES for a in PLACES[p]["affords"]]}
    if asp_set != py_set:
        print("MISMATCH between clingo and Python gate:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))
        return 1
    print(f"OK: ASP and Python agree on {len(py_set)} place/activity combinations.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about pedal, chapped hands, friendship, and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
    ap.add_argument("--trait")
    ap.add_argument("--friend-trait")
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
    activity = args.activity or rng.choice(sorted(PLACES[place]["affords"]))
    item = args.item or rng.choice(list(ITEMS))
    if activity not in PLACES[place]["affords"]:
        raise StoryError("That place cannot host that activity.")
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    friend_type = args.friend_type or rng.choice(FRIEND_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    trait = args.trait or rng.choice(TRAITS)
    friend_trait = args.friend_trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        item=item,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        hero_trait=trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_place/2."))
        combos = sorted(set(asp.atoms(model, "valid_place")))
        print(f"{len(combos)} place/activity combinations:")
        for p, a in combos:
            print(f"  {p} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("meadow", "pedal", "gloves", "Mira", "girl", "Pip", "child", "brave", "kind"),
            StoryParams("fair", "pedal", "mittens", "Nori", "boy", "Lumi", "girl", "curious", "gentle"),
            StoryParams("courtyard", "pedal", "gloves", "Elin", "child", "Bram", "boy", "cheerful", "kind"),
            StoryParams("shed", "pedal", "mittens", "Sora", "girl", "Rae", "child", "little", "brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
