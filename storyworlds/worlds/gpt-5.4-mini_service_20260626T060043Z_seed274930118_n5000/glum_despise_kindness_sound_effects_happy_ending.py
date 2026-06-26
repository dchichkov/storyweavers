#!/usr/bin/env python3
"""
A heartwarming storyworld about a glum character who thinks kindness is
annoying, only to discover that small helpful acts and cheerful sound effects
can soften a hard day into a happy ending.

The premise:
- A glum child-like hero starts off feeling unhappy and saying they despise
  kindness because it feels awkward or embarrassing.
- A gentle helper keeps offering small, concrete kindnesses with little sound
  effects: a tap-tap note, a jingle of a mug, a soft pat-pat on the back, a
  crinkle of a wrapped treat, a little whoosh of help.
- The hero first resists, then notices the practical help, and finally accepts
  the kindness.

The world model tracks:
- physical meters: tiredness, neatness, warmth, comfort, cheer, clutter
- emotional memes: glum, despise, trust, gratitude, joy, embarrassment

The story generator uses the model to create a beginning, turn, and resolution.
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
# Registries
# ---------------------------------------------------------------------------

SOUND_EFFECTS = {
    "tap": "tap-tap",
    "jingle": "jingle-jingle",
    "pat": "pat-pat",
    "crinkle": "crinkle-crinkle",
    "whoosh": "whoosh",
    "plink": "plink-plink",
}

KIND_ACTS = {
    "note": {
        "kind": "a kind note",
        "verb": "slip a kind note into the hero's pocket",
        "sound": "tap",
        "effect": {"comfort": 1, "trust": 1},
        "scene": "a folded note with a smiley corner",
    },
    "mug": {
        "kind": "a warm mug of cocoa",
        "verb": "bring a warm mug of cocoa",
        "sound": "jingle",
        "effect": {"warmth": 2, "comfort": 1},
        "scene": "a steaming mug wrapped in a bright napkin",
    },
    "blanket": {
        "kind": "a soft blanket",
        "verb": "lay a soft blanket over the hero's knees",
        "sound": "pat",
        "effect": {"warmth": 1, "comfort": 2},
        "scene": "a fluffy blanket tucked around the knees",
    },
    "help": {
        "kind": "help with a hard task",
        "verb": "help tidy the messy table",
        "sound": "whoosh",
        "effect": {"clutter": -2, "comfort": 1, "trust": 1},
        "scene": "careful hands clearing little piles of mess",
    },
    "gift": {
        "kind": "a tiny surprise gift",
        "verb": "offer a tiny surprise gift",
        "sound": "crinkle",
        "effect": {"joy": 1, "gratitude": 1},
        "scene": "a little gift tied with ribbon",
    },
    "song": {
        "kind": "a soft song",
        "verb": "hum a soft song",
        "sound": "plink",
        "effect": {"cheer": 1, "comfort": 1},
        "scene": "a gentle tune drifting through the room",
    },
}

PLACES = {
    "kitchen": {
        "name": "the kitchen",
        "starting_clutter": 2,
        "starting_warmth": 0,
        "background": "The kitchen smelled like toast and morning sunshine.",
    },
    "porch": {
        "name": "the porch",
        "starting_clutter": 1,
        "starting_warmth": 0,
        "background": "The porch was quiet except for birds in the yard.",
    },
    "living_room": {
        "name": "the living room",
        "starting_clutter": 2,
        "starting_warmth": 0,
        "background": "The living room had a soft rug and a sleepy lamp.",
    },
    "garden_bench": {
        "name": "the garden bench",
        "starting_clutter": 0,
        "starting_warmth": 0,
        "background": "The garden bench sat under a tree with bright leaves.",
    },
}

HERO_NAMES = ["Milo", "Nina", "Pip", "Luna", "Toby", "Maya", "Rae", "Owen"]
HELPER_NAMES = ["Grandma", "Aunt June", "Dad", "Mom", "Neighbor Jo", "Mr. Bean"]
TRAITS = ["small", "gentle", "curious", "quiet", "shy", "careful"]


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "uncle", "grandfather", "grandma"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0
GLUM_START = 1.0
DESPISE_START = 1.0


def bump(d: dict[str, float], key: str, amount: float) -> None:
    d[key] = d.get(key, 0.0) + amount


def entity_name(ent: Entity) -> str:
    return ent.id


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    act: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def apply_kindness(world: World, hero: Entity, helper: Entity, act_id: str) -> None:
    act = KIND_ACTS[act_id]
    hero.meters["glum"] = max(0.0, hero.meters.get("glum", 0.0) - 0.5)
    helper.meters["kindness"] = helper.meters.get("kindness", 0.0) + 1.0
    world.say(f"{helper.id} made a little {act['kind']} for {hero.id}.")
    world.say(f"{act['sound']}, went the room, like kindness trying not to be loud.")
    for key, delta in act["effect"].items():
        bump(hero.meters, key, delta)
    bump(hero.memes, "trust", 1.0)
    bump(hero.memes, "joy", 0.5)


def predicatively_helpful(world: World, hero: Entity, act_id: str) -> bool:
    act = KIND_ACTS[act_id]
    if act_id == "help":
        return world.facts.get("place_clutter", 0) >= 1
    return True


def tell_story(params: StoryParams) -> World:
    place_def = PLACES[params.place]
    world = World(place=place_def["name"])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"glum": 2.0, "comfort": 0.0, "warmth": 0.0, "joy": 0.0, "gratitude": 0.0},
        memes={"glum": GLUM_START, "despise": DESPISE_START, "trust": 0.0, "joy": 0.0, "embarrassment": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        meters={"kindness": 0.0, "warmth": float(place_def["starting_warmth"])},
        memes={"kindness": 1.0, "patience": 1.0, "joy": 0.0},
    ))

    world.facts["place_clutter"] = place_def["starting_clutter"]
    world.say(f"{hero.id} was feeling glum in {place_def['name']}.")
    world.say(place_def["background"])
    world.say(f"{hero.id} even said {hero.pronoun('subject')} despised kindness, because it made {hero.pronoun('object')} feel awkward.")

    world.para()
    if params.act == "help" and not predicatively_helpful(world, hero, params.act):
        raise StoryError("That kindness would not make sense in this setting.")
    world.say(f"{helper.id} noticed the frown and chose something gentle.")
    apply_kindness(world, hero, helper, params.act)

    world.para()
    if hero.memes.get("trust", 0.0) >= THRESHOLD:
        hero.memes["despise"] = 0.0
        hero.meters["glum"] = max(0.0, hero.meters.get("glum", 0.0) - 1.0)
        hero.meters["joy"] = hero.meters.get("joy", 0.0) + 1.0
        hero.meters["comfort"] = hero.meters.get("comfort", 0.0) + 1.0
        world.say(f"{hero.id} blinked, then gave a tiny smile.")
        world.say(f"{hero.id} stopped despising kindness, because the help was real and the sound effects felt cheerful instead of pushy.")
        world.say(f"In the end, {hero.id} held the warm thing close and the room felt softer than before.")
    else:
        world.say(f"{hero.id} stayed quiet, but the kindness still sat nearby like a small light.")

    world.facts.update(hero=hero, helper=helper, act_id=params.act, place=params.place)
    return world


# ---------------------------------------------------------------------------
# Reasonableness / selection
# ---------------------------------------------------------------------------

def valid_choices() -> list[tuple[str, str]]:
    return [(place, act) for place in PLACES for act in KIND_ACTS if predicatively_helpful(World(PLACES[place]["name"]), Entity("x"), act)]


def explain_rejection(act: str) -> str:
    return f"(No story: the kindness act '{act}' does not fit this gentle domain.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = KIND_ACTS[f["act_id"]]
    return [
        f'Write a heartwarming story for young children about a glum child named {hero.id} who says {hero.pronoun("subject")} despises kindness, but a helper offers {act["kind"]} with a small sound effect.',
        f"Tell a gentle story where {helper.id} helps {hero.id} at {world.place} using {act['sound']}, and the sadness turns into a happy ending.",
        f'Write a simple story with the words "glum" and "despise" that ends with kindness sounding cozy, not loud.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    act = KIND_ACTS[world.facts["act_id"]]
    return [
        QAItem(
            question=f"Why did {hero.id} seem glum at the start?",
            answer=f"{hero.id} felt glum because {hero.pronoun('subject')} was having a hard day and thought kindness was awkward.",
        ),
        QAItem(
            question=f"What did {helper.id} do to help {hero.id}?",
            answer=f"{helper.id} chose {act['kind']} and {act['verb']}, which gave {hero.id} comfort and trust.",
        ),
        QAItem(
            question=f"What sound did the kindness make?",
            answer=f"The kindness made a soft {SOUND_EFFECTS[act['sound']]} sound, which made the moment feel gentle.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} smiling, feeling warmer and happier, and no longer despising kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness usually do to people?",
            answer="Kindness can help people feel safer, warmer, and less alone.",
        ),
        QAItem(
            question="Why can a soft sound effect matter in a story?",
            answer="A soft sound effect can make a helpful moment feel gentle, cozy, and friendly.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets better and the characters finish feeling okay or joyful.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A helpful act is available when the place is valid for the story.
valid_place(P) :- place(P).

% Kind acts are always story-possible in this domain, but we keep the twin
% explicit so ASP and Python stay in sync.
valid_act(A) :- kind_act(A).

story_combo(P,A) :- valid_place(P), valid_act(A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in KIND_ACTS:
        lines.append(asp.fact("kind_act", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_combo/2."))
    return sorted(set(asp.atoms(model, "story_combo")))


def asp_verify() -> int:
    py = {(p, a) for p, a in valid_choices()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld about glumness, kindness, sound effects, and a happy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--act", choices=sorted(KIND_ACTS))
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandma", "grandfather", "aunt", "uncle"])
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
    combos = valid_choices()
    combos = [
        (p, a) for p, a in combos
        if (args.place is None or p == args.place)
        and (args.act is None or a == args.act)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandma", "grandfather", "aunt", "uncle"])
    return StoryParams(
        place=place,
        act=act,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", act="mug", hero_name="Milo", hero_type="boy", helper_name="Grandma", helper_type="grandma"),
    StoryParams(place="living_room", act="note", hero_name="Nina", hero_type="girl", helper_name="Mom", helper_type="mother"),
    StoryParams(place="porch", act="song", hero_name="Pip", hero_type="boy", helper_name="Dad", helper_type="father"),
    StoryParams(place="garden_bench", act="blanket", hero_name="Luna", hero_type="girl", helper_name="Aunt June", helper_type="aunt"),
    StoryParams(place="kitchen", act="help", hero_name="Toby", hero_type="boy", helper_name="Neighbor Jo", helper_type="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos:\n")
        for p, a in combos:
            print(f"  {p:12} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
