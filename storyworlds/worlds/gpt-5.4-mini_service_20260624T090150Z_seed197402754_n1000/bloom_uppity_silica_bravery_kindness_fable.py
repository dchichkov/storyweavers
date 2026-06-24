#!/usr/bin/env python3
"""
A small fable-like storyworld about a bloom, an uppity neighbor, and a little
problem solved with bravery and kindness.

Seed image:
- A bright bloom is proud of its place in the garden.
- An uppity bird or beetle teases the bloom.
- Silica dust in the soil helps keep the roots steady in dry weather.
- Bravery and kindness change the ending.

This script follows the Storyweavers contract:
- standalone stdlib Python
- story-driven world state with meters and memes
- inline ASP twin
- text, JSON, trace, QA, and verification modes
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"flower", "blossom", "girl", "mother", "woman"}
        male = {"bird", "boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"
    affordances: set[str] = field(default_factory=set)


@dataclass
class CharacterSpec:
    type: str
    label: str
    intro: str


@dataclass
class ProblemSpec:
    id: str
    verb: str
    rush: str
    risk: str
    danger: str
    tag: str


@dataclass
class AidSpec:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    protects: set[str]


@dataclass
class StoryParams:
    setting: str
    problem: str
    aid: str
    hero: str
    hero_type: str
    challenger: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def entity_lines(self) -> list[str]:
        lines = []
        for e in self.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
        return lines


def _tick_meters(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _tick_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _rule_wilt(world: World) -> list[str]:
    out: list[str] = []
    bloom = world.entities["Bloom"]
    if bloom.meters.get("dry", 0.0) >= THRESHOLD and ("wilt",) not in world.fired:
        world.fired.add(("wilt",))
        _tick_meme(bloom, "sadness", 1)
        out.append("The bloom drooped a little, as if its bright head had grown tired.")
    return out


def _rule_silica_help(world: World) -> list[str]:
    out: list[str] = []
    bloom = world.entities["Bloom"]
    if bloom.meters.get("dry", 0.0) >= THRESHOLD and bloom.meters.get("silica", 0.0) >= THRESHOLD:
        if ("steady",) not in world.fired:
            world.fired.add(("steady",))
            bloom.meters["steady"] = 1
            bloom.memes["hope"] = bloom.memes.get("hope", 0.0) + 1
            out.append("The silica in the soil kept the roots snug and steady.")
    return out


def _rule_kindness_heals(world: World) -> list[str]:
    out: list[str] = []
    bloom = world.entities["Bloom"]
    helper = world.entities["Kindness"]
    if helper.meters.get("watered", 0.0) >= THRESHOLD and ("heal",) not in world.fired:
        world.fired.add(("heal",))
        bloom.meters["water"] = bloom.meters.get("water", 0.0) + 1
        bloom.memes["joy"] = bloom.memes.get("joy", 0.0) + 1
        bloom.memes["pride"] = max(0.0, bloom.memes.get("pride", 0.0) - 1)
        out.append("Kindness brought a careful cup of water, and the bloom lifted its face again.")
    return out


CAUSAL_RULES = [_rule_wilt, _rule_silica_help, _rule_kindness_heals]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING_REGISTRY = {
    "garden": Setting(place="the garden", affordances={"dry_wind", "sparrow_tease", "water_cup"}),
    "meadow": Setting(place="the meadow", affordances={"dry_wind", "sparrow_tease", "water_cup"}),
}

PROBLEM_REGISTRY = {
    "dry_wind": ProblemSpec(
        id="dry_wind",
        verb="stand in the dry wind",
        rush="hurry into the dry wind",
        risk="lose its fresh shine",
        danger="dry and brittle",
        tag="dry",
    ),
    "sparrow_tease": ProblemSpec(
        id="sparrow_tease",
        verb="face the uppity sparrow",
        rush="flutter after the uppity sparrow",
        risk="feel small and sad",
        danger="teased and lonely",
        tag="tease",
    ),
}

AID_REGISTRY = {
    "silica": AidSpec(
        id="silica",
        label="silica dust",
        prep="spread a little silica dust around the roots first",
        tail="had made the roots steady in the warm dirt",
        helps={"dry"},
        protects={"steady"},
    ),
    "kindness": AidSpec(
        id="kindness",
        label="Kindness",
        prep="call for Kindness and bring a cup of water",
        tail="had watered the bloom and soothed the garden",
        helps={"tease", "dry"},
        protects={"water"},
    ),
    "bravery": AidSpec(
        id="bravery",
        label="Bravery",
        prep="ask Bravery to stand beside the bloom",
        tail="had helped the bloom stand tall",
        helps={"tease"},
        protects={"steady", "water"},
    ),
}

CHARACTERS = {
    "bloom": CharacterSpec(type="flower", label="Bloom", intro="a bright little bloom"),
    "uppity": CharacterSpec(type="bird", label="Uppity", intro="an uppity sparrow"),
    "kindness": CharacterSpec(type="helper", label="Kindness", intro="Kindness"),
    "bravery": CharacterSpec(type="helper", label="Bravery", intro="Bravery"),
}

GARDEN_NAMES = ["Marigold", "Poppy", "Rose", "Daisy", "Violet"]
BIRD_NAMES = ["Pip", "Tattler", "Skittish", "Jumpy"]
TRAITS = ["bright", "gentle", "small", "steady"]


def reasonableness_gate(problem: ProblemSpec, aid: AidSpec) -> bool:
    return (problem.tag in aid.helps) or (problem.tag == "dry" and "steady" in aid.protects)


def explain_rejection(problem: ProblemSpec, aid: AidSpec) -> str:
    return (
        f"(No story: {aid.label} does not honestly help with {problem.verb}. "
        f"The little conflict would not turn in a believable way.)"
    )


def build_world(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.setting]
    problem = PROBLEM_REGISTRY[params.problem]
    aid = AID_REGISTRY[params.aid]

    world = World(setting)

    bloom = world.add(Entity(id="Bloom", kind="character", type="flower", label=params.hero, phrase="a bloom"))
    uppity = world.add(Entity(id="Uppity", kind="character", type="bird", label=params.challenger, phrase="an uppity bird"))
    helper = world.add(Entity(id=aid.id.capitalize(), kind="character", type="helper", label=aid.label, phrase=aid.label))

    bloom.meters["health"] = 1
    bloom.memes["pride"] = 1
    bloom.memes["love_sun"] = 1
    uppity.memes["boast"] = 1
    helper.memes["care"] = 1

    world.say(f"In {world.setting.place}, there was {bloom.label.lower()}, a bloom that liked to stand very tall.")
    world.say(f"Nearby, {uppity.label.lower()} was an uppity sparrow who loved to chatter and show off.")
    world.say(f"And in the warm dirt, a little bit of silica helped the roots stay firm.")

    world.para()
    world.say(f"One bright day, {bloom.label.lower()} wanted to {problem.verb}, because the garden felt wide and proud.")
    _tick_meme(bloom, "desire", 1)
    _tick_meters(bloom, "dry", 1 if problem.id == "dry_wind" else 0)
    if problem.id == "dry_wind":
        world.say("But the wind was dry, and it could make soft petals lose their shine.")
        propagate(world)
    else:
        world.say(f"Then {uppity.label.lower()} began to tease, saying the bloom was too small to matter.")
        _tick_meme(bloom, "hurt", 1)
        _tick_meme(bloom, "shy", 1)

    world.para()
    world.say(f"{bloom.label} wanted to keep going, but the problem felt {problem.danger}.")
    _tick_meme(bloom, "worry", 1)
    if problem.id == "sparrow_tease":
        _tick_meme(uppity, "rudeness", 1)
        world.say(f"The {uppity.label.lower()} hopped higher and higher, all puffed up and uppity.")
        world.say(f"Still, {bloom.label.lower()} looked at the little roots and remembered the silica beneath them.")

    world.para()
    world.say(f"Then {aid.label} came close and offered a kinder way.")
    if aid.id == "silica":
        world.say("Brave care does not always shout; sometimes it spreads quietly under the soil.")
        _tick_meters(bloom, "silica", 1)
        _tick_meme(world.get("Bravery"), "courage", 1)
        world.say(f"{aid.prep.capitalize()}, and the bloom trusted that unseen help.")
        propagate(world)
        if problem.id == "dry_wind":
            _tick_meme(bloom, "bravery", 1)
            world.say(f"That made the bloom brave enough to face the wind without folding.")
    elif aid.id == "kindness":
        _tick_meters(helper, "watered", 1)
        world.say(f"{aid.prep.capitalize()}, and the uppity chatter softened.")
        propagate(world)
    else:
        _tick_meme(world.get("Bravery"), "courage", 1)
        _tick_meters(helper, "watered", 1)
        world.say(f"{aid.prep.capitalize()}, and the bloom found its heart again.")
        propagate(world)

    world.para()
    if problem.id == "sparrow_tease":
        world.say(f"The uppity sparrow grew quiet when it saw how kind the bloom stayed.")
        world.say(f"{bloom.label} did not answer with a loud boast; it answered with a steady smile.")
    else:
        world.say(f"The wind passed by, but the bloom did not droop the way it might have before.")
        world.say(f"It stood there bright and calm, with silica in the roots and hope in the petals.")

    world.facts.update(
        bloom=bloom,
        uppity=uppity,
        helper=helper,
        problem=problem,
        aid=aid,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for young children about a bloom, an uppity neighbor, and {f["aid"].label}.',
        f'Tell a short story in which {f["bloom"].label.lower()} learns bravery and kindness in {f["setting"].place}.',
        f'Write a gentle garden fable that includes the words "bloom", "uppity", and "silica".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bloom = f["bloom"]
    uppity = f["uppity"]
    helper = f["helper"]
    problem = f["problem"]
    aid = f["aid"]

    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"It is mainly about {bloom.label.lower()}, a bloom in {world.setting.place}.",
        ),
        QAItem(
            question=f"What kind of neighbor was {uppity.label.lower()}?",
            answer=f"{uppity.label} was an uppity sparrow that liked to show off and tease.",
        ),
        QAItem(
            question=f"What helped the bloom stay steady in the garden?",
            answer=f"The silica in the soil helped the bloom stay steady when the day felt hard.",
        ),
    ]
    if problem.id == "sparrow_tease":
        qa.append(
            QAItem(
                question=f"Why did the bloom need kindness?",
                answer=f"It needed kindness because the uppity sparrow was teasing it, and kindness made the hurt feel smaller.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"Why did the bloom need bravery?",
                answer=f"It needed bravery because the dry wind could make the bloom feel weak, and bravery helped it stand tall.",
            )
        )
    qa.append(
        QAItem(
            question=f"What did {helper.label} do at the end?",
            answer=f"{helper.label} helped in a gentle way, and the bloom ended the story brighter than before.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is silica?",
            answer="Silica is a natural mineral found in sand and rocks, and it can be part of soil or plant food.",
        ),
        QAItem(
            question="What are bravery and kindness?",
            answer="Bravery means doing the right thing even when it feels hard, and kindness means caring about someone else’s feelings.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses simple animals or things to teach a lesson.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(["--- world model state ---"] + world.entity_lines())


ASP_RULES = r"""
#show valid_story/4.

