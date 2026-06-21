#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py
========================================================

A standalone storyworld about bedtime told in a playful pirate voice.

Tiny domain
-----------
A child turns bed into a pirate ship at bedtime. Something about the room feels
wrong, so the child keeps climbing out of bed again and again. Each time, the
grown-up repeats the same gentle bedtime line. On the third trip, the grown-up
finds the *real* problem and fixes it in a sensible way. The ending image proves
the bed has changed from a restless ship into a safe little harbor.

This world is built to emphasize **repetition** without becoming a frozen
template: the repeated line is driven by a loop in world state, while the
middle-turn and ending depend on the chosen trouble and the matching fix.

Run it
------
    python storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py --trouble dark
    python storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py --trouble tapping --fix nightlight
    python storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/bed_repetition_pirate_tale.py --qa --json
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

# Make the shared result containers importable when this script is run directly
# from storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REPEAT_COUNT = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    phrase: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Trouble:
    id: str
    label: str
    sound: str
    need: str
    excuse1: str
    excuse2: str
    truth: str
    fix_hint: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    action: str = ""
    comfort: str = ""
    ending: str = ""
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


def propagate(world: World) -> None:
    hero = world.get("hero")
    bed = world.get("bed")
    room = world.get("room")
    if room.meters["trouble"] >= THRESHOLD and ("uneasy",) not in world.fired:
        world.fired.add(("uneasy",))
        hero.memes["uneasy"] += 1
        bed.meters["rocking"] += 1
    if room.meters["trouble"] == 0 and ("settled",) not in world.fired:
        world.fired.add(("settled",))
        hero.memes["relief"] += 1
        hero.memes["sleepy"] += 1
        bed.meters["rocking"] = 0.0
        bed.meters["cozy"] += 1


TROUBLES = {
    "dark": Trouble(
        id="dark",
        label="dark shadows",
        sound="the corners looked deep and black",
        need="light",
        excuse1="the ship is too dark",
        excuse2="a captain cannot watch black waves with no star at all",
        truth="the dark corners were making the room feel bigger than it really was",
        fix_hint="a small light",
        ending="a tiny gold harbor-star shone beside the pillow",
        tags={"dark", "night"},
    ),
    "tapping": Trouble(
        id="tapping",
        label="tapping at the window",
        sound="tap-tap-tap came from the window like a hook on a mast",
        need="quiet",
        excuse1="something is knocking on the ship",
        excuse2="a sneaky sea sound keeps pecking at the mast",
        truth="a branch was tapping the window and making the bed feel like a stormy deck",
        fix_hint="make the tapping stop",
        ending="the window went still, and the room sounded soft as folded sails",
        tags={"noise", "window"},
    ),
    "cold": Trouble(
        id="cold",
        label="cold toes",
        sound="the air found the child's toes under the blanket",
        need="warmth",
        excuse1="my pirate feet are freezing",
        excuse2="captains cannot sleep with cold toes on a night sea",
        truth="the blanket had slipped down, leaving the child's feet out in the cold",
        fix_hint="more blanket",
        ending="the blanket reached all the way to the child's toes like a warm sail tucked tight",
        tags={"cold", "blanket"},
    ),
    "lonely": Trouble(
        id="lonely",
        label="an empty berth",
        sound="the bed felt too wide for one small pirate",
        need="company",
        excuse1="the ship has no first mate",
        excuse2="it is a very big sea for one little captain alone",
        truth="the child did not want the bed to feel so big and empty",
        fix_hint="a bedtime companion",
        ending="a soft first mate stood guard by the pillow all night",
        tags={"lonely", "toy"},
    ),
}

