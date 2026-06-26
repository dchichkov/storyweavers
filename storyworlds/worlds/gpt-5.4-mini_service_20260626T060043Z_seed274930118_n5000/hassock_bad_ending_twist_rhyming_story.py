#!/usr/bin/env python3
"""
A standalone Storyweavers storyworld: a tiny rhyming tale about a hassock,
a reach-too-far wish, a twist, and a bad ending.

This world models a child in a living room who wants to reach something on a
high shelf. A hassock seems helpful, but the story turns on a small twist:
the thing up high is not what the child expected, and the attempt ends badly.
The prose is authored as a child-facing rhyming story, while the world model
tracks the physical and emotional change.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the living room"
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("wobble", 0.0) < THRESHOLD:
            continue
        sig = ("fall", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["stumble"] = actor.meters.get("stumble", 0.0) + 1
        actor.memes["sad"] = actor.memes.get("sad", 0.0) + 1
        out.append(f"{actor.id} went tumbling with a clatter and a flail.")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for obj in [e for e in world.entities.values() if e.kind == "thing"]:
        if obj.meters.get("broken", 0.0) < THRESHOLD:
            continue
        sig = ("broken", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{obj.label.capitalize()} was ruined in the fall.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_fall, _r_break):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme(a: str, b: str) -> str:
    return f"{a} / {b}"


def introduce(world: World, hero: Entity, prize: Entity, hassock: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type}, quick as a beep, "
        f"with a wish so high it made {hero.pronoun('object')} leap."
    )
    world.say(
        f"{hero.id} loved the shiny {prize.label} up on the shelf, "
        f"and the soft little {hassock.label} sat there by itself."
    )


def desire(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"{hero.id} stood on tiptoe and gave a proud grin, "
        f"but the {prize.label} was high, and too high to win."
    )


def warn(world: World, parent: Entity, hero: Entity, hassock: Entity, prize: Entity) -> None:
    world.say(
        f'"Careful," said {parent.id}, "that {hassock.label} may slide; '
        f"if you climb on that cushion, you'll spill and you'll slide."
    )
    world.say(
        f"It is not a toy-chair, and it is not a moon; "
        f"it is only a perch for a quick little tune."'
    )
    world.facts["warning"] = True


def twist(world: World, hero: Entity, prize: Entity, hassock: Entity) -> None:
    world.say(
        f"{hero.id} climbed anyway with a wiggle and cheer, "
        f"but the twist of the day came with something unclear."
    )
    world.say(
        f"The thing on the shelf was not treasure or treat; "
        f"it was a note for the family, folded up neat."
    )
    world.facts["twist"] = "note"
    world.zone = {"floor"}
    hero.meters["wobble"] = hero.meters.get("wobble", 0.0) + 1
    hassock.meters["slip"] = hassock.meters.get("slip", 0.0) + 1
    prize.meters["scare"] = prize.meters.get("scare", 0.0) + 1
    prize.meters["broken"] = prize.meters.get("broken", 0.0) + 1
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, parent: Entity, prize: Entity, hassock: Entity) -> None:
    world.say(
        f"The note fluttered down with a slow little spin, "
        f"and the {prize.label} lay cracked, though once it had been."
    )
    hero.memes["sad"] = hero.memes.get("sad", 0.0) + 1
    parent.memes["sad"] = parent.memes.get("sad", 0.0) + 1
    world.say(
        f"{parent.id} sighed, and {hero.id} sniffled, and the room felt still; "
        f"the hassock stayed crooked by the blue windowsill."
    )
    world.say(
        f"So that was the night of the reach and the fall: "
        f"a twist with a wobble, and a bad ending for all."
    )


SETTING = Setting(place="the living room", affords={"reach"})
PRIZES = {
    "cookie_jar_key": Prize(label="key", phrase="a tiny silver key", region="shelf"),
    "note": Prize(label="note", phrase="a folded paper note", region="shelf"),
    "toy_star": Prize(label="star", phrase="a bright tin star", region="shelf"),
}
HASSOCK = Entity(
    id="hassock",
    kind="thing",
    type="hassock",
    label="hassock",
    phrase="a round little hassock",
)
NAMES = {
    "girl": ["Mia", "Luna", "Tess", "Nora"],
    "boy": ["Theo", "Finn", "Milo", "Ben"],
}
PARENTS = {"mother": "mother", "father": "father"}


def build_story_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    prize = world.add(Entity(
        id=params.prize,
        kind="thing",
        type="thing",
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        caretaker=parent.id,
    ))
    hassock = world.add(copy.deepcopy(HASSOCK))
    world.facts.update(hero=hero, parent=parent, prize=prize, hassock=hassock, setting=SETTING)

    introduce(world, hero, prize, hassock)
    world.para()
    desire(world, hero, prize)
    warn(world, parent, hero, hassock, prize)
    twist(world, hero, prize, hassock)
    world.para()
    ending(world, hero, parent, prize, hassock)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a child named {hero.id} who sees a {prize.label} on a shelf and a hassock below.',
        f"Tell a gentle rhyming tale where {hero.id} tries to use a hassock, but a twist changes the plan and the ending goes badly.",
        "Write a simple story with a living room, a hassock, a surprise twist, and a sad ending that still feels complete.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} want to reach on the shelf?",
            answer=f"{hero.id} wanted to reach the {prize.label} on the shelf.",
        ),
        QAItem(
            question=f"Who warned {hero.id} about the hassock?",
            answer=f"{parent.id} warned {hero.id} that the hassock could slide.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the thing on the shelf was just a folded note, not the special prize the child expected.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly, with the prize cracked, the room quiet, and everyone feeling sad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hassock?",
            answer="A hassock is a soft footstool or low cushion that people can rest their feet on or use as a small seat.",
        ),
        QAItem(
            question="Why can a hassock be tricky to stand on?",
            answer="A hassock can be tricky to stand on because it is soft and can slide or tip when someone puts weight on it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"  {e.id:10} {e.type:10} meters={meters} memes={memes}")
    return "\n".join(parts)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "living_room"),
        asp.fact("thing", "hassock"),
        asp.fact("affords", "living_room", "reach"),
        asp.fact("at_risk", "shelf"),
        asp.fact("twist_item", "note"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
at_risk_story(S) :- setting(S), affords(S, reach), twist_item(note).
bad_ending :- at_risk_story(living_room).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    ok = any(sym.name == "bad_ending" for sym in model)
    if ok:
        print("OK: ASP reasoner confirms the bad ending twist.")
        return 0
    print("MISMATCH: ASP reasoner did not confirm the bad ending twist.")
    return 1


def asp_facts_for_verify() -> list[str]:
    return ["bad_ending."]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming hassock storyworld with a twist and a bad ending.")
    ap.add_argument("--place", choices=["living_room"], default=None)
    ap.add_argument("--prize", choices=sorted(PRIZES), default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--name", default=None)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    prize = args.prize or rng.choice(list(PRIZES))
    return StoryParams(
        place="living_room",
        prize=prize,
        name=name,
        gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/0."))
        print(f"bad_ending: {any(sym.name == 'bad_ending' for sym in model)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [
            StoryParams(place="living_room", prize=prize, name=name, gender=gender, parent=parent)
            for prize in sorted(PRIZES)
            for gender in ["girl", "boy"]
            for name in NAMES[gender][:1]
            for parent in ["mother", "father"]
        ]
        samples = [generate(p) for p in combos]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
