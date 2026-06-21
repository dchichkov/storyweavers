#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/doom_repetition_bad_ending_curiosity_nursery_rhyme.py
================================================================================

A small storyworld for a nursery-rhyme-shaped cautionary tale: a curious child
keeps peeping where they were told not to peep, a warning is repeated like a
refrain, and the story ends badly when a cherished thing is lost.

The world is intentionally narrow. A child brings a keepsake near a dangerous
place, hears the tempting "doom, doom, doom" sound, ignores a grown-up's
repeated warning, and peeps three times. On the last peep, the child is pulled
safe, but the keepsake is swallowed, swept away, or snagged. The ending is not
tragic, but it is plainly bad: the child goes home tearful and changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/doom_repetition_bad_ending_curiosity_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/doom_repetition_bad_ending_curiosity_nursery_rhyme.py --hazard well --keepsake cup
    python storyworlds/worlds/gpt-5.4/doom_repetition_bad_ending_curiosity_nursery_rhyme.py --hazard brambles --keepsake cup
    python storyworlds/worlds/gpt-5.4/doom_repetition_bad_ending_curiosity_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/doom_repetition_bad_ending_curiosity_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BAD_ENDING_RISK = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.type in male:
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    place_line: str
    sound_line: str
    warning_name: str
    loss_modes: set[str] = field(default_factory=set)
    aftermath: str = ""
    marks: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    mode: str
    carry: str
    lost_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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


def keepsake_at_risk(hazard: Hazard, keepsake: Keepsake) -> bool:
    return keepsake.mode in hazard.loss_modes


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for hazard_id, hazard in HAZARDS.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            if keepsake_at_risk(hazard, keepsake):
                combos.append((hazard_id, keepsake_id))
    return combos


def explain_rejection(hazard: Hazard, keepsake: Keepsake) -> str:
    return (
        f"(No story: {hazard.the} does not plausibly take {keepsake.phrase}. "
        f"This world only allows keepsakes whose loss fits the place: "
        f"{hazard.warning_name} can take {', '.join(sorted(hazard.loss_modes))} things.)"
    )


def introduce(world: World, child: Entity, adult: Entity, hazard: Hazard, keepsake: Keepsake) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} was a little {child.type} with a quick, bright mind and quicker feet. "
        f"{child.pronoun('possessive').capitalize()} {keepsake.label} was {keepsake.carry}, "
        f"and {adult.label_word} had told {child.pronoun('object')} to mind it well."
    )
    world.say(
        f"By the lane stood {hazard.the}, and from it came {hazard.sound_line}. "
        f"It made the day sound strange and full of wondering."
    )


def approach(world: World, child: Entity, adult: Entity, hazard: Hazard) -> None:
    world.say(
        f'"Stay from {hazard.the}, my little one, stay from {hazard.the}," '
        f"said {adult.label_word}. "
        f'"{hazard.warning_name} is no place for peeping."'
    )


def warning_refrain(child: Entity, adult: Entity, hazard: Hazard) -> str:
    return (
        f'"Peep not, peep not, {child.id}, peep not there," '
        f"said {adult.label_word}. "
        f'"{hazard.warning_name} keeps what careless fingers share."'
    )


def first_peep(world: World, child: Entity, adult: Entity, hazard: Hazard) -> None:
    child.memes["curiosity"] += 1
    child.meters["risk"] += 1
    world.say(warning_refrain(child, adult, hazard))
    world.say(
        f'But {child.id} whispered, "Only one peep, only one peep," and stepped near {hazard.the}. '
        f"{hazard.place_line}"
    )


def second_peep(world: World, child: Entity, adult: Entity, hazard: Hazard) -> None:
    child.memes["curiosity"] += 1
    child.meters["risk"] += 1
    child.memes["defiance"] += 1
    world.say(warning_refrain(child, adult, hazard))
    world.say(
        f'Yet {child.id} said, "One more peep, one more peep," and leaned still nearer. '
        f"The sound went doom, doom, doom again, and {child.pronoun('possessive')} heart beat faster."
    )


