#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nude_flex_dad_moral_value_slice_of.py
================================================================

A small slice-of-life storyworld about a child who comes out nude after a bath
or changing time, wants to copy a dad's silly flex, and learns a calm lesson
about privacy without losing the fun.

The moral value in this world is simple and concrete:
    Bodies are not shameful, but some moments are private.
    A kind grown-up can protect privacy without scolding away play.

Run it
------
    python storyworlds/worlds/gpt-5.4/nude_flex_dad_moral_value_slice_of.py
    python storyworlds/worlds/gpt-5.4/nude_flex_dad_moral_value_slice_of.py --setting breakfast_hall --cover robe
    python storyworlds/worlds/gpt-5.4/nude_flex_dad_moral_value_slice_of.py --cover cape
    python storyworlds/worlds/gpt-5.4/nude_flex_dad_moral_value_slice_of.py --all --qa
    python storyworlds/worlds/gpt-5.4/nude_flex_dad_moral_value_slice_of.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so go up three levels to
# reach storyworlds/ and import results.py from there.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    kind: str                    # "home" | "pool"
    room: str
    from_place: str
    to_place: str
    event: str
    witness: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    phrase: str
    adequate: bool = True
    warmth: int = 1
    fits: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    label: str
    applicable: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    cover: str
    response: str
    child_name: str
    child_gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "breakfast_hall": Setting(
        id="breakfast_hall",
        kind="home",
        room="the hall outside the bathroom",
        from_place="the warm bathroom",
        to_place="the breakfast table",
        event="breakfast",
        witness="the sunny front window and the clink of bowls in the kitchen",
        ending_image="sat at the table in a robe, wiggled little arms, and shared a banana with dad",
        tags={"home", "bathroom", "privacy"},
    ),
    "bedtime_room": Setting(
        id="bedtime_room",
        kind="home",
        room="the hallway by the bedroom door",
        from_place="the bath",
        to_place="the bedroom rug",
        event="bedtime",
        witness="the open bedroom door and the cool hall air",
        ending_image="stood on the bedroom rug in soft pajamas and did one last sleepy flex beside dad",
        tags={"home", "bathroom", "privacy", "bedtime"},
    ),
    "pool_locker": Setting(
        id="pool_locker",
        kind="pool",
        room="the family changing room at the pool",
        from_place="the changing stall",
        to_place="the locker bench",
        event="snack after swim class",
        witness="other families zipping bags and the wet echo of the pool nearby",
        ending_image="sat on the bench in a swimsuit, toes dripping, and grinned while dad gave a tiny flex back",
        tags={"pool", "privacy"},
    ),
}

COVERS = {
    "towel": Cover(
        id="towel",
        label="towel",
        phrase="a big striped towel",
        adequate=True,
        warmth=1,
        fits={"breakfast_hall", "pool_locker"},
        tags={"towel", "privacy"},
    ),
    "robe": Cover(
        id="robe",
        label="robe",
        phrase="a soft blue robe",
        adequate=True,
        warmth=2,
        fits={"breakfast_hall", "bedtime_room"},
        tags={"robe", "privacy"},
    ),
    "pajamas": Cover(
        id="pajamas",
        label="pajamas",
        phrase="soft moon-print pajamas",
        adequate=True,
        warmth=2,
        fits={"bedtime_room"},
        tags={"pajamas", "privacy", "bedtime"},
    ),
    "swimsuit": Cover(
        id="swimsuit",
        label="swimsuit",
        phrase="a bright green swimsuit",
        adequate=True,
        warmth=1,
        fits={"pool_locker"},
        tags={"swimsuit", "pool", "privacy"},
    ),
    "cape": Cover(
        id="cape",
        label="cape",
        phrase="a pretend hero cape",
        adequate=False,
        warmth=0,
        fits={"breakfast_hall", "bedtime_room"},
        tags={"pretend"},
    ),
}

