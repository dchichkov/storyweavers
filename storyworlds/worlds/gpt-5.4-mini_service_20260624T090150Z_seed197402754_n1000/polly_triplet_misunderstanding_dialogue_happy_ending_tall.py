#!/usr/bin/env python3
"""
storyworlds/worlds/polly_triplet_misunderstanding_dialogue_happy_ending_tall.py
===============================================================================

A small tall-tale storyworld about Polly, a triplet trio, a misunderstanding,
dialogue, and a happy ending.

The premise is simple:
- Polly meets three nearly identical triplets.
- A shared goal gets misunderstood.
- They talk it through.
- They end with a cheerful fix that proves the misunderstanding was resolved.

The world is simulated with meters and memes:
- meters: physical quantities like carried load, distance, and noise
- memes: emotional quantities like confusion, worry, trust, and joy
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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
    place: str = "the hill"
    detail: str = "a windy hill with a long path and a bright sky"


@dataclass
class Scenario:
    object_name: str
    object_phrase: str
    misunderstanding: str
    resolution_tool: str
    ending_image: str


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _apply_confusion(world: World) -> list[str]:
    out: list[str] = []
    polly = world.get("Polly")
    trio = world.get("Triplets")
    if polly.memes.get("misunderstanding", 0) >= THRESHOLD and trio.memes.get("startled", 0) >= THRESHOLD:
        sig = ("confusion",)
        if sig not in world.fired:
            world.fired.add(sig)
            polly.memes["worry"] = polly.memes.get("worry", 0) + 1
            trio.memes["worry"] = trio.memes.get("worry", 0) + 1
            out.append("The whole place felt puzzled for a moment.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines = _apply_confusion(world)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


SETTING = Setting()
SCENARIOS = {
    "kite": Scenario(
        object_name="kite",
        object_phrase="a kite as wide as a barn door",
        misunderstanding="Polly thought the triplets were pulling the kite away, but they were really trying to help lift it.",
        resolution_tool="a bright ribbon",
        ending_image="the kite rose high and steady above the hill",
    ),
    "basket": Scenario(
        object_name="basket",
        object_phrase="a picnic basket packed with bread and berries",
        misunderstanding="Polly thought the triplets were sneaking snacks, but they were really trying to keep the basket from tipping.",
        resolution_tool="a sturdy rope",
        ending_image="the basket stayed safe while the berries stayed bright and round",
    ),
    "book": Scenario(
        object_name="book",
        object_phrase="a big storybook with a flap that kept popping open",
        misunderstanding="Polly thought the triplets were making a mess, but they were really trying to hold the pages still.",
        resolution_tool="a wooden paperweight",
        ending_image="the storybook lay open and calm like a quiet pond",
    ),
}

NAMES = ["Polly", "Mabel", "June", "Lena", "Ruby", "Nora"]
TRAITS = ["brave", "cheery", "quick", "curious", "lively", "gentle"]


@dataclass
class StoryParams:
    scenario: str
    name: str = "Polly"
    trait: str = "brave"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld about Polly and a triplet misunderstanding."
    )
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scenario in SCENARIOS:
        for name in NAMES:
            for trait in TRAITS:
                combos.append((scenario, name, trait))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.scenario:
        combos = [c for c in combos if c[0] == args.scenario]
    if args.name:
        combos = [c for c in combos if c[1] == args.name]
    if args.trait:
        combos = [c for c in combos if c[2] == args.trait]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    scenario, name, trait = rng.choice(sorted(combos))
    return StoryParams(scenario=scenario, name=name, trait=trait)


def intro(world: World, polly: Entity, trio: Entity, scenario: Scenario) -> None:
    world.say(
        f"Polly was a {polly.traits[0]} little girl who could spot a story from a mile away. "
        f"One afternoon, {polly.pronoun('subject')} met the triplets, three nearly identical children with the same grin and the same muddy boots."
    )
    world.say(
        f"They were gathered at {world.setting.place}, where {world.setting.detail}, and they stood beside {scenario.object_phrase}."
    )
    trio.meters["distance"] = 1.0
    polly.memes["curiosity"] = polly.memes.get("curiosity", 0) + 1


def misunderstanding_beats(world: World, polly: Entity, trio: Entity, scenario: Scenario) -> None:
    polly.memes["misunderstanding"] = 1
    trio.memes["startled"] = 1
    world.say(
        f"Polly blinked and said, “Why are you tugging at the {scenario.object_name}? Are you trying to snatch it away?”"
    )
    world.say(
        f"The oldest triplet shook {trio.pronoun('possessive')} head. “No, ma’am,” {trio.pronoun('subject')} said. "
        f““We thought you wanted us to help, not hold back.””
    )
    propagate(world, narrate=True)
    world.say(
        f"Polly frowned, because the words had crossed like two kites in the same wind. That sort of mix-up can happen faster than a rabbit can blink."
    )


def dialogue_and_turn(world: World, polly: Entity, trio: Entity, scenario: Scenario) -> None:
    polly.memes["worry"] = polly.memes.get("worry", 0) + 1
    trio.memes["worry"] = trio.memes.get("worry", 0) + 1
    world.say(
        f"Then Polly took a deep breath and said, “Tell me plain. What do you need?”"
    )
    world.say(
        f"The middle triplet pointed to {scenario.object_phrase} and said, “It is wobbly as a fish on a fence. We need three hands, not three guesses.”"
    )
    world.say(
        f"The youngest triplet nodded so hard {trio.pronoun('possessive')} hair bobbed like a kite tail. “We were only trying to help it stand tall.”"
    )
    world.say(
        f"Polly laughed at that, because now the whole puzzle fit together as neat as a button in a buttonhole."
    )
    polly.memes["trust"] = polly.memes.get("trust", 0) + 1
    trio.memes["trust"] = trio.memes.get("trust", 0) + 1


def resolution(world: World, polly: Entity, trio: Entity, scenario: Scenario) -> None:
    polly.memes["joy"] = polly.memes.get("joy", 0) + 2
    trio.memes["joy"] = trio.memes.get("joy", 0) + 2
    polly.memes["misunderstanding"] = 0
    trio.memes["startled"] = 0
    world.say(
        f"So Polly grabbed {scenario.resolution_tool}, and the triplets took the corners and the middle. "
        f"Together they fixed the problem in one grand jiffy."
    )
    world.say(
        f"“Left a little!” Polly called. “Right a little!” called the triplets. "
        f"By the time they finished, nobody was confused anymore, and everybody was smiling."
    )
    world.say(
        f"At last, {scenario.ending_image}, and Polly waved goodbye to the triplets with a heart as light as a paper lantern."
    )


def tell(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario]
    world = World(SETTING)
    polly = world.add(Entity(
        id="Polly",
        kind="character",
        type="girl",
        traits=[params.trait, "little"],
        meters={"distance": 0.0},
        memes={"curiosity": 1.0},
    ))
    trio = world.add(Entity(
        id="Triplets",
        kind="character",
        type="child",
        label="the triplets",
        plural=True,
        meters={"distance": 1.0},
        memes={"worry": 0.0},
        traits=["three", "nearly identical"],
    ))
    world.facts.update(params=params, scenario=scenario, polly=polly, trio=trio)

    intro(world, polly, trio, scenario)
    world.para()
    misunderstanding_beats(world, polly, trio, scenario)
    world.para()
    dialogue_and_turn(world, polly, trio, scenario)
    world.para()
    resolution(world, polly, trio, scenario)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    scenario: Scenario = world.facts["scenario"]
    return [
        f"Write a tall-tale story about Polly and triplets with a misunderstanding about {scenario.object_name}.",
        f"Tell a child-friendly dialogue story where Polly and three triplets talk through a mix-up and end happily.",
        f"Write a short story in a tall-tale style where Polly learns the triplets were helping with {scenario.object_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: Scenario = world.facts["scenario"]
    polly: Entity = world.facts["polly"]
    trio: Entity = world.facts["trio"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about Polly and the triplets, who met at {world.setting.place} beside {scenario.object_phrase}.",
        ),
        QAItem(
            question=f"What did Polly first misunderstand about the triplets and the {scenario.object_name}?",
            answer=f"Polly thought the triplets were pulling the {scenario.object_name} away, but they were really trying to help it stand tall.",
        ),
        QAItem(
            question="How did the problem get solved?",
            answer=f"Polly asked questions, the triplets explained their plan, and then they all worked together with {scenario.resolution_tool}.",
        ),
        QAItem(
            question="How did Polly feel at the end?",
            answer="Polly felt happy and relieved, because the mix-up turned into teamwork and nobody was upset anymore.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people do not correctly understand what someone else meant or wanted.",
        ),
        QAItem(
            question="Why can dialogue help?",
            answer="Dialogue helps because people can say what they mean out loud and clear up confusion.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters finish feeling safe, calm, or joyful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
character(polly;triplets).
misunderstanding_story :- misunderstanding(polly, triplets).
happy_ending :- dialogue, resolution.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("character", "polly"),
        asp.fact("character", "triplets"),
        asp.fact("feature", "misunderstanding"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "happy_ending"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show character/1."))
    if asp.atoms(model, "character") == [("polly",), ("triplets",)]:
        print("OK: ASP twin is wired for Polly and the triplets.")
        return 0
    print("MISMATCH: ASP twin is not behaving as expected.")
    return 1


CURATED = [
    StoryParams(scenario="kite", name="Polly", trait="brave"),
    StoryParams(scenario="basket", name="Polly", trait="cheery"),
    StoryParams(scenario="book", name="Polly", trait="curious"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show character/1."))
    return sorted(set(asp.atoms(model, "character")))


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = list(SCENARIOS)
    if args.scenario:
        choices = [args.scenario]
    if not choices:
        raise StoryError("No valid scenario matches the given options.")
    scenario = rng.choice(sorted(choices))
    name = args.name or "Polly"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scenario=scenario, name=name, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show character/1."))
        return
    if args.asp:
        print("2 character facts: polly, triplets")
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
            header = f"### {p.name}: {p.scenario} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
