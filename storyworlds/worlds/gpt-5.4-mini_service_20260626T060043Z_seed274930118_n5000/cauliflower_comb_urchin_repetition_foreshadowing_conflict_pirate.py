#!/usr/bin/env python3
"""
storyworlds/worlds/cauliflower_comb_urchin_repetition_foreshadowing_conflict_pirate.py
======================================================================================

A small pirate-tale storyworld about a crew, a strange prize, and a foreshadowed
standoff at sea.

Premise:
- A young pirate loves a shiny comb and keeps hearing a warning about an urchin
  reef hidden near an island cove.
- The crew also carries a head of cauliflower for supper, which becomes a useful
  clue: if the vegetables are packed wrong, the reef-to-table route is too rough
  and the basket gets bumped.
- The story uses repetition (a repeated warning chant), foreshadowing (the reef
  appears in signs before it causes trouble), and conflict (the pirate wants the
  comb, but the captain worries about the urchin reef).

The world is intentionally tiny and classical: one ship, one island, one small
conflict, one resolution. The simulated state drives the prose so the ending
proves what changed.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cove"
    on_ship: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    object: str
    signal: str
    hero_name: str
    hero_type: str
    captain_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SHIP = Setting(place="the ship", on_ship=True, affords={"approach", "inspect", "dock"})
COVE = Setting(place="the island cove", on_ship=False, affords={"approach", "inspect", "dock"})

OBJECTS = {
    "comb": ObjectSpec("comb", "a small silver comb", "comb", "pocket"),
    "cauliflower": ObjectSpec("cauliflower", "a crisp head of cauliflower", "cauliflower", "crate"),
    "urchin": ObjectSpec("urchin", "a spiny sea urchin shell", "urchin", "shore"),
}

SETTINGS = {
    "ship": SHIP,
    "cove": COVE,
}

HERO_NAMES = ["Ned", "Pip", "Mara", "Jory", "Belle", "Anne"]
TRAITS = ["curious", "bold", "cheerful", "stubborn", "spry"]


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _say_repetition(world: World, hero: Entity, signal: str) -> None:
    if signal == "warning":
        world.say("The captain pointed toward the black rocks and said, \"Hear the hush, hear the hush, hear the hush.\"")
    else:
        world.say("The sea seemed to answer with a soft whisper, then another whisper, then a third.")


def _check_foreshadowing(world: World) -> None:
    if world.facts.get("reef_seen") and not world.facts.get("reef_named"):
        world.say("A spiny shape glimmered under the foam, as if the sea itself was trying to warn them.")


def _trigger_conflict(world: World, hero: Entity, captain: Entity, prize: Entity, hazard: Entity) -> None:
    if _mem(hero, "want") >= THRESHOLD and _mem(captain, "warn") >= THRESHOLD:
        if ("conflict", hero.id) not in world.fired:
            world.fired.add(("conflict", hero.id))
            hero.memes["conflict"] = hero.memes.get("conflict", 0) + 1
            world.say(
                f"{hero.id} reached for {prize.label}, but {captain.label} blocked the way and shook {captain.pronoun('possessive')} head."
            )
            world.say(
                f"\"No, no, no,\" {captain.label} said. \"Not by the urchin reef. Not with the crate of {hazard.label} on deck.\""
            )


def _resolve(world: World, hero: Entity, captain: Entity, prize: Entity, hazard: Entity) -> None:
    if _mem(hero, "conflict") >= THRESHOLD and _mem(captain, "help") >= THRESHOLD:
        world.say(
            f"{hero.id} let go of the comb and helped move the crate of {hazard.label} higher on deck."
        )
        world.say(
            f"Then the pair steered wide of the reef, and the small silver comb stayed safe in {hero.pronoun('possessive')} pocket."
        )
        hero.memes["conflict"] = 0
        hero.memes["joy"] = hero.memes.get("joy", 0) + 1
        world.facts["resolved"] = True


def tell(setting: Setting, obj: ObjectSpec, signal: ObjectSpec, hero_name: str, hero_type: str, captain_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=captain_type,
        label="Captain Reed",
        traits=["weathered", "stern", "kind"],
    ))
    prize = world.add(Entity(
        id=obj.label,
        type=obj.type,
        label=obj.label,
        phrase=obj.phrase,
        owner=hero.id,
        caretaker=hero.id,
    ))
    hazard = world.add(Entity(
        id=signal.label,
        type=signal.type,
        label=signal.label,
        phrase=signal.phrase,
    ))

    hero.memes["want"] = 0
    captain.memes["warn"] = 0
    captain.memes["help"] = 0

    world.say(f"{hero.id} was a little {trait} pirate who loved {prize.label}.")
    world.say(f"{hero.id} also carried {hazard.phrase} in a crate for supper, because the crew planned a warm meal after the tide turned.")
    world.say(
        f"Every evening, the captain muttered the same line: \"Hear the hush, hear the hush, hear the hush.\""
    )

    world.para()
    world.say(
        f"One gray day, {hero.id} and {captain.label} sailed toward {setting.place}."
    )
    world.say("The water near the rocks looked strange, and a prickly shadow flashed under the foam.")
    world.facts["reef_seen"] = True
    _check_foreshadowing(world)
    _say_repetition(world, hero, "warning")

    hero.memes["want"] += 1
    captain.memes["warn"] += 1
    world.say(f"{hero.id} wanted to keep {prize.label} close and run down to the sand.")
    world.say(f"{captain.label} worried that the urchin reef would scrape the hull and spill the crate of {hazard.label}.")

    _trigger_conflict(world, hero, captain, prize, hazard)

    world.para()
    captain.memes["help"] += 1
    world.say(
        f"At last, {captain.label} held out a steady hand and showed {hero.id} a safer path between the rocks."
    )
    world.say(
        f"{hero.id} nodded, tucked {prize.label} away, and helped carry the crate of {hazard.label} to a higher shelf."
    )
    _resolve(world, hero, captain, prize, hazard)

    world.facts.update(
        hero=hero,
        captain=captain,
        prize=prize,
        hazard=hazard,
        setting=setting,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for obj in OBJECTS:
            for sig in OBJECTS:
                if obj == sig:
                    continue
                if place == "cove" and obj == "comb" and sig == "cauliflower":
                    combos.append((place, obj, sig))
                if place == "ship" and obj == "comb" and sig == "cauliflower":
                    combos.append((place, obj, sig))
    return combos


def explain_rejection(place: str, obj: str, sig: str) -> str:
    return (
        f"(No story: the chosen elements do not support a small pirate conflict. "
        f"Try a comb, a cauliflower crate, and an urchin warning near the ship or cove.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with repetition, foreshadowing, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--signal", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--captain", choices=["captain"])
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
    if args.object and args.signal and args.object == args.signal:
        raise StoryError("(No story: the object and signal must be different.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.signal is None or c[2] == args.signal)]
    if not combos:
        raise StoryError(explain_rejection(args.place, args.object, args.signal))
    place, obj, sig = rng.choice(sorted(combos))
    gender = args.gender or "boy"
    hero_name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    captain_type = "captain"
    return StoryParams(place=place, object=obj, signal=sig, hero_name=hero_name, hero_type="pirate", captain_type=captain_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        "Write a short pirate tale for a child that repeats a warning three times.",
        f"Tell a story about {hero.id}, a pirate who wants a comb, hears foreshadowing about an urchin reef, and faces a small conflict on a ship.",
        "Write a gentle sea story where cauliflower in a crate and an urchin warning help turn danger into a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    prize = f["prize"]
    hazard = f["hazard"]
    return [
        QAItem(
            question=f"What did {hero.id} want to keep safe?",
            answer=f"{hero.id} wanted to keep the comb safe, because {hero.id} loved the small silver comb."
        ),
        QAItem(
            question=f"Why did {captain.label} worry near the cove?",
            answer=f"{captain.label} worried because an urchin reef lurked under the foam and the crate of cauliflower could be spilled on the rough water."
        ),
        QAItem(
            question=f"How did the story use repetition?",
            answer="The captain repeated the warning chant, 'Hear the hush, hear the hush, hear the hush,' so the warning sounded steady and important."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} stopped reaching for the comb on deck, helped move the cauliflower crate higher, and sailed safely past the reef."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a comb for?",
            answer="A comb is used to smooth, untangle, or tidy hair."
        ),
        QAItem(
            question="What is cauliflower?",
            answer="Cauliflower is a pale vegetable that grows in a tight, bumpy head."
        ),
        QAItem(
            question="What is an urchin?",
            answer="An urchin is a spiny sea creature, and its shell or spikes can be sharp."
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives an early hint about something important that will matter later."
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict is a problem or disagreement that makes the characters struggle before they solve it."
        ),
        QAItem(
            question="What does repetition do in a story?",
            answer="Repetition repeats words or phrases so they feel memorable, rhythmic, or important."
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
object_choice(comb).
object_choice(cauliflower).
object_choice(urchin).

valid_story(Place, Obj, Sig) :- place(Place), object_choice(Obj), object_choice(Sig), Obj != Sig,
    compatible(Place, Obj, Sig).

compatible(ship, comb, cauliflower).
compatible(cove, comb, cauliflower).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for obj in OBJECTS:
        lines.append(asp.fact("object_choice", obj))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python validity.")
    if py - asp_set:
        print(" only in python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only in clingo:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], OBJECTS[params.object], OBJECTS[params.signal],
                 params.hero_name, params.hero_type, params.captain_type, params.trait)
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
    StoryParams(place="ship", object="comb", signal="cauliflower", hero_name="Ned", hero_type="pirate", captain_type="captain", trait="curious"),
    StoryParams(place="cove", object="comb", signal="cauliflower", hero_name="Mara", hero_type="pirate", captain_type="captain", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.hero_name}: {p.object} and {p.signal} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