problem(dry_wind).
problem(sparrow_tease).

aid(silica).
aid(kindness).
aid(bravery).

helps(silica,dry).
helps(kindness,dry).
helps(kindness,tease).
helps(bravery,tease).

protects(silica,steady).
protects(kindness,water).
protects(bravery,steady).
protects(bravery,water).

valid_story(P,Prob,Aid,"fable") :- problem(Prob), aid(Aid), place(P), fits(Prob,Aid).

fits(dry_wind,silica) :- true.
fits(dry_wind,bravery) :- true.
fits(sparrow_tease,kindness) :- true.
fits(sparrow_tease,bravery) :- true.

place(garden).
place(meadow).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTING_REGISTRY:
        lines.append(asp.fact("place", p))
    for p in PROBLEM_REGISTRY:
        lines.append(asp.fact("problem", p))
    for a in AID_REGISTRY:
        lines.append(asp.fact("aid", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_rows())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} story rows).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def valid_story_rows() -> list[tuple]:
    rows = []
    for place in SETTING_REGISTRY:
        for prob in PROBLEM_REGISTRY:
            for aid in AID_REGISTRY:
                if reasonableness_gate(PROBLEM_REGISTRY[prob], AID_REGISTRY[aid]):
                    rows.append((place, prob, aid, "fable"))
    return rows


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable storyworld about bloom, uppity, and silica.")
    ap.add_argument("--setting", choices=list(SETTING_REGISTRY))
    ap.add_argument("--problem", choices=list(PROBLEM_REGISTRY))
    ap.add_argument("--aid", choices=list(AID_REGISTRY))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["flower"])
    ap.add_argument("--challenger")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    problem = args.problem or rng.choice(list(PROBLEM_REGISTRY))
    aid = args.aid or rng.choice(list(AID_REGISTRY))
    if not reasonableness_gate(PROBLEM_REGISTRY[problem], AID_REGISTRY[aid]):
        raise StoryError(f"(No story: {aid} cannot resolve {problem} in a believable way.)")
    hero = args.hero or rng.choice(GARDEN_NAMES)
    challenger = args.challenger or rng.choice(BIRD_NAMES)
    return StoryParams(
        setting=setting,
        problem=problem,
        aid=aid,
        hero=hero,
        hero_type="flower",
        challenger=challenger,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_stories():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "dry_wind", "silica", "Marigold", "flower", "Pip"),
            StoryParams("meadow", "sparrow_tease", "kindness", "Daisy", "flower", "Tattler"),
            StoryParams("garden", "sparrow_tease", "bravery", "Rose", "flower", "Jumpy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
