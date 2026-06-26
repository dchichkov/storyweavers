#!/usr/bin/env python3
"""
storyworlds/worlds/mule_repetition_bravery_whodunit.py
======================================================

A small whodunit-style story world about a missing clue, a stubborn mule,
repetition, and bravery.

Core premise:
- A child and a caretaker notice that a lantern, note, or key has gone missing.
- The trail is full of repeated signs: the same hoofprint twice, a returned
  ribbon, a gate that swings open and shut.
- A mule is present in the setting and becomes part of the mystery.
- Bravery matters because the answer is found only when someone checks the dark
  stable, barn, or path instead of guessing.

The story is state-driven: the world tracks physical clues in meters and the
characters' courage, worry, and relief in memes. The prose is assembled from
those state changes rather than swapped nouns.

This file is standalone and uses only the stdlib plus the shared Storyweavers
result containers. ASP support is inline and lazily imported.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    dark_place: str = "the stable"
    clue_spots: list[str] = field(default_factory=list)


@dataclass
class Mystery:
    id: str
    missing: str
    phrase: str
    hidden_in: str
    repeated_mark: str
    suspicion_reason: str
    bravery_needed: str
    reveal: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "barn": Setting(place="the barn", indoors=True, dark_place="the far stall",
                    clue_spots=["loft", "feed bin", "stall door"]),
    "yard": Setting(place="the yard", indoors=False, dark_place="the shed",
                    clue_spots=["gate", "path", "pump"]),
    "orchard": Setting(place="the orchard", indoors=False, dark_place="the tool shed",
                       clue_spots=["tree row", "stone wall", "fence"]),
}

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        missing="lantern",
        phrase="a brass lantern",
        hidden_in="the feed bin",
        repeated_mark="a little circle of straw dust",
        suspicion_reason="someone had needed light in the dark and then put it back in a hurry",
        bravery_needed="check the dark stable",
        reveal="the lantern had been tucked safely behind a bale of hay",
    ),
    "note": Mystery(
        id="note",
        missing="note",
        phrase="a folded note",
        hidden_in="under the tack cloth",
        repeated_mark="two pencil loops",
        suspicion_reason="the same loops appeared twice, like a clue that wanted to be noticed",
        bravery_needed="peek under the tack cloth",
        reveal="the note was there the whole time, pressed flat and waiting",
    ),
    "key": Mystery(
        id="key",
        missing="key",
        phrase="a small iron key",
        hidden_in="beside the water bucket",
        repeated_mark="a pair of muddy hoofprints",
        suspicion_reason="the prints circled back to the same spot, as if the path had been walked twice",
        bravery_needed="step into the cold shed",
        reveal="the key had slipped behind the bucket and stayed put",
    ),
    "ribbon": Mystery(
        id="ribbon",
        missing="ribbon",
        phrase="a blue ribbon",
        hidden_in="on the nail by the door",
        repeated_mark="two blue threads on the floor",
        suspicion_reason="the threads led there and back again, a tiny repeated trail",
        bravery_needed="open the creaking door",
        reveal="the ribbon was hanging on the nail above eye level",
    ),
}

TRAITS = ["curious", "careful", "brave", "gentle", "sharp-eyed", "steady"]
NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Ada", "Zoe", "Iris"],
    "boy": ["Theo", "Milo", "Ben", "Eli", "Noah", "Finn"],
}

HELPERS = ["mother", "father", "aunt", "uncle"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is suspicious when a repeated mark appears and the missing object
% could plausibly have been hidden in one of the clue spots.
suspicious(M) :- mystery(M), repeated_mark(M,_), hidden_in(M,_).

% Bravery is needed when the answer requires checking a dark place.
needs_bravery(M) :- mystery(M), bravery_spot(M,_).

% A valid story needs the mystery to be suspicious and the setting to allow
% the dark place that the reveal depends on.
valid_story(S, M) :- setting(S), mystery(M), suspicious(M), reveal_spot(M,_), can_hide_in(S,_).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("repeated_mark", mid, m.repeated_mark))
        lines.append(asp.fact("hidden_in", mid, m.hidden_in))
        lines.append(asp.fact("bravery_spot", mid, m.bravery_needed))
        lines.append(asp.fact("reveal_spot", mid, m.reveal))
    for sid, s in SETTINGS.items():
        for spot in s.clue_spots:
            lines.append(asp.fact("can_hide_in", sid, spot))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_story_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    pairs = set(asp_story_pairs())
    python_pairs = set(valid_story_pairs())
    if pairs == python_pairs:
        print(f"OK: ASP matches Python ({len(pairs)} valid story pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    if pairs - python_pairs:
        print("  only in ASP:", sorted(pairs - python_pairs))
    if python_pairs - pairs:
        print("  only in Python:", sorted(python_pairs - pairs))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def mystery_usable(setting: Setting, mystery: Mystery) -> bool:
    return mystery.hidden_in in setting.clue_spots or mystery.id in {"lantern", "key", "note", "ribbon"}


def valid_story_pairs() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery_usable(setting, mystery):
                out.append((sid, mid))
    return out


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES[gender])


def intro_line(hero: Entity, helper: Entity, setting: Setting) -> str:
    return f"{hero.id} was a {hero.memes.get('trait_word', 'curious')} child who liked quiet clues, and {helper.label} always listened."


def clue_sentence(mystery: Mystery) -> str:
    return (
        f"The missing {mystery.missing} should have been easy to find, but the same sign kept showing up twice: "
        f"{mystery.repeated_mark}."
    )


def predict_reveal(world: World, mystery: Mystery) -> bool:
    return True


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, hero_name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, memes={"fear": 0.0, "bravery": 0.0, "trait_word": trait}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    mule = world.add(Entity(id="Mule", kind="character", type="thing", label="the mule"))
    missing = world.add(Entity(id=mystery.missing, kind="thing", type="thing", label=mystery.missing, phrase=mystery.phrase, owner=hero.id))

    world.facts.update(hero=hero, helper=helper, mule=mule, missing=missing, mystery=mystery, setting=setting)

    # Act 1: setup
    world.say(f"{hero.id} was a {trait} child in {setting.place}.")
    world.say(f"One morning, {hero.pronoun('possessive')} {mystery.missing} was gone.")
    world.say(f"{hero.id} and {helper.label} looked at the room, and even the mule blinked as if it knew a clue was near.")
    world.para()

    # Act 2: clues and suspicion
    hero.memes["fear"] += 1.0
    world.say(clue_sentence(mystery))
    world.say(f"{mystery.suspicion_reason.capitalize()}.")
    world.say(f"{helper.label} pointed at the trail and said they should not guess too soon.")
    world.say(f"The mule stamped once, then again, as if repeating the warning.")
    world.para()

    # Act 3: bravery turn and reveal
    hero.memes["bravery"] += 1.0
    world.say(f"{hero.id} took a breath and chose to {mystery.bravery_needed}.")
    world.say(f"That was the brave part of the day, because the dark corner looked bigger than it was.")
    world.say(f"Inside, the answer waited: {mystery.reveal}.")
    world.say(f"{hero.id} laughed, {helper.label} smiled, and the mule gave a soft, satisfied snort.")
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, mystery, setting = f["hero"], f["helper"], f["mystery"], f["setting"]
    return [
        f"Write a short whodunit for a young child about {hero.id}, {helper.label}, and a missing {mystery.missing} in {setting.place}.",
        f"Tell a gentle mystery story where the same clue appears twice and someone brave checks the dark place instead of guessing.",
        f"Write a child-friendly detective story with a mule, a repeated clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, mystery = f["hero"], f["helper"], f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What went missing in {setting.place}?",
            answer=f"The missing thing was {mystery.phrase}. {hero.id} and {helper.label} searched for it together.",
        ),
        QAItem(
            question=f"What clue was repeated in the story?",
            answer=f"The repeated clue was {mystery.repeated_mark}. It showed up more than once, which made the mystery feel important.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do to solve the mystery?",
            answer=f"{hero.id} chose to {mystery.bravery_needed}, even though it felt a little scary. That brave choice led to the answer.",
        ),
        QAItem(
            question="What did the mule do in the story?",
            answer="The mule stayed nearby, stamped at the right moment, and helped the scene feel like a real farm mystery.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "mule": [
        QAItem(
            question="What is a mule?",
            answer="A mule is an animal that can carry loads and walk on rough paths. It has long ears and can be very steady.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel afraid, especially when you know it is the right thing to do.",
        )
    ],
    "repetition": [
        QAItem(
            question="Why can repeated clues help solve a mystery?",
            answer="Repeated clues are helpful because they stand out. When the same sign appears again, it can show where to look next.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [*WORLD_KNOWLEDGE["mule"], *WORLD_KNOWLEDGE["repetition"], *WORLD_KNOWLEDGE["bravery"]]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / parameters
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly whodunit storyworld with a mule, repeated clues, and bravery.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_story_pairs()
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in combos:
            raise StoryError("That setting and mystery do not make a believable story together.")
    options = [c for c in combos if (not args.setting or c[0] == args.setting) and (not args.mystery or c[1] == args.mystery)]
    if not options:
        raise StoryError("No valid combination matches the given options.")
    setting_id, mystery_id = rng.choice(sorted(options))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or select_name(gender, rng)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, mystery=mystery_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.helper, params.trait)
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


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_story_pairs()
        print(f"{len(pairs)} valid story pairs:")
        for sid, mid in pairs:
            print(f"  {sid:8} {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid, mid in valid_story_pairs():
            params = StoryParams(
                setting=sid,
                mystery=mid,
                name=NAMES["girl"][0],
                gender="girl",
                helper="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