def third_peep(world: World, child: Entity, adult: Entity, hazard: Hazard, keepsake: Keepsake) -> None:
    child.memes["curiosity"] += 1
    child.meters["risk"] += 1
    world.say(warning_refrain(child, adult, hazard))
    world.say(
        f'At last {child.id} breathed, "Just one last peep, one last peep," and bent too far.'
    )
    if child.meters["risk"] >= BAD_ENDING_RISK:
        child.memes["fear"] += 1
        child.memes["regret"] += 1
        child.meters["startled"] += 1
        world.say(
            f"{adult.label_word.capitalize()} caught {child.pronoun('possessive')} arm in a quick, tight pull, "
            f"but {keepsake.lost_line}"
        )
        world.say(hazard.aftermath)
        world.facts["bad_end"] = True
        world.facts["lost_keepsake"] = True
    else:
        world.facts["bad_end"] = False
        world.facts["lost_keepsake"] = False


def ending(world: World, child: Entity, adult: Entity, hazard: Hazard, keepsake: Keepsake) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} was safe, but not merry. {child.pronoun().capitalize()} looked at {child.pronoun('possessive')} empty hands "
        f"and heard the old doom sound fading behind {child.pronoun('object')}."
    )
    world.say(
        f'All the way home, {adult.label_word} said no more than this: '
        f'"Peep not, peep not where warnings bloom, or wonder walks you into gloom."'
    )
    world.say(
        f"And so the lane grew dim, {hazard.the} kept the {keepsake.label}, "
        f"and {child.id} went home quieter than when the rhyme began."
    )


def tell(
    hazard: Hazard,
    keepsake: Keepsake,
    child_name: str,
    child_gender: str,
    adult_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=["little", trait],
            label=child_name,
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the adult",
        )
    )
    place = world.add(
        Entity(
            id="hazard",
            type="place",
            label=hazard.label,
            phrase=hazard.the,
            tags=set(hazard.tags),
        )
    )
    item = world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake.label,
            phrase=keepsake.phrase,
            tags=set(keepsake.tags),
        )
    )

    introduce(world, child, adult, hazard, keepsake)
    world.para()
    approach(world, child, adult, hazard)
    first_peep(world, child, adult, hazard)
    second_peep(world, child, adult, hazard)
    world.para()
    third_peep(world, child, adult, hazard, keepsake)
    ending(world, child, adult, hazard, keepsake)

    world.facts.update(
        child=child,
        adult=adult,
        place=place,
        item=item,
        hazard_cfg=hazard,
        keepsake_cfg=keepsake,
        peeps=3,
        bad_end=True,
        repeated_warning=3,
        repeated_peep=3,
    )
    return world


KNOWLEDGE = {
    "well": [
        (
            "Why is an old well dangerous?",
            "An old well is deep and hard to climb out of. A child should stay back and tell a grown-up if something falls in.",
        )
    ],
    "millrace": [
        (
            "Why is fast water dangerous?",
            "Fast water can snatch things away before you can grab them. It can also knock little feet off balance.",
        )
    ],
    "brambles": [
        (
            "Why are brambles a bad place to reach into?",
            "Brambles have thorns that catch cloth and scratch skin. Things snag there easily and are hard to pull free.",
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to look, touch, or find out more. It can be good, but it needs careful choices.",
        )
    ],
    "warning": [
        (
            "Why do grown-ups repeat warnings?",
            "They repeat warnings when something is truly important. Repetition helps children remember the danger before they act.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pattern of words that sound alike. Nursery rhymes often repeat lines so they are easy to remember.",
        )
    ],
}
KNOWLEDGE_ORDER = ["curiosity", "warning", "rhyme", "well", "millrace", "brambles"]


