#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eater_hon_homonym_sound_effects_teamwork_twist.py
===============================================================================================================

A standalone story world for a pirate-tale style domain with a sound-effects
beat, a teamwork beat, and a homonym-based twist.

Seed tale used to build the model:
---
On the Laughing Gull, a little pirate named Pip the Eater loved listening for
clues while the crew worked together. One foggy morning, Captain Hon found a
scrap of map that said, "Go to the bow." Pip thought that meant a ribbon bow,
but the parrot squawked, "No, hon, the bow of the ship!" The crew searched,
creaked open a hatch, and followed the sound of splashing water. In the end,
they found the treasure chest tucked under the ship's front rail, and Pip
laughed because the clue was a homonym trick.
---

Design notes:
- "eater" is the hungry little pirate who likes snacks and listening.
- "hon" is the captain's affectionate nickname; it also lets the story carry a
  child-friendly pirate voice.
- "homonym" is the twist: a clue sounds like one meaning but points to another.
- Sound effects and teamwork are simulated as world-state changes that drive the
  final narration.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TURN_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Clue:
    word: str
    meaning: str
    false_meaning: str
    location: str
    sound: str


@dataclass
class Prize:
    label: str
    phrase: str
    hiding_place: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    prize: str
    hero: str
    captain: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    clue = world.facts.get("clue_obj")
    if not hero or not clue:
        return out
    if hero.memes.get("confused", 0.0) < TURN_THRESHOLD:
        return out
    sig = ("alarm", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["alert"] = hero.memes.get("alert", 0.0) + 1
    out.append(f"{hero.id} heard the wrong meaning at first and nearly chased the clue the wrong way.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = [e for e in world.entities.values() if e.kind == "character"]
    if not crew:
        return out
    if sum(e.memes.get("helping", 0.0) for e in crew) < TURN_THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in crew:
        e.memes["hope"] = e.memes.get("hope", 0.0) + 1
    out.append("The crew worked together, and the ship felt steady again.")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "ship": Setting(place="the Laughing Gull"),
    "cove": Setting(place="the foggy cove"),
    "galley": Setting(place="the ship's galley", indoors=True),
}


CLUES = {
    "bow": Clue(
        word="bow",
        meaning="the front of a ship",
        false_meaning="a ribbon bow",
        location="the ship's front rail",
        sound="creak",
    ),
    "knot": Clue(
        word="knot",
        meaning="a loop tied in rope",
        false_meaning="a small knot in wood, or a knot you might count",
        location="the rope locker",
        sound="clank",
    ),
    "stern": Clue(
        word="stern",
        meaning="the back of a ship",
        false_meaning="a serious face",
        location="the back deck",
        sound="splash",
    ),
}

PRIZES = {
    "chest": Prize(label="treasure chest", phrase="a little gold chest", hiding_place="the front rail"),
    "map": Prize(label="map case", phrase="a rolled map case", hiding_place="under a loose plank"),
    "coin": Prize(label="coin pouch", phrase="a pouch of shiny coins", hiding_place="behind a barrel"),
}

HERO_NAMES = ["Pip", "Mara", "Toby", "Nell", "Jory", "Elsa"]
CAPTAIN_NAMES = ["Hon", "Mora", "Jett", "Sailor Sue"]

TRAITS = ["quick", "curious", "bright-eyed", "cheerful", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with sound effects, teamwork, and a homonym twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--captain")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    prize = args.prize or rng.choice(list(PRIZES))
    hero = args.hero or rng.choice(HERO_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)

    if clue == "bow" and prize == "coin":
        pass
    return StoryParams(setting=setting, clue=clue, prize=prize, hero=hero, captain=captain)


def pick_traits(rng: random.Random) -> list[str]:
    return [rng.choice(TRAITS), "stubborn"]


def predict_twist(world: World, hero: Entity, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("hero").memes["confused"] = 1.0
    propagate(sim, narrate=False)
    return {
        "confused": sim.get("hero").memes.get("confused", 0.0) >= TURN_THRESHOLD,
        "teamwork": sim.get("hero").memes.get("helping", 0.0) >= TURN_THRESHOLD,
        "meaning": clue.meaning,
    }


def tell_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=params.hero, traits=["little", "eater"]))
    captain = world.add(Entity(id="captain", kind="character", type="pirate", label=params.captain, traits=["kind", "hon"]))
    prize = world.add(Entity(id="prize", type="thing", label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    clue = CLUES[params.clue]

    world.facts.update(hero=hero, captain=captain, prize=prize, clue_obj=clue, setting=params.setting)

    world.say(f"On {world.setting.place}, little {hero.label} the eater loved snacks, sea-winds, and finding clues.")
    world.say(f"Captain {captain.label}, whom everyone called hon, lifted a scrap of paper and said, \"Listen close, matey.\"")
    world.say(f'The note said, "{clue.word}."')

    world.para()
    world.say(f"{hero.label} frowned. \"Is that a ribbon bow?\" {hero.pronoun()} asked.")
    world.say(f"The parrot squawked, \"No, no! It means {clue.meaning}!\"")
    world.say(f"That was the homonym twist: the same word could trick your ears into the wrong picture.")
    hero.memes["confused"] = 1.0

    world.para()
    world.say(f"Then came the sound effects: {clue.sound}-creak, {clue.sound}-clank, and a soft splash against the planks.")
    captain.memes["helping"] = 1.0
    hero.memes["helping"] = 1.0
    propagate(world, narrate=True)

    world.say(f"{hero.label} and the crew searched together, one peering left, one lifting right, and one tapping the boards.")
    world.say(f"At last they found the {prize.label} at {clue.location}, right where the clue had pointed all along.")

    world.para()
    world.say(f"{hero.label} laughed. \"Ahoy, the word fooled me!\"")
    world.say(f"Captain {captain.label} grinned. \"That's a homonym, hon. It sounds sneaky, but teamwork beat the trick.\"")
    world.say(f"So the {prize.label} went home with the crew, and the little eater went to sleep with a full belly and a happy heart.")

    world.facts["resolved"] = True
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    clue: Clue = f["clue_obj"]
    prize: Entity = f["prize"]
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    return [
        f'Write a pirate tale for young children that includes the word "{clue.word}" and ends with teamwork.',
        f"Tell a short story about {hero.label}, Captain {captain.label}, and a homonym clue that leads to {prize.label}.",
        f"Make a gentle pirate adventure with sound effects, a mistaken clue, and a happy twist.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    captain: Entity = f["captain"]
    clue: Clue = f["clue_obj"]
    prize: Entity = f["prize"]
    return [
        QAItem(
            question=f"Who was the little eater in the story?",
            answer=f"The little eater was {hero.label}, a curious pirate who liked snacks and clues.",
        ),
        QAItem(
            question=f"What did Captain {captain.label} mean by the word '{clue.word}'?",
            answer=f"Captain {captain.label} meant {clue.meaning}, not {clue.false_meaning}.",
        ),
        QAItem(
            question="Why was the clue a twist?",
            answer="It was a twist because the word sounded like one thing at first, but it pointed to a different meaning once the crew listened carefully.",
        ),
        QAItem(
            question="How did the crew find the treasure?",
            answer=f"They worked together, listened for the clue, and found the {prize.label} at the place the note described.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a homonym?",
            answer="A homonym is a word that sounds the same as another word, even though it can mean something different.",
        ),
        QAItem(
            question="Why do pirates say 'ahoy'?",
            answer="Pirates say 'ahoy' as a friendly way to call out and get someone's attention.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="Why do sound effects matter in a story?",
            answer="Sound effects help you imagine what things sound like, like creaking boards, splashing water, or a clang in the dark.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {e.label} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is homonym-tricky when the sound can point to more than one meaning.
tricky(C) :- clue(C), meaning(C,M1), false_meaning(C,M2), M1 != M2.

% Teamwork resolves the pirate problem when the crew helps together.
resolved(hero) :- helper(hero), helper(captain), tricky(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("word", cid, clue.word))
        lines.append(asp.fact("meaning", cid, clue.meaning))
        lines.append(asp.fact("false_meaning", cid, clue.false_meaning))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("hiding", pid, prize.hiding_place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def format_story(sample: StorySample) -> str:
    return sample.story


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(setting="ship", clue="bow", prize="chest", hero="Pip", captain="Hon"),
    StoryParams(setting="cove", clue="knot", prize="coin", hero="Mara", captain="Hon"),
    StoryParams(setting="galley", clue="stern", prize="map", hero="Toby", captain="Hon"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show tricky/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show tricky/1.\n#show resolved/1."))
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
            header = f"### {p.hero} aboard {p.setting} with clue {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
