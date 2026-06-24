#!/usr/bin/env python3
"""
storyworlds/worlds/tortilla_dog_dim_cheetah_moral_value_inner.py
================================================================

A standalone storyworld about a small adventure mystery: a child, a tortilla,
a dim dog-guide, and a cheetah who may be quick, curious, or helpful. The world
tracks physical meters and emotional memes, lets inner monologue steer choices,
and resolves a simple mystery with a moral turn.

Seed idea:
- A tortilla goes missing before a little adventure.
- The child, with a dim dog companion, follows clues around a small setting.
- A cheetah appears as a fast witness, rival, or helper.
- The ending proves a moral value: honesty, sharing, or caring for others.

This file is self-contained and follows the Storyweavers storyworld contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORALS = {"honesty", "sharing", "kindness"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    dark_spot: str
    clue_spots: list[str]
    safe_paths: list[str]


@dataclass
class Mystery:
    id: str
    question: str
    reveal: str
    moral: str
    clue_kind: str
    solve_kind: str


@dataclass
class Helper:
    id: str
    label: str
    mood: str
    skill: str


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    innocent_reason: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    mystery: str
    helper: str
    suspect: str
    hero_name: str
    hero_type: str
    cheetah_name: str
    cheetah_type: str
    dog_name: str
    seed: Optional[int] = None


SETTINGS = {
    "market": Setting(
        place="the open market",
        dark_spot="the shadow under the fruit stall",
        clue_spots=["the fruit stall", "the bakery cart", "the fountain step"],
        safe_paths=["the wide path", "the stone arch", "the sunny lane"],
    ),
    "harbor": Setting(
        place="the little harbor",
        dark_spot="the shadow by the rope pile",
        clue_spots=["the rope pile", "the pier post", "the fish crate"],
        safe_paths=["the boardwalk", "the dock edge", "the bright steps"],
    ),
    "garden": Setting(
        place="the garden path",
        dark_spot="the shade beneath the fig tree",
        clue_spots=["the fig tree", "the gate latch", "the water barrel"],
        safe_paths=["the pebble path", "the flower walk", "the open lawn"],
    ),
}

MYSTERIES = {
    "missing_tortilla": Mystery(
        id="missing_tortilla",
        question="Who took the warm tortilla?",
        reveal="the tortilla had fallen into the story sack",
        moral="honesty",
        clue_kind="crumbs",
        solve_kind="return",
    ),
    "stolen_map": Mystery(
        id="stolen_map",
        question="Where did the small map go?",
        reveal="the map had been tucked under a market basket",
        moral="sharing",
        clue_kind="folds",
        solve_kind="share",
    ),
    "lost_lantern": Mystery(
        id="lost_lantern",
        question="Who hid the little lantern?",
        reveal="the lantern was hanging on a hook all along",
        moral="kindness",
        clue_kind="glow",
        solve_kind="find",
    ),
}

HELPERS = {
    "dog_dim": Helper(id="dog_dim", label="Dog-Dim", mood="quiet", skill="follow crumbs"),
    "cheetah": Helper(id="cheetah", label="Cheetah", mood="swift", skill="spot tracks"),
}

SUSPECTS = {
    "bakery": Suspect(id="bakery", label="the bakery cart", motive="it carried bread and wraps", innocent_reason="it only held lunch food"),
    "vendor": Suspect(id="vendor", label="the fruit seller", motive="it had a busy table full of baskets", innocent_reason="it was busy helping customers"),
    "child": Suspect(id="child", label="the story sack", motive="it was carried everywhere", innocent_reason="it was just a bag that held treasures"),
}

GIRL_NAMES = ["Luna", "Maya", "Nina", "Iris", "Zia", "Mina"]
BOY_NAMES = ["Arlo", "Nico", "Theo", "Milo", "Jasper", "Eli"]


def _moral_text(moral: str) -> str:
    return {
        "honesty": "telling the truth",
        "sharing": "sharing what was found",
        "kindness": "being gentle with everyone",
    }[moral]


def _resolve_reasonable(setting: Setting, mystery: Mystery) -> bool:
    return bool(setting.clue_spots) and mystery.moral in MORALS


def _inner(hero: Entity, line: str) -> str:
    return f"{hero.id} thought, “{line}”"


def _clue_line(kind: str) -> str:
    return {
        "crumbs": "small crumbs led the way",
        "folds": "a neat fold left a tiny clue",
        "glow": "a soft glow showed the next step",
    }[kind]


def _solve_line(kind: str, reveal: str) -> str:
    return {
        "return": f"That meant the right thing was to return it to {reveal.split('the ')[-1]}.",
        "share": "That meant the right thing was to share it fairly with everyone.",
        "find": "That meant the right thing was simply to find it and put it back in sight.",
    }[kind]


def tell(setting: Setting, mystery: Mystery, helper: Helper, suspect: Suspect,
         hero_name: str, hero_type: str, cheetah_name: str, cheetah_type: str,
         dog_name: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    dog = world.add(Entity(id=dog_name, kind="character", type="dog", label="Dog-Dim"))
    cheetah = world.add(Entity(id=cheetah_name, kind="character", type=cheetah_type, label=cheetah_name))
    tortilla = world.add(Entity(id="tortilla", type="food", label="a warm tortilla", owner=hero.id))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_kind))
    if helper.id == "dog_dim":
        helper_ent = dog
    else:
        helper_ent = cheetah

    hero.memes["curiosity"] += 1
    dog.memes["loyalty"] += 1
    cheetah.memes["alert"] += 1
    tortilla.meters["warm"] += 1

    world.say(
        f"At {setting.place}, {hero.id} was ready for a small adventure, "
        f"and Dog-Dim padded close beside {hero.pronoun('object')}."
    )
    world.say(
        f"Then something went wrong: the warm tortilla was missing, and "
        f"{mystery.question.lower()}"
    )
    world.say(_inner(hero, "A mystery is a door, and I get to open it."))
    world.say(
        f"{cheetah.id} arrived with quick eyes and a steady tail, while {helper_ent.label} "
        f"{helper.skill} by sniffing at {setting.dark_spot}."
    )

    world.para()
    hero.memes["worry"] += 1
    world.say(
        f"They followed the clue trail across {setting.clue_spots[0]} and then to "
        f"{setting.clue_spots[1]}, where { _clue_line(mystery.clue_kind) }."
    )
    world.say(_inner(hero, f"If I rush too fast, I might miss the kind answer."))

    world.para()
    cheetah.meters["speed"] += 1
    dog.meters["tracking"] += 1
    if suspect.id == "child":
        clue.meters["seen"] += 1
        world.say(
            f"Under the last bright spot, they found the clue at the edge of the story sack."
        )
    else:
        world.say(
            f"The clue pointed past {suspect.label}, but {suspect.innocent_reason}, so the trail kept going."
        )

    world.say(
        f"At last, they looked inside the story sack and found that {mystery.reveal}."
    )
    world.say(_inner(hero, f"I should be honest and careful, because the right answer matters."))

    world.para()
    hero.memes[mystery.moral] += 1
    dog.memes["relief"] += 1
    cheetah.memes["pride"] += 1
    tortilla.meters["found"] += 1
    world.say(
        f"{_solve_line(mystery.solve_kind, mystery.reveal)} {hero.id} smiled, "
        f"and {helper_ent.label} wagged or flicked an ear as the mystery opened up."
    )
    world.say(
        f"In the end, {hero.id} chose {_moral_text(mystery.moral)}, and the tortilla was safe again."
    )
    world.say(
        f"The adventure finished with {hero.id}, Dog-Dim, and {cheetah.id} walking home under "
        f"a clear sky, with the answer finally in the open."
    )

    world.facts.update(
        hero=hero,
        dog=dog,
        cheetah=cheetah,
        tortilla=tortilla,
        clue=clue,
        helper=helper,
        suspect=suspect,
        mystery=mystery,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure mystery for a 3-to-5-year-old where {f["hero"].id}, Dog-Dim, and {f["cheetah"].id} solve the mystery of a missing tortilla.',
        f"Tell a short story set at {f['setting'].place} with inner thoughts, clues, and a moral ending about {_moral_text(f['mystery'].moral)}.",
        f'Write a simple adventure story that uses the word "tortilla" and ends with the answer to "{f["mystery"].question}"',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, dog, cheetah, mystery = f["hero"], f["dog"], f["cheetah"], f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who went looking for the missing tortilla at {setting.place}?",
            answer=f"{hero.id}, Dog-Dim, and {cheetah.id} looked together at {setting.place}. They kept going because a mystery had to be solved.",
        ),
        QAItem(
            question=f"What clue helped them search near {setting.dark_spot}?",
            answer=f"The clue was {mystery.clue_kind}, and it led them from one place to the next. That clue helped them keep searching without giving up.",
        ),
        QAItem(
            question=f"What was the answer to the mystery?",
            answer=f"The answer was that {mystery.reveal}. The missing tortilla was not gone forever; it had been found in the right place.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} show at the end?",
            answer=f"{hero.id} showed {_moral_text(mystery.moral)}. The ending proves that the best choice was to be honest, sharing, or kind, depending on the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tortilla?",
            answer="A tortilla is a soft, flat bread that can wrap food or be eaten on its own.",
        ),
        QAItem(
            question="What kind of animal is a cheetah?",
            answer="A cheetah is a big cat that can run very fast and has spots on its fur.",
        ),
        QAItem(
            question="Why might a dog follow a trail?",
            answer="A dog can use its nose to smell crumbs or tracks and follow where they lead.",
        ),
        QAItem(
            question="What does inner monologue mean?",
            answer="Inner monologue is the quiet thinking inside a character's head, like a secret thought before a choice.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question that does not have an answer yet, so the characters must look for clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            if _resolve_reasonable(SETTINGS[s], MYSTERIES[m]):
                combos.append((s, m, "dog_dim"))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: {setting.place} needs clues and the mystery must carry a moral value.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure mystery storyworld with tortilla, Dog-Dim, and a cheetah.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--cheetah-name")
    ap.add_argument("--dog-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.setting and args.mystery:
        if not _resolve_reasonable(SETTINGS[args.setting], MYSTERIES[args.mystery]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], MYSTERIES[args.mystery]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, _ = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    cheetah_name = args.cheetah_name or "Cheetah"
    dog_name = args.dog_name or "Dog-Dim"
    return StoryParams(
        setting=setting,
        mystery=mystery,
        helper="dog_dim",
        suspect=args.suspect or rng.choice(list(SUSPECTS)),
        hero_name=hero_name,
        hero_type=gender,
        cheetah_name=cheetah_name,
        cheetah_type="cheetah",
        dog_name=dog_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        HELPERS[params.helper],
        SUSPECTS[params.suspect],
        params.hero_name,
        params.hero_type,
        params.cheetah_name,
        params.cheetah_type,
        params.dog_name,
    )
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


ASP_RULES = r"""
moral_value(honesty;sharing;kindness).
mystery(missing_tortilla;stolen_map;lost_lantern).
setting_ok(S) :- setting(S).
valid(S, M) :- setting_ok(S), mystery(M), moral_value(_).
solve(missing_tortilla, return).
solve(stolen_map, share).
solve(lost_lantern, find).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m, obj in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("moral", obj.moral))
        lines.append(asp.fact("solve", m, obj.solve_kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, mystery=m, helper="dog_dim", suspect="child",
                                        hero_name="Luna", hero_type="girl",
                                        cheetah_name="Cheetah", cheetah_type="cheetah",
                                        dog_name="Dog-Dim"))
                   for s, m, _ in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                p = resolve_params(args, random.Random(base + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base + i
            sample = generate(p)
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
    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
