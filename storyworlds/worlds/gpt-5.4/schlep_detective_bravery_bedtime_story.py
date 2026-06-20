#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py
====================================================================

A standalone story world for a gentle bedtime mystery. A child feels nervous
after hearing a strange night sound, decides to be a little detective, and
uses brave, safe steps to discover the ordinary cause.

The seed words "schlep" and "detective" are built into the world itself:
the child sometimes has to schlep a small bedtime thing along the hall, and
the story explicitly frames the child as a detective. The world model tracks
fear, bravery, comfort, and tiredness, then renders prose from that state.

Reasonableness constraint
-------------------------
Not every solving method fits every bedtime mystery. Looking out the window
won't help a dripping faucet, and bringing a water bowl won't stop a tapping
branch. This storyworld only generates combinations where the chosen method
really matches the source of the noise. Explicit mismatches are rejected with
a clear StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py --source branch --method curtain_peek
    python storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py --source faucet --method curtain_peek
    python storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/schlep_detective_bravery_bedtime_story.py --verify
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
# from the repo root. This file lives under storyworlds/worlds/gpt-5.4/, so we
# need to add storyworlds/ itself to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVE_ENOUGH = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class Setting:
    id: str
    room: str
    hall: str
    bed: str
    night_light: str
    hush: str


@dataclass
class Source:
    id: str
    sound: str
    cause: str
    location: str
    reveal: str
    safe_end: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    kind: str
    carry: str
    carry_phrase: str
    approach: str
    solve: str
    proof: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "cozy_house": Setting(
        "cozy_house",
        "a small blue bedroom",
        "the soft hall",
        "a warm little bed with a moon quilt",
        "a star-shaped night-light",
        "Outside, the whole house listened to the quiet night.",
    ),
    "attic_room": Setting(
        "attic_room",
        "a snug attic room",
        "the sloping upstairs hall",
        "a tucked-in bed under the window",
        "a pearly night-light",
        "The roof beams held the hush as gently as cupped hands.",
    ),
    "cottage": Setting(
        "cottage",
        "a tiny cottage bedroom",
        "the narrow candle-colored hall",
        "a patchwork bed",
        "a shell-shaped night-light",
        "The cottage had the kind of quiet that made small sounds seem bigger.",
    ),
}

SOURCES = {
    "branch": Source(
        "branch",
        "tap... tap... tap",
        "a windy branch brushing the window",
        "the window",
        "A leaf-shadow danced on the curtain, and a skinny branch nodded against the glass.",
        "The branch only wanted the window to know the wind was awake.",
        "window",
        tags={"wind", "window"},
    ),
    "kitten": Source(
        "kitten",
        "mew... mew...",
        "the kitten asking for its water bowl",
        "the back door",
        "By the back door sat the kitten, whiskers bright, blinking beside its empty bowl.",
        "The tiny mews turned into happy lapping sounds.",
        "pet",
        tags={"kitten", "water"},
    ),
    "robot": Source(
        "robot",
        "bzzzt... whirr",
        "a toy robot still switched on in the closet",
        "the closet",
        "On the closet floor, a toy robot blinked one red dot and buzzed in sleepy circles.",
        "Once it was switched off and tucked away, the closet became still again.",
        "toy",
        tags={"toy", "closet"},
    ),
    "faucet": Source(
        "faucet",
        "plink... plink...",
        "a bathroom faucet that was not fully closed",
        "the bathroom",
        "In the bathroom, one silver drop hung from the faucet and let go into the sink.",
        "When the handle was turned snugly shut, the plinks stopped and the room sighed quiet.",
        "water",
        tags={"bathroom", "water"},
    ),
}

