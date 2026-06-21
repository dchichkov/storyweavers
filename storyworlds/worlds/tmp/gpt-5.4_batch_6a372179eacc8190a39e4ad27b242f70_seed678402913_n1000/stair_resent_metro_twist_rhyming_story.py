#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py
====================================================================

A small storyworld about a child hurrying into the metro, resenting a slow trip
down the station stair, and then learning a hidden reason for the delay. The
world is built to read like a simple rhyming story with a twist: the grown-up
was not being fussy for nothing, but protecting a delicate surprise.

The model keeps a compact physical/emotional simulation:
- climbing the stair makes bodies tired
- hurrying while delayed grows resentment
- a hidden delicate cargo creates the need for careful steps
- the reveal changes the child's feeling from resentment to care

The reasonableness gate is intentionally narrow:
- only delicate cargo counts as a real reason to avoid a jolting escalator
- each occasion only accepts fitting cargo
- explicitly robust cargo is refused

Run it
------
python storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py
python storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py --occasion birthday --cargo cupcake_box
python storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py --cargo soccer_ball
python storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/stair_resent_metro_twist_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Occasion:
    id: str
    ride_to: str
    receiver: str
    event: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    delicate: bool = False
    reason: str = ""
    clue: str = ""
    reveal: str = ""
    ending_image: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tired(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    if child.meters["steps"] < 1:
        return []
    sig = ("tired",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["tired"] += 1
    return []


def _r_resent(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    if child.meters["tired"] < THRESHOLD:
        return []
    if child.memes["hurry"] < THRESHOLD:
        return []
    if child.memes["understands"] >= THRESHOLD:
        return []
    sig = ("resent",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["resentment"] += 1
    return []


def _r_soften(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    if child.memes["understands"] < THRESHOLD:
        return []
    sig = ("soften",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["resentment"] = 0.0
    child.memes["care"] += 1
    child.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="tired", tag="physical", apply=_r_tired),
    Rule(name="resent", tag="emotional", apply=_r_resent),
    Rule(name="soften", tag="emotional", apply=_r_soften),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        # also detect changes from newly fired rules with no text
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) > before:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


OCCASIONS = {
    "birthday": Occasion(
        id="birthday",
        ride_to="the blue-line metro",
        receiver="Cousin June",
        event="a birthday tea",
        reveal_line="for Cousin June's birthday table",
        tags={"birthday", "metro"},
    ),
    "grandma_visit": Occasion(
        id="grandma_visit",
        ride_to="the green-line metro",
        receiver="Grandma Nell",
        event="an afternoon visit",
        reveal_line="for Grandma Nell's sunny shelf",
        tags={"grandma", "metro"},
    ),
    "school_play": Occasion(
        id="school_play",
        ride_to="the red-line metro",
        receiver="the school stage",
        event="the class play",
        reveal_line="for the class play after school",
        tags={"school", "metro"},
    ),
}

CARGO = {
    "cupcake_box": Cargo(
        id="cupcake_box",
        label="cupcake box",
        phrase="a white cupcake box tied with blue string",
        delicate=True,
        reason="the icing would slosh and slide on the jolting escalator",
        clue="a sweet vanilla smell",
        reveal="Inside the tote sat a neat row of cupcakes with swirls like little moons.",
        ending_image="On the metro seat, the box stayed level and the moon-swirl icing still stood high.",
        tags={"cupcakes", "fragile"},
    ),
    "snow_globe": Cargo(
        id="snow_globe",
        label="snow globe",
        phrase="a little snow globe wrapped in a scarf",
        delicate=True,
        reason="one bump could crack the glass against the hard rail",
        clue="a tiny clink like glass kissing glass",
        reveal="Inside the tote lay a snow globe with silver flakes waiting to whirl.",
        ending_image="On the metro seat, the globe caught the lights, and the silver flakes slept safely inside.",
        tags={"glass", "fragile"},
    ),
    "paper_crown": Cargo(
        id="paper_crown",
        label="paper crown",
        phrase="a gold paper crown dotted with foil stars",
        delicate=True,
        reason="the crowded escalator could crush the foil stars flat",
        clue="a flash of gold foil peeking from the tote",
        reveal="Inside the tote rested a paper crown, bright as a tiny sun and light as a song.",
        ending_image="On the metro seat, the crown kept all its stars, sharp and bright in the train-car light.",
        tags={"craft", "fragile"},
    ),
    "soccer_ball": Cargo(
        id="soccer_ball",
        label="soccer ball",
        phrase="a scuffed soccer ball",
        delicate=False,
        reason="",
        clue="",
        reveal="",
        ending_image="",
        tags={"ball"},
    ),
    "sweater": Cargo(
        id="sweater",
        label="sweater",
        phrase="a folded wool sweater",
        delicate=False,
        reason="",
        clue="",
        reveal="",
        ending_image="",
        tags={"clothes"},
    ),
}

FITS = {
    "birthday": {"cupcake_box", "paper_crown"},
    "grandma_visit": {"snow_globe", "cupcake_box"},
    "school_play": {"paper_crown"},
}

CHILD_NAMES = {
    "girl": ["Mina", "Lila", "Nora", "Tess", "Ava", "Ruby"],
    "boy": ["Owen", "Leo", "Milo", "Finn", "Eli", "Theo"],
}
ADULT_TYPES = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["bouncy", "curious", "quick", "eager", "bright"]


def valid_combo(occasion_id: str, cargo_id: str) -> bool:
    if occasion_id not in OCCASIONS or cargo_id not in CARGO:
        return False
    cargo = CARGO[cargo_id]
    return cargo.delicate and cargo_id in FITS.get(occasion_id, set())


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for occasion_id in OCCASIONS:
        for cargo_id in CARGO:
            if valid_combo(occasion_id, cargo_id):
                out.append((occasion_id, cargo_id))
    return out


@dataclass
class StoryParams:
    occasion: str
    cargo: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    hurry: int = 1
    seed: Optional[int] = None


def station_opening(occasion: Occasion) -> str:
    return (
        f"Morning hummed in the station bright and mellow, "
        f"while they hurried for {occasion.ride_to} below."
    )


def introduce(world: World, child: Entity, adult: Entity, occasion: Occasion) -> None:
    world.say(
        f"{child.id} was a little {next(iter([t for t in child.traits if t] or ['quick']))} "
        f"{child.type} with shoes that loved to go. {station_opening(occasion)}"
    )
    world.say(
        f"{child.id} and {child.pronoun('possessive')} {adult.label_word} were bound for "
        f"{occasion.event}, and the turnstiles gave a silver glow."
    )


def want_fast_way(world: World, child: Entity) -> None:
    child.memes["hurry"] += 1
    world.say(
        f'The escalator purred, "Come quick, come quick," with a shiny, rolling flow; '
        f'but {child.id} pointed down and said, "That is the way to go!"'
    )


def choose_stair(world: World, child: Entity, adult: Entity) -> None:
    adult.memes["care"] += 1
    world.say(
        f'Yet {child.pronoun("possessive").capitalize()} {adult.label_word} shook '
        f'{adult.pronoun("possessive")} head and chose the station stair below. '
        f'"Slow feet now," {adult.pronoun()} said, "and soon we still will go."'
    )


def climb(world: World, child: Entity, cargo_cfg: Cargo) -> None:
    child.meters["steps"] += 1
    propagate(world, narrate=False)
    if child.memes["resentment"] >= THRESHOLD:
        world.say(
            f"Step by step went clump and thump; the rail felt cold as snow. "
            f"{child.id} began to resent the slow, slow trip and wished for one fast swoop below."
        )
    else:
        world.say(
            f"Step by step went clump and thump as echoes bounced in tow. "
            f"{child.id} watched the stair and wondered why they had to move so slow."
        )
    if cargo_cfg.clue:
        world.say(
            f"Then from the tote there slipped {cargo_cfg.clue}, a tiny secret sign to know."
        )


def explain(world: World, child: Entity, adult: Entity, occasion: Occasion, cargo_cfg: Cargo) -> None:
    child.memes["understands"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{adult.label_word.capitalize()} paused upon the middle stair and lifted up the tote just so. '
        f'"I picked the stair because {cargo_cfg.reason}," {adult.pronoun()} said, '
        f'"and what I carry must not tip or blow."'
    )
    world.say(
        f"{cargo_cfg.reveal} It was hidden there {occasion.reveal_line}, "
        f"and that was the twist {child.id} did not know."
    )


def help_carry(world: World, child: Entity, adult: Entity, cargo_cfg: Cargo) -> None:
    child.memes["care"] += 1
    child.memes["love"] += 1
    world.say(
        f'At once the hard little frown grew soft. "{adult.label_word.capitalize()}, '
        f'I thought you were only being slow," said {child.id}.'
    )
    world.say(
        f"Then {child.pronoun()} tucked both hands beneath the tote and matched "
        f"{adult.pronoun('possessive')} careful toe to toe. Together they walked "
        f"so still and small that even the station wind seemed low."
    )


def ride_and_end(world: World, child: Entity, adult: Entity, occasion: Occasion, cargo_cfg: Cargo) -> None:
    world.say(
        f"The train came singing through the tunnel dark with a rumbling, friendly show. "
        f"They boarded the metro side by side, not rushed, but calm and proud to go."
    )
    world.say(
        f"{cargo_cfg.ending_image} {child.id} no longer felt resentful at the stair; "
        f"{child.pronoun()} leaned on {adult.pronoun('possessive')} shoulder and smiled at what care can grow."
    )


def tell(
    occasion: Occasion,
    cargo_cfg: Cargo,
    *,
    child_name: str,
    child_gender: str,
    adult_type: str,
    trait: str,
    hurry: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
        )
    )
    adult = world.add(
        Entity(
            id="adult",
            kind="character",
            type=adult_type,
            label="the grown-up",
            role="adult",
        )
    )
    tote = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="cargo",
            label=cargo_cfg.label,
            phrase=cargo_cfg.phrase,
            role="cargo",
            tags=set(cargo_cfg.tags),
        )
    )
    child.attrs["name"] = child_name
    adult.attrs["name"] = adult.label_word
    tote.attrs["delicate"] = cargo_cfg.delicate
    world.facts["occasion"] = occasion
    world.facts["cargo_cfg"] = cargo_cfg
    world.facts["child_name"] = child_name

    if hurry > 0:
        child.memes["hurry"] = float(hurry)

    introduce(world, child, adult, occasion)
    world.para()
    want_fast_way(world, child)
    choose_stair(world, child, adult)
    climb(world, child, cargo_cfg)
    world.para()
    explain(world, child, adult, occasion, cargo_cfg)
    help_carry(world, child, adult, cargo_cfg)
    world.para()
    ride_and_end(world, child, adult, occasion, cargo_cfg)

    world.facts.update(
        child=child,
        adult=adult,
        cargo=tote,
        resent_before=child.meters["tired"] >= THRESHOLD and hurry > 0,
        understood=child.memes["understands"] >= THRESHOLD,
        softened=child.memes["care"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "metro": [
        (
            "What is a metro?",
            "A metro is a train that runs through a city and stops at stations. People use it to travel quickly from one place to another.",
        )
    ],
    "stair": [
        (
            "What is a stair?",
            "A stair is one step in a stairway. You climb stairs one step at a time to go up or down safely.",
        )
    ],
    "escalator": [
        (
            "What is an escalator?",
            "An escalator is a moving stairway. It can help people travel up or down, but you still have to stand carefully on it.",
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can break, bend, or get spoiled easily. Fragile things need gentle hands and careful movement.",
        )
    ],
    "cupcakes": [
        (
            "Why can cupcakes be hard to carry?",
            "Cupcakes have soft icing on top. If the box tips or bumps too much, the icing can slide and get squished.",
        )
    ],
    "glass": [
        (
            "Why must glass be carried carefully?",
            "Glass can crack or shatter if it hits something hard. That is why people move glass things slowly and gently.",
        )
    ],
    "craft": [
        (
            "Why can a paper crown get ruined?",
            "Paper can bend, crush, or tear if it gets pressed in a crowd. Foil stars can wrinkle too.",
        )
    ],
    "birthday": [
        (
            "Why do people bring treats to birthdays?",
            "People often bring treats to birthdays to celebrate together. Sharing a special treat helps the party feel joyful.",
        )
    ],
    "grandma": [
        (
            "Why might someone bring a gift to visit a grandma?",
            "A small gift can show love and thoughtfulness. It is one way to make a visit feel warm and special.",
        )
    ],
    "school": [
        (
            "Why do costumes and crowns matter in a school play?",
            "Costumes help children look like their story characters. A crown can help the audience understand who a character is.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "metro",
    "stair",
    "escalator",
    "fragile",
    "cupcakes",
    "glass",
    "craft",
    "birthday",
    "grandma",
    "school",
]


def generation_prompts(world: World) -> list[str]:
    occasion = world.facts["occasion"]
    cargo_cfg = world.facts["cargo_cfg"]
    child_name = world.facts["child_name"]
    return [
        (
            f'Write a short rhyming story for a 3-to-5-year-old that uses the words '
            f'"stair", "resent", and "metro". Include a gentle twist.'
        ),
        (
            f"Tell a rhyming story where {child_name} wants the fast way at a metro station, "
            f"but a grown-up chooses the stair because of {cargo_cfg.label}, and the child first feels resentful."
        ),
        (
            f"Write a child-facing twist story set on the way to {occasion.event}, where the slow stair choice "
            f"turns out to be a caring choice and the ending shows what stayed safe."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    occasion = world.facts["occasion"]
    cargo_cfg = world.facts["cargo_cfg"]
    child_name = child.attrs.get("name", child.label or "the child")
    adult_word = adult.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name} and {child_name}'s {adult_word} on the way to {occasion.event}. They are hurrying into the metro station together.",
        ),
        (
            f"Why did {child_name} feel upset on the stair at first?",
            f"{child_name} wanted the fast escalator, but {adult_word} chose the stair and moved slowly instead. The slow climb made {child_name} tired and resentful before {child.pronoun()} understood why.",
        ),
        (
            f"What was the twist in the story?",
            f"The grown-up was not choosing the stair just to be slow. {adult_word.capitalize()} was protecting {cargo_cfg.phrase}, because {cargo_cfg.reason}.",
        ),
        (
            f"How did {child_name} change after learning the reason?",
            f"{child_name} stopped feeling resentful and started helping carry the tote carefully. Understanding the reason changed the stair from something annoying into something kind.",
        ),
        (
            "How did the story end?",
            f"They rode the metro calmly with the surprise still safe. The ending image shows that careful steps on the stair helped the {cargo_cfg.label} arrive the right way.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    occasion = world.facts["occasion"]
    cargo_cfg = world.facts["cargo_cfg"]
    tags = {"metro", "stair", "escalator", "fragile"} | set(occasion.tags) | set(cargo_cfg.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        occasion="birthday",
        cargo="cupcake_box",
        child_name="Mina",
        child_gender="girl",
        adult_type="father",
        trait="eager",
        hurry=2,
        seed=1,
    ),
    StoryParams(
        occasion="grandma_visit",
        cargo="snow_globe",
        child_name="Leo",
        child_gender="boy",
        adult_type="grandmother",
        trait="curious",
        hurry=1,
        seed=2,
    ),
    StoryParams(
        occasion="school_play",
        cargo="paper_crown",
        child_name="Ruby",
        child_gender="girl",
        adult_type="mother",
        trait="quick",
        hurry=2,
        seed=3,
    ),
]


def explain_rejection(occasion_id: str, cargo_id: str) -> str:
    if cargo_id not in CARGO:
        return f"(No story: unknown cargo '{cargo_id}'.)"
    cargo_cfg = CARGO[cargo_id]
    if not cargo_cfg.delicate:
        return (
            f"(No story: {cargo_cfg.label} is not delicate enough to justify avoiding the escalator. "
            f"This world only tells metro-stair twist stories when careful steps protect something fragile.)"
        )
    allowed = ", ".join(sorted(FITS.get(occasion_id, set())))
    return (
        f"(No story: {cargo_cfg.label} does not fit the occasion '{occasion_id}'. "
        f"Try one of: {allowed}.)"
    )


ASP_RULES = r"""
delicate_reason(C) :- cargo(C), delicate(C).
valid(O, C) :- occasion(O), cargo(C), delicate_reason(C), fits(O, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for occasion_id in OCCASIONS:
        lines.append(asp.fact("occasion", occasion_id))
    for cargo_id, cargo_cfg in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        if cargo_cfg.delicate:
            lines.append(asp.fact("delicate", cargo_id))
    for occasion_id, cargoes in FITS.items():
        for cargo_id in sorted(cargoes):
            lines.append(asp.fact("fits", occasion_id, cargo_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_emit(sample: StorySample) -> None:
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=False, header="")
    finally:
        sys.stdout = old
    text = buf.getvalue()
    if not text.strip():
        raise StoryError("Smoke emit produced no output.")


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if "metro" not in sample.story.lower() or "stair" not in sample.story.lower():
            raise StoryError("Smoke test story missed required seed words.")
        _smoke_emit(sample)
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming metro stair twist storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--occasion", choices=sorted(OCCASIONS))
    ap.add_argument("--cargo", choices=sorted(CARGO))
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--adult-type", choices=ADULT_TYPES)
    ap.add_argument("--hurry", type=int, choices=[1, 2], help="how rushed the child feels")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (occasion, cargo) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.occasion and args.cargo and not valid_combo(args.occasion, args.cargo):
        raise StoryError(explain_rejection(args.occasion, args.cargo))

    combos = [
        combo
        for combo in valid_combos()
        if (args.occasion is None or combo[0] == args.occasion)
        and (args.cargo is None or combo[1] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    occasion_id, cargo_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES[child_gender])
    adult_type = args.adult_type or rng.choice(ADULT_TYPES)
    trait = rng.choice(TRAITS)
    hurry = args.hurry if args.hurry is not None else rng.choice([1, 2])

    return StoryParams(
        occasion=occasion_id,
        cargo=cargo_id,
        child_name=child_name,
        child_gender=child_gender,
        adult_type=adult_type,
        trait=trait,
        hurry=hurry,
    )


def generate(params: StoryParams) -> StorySample:
    if params.occasion not in OCCASIONS:
        raise StoryError(f"(No story: unknown occasion '{params.occasion}'.)")
    if params.cargo not in CARGO:
        raise StoryError(f"(No story: unknown cargo '{params.cargo}'.)")
    if not valid_combo(params.occasion, params.cargo):
        raise StoryError(explain_rejection(params.occasion, params.cargo))
    if params.child_gender not in CHILD_NAMES:
        raise StoryError(f"(No story: unknown child gender '{params.child_gender}'.)")
    if params.adult_type not in ADULT_TYPES:
        raise StoryError(f"(No story: unknown adult type '{params.adult_type}'.)")

    world = tell(
        OCCASIONS[params.occasion],
        CARGO[params.cargo],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
        trait=params.trait,
        hurry=params.hurry,
    )

    story_text = world.render().replace("child", params.child_name)
    child_name = params.child_name
    story_text = story_text.replace("adult", world.facts["adult"].label_word.capitalize(), 1)
    story_text = story_text.replace("adult", world.facts["adult"].label_word)

    return StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (occasion, cargo) combos:\n")
        for occasion_id, cargo_id in combos:
            print(f"  {occasion_id:14} {cargo_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
            header = f"### {p.child_name}: {p.occasion} with {p.cargo}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
