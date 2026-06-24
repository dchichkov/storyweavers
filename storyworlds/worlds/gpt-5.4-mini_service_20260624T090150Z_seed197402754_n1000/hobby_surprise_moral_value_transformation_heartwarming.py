#!/usr/bin/env python3
"""
A story world about a small hobby that grows into a warm surprise, a shared moral
choice, and a gentle transformation.

Domain premise:
A child loves a hobby, expects an ordinary day, receives a surprise that changes
the plan, and learns a warm moral value through helping someone else.

This script keeps the story grounded in world state:
- a hobby can create delight and skill
- a surprise can shift emotions and expectations
- a moral choice can repair hurt feelings or loneliness
- a transformation is shown by changed actions, not by narration only
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Hobby:
    id: str
    verb: str
    gerund: str
    tool: str
    delight: str
    skill: str
    surprise_tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    giver: str
    effect: str
    reveal: str
    warms: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralChoice:
    id: str
    value: str
    act: str
    benefit: str
    repair: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting("the kitchen", indoor=True, affords={"craft", "bake"}),
    "porch": Setting("the porch", indoor=False, affords={"craft"}),
    "library_corner": Setting("the library corner", indoor=True, affords={"read", "craft"}),
    "garden_table": Setting("the garden table", indoor=False, affords={"craft"}),
}

HOBBIES = {
    "paper_boats": Hobby(
        id="paper_boats",
        verb="fold paper boats",
        gerund="folding paper boats",
        tool="colored paper",
        delight="the paper boats floated like tiny dreams",
        skill="careful hands",
        surprise_tag="paper",
        tags={"hobby", "paper", "craft"},
    ),
    "bracelets": Hobby(
        id="bracelets",
        verb="make bead bracelets",
        gerund="stringing bead bracelets",
        tool="bright beads",
        delight="the beads clicked like a happy song",
        skill="patient fingers",
        surprise_tag="beads",
        tags={"hobby", "beads", "craft"},
    ),
    "birdhouses": Hobby(
        id="birdhouses",
        verb="paint tiny birdhouses",
        gerund="painting tiny birdhouses",
        tool="small brushes",
        delight="the colors turned the wood into a little cheerful home",
        skill="steady strokes",
        surprise_tag="paint",
        tags={"hobby", "paint", "craft"},
    ),
}

SURPRISES = {
    "gift_paper": Surprise(
        id="gift_paper",
        label="a roll of shiny paper",
        phrase="a roll of shiny paper",
        giver="Grandma",
        effect="excited",
        reveal="had tucked it inside a brown envelope",
        warms="it would be used for a new batch of boats",
        tags={"paper", "gift", "hobby"},
    ),
    "gift_beads": Surprise(
        id="gift_beads",
        label="a jar of rainbow beads",
        phrase="a jar of rainbow beads",
        giver="Uncle",
        effect="wide-eyed",
        reveal="had hidden it under a tea towel",
        warms="it would help make bracelets for everyone",
        tags={"beads", "gift", "hobby"},
    ),
    "gift_paint": Surprise(
        id="gift_paint",
        label="a box of paint sticks",
        phrase="a box of paint sticks",
        giver="Auntie",
        effect="surprised",
        reveal="had wrapped it in a ribbon",
        warms="it would brighten every little birdhouse",
        tags={"paint", "gift", "hobby"},
    ),
}

MORALS = {
    "share": MoralChoice(
        id="share",
        value="kindness",
        act="share the hobby tools",
        benefit="someone else could join in",
        repair="it turned a lonely moment into a shared one",
        tags={"share", "kindness", "hobby"},
    ),
    "help": MoralChoice(
        id="help",
        value="helpfulness",
        act="help finish the project",
        benefit="the other person would not feel stuck",
        repair="it made the room feel warmer and calmer",
        tags={"help", "kindness", "hobby"},
    ),
    "include": MoralChoice(
        id="include",
        value="inclusion",
        act="invite the shy child to join",
        benefit="the shy child would feel welcome",
        repair="it changed the story from one child alone to two children smiling",
        tags={"include", "kindness", "hobby"},
    ),
}

NAMES = ["Lily", "Mia", "Ava", "Nora", "Ivy", "Ben", "Leo", "Milo", "Noah", "Theo"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["curious", "gentle", "patient", "cheerful", "shy", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    hobby: str
    surprise: str
    moral: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming hobby story with surprise, moral value, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hobby", choices=HOBBIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=PARENTS)
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HOBBIES.items():
        lines.append(asp.fact("hobby", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("hobby_tag", hid, t))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("surprise_tag", sid, t))
    for mid, m in MORALS.items():
        lines.append(asp.fact("moral", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("moral_tag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,H,Su,M) :- setting(S), hobby(H), surprise(Su), moral(M),
    hobby_tag(H,T), surprise_tag(Su,T), moral_tag(M,T).
#show compatible/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def reasonableness_gate(setting: Setting, hobby: Hobby, surprise: Surprise, moral: MoralChoice) -> bool:
    tags = hobby.tags | surprise.tags | moral.tags
    return bool(tags & {"hobby"}) and bool(tags & (hobby.tags | {"gift"}))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HOBBIES:
            for su in SURPRISES:
                for m in MORALS:
                    if reasonableness_gate(SETTINGS[s], HOBBIES[h], SURPRISES[su], MORALS[m]):
                        combos.append((s, h, su, m))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hobby is None or c[1] == args.hobby)
              and (args.surprise is None or c[2] == args.surprise)
              and (args.moral is None or c[3] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hobby, surprise, moral = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[:5] if gender == "girl" else NAMES[5:])
    helper = args.helper or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, hobby, surprise, moral, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    hobby = HOBBIES[params.hobby]
    surprise = SURPRISES[params.surprise]
    moral = MORALS[params.moral]

    child.memes["joy"] = 1
    child.memes["anticipation"] = 1
    world.say(f"{child.id} was a {params.trait} {child.type} who loved {hobby.gerund}.")
    world.say(f"{child.pronoun('possessive').capitalize()} favorite tool was {hobby.tool}, and {hobby.delight}.")
    world.para()
    world.say(f"One day at {world.setting.place}, {child.id} was busy with {hobby.gerund} when a surprise arrived.")
    world.say(f"{surprise.giver} {surprise.reveal}, and there was {surprise.phrase}.")
    child.memes["surprised"] = 1
    child.memes["joy"] += 1
    world.say(f"{child.id} felt {surprise.effect}, because {surprise.warms}.")
    world.para()
    if moral.id == "share":
        world.say(f"Then {child.id} saw a smaller child watching quietly.")
        world.say(f"{child.id} chose to {moral.act}, so {moral.benefit}.")
        child.memes["kindness"] = 1
    elif moral.id == "help":
        world.say(f"Then {child.id} noticed {helper.id} needed a hand.")
        world.say(f"{child.id} chose to {moral.act}, so {moral.benefit}.")
        child.memes["helpfulness"] = 1
    else:
        world.say(f"Then {child.id} noticed a shy child standing by the door.")
        world.say(f"{child.id} chose to {moral.act}, so {moral.benefit}.")
        child.memes["inclusion"] = 1
    world.para()
    child.meters["skill"] = 1
    child.meters["warmth"] = 1
    world.say(f"By the end, {child.id} was no longer only practicing a hobby.")
    world.say(f"{child.pronoun().capitalize()} was {hobby.gerund} with a bigger heart, and {moral.repair}.")
    world.say(f"The little project had become a warm transformation: {child.id} smiled as the finished work sat shining nearby.")
    world.facts.update(child=child, helper=helper, hobby=hobby, surprise=surprise, moral=moral, setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    hobby = f["hobby"]
    surprise = f["surprise"]
    moral = f["moral"]
    return [
        f'Write a heartwarming story for a young child about the hobby of {hobby.gerund}.',
        f'Write a gentle story where {child.id} gets a surprise involving {surprise.phrase} and learns about {moral.value}.',
        f'Write a short story with a clear transformation: a hobby becomes a shared, kinder moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    hobby = f["hobby"]
    surprise = f["surprise"]
    moral = f["moral"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What hobby did {child.id} love at the start of the story?",
            answer=f"{child.id} loved {hobby.gerund}. The hobby used {hobby.tool} and made {hobby.delight}.",
        ),
        QAItem(
            question=f"What surprise arrived while {child.id} was at {world.setting.place}?",
            answer=f"{surprise.giver} brought {surprise.phrase}, and it made {child.id} feel surprised and happy.",
        ),
        QAItem(
            question=f"What moral choice did {child.id} make near the end?",
            answer=f"{child.id} chose {moral.act}. That meant {moral.benefit}, and it showed {moral.value}.",
        ),
        QAItem(
            question=f"How did the story transform by the end?",
            answer=f"It transformed from one child quietly doing a hobby into a warmer scene where {child.id} shared care and the room felt brighter.",
        ),
        QAItem(
            question=f"Who helped make the story feel more caring?",
            answer=f"{helper.id} was the helper in the story, and {child.id}'s choice made the moment feel kind and complete.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    hobby = f["hobby"]
    surprise = f["surprise"]
    moral = f["moral"]
    out = [
        QAItem(
            question="What is a hobby?",
            answer="A hobby is something a person likes to do in their free time because it feels fun, calm, or interesting.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone stop, look, and feel a sudden change in emotion.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind idea like kindness, helping, or sharing that guides good choices.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or feeling over time.",
        ),
    ]
    if "paper" in hobby.tags:
        out.append(QAItem(question="Why can paper be useful for a hobby?", answer="Paper is light, easy to fold, and good for making shapes and little projects."))
    if "gift" in surprise.tags:
        out.append(QAItem(question="Why can a gift feel warm?", answer="A gift can feel warm because it shows someone was thinking carefully about another person."))
    if moral.id == "share":
        out.append(QAItem(question="Why is sharing a good moral choice?", answer="Sharing is good because it helps other people join in and feel included."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams("kitchen", "paper_boats", "gift_paper", "share", "Lily", "girl", "grandma", "gentle"),
    StoryParams("porch", "bracelets", "gift_beads", "help", "Ben", "boy", "mother", "curious"),
    StoryParams("library_corner", "birdhouses", "gift_paint", "include", "Mia", "girl", "father", "thoughtful"),
]


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    clingo = set(asp_compatible())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - clingo))
    print("only clingo:", sorted(clingo - py))
    return 1


def asp_valid_combos() -> list[tuple]:
    return asp_compatible()


def asp_program_full(show: str) -> str:
    return asp_program(show)


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.hobby} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting or args.hobby or args.surprise or args.moral:
        combos = [c for c in combos
                  if (args.setting is None or c[0] == args.setting)
                  and (args.hobby is None or c[1] == args.hobby)
                  and (args.surprise is None or c[2] == args.surprise)
                  and (args.moral is None or c[3] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hobby, surprise, moral = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES[:5] if gender == "girl" else NAMES[5:])
    helper = args.helper or rng.choice(PARENTS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, hobby, surprise, moral, name, gender, helper, trait)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HOBBIES:
            for su in SURPRISES:
                for m in MORALS:
                    if reasonableness_gate(SETTINGS[s], HOBBIES[h], SURPRISES[su], MORALS[m]):
                        combos.append((s, h, su, m))
    return combos


if __name__ == "__main__":
    main()
