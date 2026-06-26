#!/usr/bin/env python3
"""
A tiny fairy-tale storyworld about a child, a borrowed persona, and a boomerang
that keeps coming back until someone learns how to rouse the right courage.

Seed-inspired premise:
- A shy child puts on a flashy persona to sound brave.
- A boomerang is used in a funny little challenge.
- The boomerang returns, causing a comic mess and a social wobble.
- A gentle rouse from a helper turns pretend-bravery into real bravery.

This world is intentionally small, constraint-checked, and state-driven.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman", "mother"}
        male = {"boy", "king", "prince", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
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


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    persona: str
    boomerang: str
    seed: Optional[int] = None


SETTINGS = {
    "castle_courtyard": "the castle courtyard",
    "forest_glade": "the forest glade",
    "village_square": "the village square",
}


@dataclass
class Persona:
    id: str
    label: str
    style: str
    brave_words: list[str]
    silliness: str


@dataclass
class Boomerang:
    id: str
    label: str
    phrase: str
    returns: bool = True
    mischievous: bool = True


PERSONAS = {
    "knightly": Persona(
        id="knightly",
        label="a knightly persona",
        style="knightly",
        brave_words=["bold", "steadfast", "ready"],
        silliness="a little too grand",
    ),
    "royal": Persona(
        id="royal",
        label="a royal persona",
        style="royal",
        brave_words=["noble", "calm", "sure"],
        silliness="very shiny and a bit silly",
    ),
    "forest": Persona(
        id="forest",
        label="a forest-hero persona",
        style="forest-hero",
        brave_words=["swift", "bright", "fearless"],
        silliness="as leafy as a joke in midsummer",
    ),
}

BOOMERANGS = {
    "oak": Boomerang(
        id="oak",
        label="an oak boomerang",
        phrase="a polished oak boomerang",
    ),
    "moon": Boomerang(
        id="moon",
        label="a moon boomerang",
        phrase="a crescent-shaped moon boomerang",
    ),
    "berry": Boomerang(
        id="berry",
        label="a berry-painted boomerang",
        phrase="a berry-painted boomerang with a bright red stripe",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lina", "Perry", "Nora", "Jasper"]
HELPER_NAMES = ["Gran", "Moss", "Bram", "Ivy", "Milo", "Wren"]
TRAITS = ["shy", "curious", "small", "cheerful", "timid", "thoughtful"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_boomerang_return(world: World) -> list[str]:
    hero = world.get("hero")
    boom = world.get("boomerang")
    if hero.meters.get("thrown", 0) < THRESHOLD:
        return []
    if ("return", boom.id) in world.fired:
        return []
    world.fired.add(("return", boom.id))
    hero.meters["surprise"] = hero.meters.get("surprise", 0) + 1
    hero.memes["wobble"] = hero.memes.get("wobble", 0) + 1
    boom.carried_by = hero.id
    return [f"The boomerang zipped back at once and nearly bonked {hero.id}'s hat."]


def _r_panic(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes.get("wobble", 0) < THRESHOLD:
        return []
    if ("panic", hero.id) in world.fired:
        return []
    world.fired.add(("panic", hero.id))
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    return [f"{hero.id} felt their borrowed brave words flutter like paper in the wind."]


def _r_rouse(world: World) -> list[str]:
    helper = world.get("helper")
    hero = world.get("hero")
    if helper.meters.get("rouse", 0) < THRESHOLD:
        return []
    if ("roused", hero.id) in world.fired:
        return []
    world.fired.add(("roused", hero.id))
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    hero.memes["doubt"] = max(0.0, hero.memes.get("doubt", 0) - 1)
    return [f"{helper.id} gave a gentle rouse: 'You do not need a false crown to be brave.'"]


CAUSAL_RULES = [
    Rule("boomerang_return", _r_boomerang_return),
    Rule("panic", _r_panic),
    Rule("rouse", _r_rouse),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_return(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").meters["thrown"] = 1
    propagate(sim, narrate=False)
    return sim.get("hero").meters.get("surprise", 0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    persona = PERSONAS[params.persona]
    boom = BOOMERANGS[params.boomerang]

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="girl" if params.hero in {"Mina", "Lina", "Nora"} else "boy",
        traits=["little", TRAITS[hash(params.hero) % len(TRAITS)]],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="woman" if params.helper in {"Gran", "Ivy", "Wren"} else "man",
        traits=["kind", "steady"],
    ))
    persona_ent = world.add(Entity(
        id="persona",
        type="persona",
        label=persona.label,
        phrase=f"a borrowed {persona.style} persona",
        owner=hero.id,
    ))
    boomerang_ent = world.add(Entity(
        id="boomerang",
        type="boomerang",
        label=boom.label,
        phrase=boom.phrase,
        owner=hero.id,
        carried_by=hero.id,
    ))

    hero.memes["shy"] = 1
    hero.memes["hope"] = 1
    hero.meters["poise"] = 0

    world.say(
        f"In {world.setting}, {hero.id} was a little {hero.traits[1]} child who loved {persona.label} stories."
    )
    world.say(
        f"To sound bold, {hero.id} put on {persona_ent.phrase} and tried to speak in a {persona.silliness} voice."
    )
    world.say(
        f"Then {hero.id} found {boom_ent.phrase} beside a mossy stone and laughed at its funny curve."
    )

    world.para()
    world.say(
        f"'{hero.id} will show the village a grand trick,' the borrowed persona seemed to say."
    )
    if predict_return(world):
        world.say(
            f"So {hero.id} tossed the boomerang high, hoping to look like a true tale-hero."
        )
    hero.meters["thrown"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{hero.id} blinked at the quick return and nearly forgot the grand words."
    )
    helper.meters["rouse"] = 1
    helper.meters["comfort"] = 1
    propagate(world, narrate=True)
    world.say(
        f"After that, {hero.id} did not need to pretend so hard. {hero.id} took a breath, smiled, and tried again with honest courage."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        persona=persona_ent,
        boomerang=boomerang_ent,
        setting=world.setting,
        persona_cfg=persona,
        boomerang_cfg=boom,
        roused=hero.memes.get("courage", 0) >= THRESHOLD,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    persona = f["persona_cfg"]
    boom = f["boomerang_cfg"]
    return [
        QAItem(
            question=f"Why did {hero.id} wear a persona at the start of the story?",
            answer=(
                f"{hero.id} felt shy and wanted to sound brave, so {hero.pronoun('subject')} tried on "
                f"{persona.label} as if it were a costume of courage."
            ),
        ),
        QAItem(
            question=f"What funny thing happened when {hero.id} threw the boomerang?",
            answer=(
                f"The {boom.label} came flying back right away, which startled {hero.id} and made the scene silly."
            ),
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} in the end?",
            answer=(
                f"{helper.id} gave a gentle rouse and reminded {hero.id} that real bravery does not need a false crown."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boomerang?",
            answer="A boomerang is a curved tool that can fly out and then come back to the person who threw it.",
        ),
        QAItem(
            question="What does it mean to rouse someone?",
            answer="To rouse someone is to wake them up or stir up their energy and attention.",
        ),
        QAItem(
            question="What is a persona?",
            answer="A persona is the kind of role or face a person shows to others, like a brave mask or a royal way of speaking.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for pid, p in PERSONAS.items():
        lines.append(asp.fact("persona", pid))
        lines.append(asp.fact("persona_label", pid, p.style))
    for bid, b in BOOMERANGS.items():
        lines.append(asp.fact("boomerang", bid))
        if b.returns:
            lines.append(asp.fact("returns", bid))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when a child can wear a persona, throw a boomerang,
% and then be roused into genuine courage.
can_tell(P, B) :- persona(P), boomerang(B), returns(B).
needs_rouse(P, B) :- can_tell(P, B).
happy_turn(P, B) :- needs_rouse(P, B).
#show can_tell/2.
#show needs_rouse/2.
#show happy_turn/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_tell/2."))
    return sorted(set(asp.atoms(model, "can_tell")))


def asp_verify() -> int:
    py = {(p, b) for p in PERSONAS for b in BOOMERANGS if BOOMERANGS[b].returns}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld of persona, boomerang, and rouse.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--persona", choices=PERSONAS)
    ap.add_argument("--boomerang", choices=BOOMERANGS)
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    persona = args.persona or rng.choice(list(PERSONAS))
    boomerang = args.boomerang or rng.choice(list(BOOMERANGS))
    if helper == hero:
        raise StoryError("The hero and helper must be different characters.")
    return StoryParams(place=place, hero=hero, helper=helper, persona=persona, boomerang=boomerang)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            "Write a short fairy tale about a shy child, a borrowed persona, and a boomerang that keeps coming back.",
            "Tell a humorous story where a child pretends to be brave, throws a boomerang, and learns real courage.",
        ],
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
        print(asp_program("#show can_tell/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible persona/boomerang combos:\n")
        for p, b in models:
            print(f"  {p:10} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in PERSONAS:
            for b in BOOMERANGS:
                params = StoryParams(
                    place=next(iter(SETTINGS)),
                    hero=HERO_NAMES[hash(p) % len(HERO_NAMES)],
                    helper=HELPER_NAMES[hash(b) % len(HELPER_NAMES)],
                    persona=p,
                    boomerang=b,
                    seed=base_seed,
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
