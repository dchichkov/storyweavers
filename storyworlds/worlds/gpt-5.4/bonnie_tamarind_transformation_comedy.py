#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py
===================================================================

A standalone storyworld for a tiny comedy domain built from the seed words
"bonnie" and "tamarind" with the feature "Transformation".

Premise
-------
Bonnie wants to turn herself into a funny stage character for a little family
show. She spots tamarind paste and decides it might work like magic costume
paint. The world model only allows *reasonable* versions of that idea:
tamarind may be dabbed on a small washable skin area like an upper lip or chin,
but not worked into hair. A matching costume prop must also genuinely create the
intended transformed look. The story's turn comes from the sticky paste drooping
at exactly the wrong moment, after which a calm grown-up helps Bonnie wash it
off and complete the transformation the proper way.

Run it
------
    python storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py
    python storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py --look wizard --attempt chin --prop beard
    python storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py --attempt hair
    python storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py --all
    python storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bonnie_tamarind_transformation_comedy.py --verify
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
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    stage: str
    audience: str
    snack_spot: str


@dataclass
class Look:
    id: str
    title: str
    region: str                 # lip | chin
    idea: str
    reveal: str
    finale: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Attempt:
    id: str
    region: str                 # lip | chin | hair
    phrase: str
    line: str
    safe: bool
    sticky_gain: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    covers: str
    looks: set[str]
    entry: str
    tags: set[str] = field(default_factory=set)


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_droop(world: World) -> list[str]:
    out: list[str] = []
    bonnie = world.entities.get("bonnie")
    if bonnie is None:
        return out
    if bonnie.meters["sticky"] < THRESHOLD:
        return out
    sig = ("droop", world.facts.get("attempt_region", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bonnie.meters["drip"] += 1
    bonnie.memes["embarrassment"] += 1
    bonnie.memes["laughter"] += 1
    out.append("__droop__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    bonnie = world.entities.get("bonnie")
    prop = world.entities.get("prop")
    look = world.facts.get("look")
    if bonnie is None or prop is None or look is None:
        return out
    if bonnie.meters["clean"] < THRESHOLD:
        return out
    if prop.attrs.get("covers") != look.region:
        return out
    if look.id not in set(prop.attrs.get("looks", [])):
        return out
    sig = ("transform", look.id, prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bonnie.meters["transformed"] += 1
    bonnie.memes["confidence"] += 1
    bonnie.memes["joy"] += 1
    out.append("__transformed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("droop", "physical", _r_droop),
    Rule("transform", "social", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable_attempt(look: Look, attempt: Attempt) -> bool:
    return attempt.safe and attempt.region == look.region


def matching_prop(look: Look, prop: Prop) -> bool:
    return prop.covers == look.region and look.id in prop.looks


def valid_combo(look: Look, attempt: Attempt, prop: Prop) -> bool:
    return reasonable_attempt(look, attempt) and matching_prop(look, prop)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for look_id, look in LOOKS.items():
        for attempt_id, attempt in ATTEMPTS.items():
            for prop_id, prop in PROPS.items():
                if valid_combo(look, attempt, prop):
                    combos.append((look_id, attempt_id, prop_id))
    return combos


def explain_attempt_rejection(look: Look, attempt: Attempt) -> str:
    if not attempt.safe:
        return (
            f"(No story: putting tamarind on Bonnie's {attempt.region} is too sticky and messy. "
            f"Food can be washed from a small skin spot, but it should not be worked into hair.)"
        )
    return (
        f"(No story: a {look.title.lower()} look needs the {look.region}, but this attempt uses the "
        f"{attempt.region}. Bonnie would not honestly get the right transformation that way.)"
    )


def explain_prop_rejection(look: Look, prop: Prop) -> str:
    return (
        f"(No story: {prop.phrase} does not make a real {look.title.lower()} look here. "
        f"The fix has to match the part of the costume Bonnie is trying to create.)"
    )


def predict_droop(world: World, attempt: Attempt) -> dict:
    sim = world.copy()
    bonnie = sim.get("bonnie")
    bonnie.meters["sticky"] += attempt.sticky_gain
    sim.facts["attempt_region"] = attempt.region
    propagate(sim, narrate=False)
    return {
        "drips": bonnie.meters["drip"] >= THRESHOLD,
        "sticky": bonnie.meters["sticky"],
    }


def setup_show(world: World, bonnie: Entity, helper: Entity, setting: Setting, look: Look) -> None:
    bonnie.memes["joy"] += 1
    world.say(
        f"Bonnie had decided that {setting.stage} needed one thing before the family show began: "
        f"a grand transformation. In her mind, she was not going to be plain Bonnie for even one minute."
    )
    world.say(
        f"She was going to become {look.idea}. {helper.label_word.capitalize()} was folding napkins near "
        f"{setting.snack_spot}, and {setting.audience} were already waiting for a laugh."
    )


def find_tamarind(world: World, bonnie: Entity, helper: Entity, attempt: Attempt) -> None:
    world.say(
        f"Then Bonnie spotted a little bowl of tamarind paste. It was glossy, brown, and much too interesting."
    )
    world.say(
        f'"This will do it," Bonnie whispered. "One tiny dab, and my {attempt.line} will be perfect."'
    )
    pred = predict_droop(world, attempt)
    world.facts["predicted_drips"] = pred["drips"]
    helper.memes["caution"] += 1
    world.say(
        f'{helper.label_word.capitalize()} looked over and said, "Bonnie, tamarind belongs in a snack, not in a costume."'
    )


def try_tamarind(world: World, bonnie: Entity, attempt: Attempt) -> None:
    bonnie.meters["sticky"] += attempt.sticky_gain
    world.facts["attempt_region"] = attempt.region
    bonnie.memes["defiance"] += 1
    world.say(
        f"But Bonnie was already busy. She {attempt.phrase} and grinned at an invisible crowd."
    )
    propagate(world, narrate=False)


def droop_beat(world: World, bonnie: Entity, look: Look, attempt: Attempt) -> None:
    if bonnie.meters["drip"] < THRESHOLD:
        return
    place = {
        "lip": "right toward her smile",
        "chin": "into a crooked little tail",
        "hair": "down past one ear",
    }.get(attempt.region, "the wrong way")
    world.say(
        f"For half a second, Bonnie held still, waiting for the magic to happen. Then the tamarind drooped {place}."
    )
    sticky_joke = {
        "lip": "The brown stripe looked more like a sticky comma than a fierce mustache.",
        "chin": "The brown swoop looked more like a sticky drip than wizard magic.",
        "hair": "The paste made one strand flop like a sleepy noodle.",
    }.get(attempt.region, "The paste made a silly shape instead of a costume.")
    world.say(
        f"{sticky_joke} Bonnie blinked, {bonnie.pronoun('possessive')} nose wrinkled, and even she let out a surprised snort."
    )


def audience_laugh(world: World, setting: Setting) -> None:
    world.say(
        f"From {setting.audience}, someone giggled first. Then everyone giggled. It was not mean laughter. "
        f"It was the kind that bubbles up when something looks wonderfully silly."
    )


def rescue_and_fix(world: World, bonnie: Entity, helper: Entity, prop: Prop, look: Look) -> None:
    bonnie.meters["sticky"] = 0.0
    bonnie.meters["clean"] += 1
    world.add(Entity(
        id="prop",
        type="prop",
        label=prop.label,
        attrs={"covers": prop.covers, "looks": sorted(prop.looks)},
    ))
    world.say(
        f'{helper.label_word.capitalize()} knelt beside her with a warm washcloth. "{prop.entry}," '
        f'{helper.pronoun()} said. "First we clean the tamarind, and then we do the funny part properly."'
    )
    world.say(
        f"Bonnie stood very still while the sticky smear was wiped away. The room smelled sweet and sour for one last second, and then her face felt like her own again."
    )
    propagate(world, narrate=False)
    if bonnie.meters["transformed"] >= THRESHOLD:
        world.say(
            f"Next came {prop.phrase}. {look.reveal}"
        )


def finale(world: World, bonnie: Entity, look: Look, setting: Setting) -> None:
    bonnie.memes["pride"] += 1
    world.say(
        f"Bonnie popped onto {setting.stage} and gave the grandest pose she could manage. {look.finale}"
    )
    world.say(
        f"This time the laughter came before she even spoke, and Bonnie laughed too. The transformation worked best once the tamarind went back to being a treat and the costume went back to being a costume."
    )


def tell(setting: Setting, look: Look, attempt: Attempt, prop: Prop,
         helper_type: str = "mother") -> World:
    world = World(setting)
    bonnie = world.add(Entity(id="bonnie", kind="character", type="girl", role="hero", label="Bonnie"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, role="helper", label="the helper"))
    world.facts.update(setting=setting, look=look, attempt=attempt, prop_cfg=prop, helper=helper, bonnie=bonnie)

    setup_show(world, bonnie, helper, setting, look)

    world.para()
    find_tamarind(world, bonnie, helper, attempt)
    try_tamarind(world, bonnie, attempt)
    droop_beat(world, bonnie, look, attempt)
    audience_laugh(world, setting)

    world.para()
    rescue_and_fix(world, bonnie, helper, prop, look)
    finale(world, bonnie, look, setting)

    world.facts.update(
        transformed=bonnie.meters["transformed"] >= THRESHOLD,
        dripped=bonnie.meters["drip"] >= THRESHOLD,
        clean=bonnie.meters["clean"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "kitchen": Setting(
        "kitchen",
        "the kitchen",
        "the bright patch of floor between the table and the fridge",
        "three chairs pushed back like a front row",
        "the counter by the fruit bowl",
    ),
    "living_room": Setting(
        "living_room",
        "the living room",
        "the rug in front of the sofa",
        "the couch and one upside-down laundry basket",
        "the side table with the family snacks",
    ),
    "porch": Setting(
        "porch",
        "the front porch",
        "the welcome mat under the porch light",
        "the porch steps and the swing",
        "a little tray beside the lemonade glasses",
    ),
}

LOOKS = {
    "pirate": Look(
        "pirate",
        "Pirate Captain",
        "lip",
        "a pirate captain with a fierce curled mustache",
        "A tiny black felt mustache curled over Bonnie's lip at last, and suddenly her squint looked important instead of sticky.",
        'She pointed one finger toward the yard and barked, "Treasure ahead!" in such a booming voice that even the swing seemed to listen.',
        tags={"pirate", "mustache"},
    ),
    "walrus": Look(
        "walrus",
        "Walrus Star",
        "lip",
        "a walrus star with magnificent droopy whiskers",
        "Soft gray whiskers sprang from her upper lip and wobbled when she breathed, which was exactly the right amount of ridiculous.",
        'She puffed out her cheeks and announced, "I require six sandwiches and a nap!" and the whole audience folded up laughing.',
        tags={"walrus", "whiskers"},
    ),
    "wizard": Look(
        "wizard",
        "Wizard",
        "chin",
        "a wizard with a long solemn beard",
        "A silver beard hung from Bonnie's chin, and now every blink looked as if it came with a secret spell.",
        'She raised a wooden spoon like a wand and declared, "Behold! I turn plain socks into royal socks!"',
        tags={"wizard", "beard"},
    ),
}

ATTEMPTS = {
    "lip": Attempt(
        "lip",
        "lip",
        "dabbed a brown stripe under her nose",
        "upper lip",
        True,
        tags={"lip", "washable"},
    ),
    "chin": Attempt(
        "chin",
        "chin",
        "painted a brown swoop right onto her chin",
        "chin",
        True,
        tags={"chin", "washable"},
    ),
    "hair": Attempt(
        "hair",
        "hair",
        "patted the tamarind straight into her hair",
        "hair",
        False,
        sticky_gain=2,
        tags={"hair", "messy"},
    ),
}

PROPS = {
    "felt_mustache": Prop(
        "felt_mustache",
        "felt mustache",
        "a tiny black felt mustache on a little stick",
        "lip",
        {"pirate"},
        "A pirate needs a proper mustache",
        tags={"mustache", "costume"},
    ),
    "whiskers": Prop(
        "whiskers",
        "whiskers",
        "a pair of soft gray walrus whiskers on elastic",
        "lip",
        {"walrus"},
        "A walrus deserves whiskers that wobble",
        tags={"whiskers", "costume"},
    ),
    "beard": Prop(
        "beard",
        "sparkly beard",
        "a long silver beard made from yarn and glitter",
        "chin",
        {"wizard"},
        "A wizard should have a beard that can swish when she turns",
        tags={"beard", "costume"},
    ),
    "hat": Prop(
        "hat",
        "striped hat",
        "a striped stage hat",
        "head",
        {"pirate", "wizard"},
        "Hats are funny, but they are not the whole trick",
        tags={"hat", "costume"},
    ),
}

HELPER_TYPES = ["mother", "father"]
@dataclass
class StoryParams:
    setting: str
    look: str
    attempt: str
    prop: str
    helper: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("living_room", "pirate", "lip", "felt_mustache", "mother"),
    StoryParams("kitchen", "walrus", "lip", "whiskers", "father"),
    StoryParams("porch", "wizard", "chin", "beard", "mother"),
]


KNOWLEDGE = {
    "tamarind": [
        (
            "What is tamarind?",
            "Tamarind is a fruit with a sweet-sour taste. People often use it in sauces, candies, and drinks."
        )
    ],
    "mustache": [
        (
            "What is a costume mustache?",
            "A costume mustache is a pretend mustache you wear for fun. It changes how a face looks without using anything sticky from the kitchen."
        )
    ],
    "whiskers": [
        (
            "What are whiskers in a costume?",
            "Costume whiskers are pretend hairs added to a face to make someone look like an animal. They are silly because they move when the person talks and wiggles."
        )
    ],
    "beard": [
        (
            "Why do people wear a fake beard in a play?",
            "A fake beard helps an actor look like a different character right away. It is part of a costume, so it can be taken off when the show is done."
        )
    ],
    "costume": [
        (
            "What is a costume?",
            "A costume is clothing or pretend pieces that help someone look like a different person or creature for a game or a play."
        )
    ],
    "washable": [
        (
            "Why is a washcloth useful for sticky messes?",
            "A warm washcloth helps wipe away sticky food or syrup. Cleaning the mess first makes it easier to start over the right way."
        )
    ],
    "comedy": [
        (
            "What makes a story feel like a comedy?",
            "A comedy has a funny problem and a light ending. People may make mistakes, but the story ends with laughter instead of harm."
        )
    ],
}
KNOWLEDGE_ORDER = ["tamarind", "costume", "mustache", "whiskers", "beard", "washable", "comedy"]


def generation_prompts(world: World) -> list[str]:
    look = world.facts["look"]
    setting = world.facts["setting"]
    attempt = world.facts["attempt"]
    return [
        f'Write a short comedy for ages 3 to 5 about Bonnie trying to make a transformation in {setting.place}. Include the word "tamarind".',
        f"Tell a funny story where Bonnie tries to become {look.idea} by putting tamarind on her {attempt.region}, and a grown-up helps her finish the costume properly.",
        f'Write a gentle transformation story with Bonnie, tamarind, a silly mistake, and an ending where everyone laughs together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    bonnie = world.facts["bonnie"]
    helper = world.facts["helper"]
    look = world.facts["look"]
    attempt = world.facts["attempt"]
    prop = world.facts["prop_cfg"]
    setting = world.facts["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Bonnie, who wanted to put on a funny family show, and her {helper.label_word} who helped when the costume idea went wrong."
        ),
        (
            "What did Bonnie want to turn into?",
            f"Bonnie wanted to transform into {look.idea}. That wish is what made her start hunting for something she thought could change her face quickly."
        ),
        (
            "Why did Bonnie use tamarind?",
            f"She thought the glossy brown tamarind paste might work like instant costume paint. Bonnie was trying to hurry the transformation and make everyone laugh."
        ),
    ]
    if world.facts.get("dripped"):
        qa.append(
            (
                "What went wrong with the tamarind?",
                f"The tamarind drooped on Bonnie's {attempt.region} instead of staying neat, so the look turned silly in the wrong way. People laughed because it was a sticky surprise, not because Bonnie was in trouble."
            )
        )
    if world.facts.get("clean") and world.facts.get("transformed"):
        qa.append(
            (
                f"How did Bonnie's {helper.label_word} help?",
                f"{helper.label_word.capitalize()} used a warm washcloth to clean the tamarind off first. Then {helper.pronoun()} gave Bonnie {prop.phrase}, which matched the costume and made the transformation work."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with Bonnie stepping onto {setting.stage} in her finished costume and laughing with everyone else. The final joke worked because the tamarind went back to being food and the costume pieces did the transforming."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tamarind", "costume", "washable", "comedy"} | set(world.facts["look"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
reasonable_attempt(L, A) :- look(L), attempt(A), safe(A), needs(L, R), uses(A, R).
matching_prop(L, P)      :- look(L), prop(P), needs(L, R), covers(P, R), helps(P, L).
valid(L, A, P)           :- reasonable_attempt(L, A), matching_prop(L, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, look in LOOKS.items():
        lines.append(asp.fact("look", lid))
        lines.append(asp.fact("needs", lid, look.region))
    for aid, attempt in ATTEMPTS.items():
        lines.append(asp.fact("attempt", aid))
        lines.append(asp.fact("uses", aid, attempt.region))
        if attempt.safe:
            lines.append(asp.fact("safe", aid))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("covers", pid, prop.covers))
        for look_id in sorted(prop.looks):
            lines.append(asp.fact("helps", pid, look_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if "Bonnie" not in sample.story or "tamarind" not in sample.story:
            raise StoryError("Random smoke test missed core story words.")
        print("OK: random resolved story generated correctly.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Bonnie, tamarind, a funny transformation, and a proper costume fix."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--look", choices=LOOKS)
    ap.add_argument("--attempt", choices=ATTEMPTS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--helper", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (look, attempt, prop) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.look and args.attempt:
        look, attempt = LOOKS[args.look], ATTEMPTS[args.attempt]
        if not reasonable_attempt(look, attempt):
            raise StoryError(explain_attempt_rejection(look, attempt))
    if args.look and args.prop:
        look, prop = LOOKS[args.look], PROPS[args.prop]
        if not matching_prop(look, prop):
            raise StoryError(explain_prop_rejection(look, prop))

    combos = [
        c for c in valid_combos()
        if (args.look is None or c[0] == args.look)
        and (args.attempt is None or c[1] == args.attempt)
        and (args.prop is None or c[2] == args.prop)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    look_id, attempt_id, prop_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    helper = args.helper or rng.choice(HELPER_TYPES)
    return StoryParams(setting, look_id, attempt_id, prop_id, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        LOOKS[params.look],
        ATTEMPTS[params.attempt],
        PROPS[params.prop],
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (look, attempt, prop) combos:\n")
        for look, attempt, prop in combos:
            print(f"  {look:8} {attempt:8} {prop}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### Bonnie as {p.look} in {p.setting} ({p.attempt} -> {p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
