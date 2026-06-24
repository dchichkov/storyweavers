#!/usr/bin/env python3
"""
A small storyworld for a pirate-tale-style feat built through teamwork and
inner monologue.

Premise:
- A young pirate crew wants to pull off a feat.
- They must track a hidden clue or object.
- Teamwork and private inner thoughts shape the turn and resolution.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    companion: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate", "sailor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affordance: str


@dataclass
class Challenge:
    id: str
    goal: str
    track_verb: str
    track_noun: str
    obstacle: str
    clue: str
    feat: str
    teamwork_need: str
    inner_thought: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    challenge: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "harbor": Setting(place="the harbor", affordance="boats and ropes"),
    "island": Setting(place="the island cove", affordance="sand, shells, and hidden paths"),
    "deck": Setting(place="the ship deck", affordance="rigging and lookout spots"),
    "cave": Setting(place="the sea cave", affordance="echoes and narrow tunnels"),
}

CHALLENGES = {
    "lost_map": Challenge(
        id="lost_map",
        goal="find the missing map",
        track_verb="track",
        track_noun="track marks",
        obstacle="the wind kept turning the paper corners",
        clue="a curl of blue thread snagged on a barrel",
        feat="follow the hidden trail to the map chest",
        teamwork_need="one pirate to search high while the other searched low",
        inner_thought="I can do this if I keep my eyes on the little clues.",
        tags={"track", "feat", "teamwork"},
    ),
    "storm_lantern": Challenge(
        id="storm_lantern",
        goal="carry the lantern through the storm",
        track_verb="track",
        track_noun="lantern sparks",
        obstacle="the rain tried to blow the flame out",
        clue="a line of warm wax drips on the wood",
        feat="guide the light to the safe dock",
        teamwork_need="one pirate to shield the flame while the other steered",
        inner_thought="If I breathe slow, I can keep the light steady.",
        tags={"track", "feat", "teamwork"},
    ),
    "buried_treasure": Challenge(
        id="buried_treasure",
        goal="find the buried treasure",
        track_verb="track",
        track_noun="shell crumbs",
        obstacle="the beach looked flat and empty at first",
        clue="a bright shell half-buried in the sand",
        feat="dig the chest out together",
        teamwork_need="one pirate to point and one pirate to dig",
        inner_thought="The clue is tiny, but tiny clues can still lead home.",
        tags={"track", "feat", "teamwork"},
    ),
}

HEROES = [
    ("Mara", "girl", "young pirate"),
    ("Jory", "boy", "young pirate"),
    ("Nell", "girl", "deckhand"),
    ("Finn", "boy", "deckhand"),
]

SIDEKICKS = [
    ("Pip", "boy", "small pirate"),
    ("Saila", "girl", "small pirate"),
    ("Crewmate Jo", "pirate", "crew mate"),
    ("Rook", "pirate", "crew mate"),
]


@dataclass
class TraceWorld:
    hero: Entity
    sidekick: Entity
    challenge: Challenge
    setting: Setting
    clue_found: bool = False
    teamwork_used: bool = False
    feat_done: bool = False
    track_found: bool = False
    inner_monologue_spoken: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with teamwork and inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CHALLENGES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.challenge:
        combos = [c for c in combos if c[1] == args.challenge]
    if not combos:
        raise StoryError("No valid setting and challenge combination matches the given options.")
    setting, challenge = rng.choice(sorted(combos))
    hero = args.hero or rng.choice([h[0] for h in HEROES])
    sidekick = args.sidekick or rng.choice([s[0] for s in SIDEKICKS if s[0] != hero])
    return StoryParams(setting=setting, challenge=challenge, hero=hero, sidekick=sidekick)


def _hero_lookup(name: str) -> tuple[str, str, str]:
    for h in HEROES:
        if h[0] == name:
            return h
    return (name, "pirate", "young pirate")


def _sidekick_lookup(name: str) -> tuple[str, str, str]:
    for s in SIDEKICKS:
        if s[0] == name:
            return s
    return (name, "pirate", "crew mate")


def tell(params: StoryParams) -> tuple[World, TraceWorld]:
    setting = SETTINGS[params.setting]
    challenge = CHALLENGES[params.challenge]
    hero_name, hero_type, hero_label = _hero_lookup(params.hero)
    side_name, side_type, side_label = _sidekick_lookup(params.sidekick)

    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_label))
    sidekick = world.add(Entity(id=side_name, kind="character", type=side_type, label=side_label))
    trace = TraceWorld(hero=hero, sidekick=sidekick, challenge=challenge, setting=setting)

    hero.meters["courage"] = 1
    sidekick.meters["courage"] = 1

    world.say(
        f"On a bright day at {setting.place}, {hero.id} and {sidekick.id} set out like two small pirates with a big plan."
    )
    world.say(
        f"They wanted to {challenge.goal}, and the whole crew called it a true {challenge.feat}."
    )
    world.say(
        f"{hero.id} stared at {challenge.clue} and thought, \"{challenge.inner_thought}\""
    )

    world.para()
    world.say(
        f"But {challenge.obstacle}. {hero.id} began to {challenge.track_verb} {challenge.track_noun}, while {sidekick.id} watched the path for a safer way."
    )
    trace.track_found = True

    trace.inner_monologue_spoken = True
    hero.memes["hope"] = 1
    hero.memes["focus"] = 1
    sidekick.memes["helpfulness"] = 1

    world.say(
        f"{hero.id} whispered, \"If I follow the little signs, I can still do this.\""
    )
    world.say(
        f"Then {sidekick.id} grinned and said they should split up for a moment, because {challenge.teamwork_need}."
    )
    trace.teamwork_used = True

    world.para()
    world.say(
        f"That teamwork did the trick. {sidekick.id} spotted {challenge.clue}, and {hero.id} followed it to the hiding spot."
    )
    trace.clue_found = True

    hero.meters["effort"] = 1
    sidekick.meters["effort"] = 1

    world.say(
        f"Together they pulled and lifted until the last part of the {challenge.feat} was done."
    )
    trace.feat_done = True

    world.para()
    world.say(
        f"In the end, {hero.id} and {sidekick.id} finished the job, and the crew cheered because the {challenge.goal} was no longer lost."
    )
    world.say(
        f"{hero.id} smiled at {sidekick.id} and thought that the best pirate feats were the ones done together."
    )

    world.facts.update(
        setting=params.setting,
        challenge=params.challenge,
        hero=params.hero,
        sidekick=params.sidekick,
        clue_found=trace.clue_found,
        teamwork_used=trace.teamwork_used,
        feat_done=trace.feat_done,
    )
    return world, trace


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch = CHALLENGES[f["challenge"]]
    return [
        f"Write a short pirate story where a crew must {ch.goal} and solve the problem by working together.",
        f"Tell a child-friendly pirate tale that uses the words 'feat' and 'track' and ends with a happy win.",
        f"Write a story about two pirates who follow clues, listen to their thoughts, and finish a brave {ch.feat}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    ch = CHALLENGES[f["challenge"]]
    return [
        QAItem(
            question=f"What did {f['hero']} and {f['sidekick']} want to do at first?",
            answer=f"They wanted to {ch.goal}.",
        ),
        QAItem(
            question=f"What did {f['hero']} think to themself while trying to solve the problem?",
            answer=f"{_hero_lookup(f['hero'])[0]} thought, \"{ch.inner_thought}\"",
        ),
        QAItem(
            question=f"How did the pirates make the {ch.feat} happen?",
            answer=f"They worked together, followed the clue, and used teamwork to finish the job.",
        ),
        QAItem(
            question=f"What clue helped them keep going?",
            answer=f"The clue was {ch.clue}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to get something done.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking someone does in their own mind.",
        ),
        QAItem(
            question="What is a feat?",
            answer="A feat is a hard or impressive thing someone manages to do.",
        ),
        QAItem(
            question="What does it mean to track a clue?",
            answer="To track a clue means to follow signs, marks, or hints to find something.",
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


def dump_trace(world: TraceWorld) -> str:
    return "\n".join(
        [
            "--- trace ---",
            f"hero: {world.hero.id} meters={world.hero.meters} memes={world.hero.memes}",
            f"sidekick: {world.sidekick.id} meters={world.sidekick.meters} memes={world.sidekick.memes}",
            f"setting: {world.setting.place}",
            f"challenge: {world.challenge.id}",
            f"clue_found: {world.clue_found}",
            f"teamwork_used: {world.teamwork_used}",
            f"feat_done: {world.feat_done}",
            f"track_found: {world.track_found}",
            f"inner_monologue_spoken: {world.inner_monologue_spoken}",
        ]
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("goal", cid, ch.goal))
        lines.append(asp.fact("track", cid, ch.track_verb))
        lines.append(asp.fact("feat", cid, ch.feat))
    return "\n".join(lines)


ASP_RULES = r"""
trackable(C) :- challenge(C).
teamwork(C) :- challenge(C).
featful(C) :- feat(C,_), track(C,_).
good_story(S,C) :- setting(S), challenge(C), trackable(C), teamwork(C), featful(C).
#show good_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world, trace = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=trace,
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
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for s, c in combos:
            print(f"  {s:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for c in CHALLENGES:
                p = StoryParams(setting=s, challenge=c, hero="Mara", sidekick="Pip")
                samples.append(generate(p))
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
