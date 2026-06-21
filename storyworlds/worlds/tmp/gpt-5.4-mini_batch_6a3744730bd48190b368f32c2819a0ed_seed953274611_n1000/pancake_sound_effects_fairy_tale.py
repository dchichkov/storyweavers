#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pancake_sound_effects_fairy_tale.py
===================================================================

A small standalone storyworld for a fairy-tale pancake story with sound effects.

Premise:
- A child or small cook is making a pancake in a fairy-tale kitchen.
- The story uses playful sound effects as concrete events in the world.
- Something goes wrong or almost goes wrong.
- A helper figure uses a sensible tool to fix it.
- The ending proves the pancake became part of a warm, happy feast.

This script follows the shared Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasonableness checks plus an inline ASP twin
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVE_INIT = 5.0
CALM_TRAITS = {"careful", "patient", "gentle", "wise"}


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
    edible: bool = False
    magical: bool = False
    makes_sound: bool = False
    good_tool: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "fairy"}
        male = {"boy", "father", "king", "prince", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    mood: str
    includes: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    word: str
    note: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Pan:
    id: str
    label: str
    heat: str
    sound: str
    can_flip: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    verb: str
    tool_sound: str
    power: int
    sense: int
    success: str
    fail: str
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
        clone = World()
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


def _r_sizzle(world: World) -> list[str]:
    out: list[str] = []
    pan = world.get("pan")
    batter = world.get("pancake")
    if batter.meters["cooking"] >= THRESHOLD and pan.meters["heat"] >= THRESHOLD:
        sig = ("sizzle", batter.id)
        if sig not in world.fired:
            world.fired.add(sig)
            batter.meters["browned"] += 1
            out.append("__sound__")
    return out


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    batter = world.get("pancake")
    if batter.meters["browned"] >= THRESHOLD:
        sig = ("smell", batter.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").memes["joy"] += 1
            out.append("The sweet smell drifted through the kitchen.")
    return out


CAUSAL_RULES = [Rule("sizzle", "sound", _r_sizzle), Rule("smell", "feeling", _r_smell)]


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


def reasonable_combo(place: Place, pan: Pan, fix: Fix) -> bool:
    return "kitchen" in place.tags and pan.can_flip and fix.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for pan_id, pan in PANS.items():
            for fix_id, fix in FIXES.items():
                if reasonable_combo(place, pan, fix):
                    combos.append((pid, pan_id, fix_id))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def predicted_risk(world: World, pan_id: str) -> bool:
    sim = world.copy()
    sim.get(pan_id).meters["heat"] += 1
    sim.get("pancake").meters["cooking"] += 1
    propagate(sim, narrate=False)
    return sim.get("pancake").meters["browned"] >= THRESHOLD


def setup(world: World, hero: Entity, helper: Entity, place: Place, pan: Pan, sound: SoundEffect) -> None:
    hero.memes["delight"] += 1
    helper.memes["delight"] += 1
    world.say(
        f"Once in a bright fairy-tale {place.label}, {hero.id} stood by the little stove. "
        f"{place.includes} {place.sound}."
    )
    world.say(
        f"{helper.id} smiled. \"We can make a pancake,\" {helper.pronoun()} said, "
        f"and {sound.word} floated from the spoon like music."
    )


def mix(world: World, hero: Entity, sound: SoundEffect, pan: Pan) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} stirred the batter with a happy {sound.word}. "
        f"The pan waited warm and shiny, ready for the first pour."
    )
    world.say(f"{pan.sound} went the pan when the butter touched it.")


def temptation(world: World, hero: Entity, helper: Entity, sound: SoundEffect, pan: Pan) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"\"Let's flip it high!\" {hero.id} whispered, and {sound.word} answered from the bowl."
    )
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip and peered at the pan. "
        f"\"A tall flip can go wrong fast,\" {helper.pronoun()} warned."
    )


