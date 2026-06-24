#!/usr/bin/env python3
"""
A small bedtime-story world about a sleepy child, a hush-hush moment, and
cattle resting in the dark while the scent of tamarind lingers nearby.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = False


@dataclass
class Comfort:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    comfort: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "barn": Setting(place="the barn", indoor=True, affords={"blurt", "tamarind"}),
    "stable": Setting(place="the quiet stable", indoor=True, affords={"blurt", "tamarind"}),
    "porch": Setting(place="the porch", indoor=False, affords={"blurt", "tamarind"}),
}

ACTIONS = {
    "blurt": Action(
        id="blurt",
        verb="blurt out the secret",
        gerund="blurting out the secret",
        rush="say it out loud",
        noise="loud",
        danger="wake the cattle",
        keyword="blurt",
        tags={"blurt", "cautionary"},
    ),
    "tamarind": Action(
        id="tamarind",
        verb="taste the tamarind",
        gerund="tasting the tamarind",
        rush="take a big bite",
        noise="sticky",
        danger="make a mess on the blanket",
        keyword="tamarind",
        tags={"tamarind", "sticky"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a little bedside lantern", type="lantern", fragile=True),
    "blanket": Prize(label="blanket", phrase="a soft bedtime blanket", type="blanket"),
    "cup": Prize(label="cup", phrase="a tiny cup of tamarind tea", type="cup", fragile=True),
}

COMFORTS = {
    "whisper": Comfort(id="whisper", label="a whisper", prep="whisper the secret instead of blurt it", tail="went on with a sleepy whisper"),
    "blanket": Comfort(id="blanket", label="the blanket", prep="pull the blanket up and keep the room cozy", tail="snuggled under the blanket and stayed quiet"),
    "lantern": Comfort(id="lantern", label="the lantern", prep="turn the lantern lower so the room felt calm", tail="let the lantern glow softly"),
}

GIRL_NAMES = ["Mina", "Lila", "Tessa", "Nora", "Ivy", "Rosa"]
BOY_NAMES = ["Milo", "Eli", "Noah", "Owen", "Theo", "Ben"]
TRAITS = ["sleepy", "gentle", "curious", "small", "cautious", "dreamy"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                for comfort in COMFORTS:
                    if act == "blurt" and comfort in {"whisper", "lantern"}:
                        out.append((place, act, prize, comfort))
                    if act == "tamarind" and comfort in {"blanket", "lantern"}:
                        out.append((place, act, prize, comfort))
    return out


def build_story(world: World, params: StoryParams) -> World:
    setting = world.setting
    act = ACTIONS[params.action]
    prize = world.add(Entity(id="Prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={"sleepy": 1.0}, memes={"worry": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="mom" if params.parent == "mother" else "dad"))
    cattle = world.add(Entity(id="Cattle", kind="character", type="cattle", plural=True, label="the cattle"))
    comfort = COMFORTS[params.comfort]

    world.facts.update(child=child, parent=parent, prize=prize, cattle=cattle, action=act, comfort=comfort)

    world.say(f"{child.id} was a {child.pronoun('possessive')} little sleepy {child.type} who loved the soft hush of bedtime.")
    world.say(f"That night, {child.id} could smell tamarind in the kitchen and hear the cattle resting in the barn.")
    world.say(f"{child.id} held {child.pronoun('possessive')} {prize.label} and thought about {act.gerund}, even though it was getting late.")

    world.para()
    world.say(f"At {setting.place}, {child.id} almost wanted to {act.rush}.")
    world.say(f"But {child.id}'s inner monologue was careful: \"If I {act.verb}, I might {act.danger}.\"")
    world.say(f"{parent.label} gave a gentle cautionary smile and said, \"Tonight, let’s be soft and keep our voices small.\"")
    child.memes["caution"] = child.memes.get("caution", 0.0) + 1.0
    child.memes["control"] = child.memes.get("control", 0.0) + 1.0

    world.para()
    if params.action == "blurt":
        world.say(f"{child.id} swallowed the big words and chose {comfort.label} instead.")
    else:
        world.say(f"{child.id} looked at the sticky tamarind and decided to enjoy it very slowly.")
    world.say(f"That way, {child.id} could stay cozy and not {act.danger}.")
    world.say(f"{parent.label} nodded, and the cattle kept resting, calm as moonlit stones.")
    world.say(f"In the end, {child.id} {comfort.tail}, and bedtime felt safe and sweet.")
    child.memes["peace"] = 1.0
    child.meters["hungry"] = 0.0
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    act = f["action"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"Who was trying not to {act.verb} at bedtime?",
            answer=f"{child.id} was trying not to {act.verb} at bedtime, because {child.id} wanted the night to stay calm."
        ),
        QAItem(
            question=f"Why did {child.id} think twice before {act.gerund}?",
            answer=f"{child.id}'s inner monologue warned that it could {act.danger}, so {child.id} chose a quieter way."
        ),
        QAItem(
            question=f"What did {parent.label} suggest to help?",
            answer=f"{parent.label} suggested {comfort.prep}, which helped {child.id} stay safe and sleepy."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are cattle?",
            answer="Cattle are large farm animals, like cows and bulls, that often stay calm in a barn or field."
        ),
        QAItem(
            question="What is tamarind?",
            answer="Tamarind is a sour-sweet fruit with sticky pulp that people use in drinks, candies, and sauces."
        ),
        QAItem(
            question="What does it mean to blurt something out?",
            answer="To blurt something out means to say it all at once without stopping to think or whisper first."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a bedtime story about {f['child'].id}, cattle resting nearby, and a tamarind moment that calls for a whisper.",
        f"Tell a cautionary story where a child nearly blurts out a secret but chooses a gentle bedtime action instead.",
        f"Write a small, dreamy story with inner monologue, tamarind, and quiet cattle in the background.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
cautionary(A) :- action(A), tags(A,cautionary).
quiet_fix(C) :- comfort(C), label(C,"a whisper").
quiet_fix(C) :- comfort(C), label(C,"the blanket").
good_story(P,A,C) :- setting(P), action(A), comfort(C), cautionary(A), quiet_fix(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", aid, t))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        lines.append(asp.fact("label", cid, c.label))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world with cattle, blurt, and tamarind.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--comfort", choices=COMFORTS)
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
    combos = valid_combos()
    if args.action and args.comfort:
        if (args.place, args.action, args.prize, args.comfort) not in combos:
            raise StoryError("No reasonable bedtime story matches those choices.")
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if args.action is None or c[1] == args.action
              if args.prize is None or c[2] == args.prize
              if args.comfort is None or c[3] == args.comfort]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, action, prize, comfort = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, action=action, prize=prize, comfort=comfort, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    build_story(world, params)
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


CURATED = [
    StoryParams(place="barn", action="blurt", prize="blanket", comfort="whisper", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="stable", action="tamarind", prize="cup", comfort="blanket", name="Theo", gender="boy", parent="father"),
    StoryParams(place="porch", action="blurt", prize="lantern", comfort="lantern", name="Ivy", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for row in combos:
            print(row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
