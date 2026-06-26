#!/usr/bin/env python3
"""
A small whodunit storyworld: a mystery, a tremble of fear, a conflict that
turns on kindness, and sound effects that help reveal the truth.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    inside: bool = False


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    trail: str
    hides: str


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    detective: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "library": Setting("the library", inside=True),
    "kitchen": Setting("the kitchen", inside=True),
    "garden": Setting("the garden", inside=False),
    "hall": Setting("the old hall", inside=True),
}

CLUES = {
    "clock": Clue("clock", "a clock", "tick-tock", "tiny dust by the door", "a late entry"),
    "cup": Clue("cup", "a chipped cup", "clink", "a wet ring on the table", "a hurried spill"),
    "bell": Clue("bell", "a brass bell", "ding", "a bright mark near the shelf", "a secret tap"),
    "shoe": Clue("shoe", "a muddy shoe", "squelch", "mud on the tiles", "a hidden step"),
    "key": Clue("key", "a little key", "jingle", "scratches at the drawer", "a locked box"),
}

SUSPECTS = {
    "cat": "cat",
    "brother": "boy",
    "sister": "girl",
    "neighbor": "woman",
    "gardener": "man",
}

DETECTIVES = {
    "Mina": "girl",
    "Nico": "boy",
    "Ada": "girl",
    "Theo": "boy",
    "June": "girl",
    "Leo": "boy",
}

NAMES_BY_TYPE = {
    "girl": ["Mina", "Ada", "June", "Nora", "Lena"],
    "boy": ["Nico", "Theo", "Leo", "Owen", "Finn"],
    "woman": ["Mrs. Pine", "Ms. Bell"],
    "man": ["Mr. Reed", "Mr. Vale"],
    "cat": ["Muffin", "Pip"],
}


def clue_at_risk(clue: Clue, setting: Setting) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for clue in CLUES:
            for det_name, det_type in DETECTIVES.items():
                for suspect, stype in SUSPECTS.items():
                    if suspect == "cat" and stype != "cat":
                        continue
                    out.append((place, clue, det_name, suspect))
    return out


def introduce(world: World, detective: Entity, clue: Clue, suspect: Entity) -> None:
    world.say(
        f"{detective.id} was a careful little detective who loved quiet rooms and small mysteries."
    )
    world.say(
        f"One evening at {world.setting.place}, {detective.id} heard a strange {clue.sound}."
    )
    world.say(
        f"Nearby, {detective.pronoun('possessive')} eyes fell on {clue.label}, and everyone looked at {suspect.id}."
    )


def tremble(world: World, detective: Entity) -> None:
    detective.memes["fear"] = detective.memes.get("fear", 0) + 1
    detective.meters["tremble"] = detective.meters.get("tremble", 0) + 1
    world.say(f"{detective.id} began to tremble, because the room felt full of clues.")


def conflict(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    detective.memes["conflict"] = detective.memes.get("conflict", 0) + 1
    world.say(
        f'"That sound came from {suspect.id}," {detective.id} said.'
    )
    world.say(
        f"{suspect.id} frowned. \"No, it wasn't me,\" {suspect.pronoun()} said, and the room went quiet."
    )
    world.say(f"The only answer was another {clue.sound} from the next room.")


def kindness(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    detective.memes["kindness"] = detective.memes.get("kindness", 0) + 1
    suspect.memes["kindness"] = suspect.memes.get("kindness", 0) + 1
    detective.memes["conflict"] = 0
    world.say(
        f"Instead of accusing {suspect.id}, {detective.id} took a breath and spoke kindly."
    )
    world.say(
        f'"Let\'s look together," {detective.id} said, softer now. '
        f"{suspect.id} relaxed, because kindness made room for truth."
    )


def reveal(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    world.say(
        f"They followed the {clue.trail} to a tiny drawer."
    )
    world.say(
        f"There, the real answer waited: {clue.label} had been moved by a windy draft, not by {suspect.id}."
    )
    world.say(
        f"{detective.id} smiled, and the last sound was a gentle {clue.sound} as the drawer shut."
    )


def build_story(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    introduce(world, detective, clue, suspect)
    world.para()
    tremble(world, detective)
    conflict(world, detective, suspect, clue)
    world.para()
    kindness(world, detective, suspect, clue)
    reveal(world, detective, suspect, clue)
    world.facts.update(
        detective=detective,
        suspect=suspect,
        clue=clue,
        resolved=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit set in {world.setting.place} with a clue that makes a {f["detective"].id} tremble.',
        f"Tell a mystery story where {f['detective'].id} hears a {f['clue'].sound} and first suspects {f['suspect'].id}, but kindness solves the conflict.",
        f'Write a short story with the word "tremble" that ends with the truth about {f["clue"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det: Entity = f["detective"]
    sus: Entity = f["suspect"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question=f"Why did {det.id} tremble in the story?",
            answer=f"{det.id} trembled because the mystery sounded serious, and the strange {clue.sound} made the room feel full of clues.",
        ),
        QAItem(
            question=f"Who did {det.id} first suspect when the clue turned up at {world.setting.place}?",
            answer=f"{det.id} first suspected {sus.id}, because the clue seemed to point that way at first.",
        ),
        QAItem(
            question="What helped solve the conflict?",
            answer="Kindness helped solve the conflict, because the detective stopped blaming and looked for the truth together with the suspect.",
        ),
        QAItem(
            question=f"What was the real reason for the {clue.sound}?",
            answer=f"The real reason was a windy draft that moved {clue.label}; {sus.id} did not do it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does it mean to tremble?",
            answer="To tremble means to shake a little, often because you feel scared or excited.",
        ),
        QAItem(
            question="Why can kindness help during conflict?",
            answer="Kindness can help because it calms people down and makes it easier to listen and solve problems.",
        ),
        QAItem(
            question="Why do sound effects matter in a whodunit?",
            answer="Sound effects can point to what happened, like a soft ding or a loud clink that becomes an important clue.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} type={e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/4.
valid(P,C,D,S) :- place(P), clue(C), detective(D), suspect(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for d in DETECTIVES:
        lines.append(asp.fact("detective", d))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with tremble, conflict, kindness, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--detective")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.detective:
        combos = [c for c in combos if c[2] == args.detective]
    if args.suspect:
        combos = [c for c in combos if c[3] == args.suspect]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, detective, suspect = rng.choice(sorted(combos))
    return StoryParams(place=place, clue=clue, suspect=suspect, detective=detective)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    clue = CLUES[params.clue]
    det_type = DETECTIVES[params.detective]
    sus_type = SUSPECTS[params.suspect]
    detective = world.add(Entity(id=params.detective, kind="character", type=det_type))
    suspect_name = params.suspect.capitalize() if sus_type == "cat" else params.suspect
    suspect = world.add(Entity(id=suspect_name, kind="character", type=sus_type))
    build_story(world, detective, suspect, clue)
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos[:50]:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for clue in CLUES:
                for detective in DETECTIVES:
                    for suspect in SUSPECTS:
                        params = StoryParams(place=place, clue=clue, suspect=suspect, detective=detective)
                        samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
