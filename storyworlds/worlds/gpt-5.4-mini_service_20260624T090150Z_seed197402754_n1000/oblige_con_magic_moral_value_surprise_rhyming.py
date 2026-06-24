#!/usr/bin/env python3
"""
Rhyming story world: a small magical con-and-oblige fable with moral value and surprise.

A child-facing, state-driven storyworld about a clever little stage trick:
someone tries to con the crowd with magic, then gets obliged to make things right.
The ending is a surprise that proves the moral value changed the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    rhymes: str


@dataclass
class Trick:
    id: str
    show: str
    claim: str
    reveal: str
    surprise: str
    moral_turn: str
    keyword: str


@dataclass
class StoryParams:
    setting: str
    trick: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_fair": Setting(place="the moonlit fair", mood="glow", rhymes="show"),
    "candle_market": Setting(place="the candle market", mood="gold", rhymes="bold"),
    "rose_lane": Setting(place="Rose Lane", mood="sweet", rhymes="neat"),
}

TRICKS = {
    "glow_coin": Trick(
        id="glow_coin",
        show="a coin that sparkled like a tiny star",
        claim="a lucky coin that would make wishes come true",
        reveal="the coin was only shiny glass, lit by a hidden lamp",
        surprise="the 'lucky' coin chimed like a bell and floated back into the helper's hand",
        moral_turn="the hero decided to give the toy coin back and tell the truth",
        keyword="glow",
    ),
    "singing_box": Trick(
        id="singing_box",
        show="a little box that hummed in tune",
        claim="a magic music box that never missed a note",
        reveal="a tiny mouse inside had been tapping the beat all along",
        surprise="the box sneezed, and out popped a ribbon of confetti",
        moral_turn="the hero bowed low, thanked the mouse, and shared the applause",
        keyword="sing",
    ),
    "flower_spell": Trick(
        id="flower_spell",
        show="a wand that made paper flowers bloom",
        claim="a spell that could grow flowers from plain air",
        reveal="the flowers were folded from bright paper and tied with string",
        surprise="one hidden petal turned into a real seed and sprouted",
        moral_turn="the hero planted the seed in the garden and promised no more tricks",
        keyword="bloom",
    ),
}

NAMES = {
    "girl": ["Mina", "Luna", "Nia", "Pip", "Zara"],
    "boy": ["Toby", "Jules", "Finn", "Otis", "Bram"],
}

HELPER_NAMES = ["Tess", "Ravi", "Mira", "Noel", "June"]


# ---------------------------------------------------------------------------
# Rhyming narration helpers
# ---------------------------------------------------------------------------

def opener(world: World, hero: Entity, helper: Entity, trick: Trick) -> None:
    world.say(
        f"At {world.setting.place}, under a bright, bright light, "
        f"{hero.id} prepared a merry show for the night."
    )
    world.say(
        f"{hero.id} had {trick.show}, neat and fine, "
        f"and {helper.id} watched close, with a curious shine."
    )


def setup_con(world: World, hero: Entity, helper: Entity, trick: Trick) -> None:
    hero.memes["pride"] = 1.0
    hero.memes["temptation"] = 1.0
    helper.memes["trust"] = 1.0
    world.say(
        f"{hero.id} said, \"{trick.claim}!\" with a grin and a wink; "
        f"the crowd leaned in fast, hardly stopping to think."
    )
    world.say(
        f"But {helper.id} frowned softly and held up a hand: "
        f"\"A trick can be fun, but let's understand.\""
    )


def reveal_magic(world: World, hero: Entity, helper: Entity, trick: Trick) -> None:
    hero.memes["shame"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(
        f"Then the secret came out in a bright, little flash: "
        f"{trick.reveal}, and the tale turned to ash."
    )
    world.say(
        f"The crowd gave a gasp and a hush went around; "
        f"{hero.id} felt small as the floor touched the ground."
    )


def oblige_and_repair(world: World, hero: Entity, helper: Entity, trick: Trick) -> None:
    hero.memes["honesty"] = 1.0
    hero.memes["kindness"] = 1.0
    helper.memes["forgiveness"] = 1.0
    world.say(
        f"{helper.id} said, \"You must fix what you did, then we'll be all right; "
        f"be brave, be true, and make the day bright.\""
    )
    world.say(
        f"So {hero.id} gave back the coin, box, or bloom, "
        f"and promised the truth would have plenty of room."
    )
    world.say(
        f"That was the oblige part: not mean, but fair, "
        f"to mend the mistake with careful care."
    )


def surprise_ending(world: World, hero: Entity, helper: Entity, trick: Trick) -> None:
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    world.say(
        f"Then came a surprise, like a tap-tap-tap tune: "
        f"{trick.surprise} beneath the moon."
    )
    world.say(
        f"The crowd laughed and clapped, and the moral was plain: "
        f"when truth leads the way, trust comes back again."
    )
    world.say(
        f"{hero.id} bowed with a smile, no longer a con, "
        f"for honest small magic can shine on and on."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    trick = TRICKS[params.trick]
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["trick"] = trick
    world.facts["setting"] = setting
    return world


def tell(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    trick = world.facts["trick"]

    opener(world, hero, helper, trick)
    world.para()
    setup_con(world, hero, helper, trick)
    world.para()
    reveal_magic(world, hero, helper, trick)
    oblige_and_repair(world, hero, helper, trick)
    world.para()
    surprise_ending(world, hero, helper, trick)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    trick = world.facts["trick"]
    setting = world.facts["setting"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a short rhyming story set at {setting.place} about {hero.id} and {helper.id}, where a magical con is undone by kindness.',
        f'Tell a child-friendly poem-story using the word "{trick.keyword}" and ending with a surprise that teaches moral value.',
        f'Create a gentle story with magic, oblige, and con, where the wrong choice is repaired in the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    trick = world.facts["trick"]
    setting = world.facts["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} try to show the magic trick?",
            answer=f"{hero.id} tried to show the trick at {setting.place}.",
        ),
        QAItem(
            question=f"What did {helper.id} help {hero.id} understand?",
            answer=f"{helper.id} helped {hero.id} understand that a trick should not be used to con people.",
        ),
        QAItem(
            question=f"What did {hero.id} do to make things right?",
            answer=f"{hero.id} gave back the trick prop and told the truth, which was the oblige part of the story.",
        ),
        QAItem(
            question=f"What surprise happened at the end?",
            answer=f"The surprise was that {trick.surprise.lower()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a magic trick?",
            answer="A magic trick is a pretend wonder made with skill, tools, or careful hiding, so it looks surprising.",
        ),
        QAItem(
            question="What does it mean to con someone?",
            answer="To con someone means to trick them unfairly so they believe something false.",
        ),
        QAItem(
            question="Why is moral value important?",
            answer="Moral value helps people choose honesty, kindness, and fairness instead of being sneaky or mean.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that makes the story feel exciting or funny.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_name(S).
trick(T) :- trick_name(T).
hero_name(N) :- name(N).
helper_name(N) :- name(N).

valid_story(S, T) :- setting(S), trick(T).
needs_repair(T) :- trick_name(T).
has_surprise(T) :- trick_name(T).
moral_value(T) :- trick_name(T).

#show valid_story/2.
#show needs_repair/1.
#show has_surprise/1.
#show moral_value/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_name", sid))
    for tid in TRICKS:
        lines.append(asp.fact("trick_name", tid))
    for name in NAMES["girl"] + NAMES["boy"] + HELPER_NAMES:
        lines.append(asp.fact("name", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy
    program = asp_program("#show valid_story/2. #show needs_repair/1. #show has_surprise/1. #show moral_value/1.")
    model = asp.one_model(program)
    py = set((s, t) for s in SETTINGS for t in TRICKS)
    asp_pairs = set(asp.atoms(model, "valid_story"))
    if py != asp_pairs:
        print("MISMATCH between Python and ASP story compatibility.")
        print("python:", sorted(py))
        print("asp:", sorted(asp_pairs))
        return 1
    print(f"OK: ASP parity checked for {len(py)} setting/trick pairs.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming magical con-and-oblige storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    trick = args.trick or rng.choice(list(TRICKS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAMES[hero_type])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        trick=trick,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print("\n--- trace ---")
        for eid, ent in sample.world.entities.items():
            print(f"{eid}: {asdict(ent)}")
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        for s, t in pairs:
            print(f"{s} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for trick in TRICKS:
                params = StoryParams(
                    setting=setting,
                    trick=trick,
                    hero_name=NAMES["girl"][0],
                    hero_type="girl",
                    helper_name=HELPER_NAMES[0],
                    helper_type="boy",
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
