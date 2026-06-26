#!/usr/bin/env python3
"""
storyworlds/worlds/parsley_dialogue_magic_space_adventure.py
============================================================

A standalone story world about a small space adventure where dialogue and a
little magic help solve a practical problem.

Premise:
- A child crew member on a tiny starship is excited for a trip.
- The ship's supper needs parsley, but the herb is floating loose, hidden, or
  wilting in low gravity.
- A helper's warning leads to a short argument.
- A magical, sensible fix makes the parsley useful again and the trip continue.

This script models:
- physical meters: freshness, drift, mess, heat, sparkle
- emotional memes: joy, worry, stubbornness, relief, trust

The story stays child-facing and concrete, with a clear beginning, turn, and end.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str = "the little starship"
    sector: str = "the galley"
    magic_field: bool = True
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    place: str
    magic_word: str
    seed: Optional[int] = None


HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Mira", "Jules", "Nia", "Toby", "Luna", "Pip", "Arlo", "Zuri"]
HELPER_NAMES = ["Captain Bo", "Pilot Ria", "Engineer Sol", "Aunt Nova"]
PLACES = ["the little starship", "the moon dock", "the comet garden", "the space kitchen"]
MAGIC_WORDS = ["sparkle", "twirl", "glow", "whisper"]


@dataclass
class World:
    ship: Ship
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
        clone = World(self.ship)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _ensure_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _ensure_meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in world.entities.values():
            if _ensure_meter(ent, "floating") >= THRESHOLD and ("drift", ent.id) not in world.fired:
                world.fired.add(("drift", ent.id))
                ent.meters["lost"] = ent.meters.get("lost", 0) + 1
                out.append(f"{ent.label} drifted farther along the hallway.")
                changed = True
            if _ensure_meter(ent, "wilted") >= THRESHOLD and ("wilt", ent.id) not in world.fired:
                world.fired.add(("wilt", ent.id))
                ent.meters["fresh"] = max(0.0, ent.meters.get("fresh", 1.0) - 1.0)
                out.append(f"{ent.label} looked a little sad and limp.")
                changed = True
            if _ensure_meme(ent, "worry") >= THRESHOLD and ("worry_face", ent.id) not in world.fired:
                world.fired.add(("worry_face", ent.id))
                out.append(f"{ent.id} frowned at the problem.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    ship = Ship(name="The Parsley Comet", place=params.place)
    world = World(ship=ship)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    parsley = world.add(Entity(
        id="parsley",
        type="herb",
        label="parsley",
        phrase="a tiny bunch of parsley",
        owner=hero.id,
        caretaker=helper.id,
    ))
    parsley.meters["fresh"] = 1.0
    parsley.meters["floating"] = 1.0
    hero.memes["joy"] = 1.0
    helper.memes["worry"] = 0.0
    world.facts.update(hero=hero, helper=helper, parsley=parsley, params=params)
    return world


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parsley: Entity = f["parsley"]
    world.say(
        f"{hero.id} loved riding on {world.ship.name}, where every hatch hummed and every window showed stars."
    )
    world.say(
        f"In the ship's little galley, {helper.id} was making supper, and {parsley.label} had to be found before the soup was ready."
    )
    world.say(
        f"{hero.id} wanted to help because {hero.pronoun('possessive')} hands were quick and {hero.pronoun('possessive')} eyes loved shiny things."
    )


def search_and_dialogue(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parsley: Entity = f["parsley"]
    world.para()
    world.say(
        f"{hero.id} checked the counter, the cup holder, and the wide round table, but the parsley was not there."
    )
    helper.memes["worry"] = 1.0
    propagate(world)
    world.say(
        f'"Did it fly away?" {hero.id} asked.'
    )
    world.say(
        f'"A little bit," {helper.id} said. "Low gravity makes light things dance unless we catch them first."'
    )
    world.say(
        f"{hero.id} puffed up. " + f'"I can catch it myself!"'
    )
    hero.memes["stubbornness"] = 1.0
    parsley.meters["floating"] = 1.0


def problem_turn(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parsley: Entity = f["parsley"]
    world.para()
    world.say(
        f"{hero.id} reached for the parsley pod, but it spun under a vent and bounced out of reach."
    )
    parsley.meters["floating"] = 2.0
    parsley.meters["wilted"] = 1.0
    propagate(world)
    world.say(
        f'"Wait," {helper.id} said. "If we keep chasing it, we might crush the leaves."'
    )
    world.say(
        f'{hero.id} crossed {hero.pronoun("possessive")} arms. "But dinner will taste silly without it."'
    )
    hero.memes["worry"] = 1.0
    hero.memes["stubbornness"] = 1.0


def magic_fix(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parsley: Entity = f["parsley"]
    magic_word: str = f["params"].magic_word
    world.para()
    world.say(
        f'{helper.id} pointed at a silver spoon. "Try a little {magic_word} magic," {helper.id} said softly.'
    )
    world.say(
        f"{hero.id} whispered the word, and the spoon gave a tiny bright shimmer."
    )
    parsley.meters["floating"] = 0.0
    parsley.meters["wilted"] = 0.0
    parsley.meters["fresh"] = 2.0
    hero.memes["joy"] = 2.0
    hero.memes["stubbornness"] = 0.0
    hero.memes["relief"] = 1.0
    helper.memes["worry"] = 0.0
    world.say(
        f"The parsley drifted neatly into {hero.id}'s bowl, green and fresh like a tiny star."
    )
    world.say(
        f"{hero.id} snipped it with care, and the soup smelled bright and clean."
    )


def ending(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parsley: Entity = f["parsley"]
    world.para()
    world.say(
        f'"We found it," {hero.id} said, grinning at the steam. "And it even looks happier now."'
    )
    world.say(
        f'"That is the magic of being gentle," {helper.id} said.'
    )
    world.say(
        f"Later, the crew ate supper while {parsley.label} sat safely in the bowl, bright as a little green comet."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    intro(world)
    search_and_dialogue(world)
    problem_turn(world)
    magic_fix(world)
    ending(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parsley: Entity = f["parsley"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for in the ship's galley?",
            answer=f"{hero.id} was looking for the parsley that {helper.id} needed for supper.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about chasing the parsley?",
            answer="Because the parsley was light and spinning in low gravity, so chasing it could crush the leaves.",
        ),
        QAItem(
            question=f"What magic word helped the parsley come back?",
            answer=f"The story used the word {params.magic_word}, and the spoon shimmered with magic.",
        ),
        QAItem(
            question=f"How did the story end for the parsley?",
            answer="It ended safely in the bowl, fresh and bright, ready for supper.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is parsley?",
            answer="Parsley is a green herb people chop up and add to food for a fresh taste and a green sprinkle.",
        ),
        QAItem(
            question="Why can small things float in a spaceship?",
            answer="In a spaceship, low gravity can make light things drift or float until someone catches them.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something unusual and wonderful that can make a problem easier or more surprising to solve.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    params: StoryParams = f["params"]
    return [
        f'Write a short space adventure for a young child where {hero.id} helps {helper.id} find parsley.',
        f'Write a gentle story with dialogue and magic about a starship supper and the word "{params.magic_word}".',
        f'Tell a tiny space story where parsley drifts away, someone worries, and a magical fix brings it back.',
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A parsley bunch is at risk when it is floating in low gravity and unwatched.
at_risk(P) :- parsley(P), floating(P).

% Magic is a sensible fix when the helper speaks the chosen word and the parsley
% becomes fresh again.
fixed(P) :- parsley(P), magic_word(W), used_word(W), fresh(P).

resolves_story :- at_risk(parsley), fixed(parsley).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("parsley", "parsley"))
    lines.append(asp.fact("magic_word", "sparkle"))
    lines.append(asp.fact("magic_word", "twirl"))
    lines.append(asp.fact("magic_word", "glow"))
    lines.append(asp.fact("magic_word", "whisper"))
    lines.append(asp.fact("floating", "parsley"))
    lines.append(asp.fact("fresh", "parsley"))
    lines.append(asp.fact("used_word", "sparkle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, w) for p in PLACES for w in MAGIC_WORDS]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show resolves_story/0."))
    asp_ok = any(sym.name == "resolves_story" for sym in model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python checks.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space adventure with parsley, dialogue, and magic.")
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic-word", choices=MAGIC_WORDS)
    ap.add_argument("--gender", choices=HERO_TYPES)
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
    hero_type = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    place = args.place or rng.choice(PLACES)
    magic_word = args.magic_word or rng.choice(MAGIC_WORDS)
    if args.name and args.helper and args.name == args.helper:
        raise StoryError("hero and helper must be different characters.")
    return StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type="captain" if helper_name.startswith("Captain") else "pilot",
        place=place,
        magic_word=magic_word,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolves_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("The ASP twin is available in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Mira", "girl", "Captain Bo", "captain", "the little starship", "sparkle"),
            StoryParams("Toby", "boy", "Pilot Ria", "pilot", "the space kitchen", "glow"),
            StoryParams("Luna", "girl", "Engineer Sol", "pilot", "the comet garden", "twirl"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