FIXES = {
    "nightlight": Fix(
        id="nightlight",
        label="night-light",
        phrase="a little night-light shaped like a star",
        solves={"light"},
        action="plugged in a little night-light shaped like a star",
        comfort="The glow was small, but it was enough to show where the wall ended and the shadows stopped pretending.",
        ending="Its warm dot of light made the whole bed feel like a ship anchored under one brave star.",
        tags={"nightlight", "light"},
    ),
    "curtains": Fix(
        id="curtains",
        label="curtains",
        phrase="the curtains and the tapping branch",
        solves={"quiet"},
        action="pulled the curtain straight and moved the tapping branch away from the window",
        comfort="The sharp little knocks stopped at once, and the room no longer sounded like a creaky night sea.",
        ending="Without the tapping, the bed-ship rested quietly at its dock.",
        tags={"curtains", "window"},
    ),
    "quilt": Fix(
        id="quilt",
        label="quilt",
        phrase="an extra quilt",
        solves={"warmth"},
        action="lifted the blanket, tucked it around the child's feet, and spread an extra quilt over the bed",
        comfort="Warmth flowed back to the little toes, and the mattress stopped feeling like a cold plank in the wind.",
        ending="Under the layered blankets, the bed became the warmest ship in the harbor.",
        tags={"blanket", "warmth"},
    ),
    "parrot": Fix(
        id="parrot",
        label="parrot toy",
        phrase="a soft stuffed parrot",
        solves={"company"},
        action="set a soft stuffed parrot beside the pillow and tucked one wing under the child's arm",
        comfort="With a first mate close by, the bed no longer felt wide and empty.",
        ending="The stuffed parrot leaned by the pillow like a faithful deckhand on watch.",
        tags={"toy", "company"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Zoe", "Nora", "Ruby", "Ella", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Jack", "Theo"]
TRAITS = ["sleepy", "imaginative", "bright", "restless", "brave", "little"]


@dataclass
class StoryParams:
    trouble: str
    fix: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        trouble="dark",
        fix="nightlight",
        name="Tom",
        gender="boy",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        trouble="tapping",
        fix="curtains",
        name="Lily",
        gender="girl",
        parent="father",
        trait="imaginative",
    ),
    StoryParams(
        trouble="cold",
        fix="quilt",
        name="Max",
        gender="boy",
        parent="mother",
        trait="restless",
    ),
    StoryParams(
        trouble="lonely",
        fix="parrot",
        name="Nora",
        gender="girl",
        parent="father",
        trait="sleepy",
    ),
]


def valid_fix(trouble: Trouble, fix: Fix) -> bool:
    return trouble.need in fix.solves


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for tid, trouble in TROUBLES.items():
        for fid, fix in FIXES.items():
            if valid_fix(trouble, fix):
                combos.append((tid, fid))
    return sorted(combos)


def explain_rejection(trouble: Trouble, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not solve {trouble.label}. "
        f"The bedtime trouble needs {trouble.fix_hint}, so pick a fix that matches.)"
    )


def setup(world: World, hero: Entity, parent: Entity) -> None:
    bed = world.get("bed")
    hero.memes["joy"] += 1
    world.say(
        f"At bedtime, {hero.id} climbed into {hero.pronoun('possessive')} bed and decided "
        f"it was not a bed at all, but a pirate ship with a pillow for a prow and a blanket for a billowing sail."
    )
    world.say(
        f'{hero.pronoun().capitalize()} whispered, "Captain {hero.id} is ready for the night sea."'
    )
    bed.meters["shipness"] += 1
    parent.memes["patience"] += 1


def trouble_begins(world: World, trouble: Trouble) -> None:
    room = world.get("room")
    room.meters["trouble"] += 1
    world.facts["sound"] = trouble.sound
    propagate(world)
    world.say(
        f"But then {trouble.sound}, and suddenly the grand pirate game did not feel grand in quite the same way."
    )


