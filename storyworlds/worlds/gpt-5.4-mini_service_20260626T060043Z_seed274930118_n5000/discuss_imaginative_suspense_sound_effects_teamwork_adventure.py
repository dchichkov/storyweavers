#!/usr/bin/env python3
"""
storyworlds/worlds/discuss_imaginative_suspense_sound_effects_teamwork_adventure.py
==================================================================================

A small adventure storyworld about kids who discuss an imaginative plan, feel
a little suspense, make sound effects, and solve a problem with teamwork.

Seed idea:
- Two children are on a tiny adventure at an old treehouse or garden path.
- They discuss an imaginative rescue mission.
- Suspense grows when a strange sound happens in the dark.
- Sound effects and teamwork help them discover a trapped kitten and bring it home safely.

The world model tracks physical meters and emotional memes, and the story is
generated from state changes rather than a frozen paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "noise", "safety", "found"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "suspense", "joy", "fear", "teamwork", "relief", "discussion"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    sounds: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    label: str
    verb: str
    suspense: str
    sound: str
    clue: str
    reward: str


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    phrase: str
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.trace_events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        return w


PLACES = {
    "treehouse": Place(id="treehouse", label="the old treehouse", dark=True, sounds=["creak", "whisper", "tap"]),
    "garden": Place(id="garden", label="the moonlit garden path", dark=True, sounds=["rustle", "tap", "chirp"]),
    "shed": Place(id="shed", label="the backyard shed", dark=True, sounds=["bump", "scrape", "drip"]),
}

QUESTS = {
    "kitten": Quest(
        id="kitten",
        label="a lost kitten",
        verb="find",
        suspense="a tiny mew from the dark",
        sound="mew",
        clue="a small paw print near the steps",
        reward="the kitten curled up safely in a warm lap",
    ),
    "lantern": Quest(
        id="lantern",
        label="a dropped lantern",
        verb="recover",
        suspense="a sudden clink in the dark",
        sound="clink",
        clue="a warm glimmer under a plank",
        reward="the lantern shining again in careful hands",
    ),
}

TOOLS = {
    "flashlight": Tool(id="flashlight", label="a flashlight", helps={"dark", "find"}, phrase="shine the flashlight", plural=False),
    "walkie": Tool(id="walkie", label="walkie-talkies", helps={"discuss", "teamwork"}, phrase="talk on the walkie-talkies", plural=True),
    "rope": Tool(id="rope", label="a short rope", helps={"reach", "teamwork"}, phrase="lower the rope together", plural=False),
    "stick": Tool(id="stick", label="a long stick", helps={"reach"}, phrase="nudge the board gently", plural=False),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ruby", "June"]
BOY_NAMES = ["Leo", "Finn", "Eli", "Max", "Noah", "Owen", "Sam"]
TRAITS = ["imaginative", "brave", "curious", "careful", "cheerful", "inventive"]


@dataclass
class StoryParams:
    place: str
    quest: str
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(p, q) for p in PLACES for q in QUESTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with discussion, imagination, suspense, sound effects, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--hero")
    ap.add_argument("--partner")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--partner-type", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, quest = rng.choice(combos)
    q = QUESTS[quest]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(BOY_NAMES if partner_type == "boy" else GIRL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if hero == partner:
        raise StoryError("Hero and partner must be different names.")
    return StoryParams(place=place, quest=quest, hero=hero, hero_type=hero_type, partner=partner, partner_type=partner_type, trait=trait)


def _dialogue(world: World, hero: Entity, partner: Entity, quest: Quest) -> None:
    hero.memes["discussion"] += 1
    partner.memes["discussion"] += 1
    world.say(
        f'{hero.id} and {partner.id} sat close and had a quiet discuss about an '
        f'imaginative rescue plan for {quest.label}.'
    )
    world.say(
        f'"If we listen carefully," {hero.pronoun("subject")} said, '
        f'"we might hear {quest.suspense}."'
    )


def _setup(world: World, hero: Entity, partner: Entity, quest: Quest) -> None:
    hero.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(f"{hero.id} was a {hero.traits[0]} {hero.type} who loved adventure.")
    world.say(f"{partner.id} was ready to help, because every good adventure needed teamwork.")
    world.say(f"That evening, they went to {world.place.label}.")
    world.say(f"{world.place.label.capitalize()} was dark enough to feel mysterious, but not too dark to be brave.")
    world.para()
    _dialogue(world, hero, partner, quest)


def _suspense(world: World, hero: Entity, partner: Entity, quest: Quest) -> None:
    hero.memes["suspense"] += 1
    partner.memes["suspense"] += 1
    world.say(f"Then they heard {quest.suspense}.")
    world.say(f"A soft {quest.sound} sounded nearby, and both children froze for a moment.")
    world.say("The air felt still, like the whole garden was holding its breath.")


def _find_tool(world: World, hero: Entity, partner: Entity, quest: Quest) -> Tool:
    if quest.id == "kitten":
        return TOOLS["flashlight"]
    return TOOLS["walkie"]


def _resolve(world: World, hero: Entity, partner: Entity, quest: Quest) -> None:
    tool = _find_tool(world, hero, partner, quest)
    t = world.add(Entity(id=tool.id, type="tool", label=tool.label, plural=tool.plural))
    t.carried_by = hero.id
    world.say(f"{hero.id} turned on {tool.label}, and a warm beam touched the dark corners.")
    world.say(f"{partner.id} helped by {tool.phrase}, so they could search without rushing.")
    world.say(f"Together they noticed {quest.clue}.")
    hero.memes["teamwork"] += 1
    partner.memes["teamwork"] += 1
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    partner.memes["fear"] = max(0.0, partner.memes["fear"] - 1.0)
    world.para()
    world.say(
        f"At last, their teamwork brought them to {quest.reward}. "
        f"They laughed softly, careful not to scare it."
    )
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"{hero.id} and {partner.id} walked home side by side, still whispering the story of their little adventure."
    )
    world.facts["tool"] = tool


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    quest = QUESTS[params.quest]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, traits=[params.trait, "imaginative"]))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_type, traits=["helpful", "steady"]))
    world.facts.update(place=place, quest=quest, hero=hero, partner=partner, params=params)
    _setup(world, hero, partner, quest)
    _suspense(world, hero, partner, quest)
    _resolve(world, hero, partner, quest)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short adventure story for a child who is {hero.traits[0]} and imaginative, using the word "discuss".',
        f"Tell a suspenseful but gentle story where {hero.id} and a friend use teamwork to {quest.verb} after hearing a strange sound.",
        f'Write a child-friendly adventure with sound effects, a quiet plan, and a happy ending at {f["place"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    quest = f["quest"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who went on the adventure at {place.label}?",
            answer=f"{hero.id} and {partner.id} went on the adventure together at {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {partner.id} discuss before searching for {quest.label}?",
            answer=f"They had an imaginative discuss about how to help {quest.label}.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"The suspense came from hearing {quest.suspense} and then a soft {quest.sound} in the dark.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used teamwork, a flashlight, and careful searching to follow the clue and reach {quest.reward}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to do something they could not do as well alone.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special sounds, like creaks, taps, or clinks, that help make a story feel more vivid.",
        ),
        QAItem(
            question="What does imaginative mean?",
            answer="Imaginative means able to think of creative ideas and pretend adventures in your mind.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={ {k: v for k, v in e.meters.items() if v} } memes={ {k: v for k, v in e.memes.items() if v} }")
    return "\n".join(lines)


ASP_RULES = r"""
place(treehouse). place(garden). place(shed).
quest(kitten). quest(lantern).
compatible(P,Q) :- place(P), quest(Q).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", p) for p in PLACES] + [asp.fact("quest", q) for q in QUESTS])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


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
    StoryParams(place="treehouse", quest="kitten", hero="Mia", hero_type="girl", partner="Leo", partner_type="boy", trait="imaginative"),
    StoryParams(place="garden", quest="lantern", hero="Noah", hero_type="boy", partner="Ava", partner_type="girl", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 50):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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
            header = f"### {p.hero} and {p.partner} at {p.place} ({p.quest})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
