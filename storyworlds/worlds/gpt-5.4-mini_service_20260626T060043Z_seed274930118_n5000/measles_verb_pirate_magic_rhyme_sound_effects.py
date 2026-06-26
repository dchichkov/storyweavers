#!/usr/bin/env python3
"""
A small storyworld about a pirate, measles, and a helpful magical rhyme.

The world is built around three narrative instruments:
- Magic: a helper spell can soothe an itchy, spotty pirate.
- Rhyme: the story speaks in gentle rhyming couplets.
- Sound Effects: small sounds help the scene feel alive ("sniff", "swish", "bing").

The premise is simple: a young pirate wants to verb, but measles make the day
uncomfortable. A magical rhyme helps the pirate rest, recover, and still feel
brave.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    verb: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "deck": "the bright ship deck",
    "cabin": "the cozy cabin",
    "harbor": "the windy harbor",
}

VERBS = {
    "sail": {
        "inf": "sail",
        "gerund": "sailing",
        "object": "the little boat",
        "place": "out on the water",
    },
    "dance": {
        "inf": "dance",
        "gerund": "dancing",
        "object": "the lantern light",
        "place": "on the deck",
    },
    "dig": {
        "inf": "dig",
        "gerund": "digging",
        "object": "for buried treasure",
        "place": "by the sand",
    },
    "sing": {
        "inf": "sing",
        "gerund": "singing",
        "object": "a sea song",
        "place": "by the mast",
    },
}

HERO_NAMES = ["Pip", "Ned", "Mara", "Lola", "Finn", "Tess"]
HELPER_NAMES = ["Bluebell", "Mimi", "Captain Dot", "Wren", "Sage"]


# ---------------------------------------------------------------------------
# Helpers for prose
# ---------------------------------------------------------------------------
def rhyme_pair(a: str, b: str) -> str:
    return f"{a} {b}"


def sfx(name: str) -> str:
    return {
        "measles": "itch-itch",
        "magic": "bing-bong",
        "sail": "swish-swash",
        "dance": "tap-tap",
        "dig": "scritch-scritch",
        "sing": "la-la",
        "rest": "hush-hush",
    }[name]


def capitalize_first(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
class MeaslesWorld(World):
    pass


def build_world(params: StoryParams) -> MeaslesWorld:
    world = MeaslesWorld(setting=SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        label="pirate",
        phrase=f"a small pirate named {params.hero_name}",
        traits=["brave", "spotty"],
        meters={"itch": 2.0, "tired": 1.0, "joy": 0.5},
        memes={"worry": 1.0, "hope": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        label="helper",
        phrase=f"a kind helper named {params.helper_name}",
        traits=["gentle", "magic"],
        meters={"calm": 2.0},
        memes={"care": 2.0},
    ))
    measles = world.add(Entity(
        id="measles",
        kind="thing",
        label="measles",
        phrase="a itchy, spotty sickness",
        owner=hero.id,
        meters={"spots": 6.0, "itch": 3.0},
    ))
    spellbook = world.add(Entity(
        id="spellbook",
        kind="thing",
        label="spellbook",
        phrase="a tiny spellbook with shiny pages",
        owner=helper.id,
    ))
    world.facts.update(
        hero=hero,
        helper=helper,
        measles=measles,
        spellbook=spellbook,
        verb=params.verb,
        verb_info=VERBS[params.verb],
    )
    return world


def intro(world: MeaslesWorld) -> None:
    hero: Entity = world.facts["hero"]
    verb = world.facts["verb_info"]["gerund"]
    world.say(
        f"{hero.phrase} lived {world.setting}. "
        f"{hero.id} loved {verb}, and {sfx(world.facts['verb'])} was the day’s sweet tune."
    )
    world.say(
        f"But then came measles, with itchy spots and a wobbly walk, "
        f"{sfx('measles')} {sfx('measles')} all the day."
    )


def trouble(world: MeaslesWorld) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    verb = world.facts["verb_info"]["inf"]
    place = world.facts["verb_info"]["place"]
    hero.meters["itch"] += 1.0
    hero.meters["tired"] += 1.0
    hero.memes["worry"] += 1.0
    world.para()
    world.say(
        f"{hero.id} wanted to {verb} {place}, but the spots said, "
        f"\"No, no, not today.\""
    )
    world.say(
        f"{helper.id} came near and said, \"Rest first, my friend; "
        f"we'll make a kind, calm bed.\""
    )


def magic_rhyme(world: MeaslesWorld) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    spellbook: Entity = world.facts["spellbook"]
    verb = world.facts["verb_info"]["inf"]
    world.para()
    world.say(
        f"{helper.id} opened the {spellbook.label} and whispered, "
        f"\"Bing-bong, hush-hush, soft as snow, let the itchy spots grow slow.\""
    )
    world.say(
        f"{sfx('magic')} went the spell, bright and light, and the room grew warm and right."
    )
    hero.memes["hope"] += 1.5
    hero.meters["itch"] = max(0.0, hero.meters["itch"] - 1.5)
    hero.meters["tired"] = max(0.0, hero.meters["tired"] - 0.5)
    world.say(
        f"{hero.id} still could not {verb} yet, but the worry felt much smaller."
    )


def ending(world: MeaslesWorld) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    verb = world.facts["verb_info"]["gerund"]
    hero.memes["joy"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    world.para()
    world.say(
        f"{hero.id} curled up under a quilt, listening to {helper.id} hum "
        f"la-la soft as foam."
    )
    world.say(
        f"Later, when the spots felt less hot, {hero.id} smiled, "
        f"and the little pirate would soon be {verb} again."
    )
    world.say(
        f"Until then, the ship was quiet, the magic was kind, and the brave "
        f"pirate rested with a peaceful sigh."
    )


def tell(params: StoryParams) -> MeaslesWorld:
    world = build_world(params)
    intro(world)
    trouble(world)
    magic_rhyme(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% The pirate wants to verb.
wants(H, V) :- hero(H), verb(V).

% Measles make the pirate itchy and tired.
unwell(H) :- has_measles(H).

% A magic helper can soothe the pirate if the helper knows a spell.
can_help(H) :- helper(H), has_spellbook(H).

% A reasonable story includes trouble plus help and a softer ending.
good_story(S) :- wants(H, V), unwell(H), can_help(K), hero(H), helper(K), story_verb(S, V).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid in VERBS:
        lines.append(asp.fact("verb", vid))
    for name in HERO_NAMES:
        lines.append(asp.fact("hero_name", name))
    for name in HELPER_NAMES:
        lines.append(asp.fact("helper_name", name))
    lines.append(asp.fact("has_measles", "pirate"))
    lines.append(asp.fact("hero", "pirate"))
    lines.append(asp.fact("helper", "magic_friend"))
    lines.append(asp.fact("has_spellbook", "magic_friend"))
    for vid in VERBS:
        lines.append(asp.fact("story_verb", "story1", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show wants/2.\n#show unwell/1.\n#show can_help/1.")
    model = asp.one_model(program)
    wants = asp.atoms(model, "wants")
    unwell = asp.atoms(model, "unwell")
    can_help = asp.atoms(model, "can_help")
    ok = ("pirate", "sail") in wants and ("pirate",) in unwell and ("magic_friend",) in can_help
    if ok:
        print("OK: ASP gate agrees with the Python story premise.")
        return 0
    print("MISMATCH: ASP gate does not match the Python premise.")
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: MeaslesWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child about a pirate with measles who wants to {f["verb"]}.',
        f"Tell a gentle magic story where {f['hero'].id} feels itchy from measles, but a kind helper uses rhyme and sound effects.",
        f"Make a tiny pirate tale with the words measles, pirate, and {f['verb']}, ending in rest and hope.",
    ]


def story_qa(world: MeaslesWorld) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    verb = f["verb_info"]["inf"]
    gerund = f["verb_info"]["gerund"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.phrase}, a pirate who has measles and wants to {verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the magic helped?",
            answer=f"{hero.id} wanted to {verb}, and loved {gerund}, but the measles made the day hard.",
        ),
        QAItem(
            question=f"Who used magic to help {hero.id}?",
            answer=f"{helper.id} used a spellbook, a rhyme, and a soft voice to help {hero.id} rest.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} resting, feeling calmer, and hoping to {verb} again soon.",
        ),
    ]


def world_knowledge_qa(world: MeaslesWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is measles?",
            answer="Measles is an illness that can make a child feel tired, feverish, and covered in itchy spots.",
        ),
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a sailor from old stories who sails on a ship and often looks for treasure.",
        ),
        QAItem(
            question="What does a rhyme do in a story?",
            answer="A rhyme makes words sound musical when their endings match, which can make a story fun to hear.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are small words like swish or bing that help the reader imagine the scene.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something surprising and impossible in real life, but it can help characters in stories.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: MeaslesWorld) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = ", ".join(f"{k}={v:.1f}" for k, v in sorted(ent.meters.items()) if v)
        memes = ", ".join(f"{k}={v:.1f}" for k, v in sorted(ent.memes.items()) if v)
        bits = []
        if meters:
            bits.append(f"meters[{meters}]")
        if memes:
            bits.append(f"memes[{memes}]")
        lines.append(f"{ent.id}: {ent.label or ent.kind} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: a pirate, measles, and magic help.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--verb", choices=VERBS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    verb = args.verb or rng.choice(sorted(VERBS))
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(setting=setting, verb=verb, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show wants/2.\n#show unwell/1.\n#show can_help/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show wants/2.\n#show unwell/1.\n#show can_help/1."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in sorted(SETTINGS):
            for verb in sorted(VERBS):
                params = StoryParams(
                    setting=setting,
                    verb=verb,
                    hero_name=HERO_NAMES[(len(samples) + 1) % len(HERO_NAMES)],
                    helper_name=HELPER_NAMES[(len(samples) + 2) % len(HELPER_NAMES)],
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### story {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