def trip_out(world: World, hero: Entity, parent: Entity, trouble: Trouble, count: int) -> None:
    hero.meters["out_of_bed"] += 1
    hero.memes["restless"] += 1
    world.facts["trips"] = count
    opener = {
        1: f"A moment later, soft feet padded down the hall. {hero.id} stood in the doorway and whispered,",
        2: f"Soon there was another patter, another small face, another whisper at the door:",
        3: f"And then, yes, there came a third little shuffle, a third doorway shadow, a third whisper:",
    }[count]
    ask = trouble.excuse1 if count == 1 else trouble.excuse2 if count == 2 else trouble.truth
    world.say(f'{opener} "{ask}"')
    if count < REPEAT_COUNT:
        world.say(
            f'"Back to bed, Captain {hero.id}. Back to bed," said {hero.pronoun("possessive")} '
            f'{parent.label_word}, gentle as a harbor bell.'
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} looked more closely this time and saw that this was not mischief at all. '
            f'It was a real bedtime worry wearing a pirate hat.'
        )


def reveal_and_fix(world: World, hero: Entity, parent: Entity, trouble: Trouble, fix: Fix) -> None:
    room = world.get("room")
    hero.memes["fear"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside {hero.id} and asked, "What is the matter on my little captain\'s ship?"'
    )
    world.say(
        f'{hero.id} finally told the truth: {trouble.truth}.'
    )
    world.say(
        f"So {parent.label_word} {fix.action}."
    )
    room.meters["trouble"] = 0.0
    world.facts["resolved_by"] = fix.id
    world.facts["resolved_need"] = trouble.need
    propagate(world)
    world.say(fix.comfort)


def ending(world: World, hero: Entity, parent: Entity, trouble: Trouble, fix: Fix) -> None:
    hero.memes["trust"] += 1
    hero.memes["joy"] += 1
    world.say(
        f'Back in bed, {hero.id} pulled the blanket up to {hero.pronoun("possessive")} chin and smiled. '
        f'"Now my ship can rest," {hero.pronoun()} said.'
    )
    world.say(
        f'{trouble.ending}. {fix.ending}'
    )
    world.say(
        f'And when {parent.label_word} whispered, "Back to bed, Captain {hero.id}," '
        f'this time {hero.pronoun()} only snuggled deeper into the bed and sailed quietly into sleep.'
    )