def defy_or_listen(world: World, hero: Entity, helper: Entity, pan: Pan, sound: SoundEffect) -> bool:
    if helper.memes["calm"] >= 1 and helper.attrs.get("older", False):
        hero.memes["doubt"] += 1
        world.say(
            f"{hero.id} listened. The spoon paused in midair, and {sound.word} softened to a tiny whisper."
        )
        return True
    world.say(
        f"{hero.id} laughed, tossed the pancake too high, and {sound.word} shot up to the rafters."
    )
    return False


def spill(world: World, pan: Pan, sound: SoundEffect) -> None:
    world.get("pancake").meters["cooking"] += 1
    pan.meters["heat"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Flip-flap! The pancake spun, wobbled, and landed crooked on the edge of the pan."
    )
    if world.get("pancake").meters["browned"] >= THRESHOLD:
        world.say(f"{sound.word} and sizzle! The little cake began to brown at once.")


def rescue(world: World, helper: Entity, fix: Fix, pan: Pan, sound: SoundEffect) -> bool:
    risky = world.get("pancake").meters["browned"] >= THRESHOLD
    if risky and fix.power < 2:
        world.say(
            f"{helper.id} tried {fix.verb}, but the hot edge kept slipping. "
            f"{fix.fail}"
        )
        return False
    world.get("pancake").meters["saved"] += 1
    world.say(
        f"{helper.id} {fix.verb} and {fix.tool_sound}, steady as a spell. "
        f"{fix.success}"
    )
    world.get("pancake").meters["served"] += 1
    return True


def ending(world: World, hero: Entity, helper: Entity, place: Place, sound: SoundEffect) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, the pancake came to the table with a golden blush. "
        f"{sound.word}! said the napkins as everyone laughed."
    )
    world.say(
        f"By candlelight, {hero.id} and {helper.id} ate the warm pancake together, "
        f"and the castle kitchen felt cozy again."
    )