METHODS = {
    "curtain_peek": Method(
        "curtain_peek",
        "window",
        "a pillow",
        "schlep her pillow",
        "tiptoed to the curtain and peeked out with a detective squint",
        "pulled the curtain aside and watched carefully",
        "The tapping made sense at once.",
        tags={"window", "peek"},
    ),
    "water_bowl": Method(
        "water_bowl",
        "pet",
        "a small bowl",
        "schlep a small bowl with both hands",
        "followed the sound to the back door and listened one more time",
        "filled the bowl with water and set it down gently",
        "The mystery melted into a kind little job.",
        tags={"kitten", "water"},
    ),
    "toy_basket": Method(
        "toy_basket",
        "toy",
        "a toy basket",
        "schlep the toy basket along the hall rug",
        "opened the closet door a crack and listened like a detective",
        "switched the robot off and parked it in the basket",
        "The buzzing turned out to be a toy that should have been asleep too.",
        tags={"toy", "basket"},
    ),
    "faucet_turn": Method(
        "faucet_turn",
        "water",
        "a washcloth",
        "schlep a washcloth in case of splashes",
        "followed the plinking to the bathroom and stood very still",
        "turned the handle until the faucet was snugly closed",
        "What had sounded spooky was only a loose little drip.",
        tags={"bathroom", "water"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Lucy", "Anna", "Rose", "Ivy", "Ella"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Finn", "Eli", "Noah"]
TRAITS = ["careful", "sleepy", "thoughtful", "gentle", "steady", "curious"]


def valid_method(source: Source, method: Method) -> bool:
    return source.kind == method.kind


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for source_id, source in SOURCES.items():
            for method_id, method in METHODS.items():
                if valid_method(source, method):
                    out.append((setting_id, source_id, method_id))
    return out


@dataclass
class StoryParams:
    setting: str
    source: str
    method: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def scene_setup(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    child.memes["safe"] += 1
    world.say(
        f"In {setting.room}, {child.id} was supposed to be settling into {setting.bed}. "
        f"{setting.night_light.capitalize()} glowed on the wall, and {child.id}'s "
        f"{parent.label_word} had just finished the last good-night kiss."
    )
    world.say(setting.hush)


def strange_sound(world: World, child: Entity, source: Source) -> None:
    child.memes["fear"] += 2
    world.say(
        f"Then the quiet changed. From {source.location} came {source.sound}, "
        f"small but clear in the dark."
    )
    world.say(
        f"{child.id} pulled the quilt up to {child.pronoun('possessive')} chin. "
        f"For one fluttery moment, the sound felt bigger than it really was."
    )


def parent_nudge(world: World, child: Entity, parent: Entity) -> None:
    child.memes["comfort"] += 1
    world.say(
        f'{parent.label_word.capitalize()} came back to the doorway. '
        f'"That sounded surprising," {parent.pronoun()} said softly. '
        f'"But surprising is not the same as dangerous."'
    )
    world.say(
        f'"You can be brave a little bit at a time. A detective uses quiet eyes, '
        f'quiet ears, and safe feet."'
    )


def take_brave_step(world: World, child: Entity, method: Method, setting: Setting) -> None:
    child.memes["bravery"] += 2
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.meters["steps"] += 1
    world.say(
        f"So {child.id} took one deep breath, slid out of bed, and decided to be a detective."
    )
    world.say(
        f"{child.pronoun().capitalize()} even had to {method.carry_phrase} through {setting.hall}. "
        f"It felt like a very long schlep for such small feet, but each step made "
        f"{child.pronoun('object')} a little steadier."
    )


def investigate(world: World, child: Entity, source: Source, method: Method) -> None:
    child.meters["steps"] += 1
    world.say(
        f"{child.id} {method.approach}. {child.pronoun().capitalize()} listened, "
        f"looked, and tried not to let the first scary guess be the boss."
    )
    world.say(source.reveal)
    world.say(method.proof)


def solve(world: World, child: Entity, parent: Entity, source: Source, method: Method) -> None:
    child.memes["fear"] = 0.0
    child.memes["bravery"] += 1
    child.memes["pride"] += 1
    child.memes["safe"] += 1
    world.say(
        f"{parent.label_word.capitalize()} stayed close behind, but {child.id} did the brave part first."
    )
    world.say(
        f"Together they {method.solve}. {source.safe_end}"
    )


def bedtime_return(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    child.meters["steps"] += 1
    world.say(
        f"Back in {setting.room}, the bed looked warmer than before because the mystery was gone."
    )
    world.say(
        f'{child.id} climbed under the moon quilt again. "{child.pronoun().capitalize()} was brave," '
        f'said {parent.label_word}.'
    )
    world.say(
        f"{child.id} smiled into the pillow. Being brave, {child.pronoun()} discovered, "
        f"did not mean never feeling scared. It meant taking one safe step anyway."
    )
    world.say(
        f"Soon the house was quiet again, and this time the quiet felt friendly."
    )


def tell(setting: Setting, source: Source, method: Method,
         name: str = "Lila", gender: str = "girl",
         parent_type: str = "mother", trait: str = "thoughtful") -> World:
    world = World()
    child = world.add(Entity(
        id=name, kind="character", type=gender, role="child",
        traits=[trait, "small detective"], label=name,
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent",
        label="the parent",
    ))
    mystery = world.add(Entity(
        id="mystery", type="source", label=source.cause, attrs={"location": source.location}
    ))
    carried = world.add(Entity(
        id="carry", type="thing", label=method.carry
    ))

    scene_setup(world, child, parent, setting)
    world.para()
    strange_sound(world, child, source)
    parent_nudge(world, child, parent)
    world.para()
    take_brave_step(world, child, method, setting)
    investigate(world, child, source, method)
    world.para()
    solve(world, child, parent, source, method)
    bedtime_return(world, child, parent, setting)

    world.facts.update(
        child=child,
        parent=parent,
        mystery=mystery,
        carried=carried,
        setting=setting,
        source=source,
        method=method,
        brave=child.memes["bravery"] >= BRAVE_ENOUGH,
        solved=True,
        schlep_item=method.carry,
        steps=int(child.meters["steps"]),
    )
    return world


KNOWLEDGE = {
    "window": [(
        "Why can a branch tap on a window at night?",
        "Wind can push a branch so it brushes the glass again and again. In the quiet night, that soft tapping can sound bigger than it really is."
    )],
    "wind": [(
        "What does wind do to tree branches?",
        "Wind makes branches sway and bob. Sometimes they tap or scratch things nearby."
    )],
    "kitten": [(
        "Why might a kitten cry near a bowl?",
        "A kitten may mew when it wants water or food or wants someone to notice it. Small pets use sounds to ask for help."
    )],
    "water": [(
        "Why does a dripping faucet make a clear sound at night?",
        "When the house is quiet, each drop can echo in the sink. A tiny plink can seem very loud in the dark."
    )],
    "toy": [(
        "Why should noisy toys be put away before bed?",
        "A toy left on can wake people up or make surprising sounds. Putting it away helps the room stay calm and quiet."
    )],
    "closet": [(
        "Why can a closet sound spooky at night?",
        "A closet is dark and closed, so noises can seem mysterious before you know what made them. Once you look safely, the sound often has an ordinary reason."
    )],
    "bathroom": [(
        "What makes a bathroom faucet drip?",
        "If the handle is not turned all the way off, water can slip out one drop at a time. Then you hear little plinks in the sink."
    )],
    "peek": [(
        "What does a detective do first?",
        "A detective looks and listens carefully before guessing. Paying attention helps the real answer appear."
    )],
    "basket": [(
        "Why use a basket for toys?",
        "A basket keeps toys together in one safe place. That makes the room tidier and bedtime quieter."
    )],
}
KNOWLEDGE_ORDER = ["peek", "window", "wind", "kitten", "water", "toy", "closet", "bathroom", "basket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    source = f["source"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "schlep" and "detective".',
        f"Tell a gentle story where a {child.type} named {child.id} hears {source.sound} at bedtime, feels afraid, and shows bravery by solving the mystery safely.",
        f"Write a cozy night story about a child detective who learns that brave steps can be small steps.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    source = f["source"]
    method = f["method"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a sleepy little detective at bedtime, and {child.pronoun('possessive')} {parent.label_word}. Together they listened for the truth behind a strange night sound."
        ),
        (
            "What made the mystery begin?",
            f"The mystery began when {child.id} heard {source.sound} coming from {source.location}. In the nighttime quiet, that small sound felt much bigger and scarier than it really was."
        ),
        (
            f"Why did {child.id} have to schlep {method.carry}?",
            f"{child.id} carried {method.carry} while going to investigate the sound. That little schlep showed bravery because {child.pronoun()} kept moving even while still feeling nervous."
        ),
        (
            f"What did {child.id} find?",
            f"{child.id} found that the noise was really {source.cause}. The mystery changed as soon as careful looking replaced the first scary guess."
        ),
        (
            "How was the problem solved?",
            f"They {method.solve}. After that, {source.safe_end.lower()} so the house felt calm again."
        ),
        (
            "What did the child learn about bravery?",
            f"{child.id} learned that bravery does not mean having no fear at all. It means taking one safe step, then another, until the scary thing makes sense."
        ),
        (
            "How did the story end?",
            f"It ended back in {setting.room}, with {child.id} tucked into bed again. The same house was quiet as before, but now the quiet felt friendly instead of mysterious."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["source"].tags) | set(world.facts["method"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cozy_house", "branch", "curtain_peek", "Lila", "girl", "mother", "thoughtful"),
    StoryParams("attic_room", "robot", "toy_basket", "Max", "boy", "father", "careful"),
    StoryParams("cottage", "kitten", "water_bowl", "Nora", "girl", "mother", "gentle"),
    StoryParams("cozy_house", "faucet", "faucet_turn", "Theo", "boy", "father", "steady"),
]


def explain_rejection(source: Source, method: Method) -> str:
    return (
        f"(No story: {method.id} solves a {method.kind} mystery, but {source.id} is a "
        f"{source.kind} mystery. Pick a method that really fits the sound's cause.)"
    )


ASP_RULES = r"""
compatible(Src, M) :- source(Src), method(M), source_kind(Src, K), method_kind(M, K).
valid(St, Src, M) :- setting(St), source(Src), method(M), compatible(Src, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_kind", source_id, source.kind))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("method_kind", method_id, method.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child detective hears a bedtime noise and solves it with bravery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.method:
        source = SOURCES[args.source]
        method = METHODS[args.method]
        if not valid_method(source, method):
            raise StoryError(explain_rejection(source, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.source is None or c[1] == args.source)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, source_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting_id, source_id, method_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SOURCES[params.source],
        METHODS[params.method],
        params.name,
        params.gender,
        params.parent,
        params.trait,
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
        print(f"{len(combos)} compatible (setting, source, method) combos:\n")
        for setting_id, source_id, method_id in combos:
            print(f"  {setting_id:11} {source_id:8} {method_id}")
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
            header = f"### {p.name}: {p.source} with {p.method} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