RESPONSES = {
    "gentle_wrap": Response(
        id="gentle_wrap",
        sense=3,
        label="gentle wrap",
        applicable={"home"},
        tags={"privacy", "kindness"},
    ),
    "mirror_race": Response(
        id="mirror_race",
        sense=3,
        label="mirror race",
        applicable={"home"},
        tags={"privacy", "kindness", "flex"},
    ),
    "turn_and_offer": Response(
        id="turn_and_offer",
        sense=3,
        label="turn and offer",
        applicable={"pool"},
        tags={"privacy", "kindness", "pool"},
    ),
    "shout_across": Response(
        id="shout_across",
        sense=1,
        label="shout across the room",
        applicable={"home", "pool"},
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Max", "Ben", "Sam", "Noah", "Eli"]
TRAITS = ["bouncy", "curious", "sleepy", "cheerful", "wriggly", "playful"]


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


def cover_works(setting: Setting, cover: Cover) -> bool:
    return cover.adequate and setting.id in cover.fits


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(setting: Setting, response: Response) -> bool:
    return setting.kind in response.applicable


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for cid, cover in COVERS.items():
            if not cover_works(setting, cover):
                continue
            for rid, response in RESPONSES.items():
                if response.sense >= SENSE_MIN and response_fits(setting, response):
                    combos.append((sid, cid, rid))
    return combos


def explain_cover_rejection(setting: Setting, cover: Cover) -> str:
    if not cover.adequate:
        return (
            f"(No story: {cover.phrase} is not enough cover for a private-body moment. "
            f"This world needs a real covering item, not just dress-up clothes.)"
        )
    return (
        f"(No story: {cover.phrase} does not fit the {setting.event} setting. "
        f"Choose something that makes sense in {setting.room}.)"
    )


def explain_response_rejection(setting: Setting, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it is too harsh for this world. "
            f"The story prefers calm, sensible guidance.)"
        )
    return (
        f"(No story: response '{response.id}' does not fit a {setting.kind} setting.)"
    )


def intro(world: World, child: Entity, dad: Entity, setting: Setting) -> None:
    if setting.id == "pool_locker":
        world.say(
            f"After swim class, {child.id} padded into {setting.room} with {child.pronoun('possessive')} dad. "
            f"The air smelled like soap and pool water."
        )
    else:
        world.say(
            f"At home, {child.id} came from {setting.from_place} while {child.pronoun('possessive')} dad was getting ready for {setting.event}."
        )
    child.memes["safe"] += 1
    dad.memes["care"] += 1


def spark(world: World, child: Entity, dad: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    if setting.kind == "pool":
        world.say(
            f"Dad lifted the snack bag with one hand and made a tiny flex to make {child.id} laugh."
        )
    else:
        world.say(
            f"Dad picked up a basket with one arm and made a silly little flex, and {child.id} giggled at once."
        )


def dash_out(world: World, child: Entity, setting: Setting) -> None:
    child.meters["nude"] += 1
    child.meters["damp"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Wanting to copy it, {child.id} hurried into {setting.room}, still nude and damp, and puffed up {child.pronoun('possessive')} tiny arms."
    )
    world.say(
        f'"Look! I can flex too!" {child.pronoun().capitalize()} said, right by {setting.witness}.'
    )


def risk_beat(world: World, child: Entity, dad: Entity, setting: Setting) -> None:
    child.memes["surprise"] += 1
    dad.memes["calm"] += 1
    world.say(
        f"For a second, the moment felt too open. {dad.label_word.capitalize()} saw how easy it would be for a private bath-time moment to slip into a shared space."
    )
    world.facts["privacy_risk"] = setting.witness


def guide(world: World, child: Entity, dad: Entity, setting: Setting,
          cover: Cover, response: Response) -> None:
    child.meters["covered"] += 1
    child.meters["nude"] = 0.0
    child.meters["warm"] += float(max(cover.warmth, 1))
    child.memes["trust"] += 1
    child.memes["embarrassment"] = 0.0
    dad.memes["care"] += 1
    world.facts["lesson"] = "Bodies are private in shared spaces, and kindness can protect privacy."

    if response.id == "gentle_wrap":
        world.say(
            f"{dad.label_word.capitalize()} did not scold. He knelt down, opened {cover.phrase}, and wrapped it around {child.id}."
        )
        world.say(
            f'"Your body is good," he said softly. "And some moments are private. We cover up before we walk into shared spaces."'
        )
    elif response.id == "mirror_race":
        world.say(
            f'{dad.label_word.capitalize()} smiled and whispered, "First {cover.label}, then flex." He helped {child.id} into {cover.phrase} as if it were part of the game.'
        )
        world.say(
            f'"Let\'s race to {setting.to_place} and do our strongest covered flexes there," he said.'
        )
    elif response.id == "turn_and_offer":
        world.say(
            f"{dad.label_word.capitalize()} turned his shoulders a little to give {child.id} privacy, then held out {cover.phrase}."
        )
        world.say(
            f'"Pool bodies need privacy too," he said. "Get covered, and then show me your flex on the bench."'
        )
    else:
        raise StoryError(explain_response_rejection(setting, response))


def ending(world: World, child: Entity, dad: Entity, setting: Setting, cover: Cover) -> None:
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    dad.memes["joy"] += 1
    if setting.id == "breakfast_hall":
        world.say(
            f"A minute later, {child.id} was covered and cozy. In the shiny oven door, child and dad each tried one more flex and both burst out laughing."
        )
        world.say(
            f"Then {child.id} {setting.ending_image}. The fun stayed, but the private part was private again."
        )
    elif setting.id == "bedtime_room":
        world.say(
            f"Soon {child.id} was warm in {cover.phrase}. On the way to bed, {dad.label_word} gave one sleepy flex, and {child.id} copied it with a grin."
        )
        world.say(
            f"Then {child.id} {setting.ending_image}. The hallway felt calm because the silly game had found the right place."
        )
    else:
        world.say(
            f"In another moment, the wet feet were tucked under the bench and the private part of changing time was over."
        )
        world.say(
            f"Then {child.id} {setting.ending_image}. Even at the pool, they had made room for both play and privacy."
        )


def tell(setting: Setting, cover: Cover, response: Response,
         child_name: str, child_gender: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        attrs={"trait": trait},
    ))
    dad = world.add(Entity(
        id="Dad",
        kind="character",
        type="father",
        role="dad",
        label="dad",
    ))

    intro(world, child, dad, setting)
    spark(world, child, dad, setting)

    world.para()
    dash_out(world, child, setting)
    risk_beat(world, child, dad, setting)

    world.para()
    guide(world, child, dad, setting, cover, response)
    ending(world, child, dad, setting, cover)

    world.facts.update(
        child=child,
        dad=dad,
        setting=setting,
        cover=cover,
        response=response,
        covered=child.meters["covered"] >= THRESHOLD,
        warm=child.meters["warm"] >= THRESHOLD,
        moral=world.facts["lesson"],
    )
    return world


KNOWLEDGE = {
    "privacy": [(
        "What does privacy mean for bodies?",
        "Privacy means some parts of our bodies are for private moments like bathing, dressing, or changing. A grown-up can help us keep those moments respectful and calm."
    )],
    "towel": [(
        "What is a towel for after a bath or swim?",
        "A towel dries your skin and helps cover your body while you get ready. It can help you stay warm and private."
    )],
    "robe": [(
        "What is a robe?",
        "A robe is a soft piece of clothing you wear over your body after bathing or before bed. It helps you stay warm and covered."
    )],
    "pajamas": [(
        "What are pajamas for?",
        "Pajamas are clothes people wear for sleeping or bedtime. They help your body feel comfortable and ready to rest."
    )],
    "swimsuit": [(
        "Why do people wear swimsuits at a pool?",
        "Swimsuits are clothes made for swimming and moving in water. They help people stay properly covered at the pool."
    )],
    "flex": [(
        "What does flex mean here?",
        "Here, flex means tightening your arm muscles in a playful way to look strong. It can be a silly game, not a mean one."
    )],
    "pool": [(
        "Why do changing rooms matter at a pool?",
        "Changing rooms give people a private place to take wet things off and put dry things on. That helps everyone feel comfortable and respected."
    )],
    "bathroom": [(
        "Why are bathrooms private places?",
        "Bathrooms are private because people bathe, dry off, and get dressed there. Privacy helps people feel safe and respected."
    )],
}
KNOWLEDGE_ORDER = ["privacy", "bathroom", "pool", "towel", "robe", "pajamas", "swimsuit", "flex"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, setting, cover = f["child"], f["setting"], f["cover"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "nude", "flex", and "dad", and teaches a gentle lesson about privacy.',
        f"Tell a homey moral-value story where {child.id} copies a dad's silly flex while still nude after changing time, and a calm grown-up helps with {cover.label} instead of scolding.",
        f"Write a simple everyday story set around {setting.event} where play and privacy both matter, and the ending shows the child feeling safe, covered, and still happy.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    dad = f["dad"]
    setting = f["setting"]
    cover = f["cover"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} dad during an ordinary {setting.event} moment. The story stays small and everyday so the lesson feels gentle and real."
        ),
        (
            f"Why did {child.id} come out nude?",
            f"{child.id} had just come from {setting.from_place}, so {child.pronoun()} was still damp and not dressed yet. That is why the private-body moment needed quick, calm help."
        ),
        (
            f"What made {child.id} want to flex?",
            f"{dad.label_word.capitalize()} made a silly little flex first, and {child.id} wanted to copy him. The problem was not the game itself, but where and when it happened."
        ),
        (
            f"Why did dad help {child.id} cover up?",
            f"He could see that {setting.witness} made the moment too open for a private body moment. He wanted to protect {child.id}'s privacy without making {child.pronoun('object')} feel ashamed."
        ),
        (
            "What did the child learn?",
            f"{f['moral']} The story shows that a body is not bad, but shared spaces need care and covering."
        ),
        (
            "How did the story end?",
            f"It ended happily, with {child.id} covered in {cover.phrase} and still getting to share the silly flex game with dad. The ending proves that kindness kept both the fun and the privacy."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["setting"].tags) | set(world.facts["cover"].tags) | set(world.facts["response"].tags)
    tags.add("flex")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  moral: {world.facts.get('moral', '')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="breakfast_hall",
        cover="robe",
        response="gentle_wrap",
        child_name="Maya",
        child_gender="girl",
        trait="bouncy",
    ),
    StoryParams(
        setting="bedtime_room",
        cover="pajamas",
        response="mirror_race",
        child_name="Leo",
        child_gender="boy",
        trait="sleepy",
    ),
    StoryParams(
        setting="pool_locker",
        cover="swimsuit",
        response="turn_and_offer",
        child_name="Nora",
        child_gender="girl",
        trait="cheerful",
    ),
    StoryParams(
        setting="breakfast_hall",
        cover="towel",
        response="mirror_race",
        child_name="Ben",
        child_gender="boy",
        trait="playful",
    ),
]


ASP_RULES = r"""
adequate_cover(C) :- cover(C), adequate(C).
sensible(R)       :- response(R), sense(R, S), sense_min(M), S >= M.
response_fits(S, R) :- setting(S), response(R), kind(S, K), applies_to(R, K).
cover_fits(S, C)    :- setting(S), cover(C), fits(C, S).
valid(S, C, R)      :- cover_fits(S, C), adequate_cover(C), sensible(R), response_fits(S, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("kind", sid, setting.kind))
    for cid, cover in COVERS.items():
        lines.append(asp.fact("cover", cid))
        if cover.adequate:
            lines.append(asp.fact("adequate", cid))
        for sid in sorted(cover.fits):
            lines.append(asp.fact("fits", cid, sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        for kind in sorted(response.applicable):
            lines.append(asp.fact("applies_to", rid, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def smoke_test_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "dad" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story was empty or missing dad.")
    sink = io.StringIO()
    with contextlib.redirect_stdout(sink):
        emit(sample, trace=True, qa=True, header="### smoke")
    text = sink.getvalue()
    if "### smoke" not in text or "world model state" not in text:
        raise StoryError("Smoke test failed: emit() did not produce expected output.")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    try:
        smoke_test_generate()
        print("OK: smoke test generation and emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a child copies a dad's flex during a private-body moment, and privacy is taught with kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {args.setting})")
    if args.cover is not None and args.cover not in COVERS:
        raise StoryError(f"(Unknown cover: {args.cover})")
    if args.response is not None and args.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {args.response})")

    if args.setting and args.cover:
        setting = SETTINGS[args.setting]
        cover = COVERS[args.cover]
        if not cover_works(setting, cover):
            raise StoryError(explain_cover_rejection(setting, cover))

    if args.setting and args.response:
        setting = SETTINGS[args.setting]
        response = RESPONSES[args.response]
        if not (response.sense >= SENSE_MIN and response_fits(setting, response)):
            raise StoryError(explain_response_rejection(setting, response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cover is None or combo[1] == args.cover)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cover_id, response_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        child_name = args.name
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        child_name = rng.choice(pool)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        cover=cover_id,
        response=response_id,
        child_name=child_name,
        child_gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting in params: {params.setting})")
    if params.cover not in COVERS:
        raise StoryError(f"(Unknown cover in params: {params.cover})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response in params: {params.response})")

    setting = SETTINGS[params.setting]
    cover = COVERS[params.cover]
    response = RESPONSES[params.response]

    if not cover_works(setting, cover):
        raise StoryError(explain_cover_rejection(setting, cover))
    if not (response.sense >= SENSE_MIN and response_fits(setting, response)):
        raise StoryError(explain_response_rejection(setting, response))

    world = tell(
        setting=setting,
        cover=cover,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
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
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sensible = asp_sensible()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} valid (setting, cover, response) combos:\n")
        for setting_id, cover_id, response_id in combos:
            print(f"  {setting_id:15} {cover_id:10} {response_id}")
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
            header = f"### {p.child_name}: {p.setting}, {p.cover}, {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
