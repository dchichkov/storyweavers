#!/usr/bin/env python3
"""
Story world: a tiny Animal Story with a ladle, a critic, and a rhyming turn.

Premise:
A small animal wants to make soup with a ladle while a picky critic watches and
doubts the plan.

Turn:
The soup goes wrong at first, then the animal uses the ladle carefully, adds one
small fix, and answers the critic with a rhyme.

Resolution:
The critic tastes the soup, smiles, and becomes kind.
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


# ---------------------------------------------------------------------------
# Small typed world model.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "thing"
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
        if self.type in {"fox", "cat", "rabbit", "mouse", "bear", "dog"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little kitchen"
    affords: set[str] = field(default_factory=lambda: {"soup"})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    rhyme: str


@dataclass
class CriticStyle:
    title: str
    temper: str
    rhyme_reply: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the little kitchen", affords={"soup"}),
    "garden": Setting(place="the garden table", affords={"soup"}),
}

ANIMALS = {
    "fox": "fox",
    "cat": "cat",
    "rabbit": "rabbit",
    "mouse": "mouse",
    "bear": "bear",
    "dog": "dog",
}

TOOLS = {
    "ladle": Tool(
        id="ladle",
        label="ladle",
        phrase="a shiny ladle",
        action="stir the soup",
        rhyme="swing and sing",
    )
}

CRITICS = {
    "critic": CriticStyle(
        title="critic",
        temper="picky",
        rhyme_reply="If it's too thin, give it a spin.",
    ),
    "judge": CriticStyle(
        title="critic",
        temper="fussy",
        rhyme_reply="If it's too plain, add joy again.",
    ),
}

FRUITS = ["pea", "carrot", "corn", "bean"]
GREETINGS = ["softly", "brightly", "politely"]


# ---------------------------------------------------------------------------
# Story params.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str = "kitchen"
    animal: str = "fox"
    critic: str = "critic"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate.
# ---------------------------------------------------------------------------
def valid_combo(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.animal in ANIMALS and params.critic in CRITICS


def explain_invalid(params: StoryParams) -> str:
    return "(No story: the setting, animal, or critic choice is not supported.)"


# ---------------------------------------------------------------------------
# Narrative helpers.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, critic: Entity, tool: Entity) -> None:
    world.say(
        f"In {world.setting.place}, a little {hero.type} named {hero.id} found "
        f"{tool.phrase} by the soup pot."
    )
    world.say(
        f"Near the door stood the {critic.label}, who looked picky and said, "
        f'"Hmm."'
    )


def want_soup(world: World, hero: Entity, tool: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(
        f"{hero.id} wanted to make soup that would sound sweet and neat, "
        f"so {hero.pronoun('subject')} lifted the ladle with care."
    )


def mishap(world: World, hero: Entity, critic: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    critic.memes["doubt"] = critic.memes.get("doubt", 0) + 1
    world.say(
        f"But the first spoonful was thin, and the {critic.label} made a tiny frown. "
        f'"This soup may flop," {critic.pronoun()} said with a pop.'
    )


def fix_soup(world: World, hero: Entity, tool: Entity, fruit: str) -> None:
    hero.meters["stir"] = hero.meters.get("stir", 0) + 1
    hero.meters["soup"] = hero.meters.get("soup", 0) + 1
    world.say(
        f"{hero.id} did not stop; {hero.pronoun('subject')} stirred the pot, "
        f"then dropped in one small {fruit}. "
        f"With a swish-swish twist, the soup grew rich."
    )
    world.say(
        f"{hero.id} smiled and said, \"A ladle can mend what a wobble has sent.\""
    )


def answer_critic(world: World, hero: Entity, critic: Entity) -> None:
    critic.memes["doubt"] = 0
    critic.memes["delight"] = critic.memes.get("delight", 0) + 1
    world.say(
        f"The {critic.label} tasted the soup and blinked twice, then grinned wide and bright. "
        f'"That is fine," {critic.pronoun()} said. "It tastes just right."'
    )
    world.say(
        f"{hero.id} bowed low. \"If you want to eat, take a seat,\" {hero.pronoun('subject')} replied. "
        f'"Good soup grows slow, but it shines with glow."'
    )


def tell(setting: Setting, animal: str, critic_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Milo", kind="animal", type=animal))
    critic = world.add(Entity(id="Critic", kind="animal", type="fox", label="critic"))
    tool = world.add(Entity(id="Ladle", kind="thing", type="ladle", label="ladle", phrase="a shiny ladle"))
    fruit = random.choice(FRUITS)

    world.facts.update(hero=hero, critic=critic, tool=tool, fruit=fruit, critic_kind=critic_kind)

    introduce(world, hero, critic, tool)
    world.para()
    want_soup(world, hero, tool)
    mishap(world, hero, critic)
    world.para()
    fix_soup(world, hero, tool, fruit)
    answer_critic(world, hero, critic)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a short Animal Story about a ladle, a picky critic, and a rhyme.',
        f"Tell a gentle story where {hero.id} uses a ladle to make soup while a critic watches.",
        "Write a rhyming story that ends with the critic tasting the soup and smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    critic = f["critic"]
    fruit = f["fruit"]
    return [
        QAItem(
            question="Who made the soup?",
            answer=f"{hero.id} made the soup with a ladle.",
        ),
        QAItem(
            question="What did the critic think at first?",
            answer="The critic was picky and thought the soup might flop.",
        ),
        QAItem(
            question="What small thing helped fix the soup?",
            answer=f"A small {fruit} helped make the soup richer and tastier.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The critic tasted the soup, smiled, and said it was just right.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ladle for?",
            answer="A ladle is a big spoon used to scoop soup or other food from a pot.",
        ),
        QAItem(
            question="What does a critic do?",
            answer="A critic looks at something and says what they think about it, often with careful or picky words.",
        ),
        QAItem(
            question="Why can soup be stirred?",
            answer="Soup is stirred so the ingredients mix together evenly and cook well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- animal(H).
critic(C) :- critic_kind(C).
has_ladle(T) :- tool(T), tool_type(T, ladle).
story_ok :- hero(_), critic(_), has_ladle(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for cid in CRITICS:
        lines.append(asp.fact("critic_kind", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_type", tid, "ladle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(sym.name == "story_ok" for sym in model)
    if ok:
        print("OK: ASP program can derive a valid story.")
        return 0
    print("MISMATCH: ASP program did not derive story_ok.")
    return 1


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story: a ladle, a critic, and a rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--critic", choices=CRITICS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    critic = args.critic or rng.choice(list(CRITICS))
    params = StoryParams(setting=setting, animal=animal, critic=critic, seed=args.seed)
    if not valid_combo(params):
        raise StoryError(explain_invalid(params))
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.animal, params.critic)
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
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for animal in ANIMALS:
                for critic in CRITICS:
                    params = StoryParams(setting=setting, animal=animal, critic=critic, seed=base_seed)
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
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
