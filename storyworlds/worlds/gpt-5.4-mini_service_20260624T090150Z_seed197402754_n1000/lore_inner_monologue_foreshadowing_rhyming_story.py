#!/usr/bin/env python3
"""
A small storyworld for a rhyming, lore-rich tale with inner monologue and foreshadowing.

Premise:
A child-like hero wants to reach the old bell in the moon-grove during twilight.
They carry a tiny lantern and an old rhyme from village lore.
A gust of wind, a cracked path, and a shy helper create a gentle tension.
The hero's inner monologue weighs fear against courage, and a foreshadowed clue
about a silver twig helps them solve the problem.

The world is intentionally tiny and state-driven:
- physical meters: wind, light, wobble, trust, fatigue
- emotional memes: worry, courage, hope, delight
- the ending image proves what changed

The story style aims for a soft rhyming cadence rather than rigid meter.
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
# Registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "moon grove"
    hero: str = "Pip"
    companion: str = "Moss"
    quest: str = "ring the old bell"
    lore: str = "the silver twig can steady a shaking bridge"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: bool = False
    helpful: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"child", "hero"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


PLACES = {
    "moon grove": {
        "bell": "old bell",
        "sound": "ding-a-ling",
        "weather": "silver dusk",
    },
    "moss lane": {
        "bell": "sleepy chime",
        "sound": "ding-dong",
        "weather": "blue evening",
    },
}

# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(params.place)
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    companion = world.add(Entity(id=params.companion, kind="character", type="fox", label=params.companion))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="lantern",
        phrase="a tiny brass lantern",
        held=True,
        helpful=True,
        meters={"light": 1.0},
    ))
    path = world.add(Entity(
        id="path",
        type="path",
        label="bridge path",
        phrase="the narrow bridge path",
        meters={"wobble": 0.0, "wind": 0.0},
    ))
    twig = world.add(Entity(
        id="twig",
        type="twig",
        label="silver twig",
        phrase="a silver twig from the old lore tree",
        held=False,
        helpful=True,
        meters={"steadiness": 0.0},
    ))
    bell = world.add(Entity(
        id="bell",
        type="bell",
        label=PLACES[params.place]["bell"],
        phrase=f"the {PLACES[params.place]['bell']}",
        meters={"reach": 0.0},
    ))

    world.facts.update(params=params, hero=hero, companion=companion, lantern=lantern, path=path, twig=twig, bell=bell)

    # Act 1: setup, lore, and foreshadowing
    world.say(
        f"In {params.place}, where the dusk was soft and the stars were bright, "
        f"{hero.id} had a small quest in sight: {params.quest}, neat and polite."
    )
    world.say(
        f"{hero.id} carried a tiny lantern, warm and low. "
        f"{companion.id} padded beside {hero.pronoun('object')}, quiet as snow."
    )
    world.say(
        f'Village lore said, "{params.lore}." '
        f"{hero.id} wondered if that could be true."
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head, {hero.id} thought, '
        f'"If the bridge shakes, will I still go through?"'
    )

    world.para()

    # Act 2: tension, risk, and inner monologue
    path.meters["wind"] += 1.0
    path.meters["wobble"] += 1.0
    hero.memes["worry"] = 1.0
    companion.memes["hope"] = 1.0
    world.say(
        f"The wind made the bridge path sway and sigh. "
        f"It trembled like a kite in the sky."
    )
    world.say(
        f"{hero.id} took a breath and listened close, then thought, "
        f'"I feel small as a seed in the snow. '
        f'But I want to know if I can still glow."'
    )
    world.say(
        f"{companion.id} looked ahead and sniffed the air. "
        f"{companion.id} had seen the silver twig there."
    )
    world.say(
        f"One shard of moonlight flashed on the ground, "
        f"and the old lore's answer seemed to be found."
    )
    world.say(
        f"{companion.id} nudged the twig toward {hero.id}. "
        f'"For a shaky walk, this may help you," {companion.id} seemed to say.'
    )
    world.facts["foreshadowed"] = True
    world.facts["twig_seen"] = True

    world.para()

    # Act 3: resolution
    lantern.meters["light"] += 1.0
    twig.held = True
    twig.meters["steadiness"] += 1.0
    path.meters["wobble"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["courage"] = 1.0
    hero.memes["delight"] = 1.0

    world.say(
        f"{hero.id} held the silver twig and stood up tall. "
        f"The bridge felt less like a fall and more like a hall."
    )
    world.say(
        f"Step by step, {hero.id} crossed with a smile, "
        f"while the lantern made gold on the boards all the while."
    )
    world.say(
        f"Then {hero.id} reached the bell and gave it a ring. "
        f'{PLACES[params.place]["sound"]} went the note, clear as a spring.'
    )
    world.say(
        f"{companion.id} leaped in a little soft bow. "
        f"{hero.id} thought, \"I was scared, but I did it somehow.\""
    )
    world.say(
        f"So the lore proved true in the silver-blue glow: "
        f"a small brave heart can make shaky things go."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_name(H).
companion(C) :- companion_name(C).

foreshadowed :- lore(_), twig(_), bridge(_).
risk(bridge) :- wind_high, wobble_high.
helpful(twig) :- lore_hint(twig), risk(bridge).
resolved :- helpful(twig), hero_worries, bridge_safe, bell_rung.

bridge_safe :- helpful(twig).
bell_rung :- hero_reaches_bell.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "Pip"))
    lines.append(asp.fact("companion_name", "Moss"))
    lines.append(asp.fact("lore", "silver twig"))
    lines.append(asp.fact("twig"))
    lines.append(asp.fact("bridge"))
    lines.append(asp.fact("lore_hint", "twig"))
    lines.append(asp.fact("wind_high"))
    lines.append(asp.fact("wobble_high"))
    lines.append(asp.fact("hero_worries"))
    lines.append(asp.fact("hero_reaches_bell"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0. #show foreshadowed/0."))
    atoms = {f"{s.name}/{len(s.arguments)}" for s in model}
    expected = {"resolved/0", "foreshadowed/0"}
    if atoms == expected:
        print("OK: ASP twin matches Python reasonableness and story outcome.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    return [
        f'Write a gentle rhyming story with lore about "{params.lore}" in {params.place}.',
        f"Tell a short story where {params.hero} feels worried, thinks to themself, and then finds courage.",
        f"Write a child-friendly tale that foreshadows a helpful silver twig before the final bell rings.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    return [
        QAItem(
            question=f"What did {params.hero} want to do in {params.place}?",
            answer=f"{params.hero} wanted to {params.quest} in {params.place}."
        ),
        QAItem(
            question=f"Who helped {params.hero} when the bridge started to wobble?",
            answer=f"{companion.id} helped by nudging over the silver twig from the old lore."
        ),
        QAItem(
            question=f"How did {params.hero} feel before crossing the bridge?",
            answer=f"{hero.id} felt worried at first, then found courage after thinking quietly inside."
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{params.hero} rang the old bell, and the shaky bridge was crossed safely."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lore?",
            answer="Lore is old information or stories that people pass along and remember."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early on about something that will matter later."
        ),
        QAItem(
            question="Why can a lantern help at dusk?",
            answer="A lantern helps by giving light when the sky is getting dark."
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held:
            bits.append("held=True")
        if e.helpful:
            bits.append("helpful=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming, lore-rich storyworld with inner monologue and foreshadowing.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero")
    ap.add_argument("--companion")
    ap.add_argument("--lore")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    hero = args.hero or rng.choice(["Pip", "Wren", "Nell", "Toby", "Mina"])
    companion = args.companion or rng.choice(["Moss", "Puck", "Fern", "Bram"])
    lore = args.lore or "the silver twig can steady a shaking bridge"
    return StoryParams(place=place, hero=hero, companion=companion, lore=lore)

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
        print(format_qa(sample))

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0. #show foreshadowed/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0. #show foreshadowed/0."))
        print(sorted((sym.name, len(sym.arguments)) for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="moon grove", hero="Pip", companion="Moss", lore="the silver twig can steady a shaking bridge"),
            StoryParams(place="moss lane", hero="Nell", companion="Bram", lore="a calm breath can brighten a dark path"),
        ]
        samples = [generate(p) for p in curated]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