def tale(world: World, hero: Entity, helper: Entity, place: Place, sound: SoundEffect,
         pan: Pan, fix: Fix, aversion: bool) -> None:
    setup(world, hero, helper, place, pan, sound)
    world.para()
    mix(world, hero, sound, pan)
    temptation(world, hero, helper, sound, pan)
    listened = aversion or defy_or_listen(world, hero, helper, pan, sound)
    world.para()
    if listened:
        world.say(f"With a gentle nod, {helper.id} lowered the heat and the pancake sang softly instead of leaping.")
        rescue(world, helper, fix, pan, sound)
    else:
        spill(world, pan, sound)
        rescue(world, helper, fix, pan, sound)
    world.para()
    ending(world, hero, helper, place, sound)
    world.facts.update(hero=hero, helper=helper, place=place, sound=sound, pan=pan, fix=fix, listened=listened)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child about a pancake and the sound "{f["sound"].word}".',
        f"Tell a cozy castle-kitchen story where {f['hero'].id} makes a pancake, hears {f['sound'].word}, and learns a gentle lesson.",
        f'Write a magical story that uses sound effects like "{f["sound"].word}" and ends with a warm pancake shared at a table.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, place, sound, fix = f["hero"], f["helper"], f["place"], f["sound"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id} in {place.label}. They are the two people who make the pancake story happen."),
        ("What sound effect is important in the story?",
         f"The story leans on {sound.word}. It marks the moment when the pancake starts to cook and the kitchen feels lively."),
        ("How did the helper keep things safe?",
         f"{helper.id} used {fix.label} and a calm voice. That slowed the trouble down and helped the pancake stay in the kitchen instead of flying away."),
    ]
    if f["listened"]:
        qa.append((
            "Did the hero listen?",
            f"Yes. {hero.id} listened before anything truly went wrong, so the story stays warm and gentle. The pancake was cooked with care instead of a big scramble."
        ))
    else:
        qa.append((
            "What happened when the hero did not listen?",
            f"{hero.id} flipped the pancake too high, so it wobbled and landed crooked. That made the helper step in quickly with a sensible fix."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with a golden pancake at the table and everyone laughing by candlelight. The sound of the kitchen turned into a happy feast."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set()
    tags |= set(f["place"].tags)
    tags |= set(f["sound"].tags)
    tags |= set(f["fix"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: Place, pan: Pan, fix: Fix) -> str:
    return (
        f"(No story: the chosen place or fix does not support a fairytale pancake scene. "
        f"Try a kitchen-like place, a pan that can flip, and a sensible fix with common sense.)"
    )


def explain_fix(rid: str) -> str:
    fix = FIXES[rid]
    if fix.sense < 2:
        return f"(Refusing fix '{rid}': it sounds too shaky for a story that should end safely.)"
    return "(No story: invalid fix choice.)"


def valid_fix_ids() -> list[str]:
    return [fid for fid, fix in FIXES.items() if fix.sense >= 2]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.fix and FIXES[args.fix].sense < 2:
        raise StoryError(explain_fix(args.fix))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.pan is None or c[1] == args.pan)
        and (args.fix is None or c[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, pan_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(rng, gender)
    helper_gender = "girl" if gender == "boy" else "boy"
    helper_name = rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    helper_trait = rng.choice(sorted(CALM_TRAITS))
    aversion = args.avert if args.avert is not None else bool(rng.randint(0, 1))
    return StoryParams(
        place=place_id,
        pan=pan_id,
        fix=fix_id,
        hero=name,
        hero_gender=gender,
        helper=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        aversion=aversion,
    )


@dataclass
class StoryParams:
    place: str
    pan: str
    fix: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    helper_trait: str
    aversion: bool = False
    seed: Optional[int] = None


PLACES = {
    "castle_kitchen": Place(
        id="castle_kitchen",
        label="castle kitchen",
        mood="warm",
        includes="The copper pots shone and the hearth blinked like a sleepy eye.",
        sound="Clink-clink, went the spoons.",
        tags={"kitchen", "castle"},
    ),
    "fairy_cottage": Place(
        id="fairy_cottage",
        label="fairy cottage",
        mood="bright",
        includes="Tiny shelves held jam jars and flower cups.",
        sound="Tink-tink, sang the teacups.",
        tags={"kitchen", "cottage", "fairy"},
    ),
    "sunny_sunroom": Place(
        id="sunny_sunroom",
        label="sunny sunroom",
        mood="golden",
        includes="The window was wide and the table was bright as butter.",
        sound="Hum-hum, whispered the oven.",
        tags={"kitchen", "sunny"},
    ),
}

PANS = {
    "iron_pan": Pan(id="iron_pan", label="iron pan", heat="hot", sound="Ssssss", tags={"pan"}),
    "silver_pan": Pan(id="silver_pan", label="silver pan", heat="warm", sound="Pip-pip", tags={"pan"}),
    "star_pan": Pan(id="star_pan", label="star pan", heat="glow", sound="Shimmer-shh", tags={"pan", "magic"}),
}

SOUNDS = {
    "sizzle": SoundEffect(id="sizzle", word="sizzle", note="A long hot whisper from the pan.", helps="It tells you the pancake is cooking.", tags={"sound", "cooking"}),
    "flip_flap": SoundEffect(id="flip_flap", word="flip-flap", note="The sound of a pancake turning in the air.", helps="It makes the flip feel like a little dance.", tags={"sound", "flip"}),
    "whisk_whisk": SoundEffect(id="whisk_whisk", word="whisk-whisk", note="A quick bright sound from mixing batter.", helps="It marks the start of the batter's magic.", tags={"sound", "mix"}),
}

FIXES = {
    "lower_heat": Fix(
        id="lower_heat",
        label="the heat dial",
        verb="turned the heat lower",
        tool_sound="click",
        power=3,
        sense=3,
        success="The pancake settled down and browned evenly.",
        fail="The heat was still too fierce, so the pancake kept wobbling.",
        tags={"fix", "safe"},
    ),
    "lid_catch": Fix(
        id="lid_catch",
        label="a wide lid",
        verb="held up a wide lid",
        tool_sound="clap",
        power=3,
        sense=3,
        success="The lid caught the pancake gently, and it landed safely back in the pan.",
        fail="The lid missed by a whisker, and the pancake nearly slipped away.",
        tags={"fix", "safe"},
    ),
    "spoon_stir": Fix(
        id="spoon_stir",
        label="a wooden spoon",
        verb="stirred with a wooden spoon",
        tool_sound="tap-tap",
        power=2,
        sense=2,
        success="The spoon steadied the edges and the pancake came right again.",
        fail="The spoon was too small, and the wobble kept going.",
        tags={"fix", "safe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ella", "Nora", "Rose", "Ava"]
BOY_NAMES = ["Tom", "Ben", "Leo", "Finn", "Jack", "Theo"]
KNOWLEDGE = {
    "pancake": [("What is a pancake?", "A pancake is a flat cake cooked on a pan or griddle. It is often soft, warm, and eaten at breakfast.")],
    "sound": [("What is a sound effect in a story?", "A sound effect is a word like sizzle or bang that helps you imagine what is happening.")],
    "flip": [("What does flip mean?", "To flip something is to turn it over quickly, often in the air or in a pan.")],
    "pan": [("What is a pan?", "A pan is a flat cooking dish used to heat food on a stove.")],
    "mix": [("Why do people whisk batter?", "People whisk batter to mix the ingredients together smoothly before cooking.")],
    "safe": [("Why is lowering the heat helpful?", "Lowering the heat can keep food from burning and gives you more time to cook it well.")],
}
KNOWLEDGE_ORDER = ["pancake", "sound", "flip", "pan", "mix", "safe"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for pan_id, pan in PANS.items():
            for fix_id, fix in FIXES.items():
                if reasonable_combo(place, pan, fix):
                    combos.append((place_id, pan_id, fix_id))
    return combos


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.pan not in PANS or params.fix not in FIXES:
        raise StoryError("(Invalid StoryParams values.)")
    world = World()
    place = world.add(Entity(id=params.place, label=PLACES[params.place].label))
    place.attrs = {"mood": PLACES[params.place].mood}
    sound = world.add(Entity(id="sound", label=SOUNDS["sizzle"].word, magical=True, makes_sound=True))
    sound.tags = set(SOUNDS["sizzle"].tags)
    # Select actual sound from params
    sfx = SOUNDS[sorted(SOUNDS)[0]] if False else None
    sfx = rng_sound = None
    sfx = SOUNDS["sizzle"]
    # Use a chosen sound based on the pan / fix combo for variety
    if params.fix == "lid_catch":
        sfx = SOUNDS["flip_flap"]
    elif params.place == "fairy_cottage":
        sfx = SOUNDS["whisk_whisk"]
    pan = world.add(Entity(id="pan", label=PANS[params.pan].label, good_tool=True, makes_sound=True))
    pan.meters["heat"] = 1.0
    pancake = world.add(Entity(id="pancake", label="pancake", edible=True))
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, role="hero", attrs={"name": params.hero}))
    hero.id = params.hero
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=[params.helper_trait], attrs={"older": True}))
    helper.memes["calm"] = 1.0
    helper.memes["care"] = 1.0
    fix = FIXES[params.fix]
    tale(world, hero, helper, PLACES[params.place], sfx, PANS[params.pan], fix, params.aversion)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
good_combo(P, N, F) :- place(P), pan(N), fix(F), kitchen_place(P), flip_pan(N), sensible(F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "kitchen" in p.tags:
            lines.append(asp.fact("kitchen_place", pid))
    for pan_id, pan in PANS.items():
        lines.append(asp.fact("pan", pan_id))
        if pan.can_flip:
            lines.append(asp.fact("flip_pan", pan_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sensible", fix_id) if fix.sense >= 2 else asp.fact("unsensible", fix_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams(place="castle_kitchen", pan="iron_pan", fix="lower_heat", hero="Lily", hero_gender="girl", helper="Mira", helper_gender="girl", helper_trait="wise", aversion=False),
    StoryParams(place="fairy_cottage", pan="star_pan", fix="lid_catch", hero="Tom", hero_gender="boy", helper="Nora", helper_gender="girl", helper_trait="gentle", aversion=True),
    StoryParams(place="sunny_sunroom", pan="silver_pan", fix="spoon_stir", hero="Ava", hero_gender="girl", helper="Ben", helper_gender="boy", helper_trait="patient", aversion=False),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale pancake storyworld with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pan", choices=PANS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