HAZARDS = {
    "well": Hazard(
        id="well",
        label="well",
        the="the old well",
        place_line="The stones were cool, the moss was slick, and the black round water would not show its bottom.",
        sound_line='a hollow little call: "doom, doom, doom."',
        warning_name="the old well",
        loss_modes={"sink", "drop"},
        aftermath="Down went the small sound, down went the bright thing, and the well made only one last doom in reply.",
        marks={"cold", "dark"},
        tags={"well"},
    ),
    "millrace": Hazard(
        id="millrace",
        label="millrace",
        the="the mill race",
        place_line="The narrow water flashed silver under the boards and hurried past as if it had somewhere stern to go.",
        sound_line='the clack and gluck of water saying "doom, doom, doom."',
        warning_name="the mill race",
        loss_modes={"drift", "drop"},
        aftermath="Away it twirled with the racing water, smaller and smaller, while the stream kept up its doom-song.",
        marks={"wet", "swift"},
        tags={"millrace"},
    ),
    "brambles": Hazard(
        id="brambles",
        label="brambles",
        the="the blackberry brambles",
        place_line="The canes bowed low, the thorns flashed small and bright, and shadows stitched dark knots between the leaves.",
        sound_line='the wind in the thorns, whispering "doom, doom, doom."',
        warning_name="the blackberry brambles",
        loss_modes={"snag", "drop"},
        aftermath="The thorns held fast and would not give it back. They only shook and hissed in the hedge like a cross old song.",
        marks={"thorny", "dark"},
        tags={"brambles"},
    ),
}

