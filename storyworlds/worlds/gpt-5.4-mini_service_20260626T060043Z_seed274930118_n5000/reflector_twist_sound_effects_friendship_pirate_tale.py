#!/usr/bin/env python3
"""
storyworlds/worlds/reflector_twist_sound_effects_friendship_pirate_tale.py
=========================================================================

A small pirate-tale story world about a brave little crew, a shiny reflector,
a surprising twist, sound effects on deck, and a friendship that helps steer
the day home.

Seed tale idea:
---
A young deckhand on a tiny pirate sloop loves a brass reflector that can throw
sunlight across the water. One foggy morning, the crew searches for a hidden
cove but cannot see the cliffs. A gust of wind nearly sends the reflector over
the rail. The deckhand's friend catches it, and together they use the mirror to
flash light against the mist. The beam bounces off a secret sign and reveals
the safe passage after all.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain", "matey"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    weather: str
    afford: set[str] = field(default_factory=set)
    features: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    twist: str
    risk: str
    zone: set[str]
    keyword: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "hands"


@dataclass
class FriendGear:
    id: str
    label: str
    help_line: str
    result_line: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    friend: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "deck": Place(
        id="deck",
        label="the ship deck",
        weather="foggy",
        afford={"signal", "search"},
        features={"rope", "rail", "mast"},
    ),
    "cove": Place(
        id="cove",
        label="the hidden cove",
        weather="misty",
        afford={"signal", "search"},
        features={"cliff", "water", "rocks"},
    ),
    "harbor": Place(
        id="harbor",
        label="the harbor",
        weather="windy",
        afford={"signal", "search"},
        features={"beacon", "dock", "waves"},
    ),
}

ACTIONS = {
    "signal": Action(
        id="signal",
        verb="signal the way",
        gerund="signaling the way",
        rush="wave the reflector high",
        sound="flash",
        twist="the light bounces off the mist and shows a hidden mark",
        risk="lost in the fog",
        zone={"hands", "eyes"},
        keyword="reflector",
    ),
    "search": Action(
        id="search",
        verb="search for the safe path",
        gerund="searching for the safe path",
        rush="lean over the rail to peer below",
        sound="creak",
        twist="the reflector reveals a bright stripe on the water",
        risk="bumping the rocks",
        zone={"hands", "eyes"},
        keyword="reflector",
    ),
}

PRIZES = {
    "reflector": Prize(
        id="reflector",
        label="reflector",
        phrase="a polished brass reflector",
        region="hands",
    ),
}

FRIENDS = {
    "parrot": FriendGear(
        id="parrot",
        label="a chatty parrot",
        help_line="The parrot squawked a warning before the wind could snatch the shine away.",
        result_line="Its bright cry matched the flash and made the crew laugh.",
    ),
    "mate": FriendGear(
        id="mate",
        label="a loyal deck friend",
        help_line="The friend reached out fast and kept the reflector from tumbling overboard.",
        result_line="Together, they held the mirror steady and flashed the beam again.",
    ),
}

NAMES = ["Mara", "Finn", "June", "Toby", "Nell", "Rowan", "Pip", "Luna"]
TRAITS = ["brave", "cheerful", "curious", "quick", "lively", "stubborn"]


class PirateWorld(World):
    def __init__(self, place: Place) -> None:
        super().__init__(place)
        self.sound_count = 0
        self.twist_seen = False
        self.friendship = 0.0
        self.fog = 1.0


def _rule_sound(world: PirateWorld) -> list[str]:
    out = []
    actor = world.entities.get("hero")
    if not actor:
        return out
    if actor.meters.get("motion", 0.0) >= THRESHOLD and world.sound_count == 0:
        world.sound_count = 1
        out.append("The deck went creak-creak as the little ship rocked.")
    if actor.meters.get("flash", 0.0) >= THRESHOLD and world.sound_count == 1:
        world.sound_count = 2
        out.append("Flash! The reflector flashed bright over the water.")
    return out


def _rule_twist(world: PirateWorld) -> list[str]:
    out = []
    if world.twist_seen:
        return out
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    reflector = world.entities.get("reflector")
    if not hero or not friend or not reflector:
        return out
    if hero.memes.get("hope", 0.0) >= THRESHOLD and friend.memes.get("care", 0.0) >= THRESHOLD:
        world.twist_seen = True
        out.append("The light bounced back from the mist and drew a silver arrow on the waves.")
    return out


def propagate(world: PirateWorld) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_sound, _rule_twist):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    for line in out:
        world.say(line)
    return out


def tell(place: Place, action: Action, hero_name: str, friend_kind: str, trait: str) -> PirateWorld:
    world = PirateWorld(place)
    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=hero_name, traits=["little", trait]))
    friend = world.add(Entity(id="friend", kind="character", type="pirate", label=friend_kind, traits=["matey", "kind"]))
    reflector = world.add(Entity(
        id="reflector",
        kind="thing",
        type="reflector",
        label="reflector",
        phrase="a polished brass reflector",
        owner=hero.id,
        caretaker=hero.id,
    ))

    world.say(f"{hero.label} was a little {trait} pirate who loved {reflector.phrase}.")
    world.say(f"{hero.label} and {friend.label} sailed a tiny ship through the fog, hunting for the hidden cove.")
    world.para()

    world.say(f"The sea was {place.weather}, and the mast gave a low creak.")
    world.say(f"{hero.label} wanted to {action.verb}, but the mist made everything look gray.")
    hero.memes["hope"] = 1.0
    hero.meters["motion"] = 1.0
    propagate(world)
    world.say(f"{action.sound.capitalize()}! {hero.label} raised the reflector to catch a little light.")
    world.say(f"That was when the wind snapped the air and nearly took the mirror over the rail.")

    world.para()
    hero.memes["worry"] = 1.0
    friend.memes["care"] = 1.0
    world.say(f"{friend.label} grabbed the reflector just in time.")
    world.say(FRIENDS[friend_kind].help_line)
    world.say(f"Then came the twist: {action.twist}.")
    hero.meters["flash"] = 1.0
    propagate(world)

    world.para()
    world.say(FRIENDS[friend_kind].result_line)
    world.say(f"{hero.label} and {friend.label} followed the shining mark and found the safe water at last.")
    world.say(f"In the end, the little crew sailed on with the reflector held high, and the fog did not seem so big anymore.")

    world.facts.update(
        hero=hero,
        friend=friend,
        reflector=reflector,
        action=action,
        place=place,
        twist=action.twist,
        friend_kind=friend_kind,
        resolved=True,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a reflector, sound effects, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--friend-kind", choices=FRIENDS)
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, a, "reflector", f) for p in SETTINGS for a in ACTIONS for f in FRIENDS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.friend_kind:
        combos = [c for c in combos if c[3] == args.friend_kind]
    if not combos:
        raise StoryError("No valid pirate story matches those choices.")
    place, action, prize, friend_kind = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, friend=friend_kind, trait=trait)


def generation_prompts(world: PirateWorld) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a young child that includes a shiny reflector and a sudden twist.',
        f"Tell a gentle pirate story where {f['hero'].label} and {f['friend'].label} travel through {f['place'].label} and use a reflector to find the way.",
        f"Write a story with sound effects like creak and flash, and end with friendship helping the crew.",
    ]


def story_qa(world: PirateWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    action = f["action"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.label}, a little {hero.traits[-1]} pirate, and {friend.label}, who stayed close and helped on the ship.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do in {place.label}?",
            answer=f"{hero.label} wanted to {action.verb}. The fog made it hard at first, so the crew had to be patient.",
        ),
        QAItem(
            question="What changed the story in the middle?",
            answer=f"The twist was that {action.twist}. That showed the crew a safer path through the mist.",
        ),
        QAItem(
            question=f"How did {friend.label} help?",
            answer=f"{friend.label} kept the reflector from falling and stood with {hero.label} until the light could be used again.",
        ),
    ]


def world_knowledge_qa(world: PirateWorld) -> list[QAItem]:
    return [
        QAItem(question="What is a reflector?", answer="A reflector is a shiny object that bounces light from one place to another."),
        QAItem(question="Why do pirates listen for sound effects on a ship?", answer="Because sounds like creak, splash, and whoosh can warn them about wind, water, and moving ropes."),
        QAItem(question="What is friendship?", answer="Friendship is when people care about each other, help each other, and stay kind together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: PirateWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"  fired={sorted(world.fired)}")
    lines.append(f"  sound_count={world.sound_count} twist_seen={world.twist_seen} friendship={world.friendship}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
action(A) :- action_kind(A).
friend(F) :- friend_kind(F).

valid(P,A,F) :- place(P), action(A), friend(F).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("action_kind", aid))
    for fid in FRIENDS:
        lines.append(asp.fact("friend_kind", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], params.name, params.friend, params.trait)
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
    StoryParams(place="deck", action="signal", prize="reflector", name="Mara", friend="mate", trait="brave"),
    StoryParams(place="cove", action="search", prize="reflector", name="Finn", friend="parrot", trait="curious"),
    StoryParams(place="harbor", action="signal", prize="reflector", name="Nell", friend="mate", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for item in combos:
            print(" ", item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
