#!/usr/bin/env python3
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "goose", "sheep", "doe", "mother", "aunt"}
        male = {"boy", "fox", "badger", "mole", "uncle", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def plain_type(self) -> str:
        return self.type.replace("_", " ")


@dataclass
class Setting:
    id: str
    place: str
    hazard: str
    spark_source: str
    afford_race: bool = True
    gear: set[str] = field(default_factory=set)
    omen: str = ""
    closing: str = ""


@dataclass
class Automobile:
    id: str
    label: str
    phrase: str
    material: str
    motion: str
    flaw: str
    vulnerable: str
    sound: str


@dataclass
class Method:
    id: str
    label: str
    gear_needed: str
    works_for: set[str]
    action: str
    repair: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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

    def note(self, text: str) -> None:
        self.trace.append(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tip_into_hazard(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    auto = world.get("auto")
    if hero.meters["speed"] < THRESHOLD or auto.meters["wobble"] < THRESHOLD:
        return out
    sig = ("tip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    auto.meters["heat"] += 1
    auto.meters["soot"] += 1
    auto.meters["broken"] += 1
    hero.memes["shame"] += 1
    hero.memes["fear"] += 1
    out.append(
        f"The loose wheel gave a hop, and the little automobile tipped toward {world.setting.hazard}."
    )
    out.append(
        f"A breath of heat licked its side, and dark soot striped the {auto.material} frame."
    )
    world.note("speed plus wobble caused the automobile to tip into the heat")
    return out


def _r_abject(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["shame"] < THRESHOLD:
        return []
    sig = ("abject",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["abject"] += 1
    world.note("the mishap made the hero feel abject")
    return ["At once the proud driver felt abject, as if all the cheer had run out through his toes."]


CAUSAL_RULES = [
    Rule("tip_into_hazard", _r_tip_into_hazard),
    Rule("abject_feeling", _r_abject),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rescue_method(setting: Setting, auto: Automobile) -> Optional[Method]:
    for method in METHODS:
        if method.gear_needed in setting.gear and auto.material in method.works_for:
            return method
    return None


def combo_valid(setting: Setting, auto: Automobile) -> bool:
    return setting.afford_race and rescue_method(setting, auto) is not None


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    auto = sim.get("auto")
    hero.meters["speed"] += 1
    auto.meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "tips": auto.meters["heat"] >= THRESHOLD,
        "broken": auto.meters["broken"] >= THRESHOLD,
        "soot": auto.meters["soot"] >= THRESHOLD,
    }


def opening_detail(setting: Setting) -> str:
    return {
        "village_green": "The morning sun made every brass bell wink.",
        "kiln_yard": "Warm brick walls held yesterday's heat like a secret.",
        "orchard_lane": "Dry leaves whispered under every paw and hoof.",
    }.get(setting.id, "The day looked simple, though it was not.")


def introduce(world: World, hero: Entity) -> None:
    trait = hero.traits[0] if hero.traits else "eager"
    world.say(
        f"In a small animal village lived {hero.id}, a {trait} young {hero.plain_type} who loved to go first."
    )
    world.say(opening_detail(world.setting))


def present_automobile(world: World, hero: Entity, auto: Entity, auto_cfg: Automobile) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id}'s finest treasure was {auto_cfg.phrase}, a tiny automobile that {auto_cfg.sound} when it rolled."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} liked to guide it with {auto_cfg.motion}, and for many days that pleased him greatly."
    )
    world.note("hero begins proud of the automobile")


def foreshadow(world: World, elder: Entity) -> None:
    world.say(
        f"Near {world.setting.spark_source} stood {world.setting.omen}. No one called it important then, but wise {elder.id} noticed it."
    )
    world.note("foreshadowing object is placed in view before the accident")


def warning(world: World, hero: Entity, elder: Entity, auto_cfg: Automobile) -> bool:
    pred = predict_trouble(world)
    if not pred["tips"]:
        return False
    world.facts["predicted"] = pred
    world.say(
        f'"Do not race so fast beside {world.setting.hazard}," said {elder.id}. '
        f'"Your {auto_cfg.label} has {auto_cfg.flaw}, and heat is a poor friend to {auto_cfg.vulnerable} things."'
    )
    world.say(
        f'{elder.id} even added, "If a spark catches it, some gloomy grown-up might use the hard word cremate, meaning burn it into ash. Let us not give the day such a sad ending."'
    )
    world.note("elder warns by predicting wobble plus fire risk")
    return True


def defy(world: World, hero: Entity, auto: Entity, auto_cfg: Automobile) -> None:
    hero.memes["defiance"] += 1
    hero.meters["speed"] += 1
    auto.meters["wobble"] += 1
    world.say(
        f"But pride puffed up {hero.id}'s chest. {hero.pronoun('subject').capitalize()} gave the little automobile a strong push and hurried after it."
    )
    world.say(
        f"It ran with a merry {auto_cfg.sound}, yet the weak part made a worried little shake."
    )
    world.note("hero chooses speed over caution")


def mishap(world: World) -> None:
    propagate(world, narrate=True)


def low_point(world: World, hero: Entity, auto_cfg: Automobile) -> None:
    if hero.memes["abject"] >= THRESHOLD:
        world.say(
            f'{hero.id} stared at the scorched toy and whispered, "I was trying to look grand, and now my {auto_cfg.label} looks small and sorry."'
        )


def rescue(world: World, hero: Entity, elder: Entity, auto: Entity, auto_cfg: Automobile) -> Method:
    method = rescue_method(world.setting, auto_cfg)
    if method is None:
        raise StoryError(
            f"No reasonable rescue exists for a {auto_cfg.material} automobile at {world.setting.place}."
        )
    auto.meters["heat"] = 0.0
    auto.meters["soot"] = max(0.0, auto.meters["soot"] - 1)
    auto.meters["repaired"] += 1
    hero.memes["gratitude"] += 1
    hero.memes["pride"] = 0.0
    hero.memes["patience"] += 1
    world.say(
        f"{elder.id} did not scold. {elder.pronoun('subject').capitalize()} {method.action}."
    )
    world.say(
        f"Then {elder.pronoun('subject')} {method.repair}, and the little machine was safe again."
    )
    world.note(f"rescue method {method.id} matched setting gear and automobile material")
    return method


def resolution(world: World, hero: Entity, elder: Entity, auto_cfg: Automobile, method: Method) -> None:
    world.say(
        f'After that, {hero.id} walked beside the automobile instead of chasing it. "Slow wheels reach home too," {hero.pronoun("subject")} said.'
    )
    world.say(
        f"At sunset {world.setting.closing}, and the mended {auto_cfg.label} rolled neatly at {hero.id}'s side."
    )
    world.say(
        f"So the villagers remembered: a warning may sound small, but it can save what pride would almost lose."
    )
    world.facts["moral"] = "A warning may sound small, but it can save what pride would almost lose."
    world.note("hero ends patient and grateful")


def tell(
    setting: Setting,
    auto_cfg: Automobile,
    hero_name: str,
    species: str,
    trait: str,
    elder_name: str,
    elder_type: str,
) -> World:
    if not combo_valid(setting, auto_cfg):
        raise StoryError(
            f"{auto_cfg.label.capitalize()} cannot make a sound story at {setting.place}: no fitting rescue method."
        )

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=species, label=hero_name, traits=[trait]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name))
    auto = world.add(
        Entity(
            id="auto",
            kind="thing",
            type="automobile",
            label=auto_cfg.label,
            phrase=auto_cfg.phrase,
            owner=hero.id,
            caretaker=elder.id,
            material=auto_cfg.material,
        )
    )

    introduce(world, hero)
    present_automobile(world, hero, auto, auto_cfg)

    world.para()
    foreshadow(world, elder)
    warning(world, hero, elder, auto_cfg)
    defy(world, hero, auto, auto_cfg)
    mishap(world)

    world.para()
    low_point(world, hero, auto_cfg)
    method = rescue(world, hero, elder, auto, auto_cfg)
    resolution(world, hero, elder, auto_cfg, method)

    world.facts.update(
        hero=hero,
        elder=elder,
        auto=auto,
        auto_cfg=auto_cfg,
        setting=setting,
        method=method,
    )
    return world


SETTINGS = {
    "village_green": Setting(
        id="village_green",
        place="the village green",
        hazard="the cook-fire ring",
        spark_source="the cook-fire ring",
        gear={"sand", "hook"},
        omen="a quiet bucket of sand beside a long iron hook",
        closing="the bells rang for supper",
    ),
    "kiln_yard": Setting(
        id="kiln_yard",
        place="the kiln yard",
        hazard="the warm ash trench",
        spark_source="the potter's kiln",
        gear={"hook"},
        omen="a black iron hook leaning against the kiln wall",
        closing="the last warm smoke curled into the evening sky",
    ),
    "orchard_lane": Setting(
        id="orchard_lane",
        place="orchard lane",
        hazard="the leaf-fire barrel",
        spark_source="the leaf-fire barrel",
        gear={"water"},
        omen="a blue water pail waiting by the barrel",
        closing="apple leaves spun down like little brown boats",
    ),
}

AUTOMOBILES = {
    "wood_roadster": Automobile(
        id="wood_roadster",
        label="wooden roadster",
        phrase="a red wooden roadster with a brass bell on the nose",
        material="wood",
        motion="both paws on the steering bar",
        flaw="a loose wheel peg",
        vulnerable="wooden",
        sound="brim-brim",
    ),
    "tin_runabout": Automobile(
        id="tin_runabout",
        label="tin runabout",
        phrase="a silver tin runabout with painted blue doors",
        material="metal",
        motion="one paw on the wheel and one foot on the pedal",
        flaw="a bent front axle",
        vulnerable="metal-painted",
        sound="ting-ting",
    ),
    "reed_buggy": Automobile(
        id="reed_buggy",
        label="reed buggy",
        phrase="a woven reed buggy trimmed with green ribbon",
        material="reed",
        motion="a light push and a skipping step",
        flaw="a frayed side spoke",
        vulnerable="dry reed",
        sound="whish-whish",
    ),
}

METHODS = [
    Method(
        id="sand_smother",
        label="cool sand",
        gear_needed="sand",
        works_for={"wood", "reed"},
        action="threw cool sand over the hot edge until the ember gave up and slept",
        repair="set the loose part straight with steady fingers",
    ),
    Method(
        id="hook_pull",
        label="iron hook",
        gear_needed="hook",
        works_for={"metal"},
        action="caught the axle with the iron hook and drew the hot toy clear of danger",
        repair="tapped the bent place true against a flat stone",
    ),
    Method(
        id="water_douse",
        label="water pail",
        gear_needed="water",
        works_for={"wood", "reed", "metal"},
        action="poured a shining ribbon of water until the heat hissed away",
        repair="wiped the wheels and tightened the weak part with a patient knot",
    ),
]

NAMES = {
    "fox": ["Rill", "Pip", "Nim", "Tavi"],
    "badger": ["Bran", "Moss", "Toll", "Ruf"],
    "mole": ["Mib", "Nook", "Pell", "Dib"],
    "hen": ["Poppy", "Dot", "Bramble", "Tansy"],
    "goose": ["Willa", "Merry", "Dapple", "Fern"],
}

ELDERS = {
    "uncle": [("Uncle Brindle", "fox"), ("Uncle Rowan", "badger"), ("Uncle Morrow", "mole")],
    "aunt": [("Aunt Tansy", "hen"), ("Aunt Willow", "goose"), ("Aunt Hazel", "hen")],
}

TRAITS = ["swift", "proud", "eager", "bright", "restless"]

CURATED = [
    ("village_green", "wood_roadster", "Rill", "fox", "proud", "Uncle Rowan", "badger"),
    ("kiln_yard", "tin_runabout", "Mib", "mole", "swift", "Aunt Hazel", "hen"),
    ("orchard_lane", "reed_buggy", "Willa", "goose", "eager", "Uncle Morrow", "mole"),
]


@dataclass
class StoryParams:
    setting: str
    automobile: str
    hero_name: str
    species: str
    trait: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for aid, auto in AUTOMOBILES.items():
            if combo_valid(setting, auto):
                out.append((sid, aid))
    return sorted(out)


def explain_rejection(setting: Setting, auto: Automobile) -> str:
    if not setting.afford_race:
        return f"(No story: {setting.place} does not afford a race at all.)"
    return (
        f"(No story: {setting.place} lacks a fitting rescue for a {auto.material} automobile. "
        f"The turn must be honest: the helper needs real gear that could save the toy.)"
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    auto = world.facts["auto_cfg"]
    setting = world.facts["setting"]
    return [
        f'Write a short fable for young children about a {hero.plain_type} and a little automobile at {setting.place}.',
        f"Tell a gentle story with foreshadowing where {elder.label} warns {hero.label} not to race {auto.phrase} beside {setting.hazard}.",
        'Write a TinyStories-style fable that includes the words "automobile", "abject", and "cremate" in child-safe context.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    auto = world.facts["auto_cfg"]
    setting = world.facts["setting"]
    method = world.facts["method"]
    return [
        QAItem(
            question=f"Who is the story about at {setting.place}?",
            answer=(
                f"The story is about {hero.label}, a young {hero.plain_type}, and {elder.label}, "
                f"the careful elder who watches over {hero.pronoun('object')}."
            ),
        ),
        QAItem(
            question=f"What treasure did {hero.label} love?",
            answer=(
                f"{hero.label} loved {auto.phrase}. It was a little automobile, and {hero.pronoun('subject')} felt proud when it rolled well."
            ),
        ),
        QAItem(
            question=f"What early sign foreshadowed the rescue later in the story?",
            answer=(
                f"The story quietly showed {setting.omen} near {setting.spark_source}. "
                f"That detail mattered later because the elder used that very help when the automobile tipped into danger."
            ),
        ),
        QAItem(
            question=f"Why did {elder.label} warn {hero.label} not to race beside {setting.hazard}?",
            answer=(
                f"{elder.label} saw that the {auto.label} had {auto.flaw}. "
                f"If {hero.label} raced too fast, the wobble could send the little automobile into heat and soot."
            ),
        ),
        QAItem(
            question=f"How did {hero.label} feel after the accident?",
            answer=(
                f"{hero.label} felt abject. {hero.pronoun('subject').capitalize()} had wanted to look grand, but instead {hero.pronoun('subject')} saw the scorched toy and felt ashamed."
            ),
        ),
        QAItem(
            question=f"How was the little automobile saved?",
            answer=(
                f"{elder.label} used {method.label}. {elder.pronoun('subject').capitalize()} {method.action}, then repaired the weak part so the little machine was safe again."
            ),
        ),
        QAItem(
            question="What lesson does the story teach?",
            answer=world.facts["moral"],
        ),
    ]


KNOWLEDGE = {
    "automobile": QAItem(
        question="What is an automobile?",
        answer="An automobile is a vehicle with wheels that carries someone from one place to another."
    ),
    "foreshadowing": QAItem(
        question="What is foreshadowing in a story?",
        answer="Foreshadowing is when a story shows a small clue early, and that clue becomes important later."
    ),
    "cremate": QAItem(
        question="What does cremate mean in this story?",
        answer="Here it means to burn something down into ash. The elder mentions the word to warn what might happen if the toy stayed in the fire."
    ),
    "abject": QAItem(
        question="What does abject mean?",
        answer="Abject means feeling very low, miserable, and ashamed."
    ),
    "soot": QAItem(
        question="What is soot?",
        answer="Soot is the black powder that comes from smoke or fire and can smear onto things."
    ),
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        KNOWLEDGE["automobile"],
        KNOWLEDGE["foreshadowing"],
        KNOWLEDGE["cremate"],
        KNOWLEDGE["abject"],
        KNOWLEDGE["soot"],
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.material:
            bits.append(f"material={ent.material}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(name for name, *rest in world.fired)}")
    lines.append("  trace:")
    for item in world.trace:
        lines.append(f"    - {item}")
    return "\n".join(lines)


ASP_RULES = r"""
rescue_possible(S,A) :- gear_at(S,G), method_gear(M,G), method_works(M,Mat), auto_material(A,Mat).
valid(S,A) :- setting(S), automobile(A), affords_race(S), rescue_possible(S,A).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.afford_race:
            lines.append(asp.fact("affords_race", sid))
        for g in sorted(setting.gear):
            lines.append(asp.fact("gear_at", sid, g))
    for aid, auto in AUTOMOBILES.items():
        lines.append(asp.fact("automobile", aid))
        lines.append(asp.fact("auto_material", aid, auto.material))
    for method in METHODS:
        lines.append(asp.fact("method", method.id))
        lines.append(asp.fact("method_gear", method.id, method.gear_needed))
        for mat in sorted(method.works_for):
            lines.append(asp.fact("method_works", method.id, mat))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py != ap:
        print("MISMATCH between python and ASP gates.")
        if py - ap:
            print("only in python:", sorted(py - ap))
        if ap - py:
            print("only in asp:", sorted(ap - py))
        return 1
    print(f"OK: ASP gate matches Python gate ({len(py)} combos).")
    try:
        for sid, aid in sorted(py):
            params = StoryParams(
                setting=sid,
                automobile=aid,
                hero_name="Rill" if aid != "reed_buggy" else "Willa",
                species="fox" if aid != "reed_buggy" else "goose",
                trait="eager",
                elder_name="Aunt Hazel",
                elder_type="hen",
            )
            sample = generate(params)
            if not sample.story.strip():
                print("Verification failed: empty story.")
                return 1
    except StoryError as err:
        print(f"Verification failed while generating a valid combo: {err}")
        return 1
    print("OK: generated stories for every valid combo.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable storyworld: a little automobile, a warning, foreshadowing, and a rescue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--automobile", choices=AUTOMOBILES)
    ap.add_argument("--species", choices=sorted(NAMES))
    ap.add_argument("--hero-name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--elder-role", choices=sorted(ELDERS))
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
    if args.setting and args.automobile:
        setting = SETTINGS[args.setting]
        auto = AUTOMOBILES[args.automobile]
        if not combo_valid(setting, auto):
            raise StoryError(explain_rejection(setting, auto))

    combos = [
        (sid, aid)
        for sid, aid in valid_combos()
        if (args.setting is None or sid == args.setting)
        and (args.automobile is None or aid == args.automobile)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, auto_id = rng.choice(combos)
    species = args.species or rng.choice(sorted(NAMES))
    hero_name = args.hero_name or rng.choice(NAMES[species])
    trait = args.trait or rng.choice(TRAITS)
    elder_role = args.elder_role or rng.choice(sorted(ELDERS))
    elder_name, elder_type = rng.choice(ELDERS[elder_role])

    return StoryParams(
        setting=setting_id,
        automobile=auto_id,
        hero_name=hero_name,
        species=species,
        trait=trait,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        AUTOMOBILES[params.automobile],
        params.hero_name,
        params.species,
        params.trait,
        params.elder_name,
        params.elder_type,
    )
    hero = world.get("hero")
    elder = world.get("elder")
    world.facts["hero"].label = params.hero_name
    world.facts["elder"].label = params.elder_name
    story_text = world.render().replace("hero", hero.label).replace("elder", elder.label)
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for sid, aid in asp_valid_combos():
            print(f"{sid:12} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for i, item in enumerate(CURATED):
            sid, aid, hero_name, species, trait, elder_name, elder_type = item
            params = StoryParams(
                setting=sid,
                automobile=aid,
                hero_name=hero_name,
                species=species,
                trait=trait,
                elder_name=elder_name,
                elder_type=elder_type,
                seed=base_seed + i,
            )
            samples.append(generate(params))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.hero_name}: {sample.params.automobile} at {sample.params.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