KEEPSAKES = {
    "cup": Keepsake(
        id="cup",
        label="tin cup",
        phrase="a little tin cup",
        mode="sink",
        carry="shining on a blue string from one wrist",
        lost_line="the little tin cup slipped from the string, rang once on the stone, and went plink into the dark below.",
        tags={"metal"},
    ),
    "ball": Keepsake(
        id="ball",
        label="red ball",
        phrase="a red ball",
        mode="drift",
        carry="tucked warm under one arm",
        lost_line="the red ball popped from under one arm, bounced once, and bobbed away before either of them could catch it.",
        tags={"toy"},
    ),
    "ribbon": Keepsake(
        id="ribbon",
        label="yellow ribbon",
        phrase="a yellow ribbon",
        mode="snag",
        carry="looped in a neat bow at the collar",
        lost_line="the yellow ribbon brushed the thorns, caught in a dozen tiny claws, and tore free from the collar.",
        tags={"cloth"},
    ),
    "shell": Keepsake(
        id="shell",
        label="striped shell",
        phrase="a striped shell",
        mode="drop",
        carry="cupped proudly in two small hands",
        lost_line="the striped shell flipped from the small hands, struck the edge, and was gone where little fingers could not follow.",
        tags={"shell"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Poppy", "Tilly", "Mabel", "Rosie"]
BOY_NAMES = ["Ned", "Toby", "Bram", "Jem", "Ollie", "Kit"]
TRAITS = ["curious", "quick", "bright", "restless", "eager"]


@dataclass
class StoryParams:
    hazard: str
    keepsake: str
    child_name: str
    child_gender: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    hazard = world.facts["hazard_cfg"]
    keepsake = world.facts["keepsake_cfg"]
    return [
        'Write a nursery-rhyme-style cautionary story for a 3-to-5-year-old that includes the word "doom".',
        f"Tell a repetitive story where {child.id}, a curious little {child.type}, keeps peeping at {hazard.the} even after {child.pronoun('possessive')} {adult.label_word} warns {child.pronoun('object')} three times.",
        f"Write a short rhyme-like tale where a child loses {keepsake.phrase} because curiosity beats caution, and the ending is clearly bad but not gruesome.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    adult = world.facts["adult"]
    hazard = world.facts["hazard_cfg"]
    keepsake = world.facts["keepsake_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {child.pronoun('possessive')} {adult.label_word}. "
            f"{child.id} carried {keepsake.phrase} and wandered near {hazard.the}.",
        ),
        (
            f"Why did {child.id} keep going near {hazard.the}?",
            f"{child.id} was curious about the strange doom sound coming from {hazard.the}. "
            f"That curiosity kept pulling {child.pronoun('object')} back even after the warning was repeated.",
        ),
        (
            "What was repeated in the story?",
            f"The warning was repeated three times, and {child.id}'s promise to take just one more peep was repeated too. "
            f"The repetition makes the danger feel bigger each time.",
        ),
        (
            f"What bad thing happened at the end?",
            f"{adult.label_word.capitalize()} pulled {child.id} safe, but {keepsake.phrase} was lost to {hazard.the}. "
            f"The ending is bad because {child.id} kept peeping after three warnings and came home sad and empty-handed.",
        ),
        (
            f"Did {child.id} get hurt?",
            f"No, {child.id} stayed safe because {adult.label_word} grabbed {child.pronoun('possessive')} arm in time. "
            f"But losing the keepsake still made the ending feel heavy and full of regret.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity", "warning", "rhyme"}
    hazard = world.facts["hazard_cfg"]
    tags |= set(hazard.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if entity.tags:
            bits.append(f"tags={sorted(entity.tags)}")
        lines.append(f"  {entity.id:10} ({entity.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: peeps={world.facts.get('peeps')} bad_end={world.facts.get('bad_end')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hazard="well",
        keepsake="cup",
        child_name="Molly",
        child_gender="girl",
        adult_type="mother",
        trait="curious",
    ),
    StoryParams(
        hazard="millrace",
        keepsake="ball",
        child_name="Ned",
        child_gender="boy",
        adult_type="father",
        trait="eager",
    ),
    StoryParams(
        hazard="brambles",
        keepsake="ribbon",
        child_name="Poppy",
        child_gender="girl",
        adult_type="mother",
        trait="quick",
    ),
    StoryParams(
        hazard="well",
        keepsake="shell",
        child_name="Toby",
        child_gender="boy",
        adult_type="father",
        trait="bright",
    ),
]


ASP_RULES = r"""
takes(H, K) :- hazard(H), keepsake(K), loss_mode(H, M), item_mode(K, M).
valid(H, K) :- takes(H, K).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        for mode in sorted(hazard.loss_modes):
            lines.append(asp.fact("loss_mode", hazard_id, mode))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("item_mode", keepsake_id, keepsake.mode))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in asp:", sorted(asp_set - py_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "doom" not in sample.story.lower():
            raise StoryError("Smoke test failed: generated story missing expected content.")
        print("OK: smoke test story generated successfully.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme cautionary storyworld: a curious child keeps peeping and loses a keepsake."
    )
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (hazard, keepsake) pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.keepsake:
        hazard = HAZARDS[args.hazard]
        keepsake = KEEPSAKES[args.keepsake]
        if not keepsake_at_risk(hazard, keepsake):
            raise StoryError(explain_rejection(hazard, keepsake))

    combos = [
        combo
        for combo in valid_combos()
        if (args.hazard is None or combo[0] == args.hazard)
        and (args.keepsake is None or combo[1] == args.keepsake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hazard_id, keepsake_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    adult_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        hazard=hazard_id,
        keepsake=keepsake_id,
        child_name=child_name,
        child_gender=gender,
        adult_type=adult_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Invalid hazard: {params.hazard})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Invalid keepsake: {params.keepsake})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid gender: {params.child_gender})")
    if params.adult_type not in {"mother", "father"}:
        raise StoryError(f"(Invalid parent: {params.adult_type})")
    hazard = HAZARDS[params.hazard]
    keepsake = KEEPSAKES[params.keepsake]
    if not keepsake_at_risk(hazard, keepsake):
        raise StoryError(explain_rejection(hazard, keepsake))

    world = tell(
        hazard=hazard,
        keepsake=keepsake,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult_type,
        trait=params.trait,
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hazard, keepsake) pairs:\n")
        for hazard, keepsake in combos:
            print(f"  {hazard:10} {keepsake}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.keepsake} at {p.hazard}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
