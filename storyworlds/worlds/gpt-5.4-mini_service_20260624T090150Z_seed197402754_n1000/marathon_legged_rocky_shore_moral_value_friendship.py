#!/usr/bin/env python3
"""
A small storyworld about a rocky-shore marathon, where a legged runner learns
that friendship matters more than winning. The stories are fable-like, suspenseful,
and child-facing, with world state driving the turn and ending.
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
    name: str = ""
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"hare", "fox", "dog", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"deer", "bird", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.name or self.type


@dataclass
class Setting:
    place: str = "the rocky shore"
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    turn: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Moral:
    id: str
    lesson: str
    reveal: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.suspense: float = 0.0
        self.ending_image: str = ""

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


SETTINGS = {
    "rocky_shore": Setting(place="the rocky shore", affords={"marathon"}),
}

EVENTS = {
    "marathon": Event(
        id="marathon",
        verb="run the marathon",
        gerund="running the marathon",
        rush="dash along the shore path",
        risk="slip on the wet rocks",
        turn="slow down and ask for help",
        zone={"feet", "legs"},
        tags={"marathon", "rocky", "shore", "suspense"},
    )
}

PRIZES = {
    "cup": Prize(
        id="cup",
        label="cup",
        phrase="a shiny silver cup",
        type="cup",
        region="paws",
    ),
    "ribbon": Prize(
        id="ribbon",
        label="ribbon",
        phrase="a bright blue ribbon",
        type="ribbon",
        region="neck",
    ),
}

MORALS = {
    "friendship": Moral(
        id="friendship",
        lesson="A friend who helps you is worth more than a prize.",
        reveal="the best win was staying together",
        tags={"friendship"},
    )
}

NAMES = ["Pip", "Milo", "Tara", "June", "Nina", "Bram", "Luna", "Otto"]
TYPES = ["hare", "fox", "deer", "dog", "bird"]
TRAITS = ["quick", "kind", "brave", "bright", "gentle"]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("risk_zone", eid, "legs"))
        lines.append(asp.fact("risk_zone", eid, "feet"))
        for t in sorted(e.tags):
            lines.append(asp.fact("tag", eid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S,E,P,M) :- affords(S,E), event(E), prize(P), moral(M), tag(E, marathon), tag(E, shore), tag(M, friendship).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("rocky_shore", "marathon", "cup", "friendship"), ("rocky_shore", "marathon", "ribbon", "friendship")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like rocky shore marathon storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=TYPES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random):
    if args.place and args.place != "rocky_shore":
        raise StoryError("This world only happens on the rocky shore.")
    place = args.place or "rocky_shore"
    event = args.event or "marathon"
    prize = args.prize or rng.choice(list(PRIZES))
    moral = args.moral or "friendship"
    name = args.name or rng.choice(NAMES)
    typ = args.type or rng.choice(TYPES)
    trait = args.trait or rng.choice(TRAITS)
    if event != "marathon":
        raise StoryError("Only the marathon tale is available here.")
    return StoryParams(place=place, event=event, prize=prize, moral=moral, name=name, type=typ, trait=trait)


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    moral: str
    name: str
    type: str
    trait: str
    seed: Optional[int] = None


def _start(world: World, hero: Entity, rival: Entity, prize: Entity, event: Event) -> None:
    world.say(
        f"On the rocky shore, {hero.noun()} was a {hero.pronoun('possessive')} "
        f"{hero.type} with swift legs and a {hero.meters.get('speed', 0):.0f} kind heart, "
        f"and {rival.noun()} was always near."
    )
    world.say(
        f"Every day, {hero.noun()} loved {event.gerund} along the salt-sparkled path, "
        f"where the waves clapped like little drums."
    )
    world.say(
        f"They had come for a grand marathon, and {prize.label} shone at the finish stone."
    )


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.type, name=params.name, label=params.name))
    rival = world.add(Entity(id="rival", kind="character", type="fox", name="Rill", label="Rill"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label))
    moral = MORALS[params.moral]
    event = EVENTS[params.event]
    hero.meters["speed"] = 2
    hero.memes["friendship"] = 1
    rival.meters["speed"] = 2
    world.facts.update(hero=hero, rival=rival, prize=prize, moral=moral, event=event, setting=setting)
    _start(world, hero, rival, prize, event)

    world.para()
    world.suspense = 1.0
    world.say(
        f"When the race began, dark clouds slid over the sea, and a slick shine covered the rocks."
    )
    world.say(
        f"{hero.noun()} hurried forward, but one wrong step could make {hero.pronoun('object')} {event.risk}."
    )
    world.say(
        f"Rill noticed the trouble and whispered, 'The shore is tricky today.'"
    )

    world.para()
    hero.memes["worry"] = 1
    rival.memes["care"] = 1
    world.say(
        f"Near the sharp bend, {hero.noun()} saw {rival.noun()} stumble and nearly fall."
    )
    world.say(
        f"{hero.noun()} could still race for {prize.label}, but now the finish felt far away."
    )
    world.say(
        f"Then {hero.noun()} remembered that a friend should not be left behind."
    )
    hero.memes["choice"] = 1
    world.suspense = 2.0

    world.para()
    world.say(
        f"{hero.noun()} turned back and chose to {event.turn}, even though the cup was waiting."
    )
    rival.memes["relief"] = 1
    hero.memes["friendship"] = 2
    world.say(
        f"Together they stepped from rock to rock, and each careful step was safer than a lonely dash."
    )
    world.say(
        f"At last they reached the finish stone side by side."
    )
    world.ending_image = f"{hero.noun()} and {rival.noun()} stood together by the sea, while {prize.label} stayed on the stone."
    world.say(
        f"The crowd cheered for their kindness more than for speed, and {moral.reveal}."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short fable about a marathon on a rocky shore where friendship matters more than winning.',
        f"Tell a suspenseful story about {hero.noun()} the {hero.type} choosing between a prize and a friend.",
        "Write a child-friendly moral tale set on the rocky shore with a risky race and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    prize = f["prize"]
    qa = [
        QAItem(
            question=f"Where did {hero.noun()} race?",
            answer="They raced on the rocky shore, where the wet stones made every step careful.",
        ),
        QAItem(
            question=f"What was the big event in the story?",
            answer="It was a marathon, and the runners had to keep going along the shore path.",
        ),
        QAItem(
            question=f"What did {hero.noun()} almost lose by stopping?",
            answer=f"{hero.pronoun('possessive').capitalize()} chance to win the {prize.label} was almost lost, because the finish was waiting ahead.",
        ),
        QAItem(
            question=f"Why did {hero.noun()} turn back for {rival.noun()}?",
            answer="Because the story taught that friendship is more important than winning alone.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marathon?",
            answer="A marathon is a long race where runners keep going for a very long time.",
        ),
        QAItem(
            question="What does it mean for rocks to be slippery?",
            answer="Slippery rocks are hard to stand on because feet can slide on them.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is being kind, helping each other, and staying close when things are hard.",
        ),
        QAItem(
            question="Why can a story have suspense?",
            answer="A story has suspense when the reader wonders what will happen next.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"suspense={world.suspense}")
    lines.append(f"ending_image={world.ending_image}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="rocky_shore", event="marathon", prize="cup", moral="friendship", name="Pip", type="hare", trait="quick"),
    StoryParams(place="rocky_shore", event="marathon", prize="ribbon", moral="friendship", name="Luna", type="deer", trait="brave"),
]


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base + i
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