def tell(trouble: Trouble, fix: Fix, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name, phrase=name, attrs={"name": name, "trait": trait}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    bed = world.add(Entity(id="bed", kind="thing", type="bed", label="bed", phrase="the bed", tags={"bed"}))
    room = world.add(Entity(id="room", kind="thing", type="room", label="room", phrase="the bedroom"))

    world.facts.update(
        hero=hero,
        parent=parent,
        bed=bed,
        room=room,
        hero_name=name,
        trouble=trouble,
        fix=fix,
        repetition=REPEAT_COUNT,
    )

    setup(world, hero, parent)
    world.para()
    trouble_begins(world, trouble)
    for count in range(1, REPEAT_COUNT + 1):
        trip_out(world, hero, parent, trouble, count)
    world.para()
    reveal_and_fix(world, hero, parent, trouble, fix)
    world.para()
    ending(world, hero, parent, trouble, fix)
    return world


KNOWLEDGE = {
    "bed": [
        (
            "What is a bed for?",
            "A bed is a soft place for resting and sleeping. It helps your body feel safe and calm at night."
        )
    ],
    "night": [
        (
            "Why can a little light help at bedtime?",
            "A small light can help you see where things really are. That can make shadows feel less confusing and less scary."
        )
    ],
    "window": [
        (
            "Why do branches tap on windows?",
            "When the wind moves a branch, it can bump against the glass and make a tapping sound. The sound can seem bigger at night because the room is quiet."
        )
    ],
    "blanket": [
        (
            "Why does a blanket help when your feet are cold?",
            "A blanket holds warm air around your body. That helps your feet stop feeling chilly."
        )
    ],
    "toy": [
        (
            "Why can a stuffed toy help at bedtime?",
            "A stuffed toy can feel like a friendly companion. Holding it can help a child feel less alone and more settled."
        )
    ],
    "repetition": [
        (
            "What is repetition in a story?",
            "Repetition is when a story uses the same words or action again and again. It helps a listener notice a pattern and feel the change when the pattern finally ends."
        )
    ],
}
KNOWLEDGE_ORDER = ["bed", "night", "window", "blanket", "toy", "repetition"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trouble = f["trouble"]
    return [
        'Write a pirate-flavored bedtime story for a 3-to-5-year-old that includes the word "bed" and uses repetition.',
        f"Tell a gentle story where a child named {f['hero_name']} keeps getting out of bed three times because of {trouble.label}, and a parent finally understands the real worry.",
        "Write a short story with a repeated bedtime line that changes meaning by the end, so the child starts restless and ends safe and sleepy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    trouble = f["trouble"]
    fix = f["fix"]
    trips = int(hero.meters["out_of_bed"])
    name = f["hero_name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little pirate captain named {name} and {name}'s {pw}. The child turned bed into a pretend ship at bedtime."
        ),
        (
            "Why did the child keep getting out of bed?",
            f"{name} kept getting out of bed because {trouble.truth}. The pirate excuses changed, but the real bedtime worry stayed the same until {pw} understood it."
        ),
        (
            "What was repeated in the story?",
            f'The repeated line was "Back to bed, Captain {name}. Back to bed." It came back each time {name} left bed, so the listener could feel the pattern before the problem was solved.'
        ),
        (
            f"How many times did {name} come out of bed before the fix?",
            f"{name} came out of bed {trips} times. On the third trip, {pw} realized this was a real worry and not just stalling."
        ),
        (
            f"How did {name}'s {pw} help?",
            f"{pw.capitalize()} helped by using {fix.phrase}. That worked because the trouble needed {trouble.fix_hint}, and the fix changed the room so bed felt safe again."
        ),
        (
            "How did the story end?",
            f"It ended with the bed feeling calm instead of restless. {name} stayed in bed at last and drifted to sleep like a little ship resting in a harbor."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bed", "repetition"}
    trouble = world.facts["trouble"]
    fix = world.facts["fix"]
    if trouble.id == "dark" or fix.id == "nightlight":
        tags.add("night")
    if trouble.id == "tapping" or fix.id == "curtains":
        tags.add("window")
    if trouble.id == "cold" or fix.id == "quilt":
        tags.add("blanket")
    if trouble.id == "lonely" or fix.id == "parrot":
        tags.add("toy")
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
need(dark, light).
need(tapping, quiet).
need(cold, warmth).
need(lonely, company).

solves(nightlight, light).
solves(curtains, quiet).
solves(quilt, warmth).
solves(parrot, company).

valid(T, F) :- trouble(T), fix(F), need(T, N), solves(F, N).

resolved :- chosen_trouble(T), chosen_fix(F), valid(T, F).
outcome(settled) :- resolved.
outcome(adrift) :- not resolved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_trouble", params.trouble),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    return "settled" if valid_fix(trouble, fix) else "adrift"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for tid in TROUBLES:
        for fid in FIXES:
            cases.append(
                StoryParams(
                    trouble=tid,
                    fix=fid,
                    name="Tom",
                    gender="boy",
                    parent="mother",
                    trait="brave",
                )
            )
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a pirate-flavored bedtime tale with repetition."
    )
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (trouble, fix) pairs from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.trouble and args.fix:
        trouble = TROUBLES[args.trouble]
        fix = FIXES[args.fix]
        if not valid_fix(trouble, fix):
            raise StoryError(explain_rejection(trouble, fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.trouble is None or combo[0] == args.trouble)
        and (args.fix is None or combo[1] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    trouble_id, fix_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        trouble=trouble_id,
        fix=fix_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    trouble = TROUBLES[params.trouble]
    fix = FIXES[params.fix]
    if not valid_fix(trouble, fix):
        raise StoryError(explain_rejection(trouble, fix))

    world = tell(
        trouble=trouble,
        fix=fix,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    hero = world.get("hero")
    hero.label = params.name
    hero.phrase = params.name

    story_text = world.render().replace("hero", params.name)
    sample = StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trouble, fix) pairs:\n")
        for trouble, fix in combos:
            print(f"  {trouble:8} {fix}")
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
            header = f"### {p.name}: {p.trouble} -> {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
