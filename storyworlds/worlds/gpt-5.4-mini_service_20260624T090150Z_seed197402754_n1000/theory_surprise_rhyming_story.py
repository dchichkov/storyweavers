#!/usr/bin/env python3
"""
storyworlds/worlds/theory_surprise_rhyming_story.py
====================================================

A tiny, self-contained story world in a rhyming, child-facing style.

Premise:
A curious child makes a theory about a surprise that seems to be hiding at
home. The world model tracks their clues, guessing, effort, and delight, and
the ending reveals that the theory was right in a sweet, surprising way.
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
    plural: bool = False
    owner: Optional[str] = None
    hidden: bool = False
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
    place: str


@dataclass
class Clue:
    id: str
    label: str
    rhyme: str
    meter_key: str
    meme_key: str
    theory_hint: str


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    joy: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _rule_think(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("wonder", 0) >= 1 and "theory" not in world.fired:
        world.fired.add("theory")
        child.memes["theory"] = child.memes.get("theory", 0) + 1
        out.append("A little theory blossomed bright, like a star in the night.")
    return out


def _rule_find(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    for clue_id in world.facts["clue_order"]:
        clue = world.facts["clues"][clue_id]
        if child.meters.get(clue.meter_key, 0) >= 1 and clue_id not in world.fired:
            world.fired.add(clue_id)
            child.memes["confidence"] = child.memes.get("confidence", 0) + 1
            out.append(f"{child.id} spotted the {clue.label}, tidy and bright, and smiled with delight.")
    return out


RULES = [Rule("think", _rule_think), Rule("find", _rule_find)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    for s in produced:
        world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    clue: str
    surprise: str
    place: str = "home"
    seed: Optional[int] = None


CHILD_NAMES = ["Mia", "Lily", "Nora", "Theo", "Ben", "Max", "Ava", "Zoe"]
PARENTS = {"mother": "mother", "father": "father"}

SETTINGS = {
    "home": Setting(place="home"),
    "kitchen": Setting(place="kitchen"),
    "garden": Setting(place="garden"),
    "playroom": Setting(place="playroom"),
}

CLUES = {
    "crumb": Clue("crumb", "crumb trail", "crumbs on the floor", "crumbs", "wonder", "maybe something sweet was near"),
    "ribbon": Clue("ribbon", "ribbon loop", "a ribbon red and bright", "ribbon", "wonder", "maybe a gift was tucked away"),
    "giggle": Clue("giggle", "tiny giggle", "a giggle soft and light", "giggle", "wonder", "maybe a friend was hiding close"),
}

SURPRISES = {
    "cake": Surprise("cake", "birthday cake", "a birthday cake", "a candlelit cake", "a sweet surprise"),
    "puppy": Surprise("puppy", "puppy pal", "a puppy in a bow", "a fluffy puppy friend", "a happy surprise"),
    "book": Surprise("book", "picture book", "a picture book", "a storybook surprise", "a cozy surprise"),
}


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("meter_key", cid, clue.meter_key))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,C,S) :- place(P), clue(C), surprise(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c, s) for p in SETTINGS for c in CLUES for s in SURPRISES}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming surprise story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.clue and args.surprise is None:
        pass
    choices = [(p, c, s) for p in SETTINGS for c in CLUES for s in SURPRISES]
    if args.place:
        choices = [x for x in choices if x[0] == args.place]
    if args.clue:
        choices = [x for x in choices if x[1] == args.clue]
    if args.surprise:
        choices = [x for x in choices if x[2] == args.surprise]
    if not choices:
        raise StoryError("No valid story matches those options.")
    place, clue, surprise = rng.choice(sorted(choices))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(name=name, gender=gender, parent=parent, clue=clue, surprise=surprise, place=place)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    clue = CLUES[params.clue]
    surprise = SURPRISES[params.surprise]
    world.facts["clues"] = {clue.id: clue}
    world.facts["clue_order"] = [clue.id]
    world.facts["surprise"] = surprise
    world.facts["child"] = child
    world.facts["parent"] = parent

    world.say(f"{params.name} was small and spry, with curious eyes so wide.")
    world.say(f"{params.name} loved a rhyme and a reason, a question tucked inside.")
    world.say(f"“I have a theory,” {params.name} would say, “about the hush I hear tonight.”")
    child.memes["wonder"] = 1
    child.memes["theory"] = 1
    propagate(world)

    world.para()
    world.say(f"At {world.setting.place}, {params.name} found a {clue.label}, neat and fine.")
    child.meters[clue.meter_key] = child.meters.get(clue.meter_key, 0) + 1
    world.say(f"That clue did chime like a tiny rhyme: “Look here, sweet one, look here in line.”")
    propagate(world)
    world.say(f"{params.name} grinned and twirled with glee, and followed the clue so bright.")
    child.memes["confidence"] = child.memes.get("confidence", 0) + 1

    world.para()
    world.say(f"Then came a pause, a hush, a wait, a door left closed just right.")
    world.say(f"{params.parent.capitalize()} smiled and said, “Keep peeking, dear, but peep with care and light.”")
    world.say(f"{params.name} leaned near, with breath held still, and guessed the hidden plan.")
    world.say(f"“My theory says a {surprise.label} is here,” {params.name} said, “or maybe tucked by hand.”")

    child.memes["hope"] = child.memes.get("hope", 0) + 1
    if clue.id == "giggle":
        child.meters["listened"] = 1
    elif clue.id == "ribbon":
        child.meters["looked"] = 1
    else:
        child.meters["searched"] = 1
    propagate(world)

    world.para()
    child.memes["surprise_ready"] = 1
    world.say(f"At last the door swung open wide, and oh, what a sight to see!")
    world.say(f"There was {surprise.reveal}, a shining surprise, as happy as could be.")
    world.say(f"{params.name} clapped and laughed, then hugged {params.parent} tight with delight.")
    world.say(f"The theory was true, the guess was right, and the whole room glowed that night.")
    child.memes["joy"] = child.memes.get("joy", 0) + 2
    child.memes["surprised"] = 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["surprise"]
    c = world.facts["clue"]
    return [
        f'Write a short rhyming story for a child who says “theory” and finds a {c.label} clue.',
        f"Tell a surprise story where {p.name} makes a little theory and discovers {s.phrase}.",
        f"Write a gentle rhyming tale about a hidden surprise, a clue, and a happy guess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    clue: Clue = world.facts["clue"]
    surprise: Surprise = world.facts["surprise"]
    return [
        QAItem(
            question=f"What was {p.name}'s theory about?",
            answer=f"{p.name}'s theory was that a {surprise.label} was hidden nearby, and the clue pointed them in the right direction.",
        ),
        QAItem(
            question=f"What clue did {p.name} find?",
            answer=f"{p.name} found a {clue.label}, which helped the guess grow stronger.",
        ),
        QAItem(
            question=f"What surprise was waiting at the end?",
            answer=f"The surprise was {surprise.reveal}, and it made {p.name} feel joyful and amazed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a theory?", answer="A theory is a guess about why something is happening or what might be hidden, based on clues."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that makes someone stop and feel wonder or delight."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos:")
        for x in combos:
            print(x)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for clue in CLUES:
                for surprise in SURPRISES:
                    params = StoryParams(
                        name="Mia",
                        gender="girl",
                        parent="mother",
                        clue=clue,
                        surprise=surprise,
                        place=place,
                    )
                    samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
