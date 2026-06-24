#!/usr/bin/env python3
"""
storyworlds/worlds/origin_semantic_repetition_fable.py
======================================================

A small fable-like story world about origin, semantic meaning, and repetition.

Seed tale sketch:
- An old owl shares a warning that began at the river.
- A young crow repeats the warning, but at first he repeats only the sound of it,
  not the meaning.
- The birds become confused until the owl explains the origin and the semantic
  core of the message.
- The crow repeats it again, carefully this time, and the flock crosses safely.

This world is deliberately small: one lesson, one tension, one repair.
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "owl"}
        male = {"boy", "father", "dad", "man", "crow", "fox", "rabbit", "mouse", "turtle"}
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Tale:
    id: str
    title: str
    origin: str
    semantic: str
    refrain: str
    danger: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"repetition"}),
    "riverbank": Setting(place="the riverbank", affords={"repetition"}),
    "orchard": Setting(place="the orchard", affords={"repetition"}),
}

TALES = {
    "bridge_warning": Tale(
        id="bridge_warning",
        title="The Bridge Warning",
        origin="an old sign by the river",
        semantic="the bridge is safe only if everyone walks slowly and one at a time",
        refrain="slow steps, one by one",
        danger="someone may rush and wobble the bridge",
        fix="repeat the warning with its meaning",
        tags={"river", "warning", "bridge", "origin", "semantic", "repetition"},
    ),
    "berry_rule": Tale(
        id="berry_rule",
        title="The Berry Rule",
        origin="a grandparent hare in the orchard",
        semantic="berries should be shared after the baskets are counted",
        refrain="count first, then share",
        danger="someone may take too much and leave none for the rest",
        fix="say the rule clearly and kindly",
        tags={"orchard", "sharing", "origin", "semantic", "repetition"},
    ),
}

HERO_NAMES = ["Milo", "Nia", "Tavi", "Lena", "Pip", "Sora"]
MENTOR_NAMES = ["Owl", "Grandma Hare", "Old Turtle"]
COMPANION_NAMES = ["Crow", "Mouse", "Robin", "Sparrow"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    tale = world.facts["tale"]
    if hero.memes.get("echo", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("clarity", 0.0) >= THRESHOLD:
        return out
    sig = ("confusion", tale.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    out.append(
        f"The repeated words drifted around the meadow, but their meaning grew muddy."
    )
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mentor = world.get("mentor")
    tale = world.facts["tale"]
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("fix", tale.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["clarity"] = hero.memes.get("clarity", 0.0) + 1
    mentor.memes["gentleness"] = mentor.memes.get("gentleness", 0.0) + 1
    out.append(
        f"{mentor.label} reminded {hero.id} where the words came from and what they truly meant."
    )
    return out


CAUSAL_RULES = [Rule("confusion", _r_confusion), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, tale: Tale, hero_name: str, mentor_name: str, companion_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="crow", label=hero_name, traits=["young", "curious"]))
    mentor = world.add(Entity(id="mentor", kind="character", type="owl", label=mentor_name, traits=["wise", "calm"]))
    companion = world.add(Entity(id="companion", kind="character", type="mouse", label=companion_name, traits=["small", "quick"]))
    world.facts["tale"] = tale
    world.facts["hero_name"] = hero_name
    world.facts["mentor_name"] = mentor_name
    world.facts["companion_name"] = companion_name
    world.facts["setting"] = setting

    hero.memes["curiosity"] = 1
    mentor.memes["wisdom"] = 1
    companion.memes["listening"] = 1

    world.say(
        f"{hero.label} was a young crow who liked to repeat everything he heard."
    )
    world.say(
        f"One day at {setting.place}, {mentor.label} told a tale from {tale.origin}."
    )
    world.say(
        f'The tale had a clear heart: "{tale.refrain}."'
    )

    world.para()
    hero.memes["echo"] = hero.memes.get("echo", 0.0) + 1
    world.say(
        f"{hero.label} repeated the words to {companion.label}, but at first he copied only the sound."
    )
    world.say(
        f"That was not enough, because {tale.danger}."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{mentor.label} paused him and asked him to say where the words had come from and what they meant."
    )
    world.say(
        f'{hero.label} took a breath and said, "{tale.refrain}. It means {tale.semantic}."'
    )
    hero.memes["echo"] = hero.memes.get("echo", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    companion.memes["trust"] = companion.memes.get("trust", 0.0) + 1
    world.say(
        f"After that, {hero.label} repeated the saying again, this time with its origin and meaning."
    )
    world.say(
        f"The birds understood, and {tale.fix}. In the end, the little flock moved safely, one by one."
    )

    world.facts.update(hero=hero, mentor=mentor, companion=companion, resolved=True)
    return world


def validity_checks(setting: Setting, tale: Tale) -> None:
    if "repetition" not in setting.affords:
        raise StoryError("That setting does not support the repetition-based tale.")
    if "origin" not in tale.tags or "semantic" not in tale.tags:
        raise StoryError("The tale must include origin and semantic meaning.")


@dataclass
class StoryParams:
    place: str
    tale: str
    hero_name: str
    mentor_name: str
    companion_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about repetition, origin, and meaning.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--tale", choices=TALES)
    ap.add_argument("--name")
    ap.add_argument("--mentor")
    ap.add_argument("--companion")
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
    place = args.place or rng.choice(list(SETTINGS))
    tale = args.tale or rng.choice(list(TALES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    mentor_name = args.mentor or rng.choice(MENTOR_NAMES)
    companion_name = args.companion or rng.choice(COMPANION_NAMES)
    validity_checks(SETTINGS[place], TALES[tale])
    return StoryParams(place=place, tale=tale, hero_name=hero_name, mentor_name=mentor_name, companion_name=companion_name)


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    hero = world.facts["hero_name"]
    mentor = world.facts["mentor_name"]
    return [
        f'Write a short fable for a child about "{tale.origin}" and "{tale.semantic}" using repetition.',
        f"Tell a gentle animal story where {hero} repeats a saying from {mentor} but learns to repeat its meaning too.",
        f'Write a simple moral tale that includes the words "origin" and "semantic" and ends with safer repetition.',
    ]


def story_qa(world: World) -> list[QAItem]:
    tale = world.facts["tale"]
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    companion = world.facts["companion"]
    return [
        QAItem(
            question=f"Who first shared the wise saying in the story?",
            answer=f"{mentor.label} first shared it, and the saying came from {tale.origin}.",
        ),
        QAItem(
            question=f"What did the saying mean?",
            answer=f"It meant that {tale.semantic}.",
        ),
        QAItem(
            question=f"Why did {hero.label} get into trouble when he repeated it at first?",
            answer=f"He repeated the sound but not the meaning, so the words became confusing and made the flock uneasy.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and {companion.label}?",
            answer=f"{hero.label} repeated the saying with its origin and meaning, so {companion.label} understood it and everyone moved safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again. It can help people remember a message.",
        ),
        QAItem(
            question="What is an origin?",
            answer="An origin is where something begins or comes from.",
        ),
        QAItem(
            question="What does semantic mean?",
            answer="Semantic meaning is the meaning of words or signs, not just their sound.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TALES[params.tale], params.hero_name, params.mentor_name, params.companion_name)
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
    StoryParams(place="riverbank", tale="bridge_warning", hero_name="Milo", mentor_name="Owl", companion_name="Mouse"),
    StoryParams(place="orchard", tale="berry_rule", hero_name="Nia", mentor_name="Grandma Hare", companion_name="Sparrow"),
]


ASP_RULES = r"""
% A tale is valid when the setting supports repetition and the tale carries
% both an origin and a semantic meaning.
valid_story(Place, Tale) :- setting(Place), tale(Tale),
                            affords(Place, repetition),
                            has_origin(Tale), has_semantic(Tale).

% A tale is one of the approved fable-shaped seeds.
tale(bridge_warning) :- .
tale(berry_rule) :- .

has_origin(bridge_warning) :- .
has_semantic(bridge_warning) :- .
has_origin(berry_rule) :- .
has_semantic(berry_rule) :- .

valid_combo(Place, Tale) :- valid_story(Place, Tale).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid in TALES:
        lines.append(asp.fact("tale", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(p, t) for p in SETTINGS for t in TALES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, tale) combos:\n")
        for place, tale in combos:
            print(f"  {place:10} {tale}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.tale} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
