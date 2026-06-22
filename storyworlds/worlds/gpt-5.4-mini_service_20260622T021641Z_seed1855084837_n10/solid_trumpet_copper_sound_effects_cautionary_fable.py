#!/usr/bin/env python3
"""
storyworlds/worlds/solid_trumpet_copper_sound_effects_cautionary_fable.py
=========================================================================

A small, self-contained storyworld for a cautionary fable about sound,
pride, and the trouble that can follow a loud brass trumpet.

The seed inspiration is a tiny tale in the style of a fable:
an animal finds a trumpet, makes a showy sound effect, and learns that
noise can frighten a flock and break a calm moment. The world keeps the
premise small: one creature, one instrument, one copper object, one lesson.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "goose"}
        male = {"boy", "father", "dad", "man", "fox", "wolf", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    animal: str
    instrument: str
    treasure: str
    helper: str
    place: str
    seed: Optional[int] = None


@dataclass
class AnimalCfg:
    id: str
    type: str
    label: str
    voice: str
    trait: str
    lesson_voice: str
    gendered_name_hint: str = ""


@dataclass
class InstrumentCfg:
    id: str
    label: str
    phrase: str
    sound: str
    sound_word: str
    loudness: str
    can_startle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TreasureCfg:
    id: str
    label: str
    phrase: str
    material: str
    solidity: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    advice: str
    safe_alternative: str
    tag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SettingCfg:
    id: str
    place: str
    scene: str
    afford: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: SettingCfg) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("startle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "flock" in world.entities:
            world.get("flock").memes["fear"] += 1
        out.append("sounded_startling")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    fox = world.entities.get("hero")
    cup = world.entities.get("cup")
    if not fox or not cup:
        return out
    if fox.meters["pride"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cup.meters["shaken"] += 1
    out.append("shaken_cup")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("startle", "sound", _r_startle),
    Rule("spill", "physical", _r_spill),
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
            if s == "sounded_startling":
                world.say("The trumpet sounded so bright and loud that the flock lifted at once.")
            elif s == "shaken_cup":
                world.say("The copper cup rattled on the stone and nearly slipped from the ledge.")
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for animal in ANIMALS:
        for instrument in INSTRUMENTS:
            for treasure in TREASURES:
                if instrument.can_startle and treasure.solidity == "solid":
                    combos.append((animal, instrument.id, treasure.id))
    return combos


def reason_check(instrument: InstrumentCfg, treasure: TreasureCfg) -> None:
    if not instrument.can_startle:
        raise StoryError("This trumpet tale needs a real sound effect.")
    if treasure.solidity != "solid":
        raise StoryError("This fable needs a solid object that can be jostled but not shattered.")


def setting_for(place: str) -> SettingCfg:
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return SETTINGS[place]


def pick_name(rng: random.Random, cfg: AnimalCfg) -> str:
    return rng.choice(GOOD_NAMES[cfg.type])


def tell(setting: SettingCfg, animal: AnimalCfg, instrument: InstrumentCfg,
         treasure: TreasureCfg, helper: HelperCfg, name: str) -> World:
    world = World(setting)
    world.facts["setting"] = setting
    world.facts["animal_cfg"] = animal
    world.facts["instrument_cfg"] = instrument
    world.facts["treasure_cfg"] = treasure
    world.facts["helper_cfg"] = helper

    hero = world.add(Entity(
        id="hero", kind="character", type=animal.type, label=name,
        role="hero", attrs={"trait": animal.trait}, tags={animal.id},
    ))
    guide = world.add(Entity(
        id="guide", kind="character", type=helper.tag, label=helper.label,
        role="guide", tags={helper.tag},
    ))
    cup = world.add(Entity(
        id="cup", kind="thing", type="cup", label=treasure.label,
        phrase=treasure.phrase, owner="hero", caretaker="guide",
        tags=set(treasure.tags),
    ))
    trumpet = world.add(Entity(
        id="trumpet", kind="thing", type="instrument", label=instrument.label,
        phrase=instrument.phrase, owner="hero", tags=set(instrument.tags),
    ))
    flock = world.add(Entity(
        id="flock", kind="thing", type="birds", label="the flock",
        plural=True, tags={"flock"},
    ))
    table = world.add(Entity(
        id="table", kind="thing", type="table", label="the stone table",
        tags={"stone", "solid"},
    ))

    world.say(
        f"Once in {setting.place}, a {animal.label} named {name} found {instrument.phrase} beside {setting.scene}."
    )
    world.say(
        f"{name} loved the {instrument.sound_word} of {instrument.label}, because {instrument.sound} made the day feel grand."
    )
    world.say(
        f"Nearby stood {treasure.phrase}, {treasure.solidity} and calm on {table.label}."
    )

    world.para()
    hero.meters["pride"] += 1
    world.say(
        f"{name} puffed up with pride and tried to show the others a louder tune."
    )
    world.say(
        f'But {helper.advice}, said {helper.label}.'
    )
    hero.meters["noise"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{name} listened, lowered the {instrument.label}, and chose {helper.safe_alternative} instead."
    )
    if world.get("flock").memes["fear"] >= THRESHOLD:
        world.say(
            f"The flock settled again, and the {treasure.label} stayed solid and safe on the stone table."
        )
    else:
        world.say(
            f"The morning stayed gentle, and nothing in {setting.place} was harmed."
        )

    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["cup"] = cup
    world.facts["flock"] = flock
    world.facts["table"] = table
    world.facts["name"] = name
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["animal_cfg"]
    i = f["instrument_cfg"]
    t = f["treasure_cfg"]
    h = f["helper_cfg"]
    s = f["setting"]
    return [
        f'Write a short fable for a child about a {a.label} who finds {i.phrase} near {s.place}. Include the words "solid", "{i.id}", and "{t.material}".',
        f'Tell a cautionary story where a proud {a.label} makes a sound effect with a {i.label}, and a helper warns them before the noise frightens the flock.',
        f'Write a gentle fable ending where the hero chooses {h.safe_alternative} and leaves the {t.label} solid and safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["animal_cfg"]
    i = f["instrument_cfg"]
    t = f["treasure_cfg"]
    h = f["helper_cfg"]
    name = f["name"]
    qas = [
        QAItem(
            question=f"What did {name} find in {world.setting.place}?",
            answer=f"{name} found {i.phrase}. The {i.label} made a bright sound, so it was tempting to show off with it.",
        ),
        QAItem(
            question=f"Why did {name} need to be careful with the {i.label}?",
            answer=f"The trumpet could make a very loud sound effect. Loud sounds can startle a flock, so the helper warned {name} to choose a gentler way.",
        ),
        QAItem(
            question=f"What was {t.phrase} like in the story?",
            answer=f"It was solid and stayed steady on the stone table. Because it was solid, it could be jostled without breaking, which made the warning feel real.",
        ),
        QAItem(
            question=f"How did the helper keep the story safe?",
            answer=f"{h.label} told {name} to use {h.safe_alternative} instead of making another blast on the {i.label}. That choice calmed the flock and kept the treasure safe.",
        ),
    ]
    if world.get("flock").memes["fear"] >= THRESHOLD:
        qas.append(QAItem(
            question=f"What happened after the trumpet was played too loudly?",
            answer=f"The flock lifted in alarm, because the sound was startling. That showed why a shiny trumpet can cause trouble when pride makes someone play it too hard.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    t = f["treasure_cfg"]
    i = f["instrument_cfg"]
    return [
        QAItem(
            question="What does solid mean?",
            answer="Solid means something stays firm and keeps its shape. A solid thing does not splash, melt, or wobble like a puddle.",
        ),
        QAItem(
            question="What is a trumpet?",
            answer="A trumpet is a brass instrument that makes a bright, strong sound when you blow into it. People can use it for music or for a loud call.",
        ),
        QAItem(
            question=f"What is copper?",
            answer=f"Copper is a reddish metal. It can be shaped into cups, bells, or instruments, and it often shines warmly.",
        ),
        QAItem(
            question=f"Why can a loud sound effect be a warning?",
            answer="A loud sound can startle animals and people. That is why fables often teach children to be gentle with noisy things.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "orchard": SettingCfg(id="orchard", place="the orchard", scene="a low apple wall", afford={"sound"}),
    "courtyard": SettingCfg(id="courtyard", place="the courtyard", scene="a copper fountain", afford={"sound"}),
    "barn": SettingCfg(id="barn", place="the barn loft", scene="a haystack and a beam", afford={"sound"}),
}

ANIMALS = {
    "fox": AnimalCfg(id="fox", type="fox", label="fox", voice="bright", trait="proud", lesson_voice="wise"),
    "crow": AnimalCfg(id="crow", type="crow", label="crow", voice="sharp", trait="vain", lesson_voice="careful"),
    "goat": AnimalCfg(id="goat", type="goat", label="goat", voice="bold", trait="showy", lesson_voice="humble"),
}

INSTRUMENTS = {
    "trumpet": InstrumentCfg(
        id="trumpet", label="trumpet", phrase="a brass trumpet",
        sound="toot-toot", sound_word="toot", loudness="loud", can_startle=True,
        tags={"trumpet", "sound", "brass"},
    ),
    "bugle": InstrumentCfg(
        id="bugle", label="bugle", phrase="a bright bugle",
        sound="brraaa", sound_word="call", loudness="loud", can_startle=True,
        tags={"bugle", "sound", "brass"},
    ),
}

TREASURES = {
    "cup": TreasureCfg(
        id="cup", label="copper cup", phrase="a copper cup",
        material="copper", solidity="solid", risk="could rattle and spill",
        tags={"copper", "cup", "solid"},
    ),
    "bell": TreasureCfg(
        id="bell", label="copper bell", phrase="a copper bell",
        material="copper", solidity="solid", risk="could ring and wake the hens",
        tags={"copper", "bell", "solid"},
    ),
}

HELPERS = {
    "goat": HelperCfg(
        id="goat", label="the old goat", advice="Keep your toot soft",
        safe_alternative="a quiet hum", tag="goat", tags={"helper"},
    ),
    "owl": HelperCfg(
        id="owl", label="the owl", advice="A soft call is wiser than a blast",
        safe_alternative="a small whistle", tag="owl", tags={"helper"},
    ),
}

GOOD_NAMES = {
    "fox": ["Fenn", "Rufus", "Milo", "Toby", "Pip"],
    "crow": ["Cora", "Mina", "Lark", "Nell", "Suri"],
    "goat": ["Gus", "Bram", "Otis", "Nico", "Rue"],
}

CURATED = [
    StoryParams(animal="fox", instrument="trumpet", treasure="cup", helper="goat", place="orchard"),
    StoryParams(animal="crow", instrument="trumpet", treasure="bell", helper="owl", place="courtyard"),
    StoryParams(animal="goat", instrument="bugle", treasure="cup", helper="owl", place="barn"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this fable needs a trumpet-like sound and a solid copper treasure.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("trait", a.trait))
    for iid, i in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if i.can_startle:
            lines.append(asp.fact("startling", iid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("solidity", tid, t.solidity))
        if t.material:
            lines.append(asp.fact("material", tid, t.material))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,I,T) :- animal(A), instrument(I), treasure(T), startling(I), solidity(T, solid).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary fable about trumpet sounds and a copper thing.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=SETTINGS)
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
    combos = [c for c in valid_combos()
              if (args.animal is None or c[0] == args.animal)
              and (args.instrument is None or c[1] == args.instrument)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    animal, instrument, treasure = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    place = args.place or rng.choice(sorted(SETTINGS))
    return StoryParams(animal=animal, instrument=instrument, treasure=treasure, helper=helper, place=place)


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS or params.instrument not in INSTRUMENTS or params.treasure not in TREASURES or params.helper not in HELPERS or params.place not in SETTINGS:
        raise StoryError("Invalid story parameters.")
    animal = ANIMALS[params.animal]
    instrument = INSTRUMENTS[params.instrument]
    treasure = TREASURES[params.treasure]
    helper = HELPERS[params.helper]
    reason_check(instrument, treasure)
    setting = SETTINGS[params.place]
    rng = random.Random(params.seed or 0)
    name = pick_name(rng, animal)
    world = tell(setting, animal, instrument, treasure, helper, name)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in ANIMALS:
        for i in INSTRUMENTS:
            for t in TREASURES:
                if INSTRUMENTS[i].can_startle and TREASURES[t].solidity == "solid":
                    combos.append((a, i, t))
    return combos


def asp_verify() -> int:
    import asp
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p != c:
        print("MISMATCH in ASP parity")
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        emit(sample)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
