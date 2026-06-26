#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gore_humor_kindness_superhero_story.py
=========================================================================================

A standalone storyworld for a small superhero domain with humor, kindness, and
comic-book gore.

Premise:
- A young superhero wants to stop a prankish villain.
- The prank goes too far and makes a dramatic, red, splattery mess.
- The hero tries to fight, but kindness and a funny trick solve the problem
  better than anger.
- The ending image proves the mess was cleaned and nobody was left hurt.

The world is intentionally tiny and state-driven:
- physical meters track mess, damage, cleanedness, and rescue progress
- emotional memes track courage, worry, humor, kindness, and conflict

The prose is authored from the simulation rather than a frozen template.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def s(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amt: float) -> None:
        self.meters[key] = self.m(key) + amt

    def add_meme(self, key: str, amt: float) -> None:
        self.memes[key] = self.s(key) + amt

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    verb: str
    style: str
    tag: str
    mess: str
    cleanup: str
    heals: bool = False


@dataclass
class Trouble:
    id: str
    label: str
    verb: str
    mess: str
    zone: str
    damage_kind: str
    joke: str


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    guards: set[str]
    fixes: set[str]
    joke: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "rooftop": Setting("the rooftop", "windy", {"blast", "gore", "rescue"}),
    "city": Setting("the city square", "bright", {"blast", "gore", "rescue"}),
    "lab": Setting("the rooftop lab", "glossy", {"blast", "gore", "rescue"}),
}

POWERS = {
    "foam": Power(
        id="foam",
        label="foam hands",
        verb="spray foam over the mess",
        style="spray",
        tag="humor",
        mess="foam",
        cleanup="the foam covered the splatter",
        heals=False,
    ),
    "bandage_ray": Power(
        id="bandage_ray",
        label="bandage ray",
        verb="seal the wound with a glowing bandage",
        style="beam",
        tag="kindness",
        mess="clean",
        cleanup="the glowing bandage made everything neat",
        heals=True,
    ),
    "giggle_smoke": Power(
        id="giggle_smoke",
        label="giggle smoke",
        verb="fill the air with tickly giggles",
        style="cloud",
        tag="humor",
        mess="sparkle",
        cleanup="the giggles softened the whole scene",
        heals=False,
    ),
    "sun_patch": Power(
        id="sun_patch",
        label="sun patch",
        verb="warm the hero and calm the crowd",
        style="shine",
        tag="kindness",
        mess="glow",
        cleanup="the warm light made the red splash look less scary",
        heals=False,
    ),
}

TROUBLES = {
    "tomato_blaster": Trouble(
        id="tomato_blaster",
        label="tomato blaster",
        verb="fire a red tomato blast",
        mess="gore",
        zone="face",
        damage_kind="stain",
        joke="It looked like a huge comic-book ketchup sneeze.",
    ),
    "paint_sneeze": Trouble(
        id="paint_sneeze",
        label="paint sneeze cannon",
        verb="sneeze out red paint",
        mess="gore",
        zone="cape",
        damage_kind="stain",
        joke="The whole wall got spotted like a clown’s apron.",
    ),
    "berry_bomb": Trouble(
        id="berry_bomb",
        label="berry bomb",
        verb="pop a berry bomb",
        mess="gore",
        zone="ground",
        damage_kind="spill",
        joke="It splatted in a way that was more silly than scary.",
    ),
}

TOOLS = {
    "mop": Tool(
        id="mop",
        label="mop and bucket",
        verb="mop the floor clean",
        guards={"gore", "foam"},
        fixes={"spill", "stain"},
        joke="The mop looked like a tired sidekick.",
    ),
    "cape_cloth": Tool(
        id="cape_cloth",
        label="a soft cape cloth",
        verb="wipe the cape gently",
        guards={"gore"},
        fixes={"stain"},
        joke="It fluttered like a tiny flag of help.",
    ),
    "soup": Tool(
        id="soup",
        label="warm soup",
        verb="offer warm soup and a seat",
        guards={"gloom"},
        fixes=set(),
        joke="No one can stay grumpy while holding soup for long.",
    ),
}

HERO_NAMES = ["Nova", "Sky", "Mira", "Max", "Jules", "Rae", "Ivy", "Pax"]
VILLAIN_NAMES = ["Dr. Splash", "Captain Chuckle", "The Crimson Prank", "Mister Splat"]
SIDEKICK_NAMES = ["Bean", "Dot", "Zig", "Pip", "Nim"]


@dataclass
class StoryParams:
    place: str
    power: str
    trouble: str
    hero: str
    sidekick: str
    villain: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with humor, kindness, and comic gore.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    place = args.place or rng.choice(list(SETTINGS))
    power = args.power or rng.choice(list(POWERS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    if power == "bandage_ray" and trouble == "berry_bomb":
        pass
    hero = args.hero or rng.choice(HERO_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICK_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    if place not in SETTINGS:
        raise StoryError("Unknown place.")
    return StoryParams(place=place, power=power, trouble=trouble, hero=hero, sidekick=sidekick, villain=villain)


def _reasonableness_gate(params: StoryParams) -> None:
    trouble = TROUBLES[params.trouble]
    power = POWERS[params.power]
    if trouble.mess != "gore":
        raise StoryError("This world is built for the comic-book gore premise.")
    if power.tag not in {"humor", "kindness"}:
        raise StoryError("The story needs either humor or kindness to resolve the problem.")
    if trouble.zone not in {"face", "cape", "ground"}:
        raise StoryError("Unreasonable trouble zone.")
    if power.id == "bandage_ray" and not power.heals:
        raise StoryError("Internal power mismatch.")


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.hero, kind="character", type="hero", label=params.hero,
        traits=["brave", "kind"], meters={"health": 3.0}, memes={"courage": 2.0, "humor": 1.0, "kindness": 2.0}
    ))
    sidekick = world.add(Entity(
        id=params.sidekick, kind="character", type="sidekick", label=params.sidekick,
        traits=["funny", "loyal"], meters={"health": 2.0}, memes={"humor": 2.0, "kindness": 1.0}
    ))
    villain = world.add(Entity(
        id=params.villain, kind="character", type="villain", label=params.villain,
        traits=["prankish"], meters={"health": 2.0}, memes={"mischief": 2.0}
    ))
    world.add(Entity(
        id="civilians", kind="group", type="crowd", label="the crowd",
        plural=True, meters={"fear": 1.0}, memes={"worry": 1.0}
    ))
    world.facts.update(hero=hero, sidekick=sidekick, villain=villain, power=POWERS[params.power], trouble=TROUBLES[params.trouble], place=params.place)
    return world


def _narrate_setup(world: World, params: StoryParams) -> None:
    h = world.get(params.hero)
    s = world.get(params.sidekick)
    v = world.get(params.villain)
    t = TROUBLES[params.trouble]
    p = POWERS[params.power]
    world.say(f"{h.id} was a small superhero who loved helping people and telling jokes.")
    world.say(f"{s.id} stayed close, because every hero works better with a sidekick who can laugh at danger.")
    world.say(f"One bright day in {world.setting.place}, {v.id} rolled out {t.label} and shouted, \"Time for a giant {t.mess} mess!\"")
    world.say(f"{h.id} lifted {p.label} and tried to stay calm, even though the air already looked messy.")
    world.say(f"{t.joke}")


def _apply_trouble(world: World, params: StoryParams) -> None:
    h = world.get(params.hero)
    v = world.get(params.villain)
    t = TROUBLES[params.trouble]
    h.add_meter("mess", 1.0)
    h.add_meter("damage", 1.0)
    h.add_meme("worry", 1.0)
    v.add_meme("mischief", 1.0)
    if t.zone == "face":
        world.say(f"{t.label.capitalize()} splashed across {h.id}'s mask like a red slapstick pie.")
    elif t.zone == "cape":
        world.say(f"The splash landed on {h.id}'s cape and made the bright fabric look dramatic and wild.")
    else:
        world.say(f"The ground turned red and slippery, so every step looked like a comic-book tiptoe.")
    world.say(f"{h.id} gasped, then remembered that panicking never cleaned a single thing.")


def _kind_turn(world: World, params: StoryParams) -> None:
    h = world.get(params.hero)
    s = world.get(params.sidekick)
    v = world.get(params.villain)
    power = POWERS[params.power]
    t = TROUBLES[params.trouble]
    if power.tag == "humor":
        h.add_meme("humor", 2.0)
        s.add_meme("humor", 1.0)
        world.say(f"{s.id} pointed at the mess and said, \"Well, that is the biggest tomato moustache I have ever seen.\"")
        world.say(f"{h.id} blinked, snorted, and almost laughed.")
        world.say(f"Then {h.id} used {power.label} to {power.verb}.")
    else:
        h.add_meme("kindness", 2.0)
        s.add_meme("kindness", 1.0)
        world.say(f"{h.id} saw that {v.id} looked embarrassed, not brave.")
        world.say(f"Instead of shouting, {h.id} used {power.label} to {power.verb}.")
        world.say(f"{v.id} looked up, surprised that the hero was helping before scolding.")
    h.add_meter("cleaned", 1.0)
    if power.heals:
        h.add_meter("damage", -1.0)
        h.add_meter("health", 1.0)
        world.say(f"The glowing bandage covered the ugly splatter and made the hurt feel much smaller.")
    else:
        world.say(f"{power.cleanup.capitalize()}, and the red mess stopped spreading.")
    if t.zone == "face":
        world.say(f"{h.id} wiped the mask clean so the crowd could see a grin again.")
    elif t.zone == "cape":
        world.say(f"{h.id}'s cape fluttered free once the stain was lifted.")
    else:
        world.say(f"The sidewalk shone again, and nobody had to hop around the puddle of red goop.")


def _resolution(world: World, params: StoryParams) -> None:
    h = world.get(params.hero)
    s = world.get(params.sidekick)
    v = world.get(params.villain)
    h.add_meme("kindness", 1.0)
    s.add_meme("kindness", 1.0)
    v.add_meme("worry", -1.0)
    v.add_meme("relief", 1.0)
    world.say(f"{h.id} offered {v.id} a hand, not a lecture.")
    world.say(f"{s.id} handed over {TOOLS['mop'].label} so the floor could get clean too.")
    world.say(f"{v.id} sighed, picked up the {t := TOOLS['mop'].label}, and muttered, \"I guess I made a ridiculous mess.\"")
    world.say(f"{h.id} smiled and said, \"Ridiculous messes are easier to fix when we do it together.\"")
    world.say(f"By the end, the red spots were gone, the crowd was laughing, and {v.id} was helping instead of hiding.")


def tell(params: StoryParams) -> World:
    _reasonableness_gate(params)
    world = _setup_world(params)
    _narrate_setup(world, params)
    world.para()
    _apply_trouble(world, params)
    world.para()
    _kind_turn(world, params)
    world.para()
    _resolution(world, params)
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    h = f["hero"].id
    v = f["villain"].id
    t = f["trouble"].label
    p = f["power"].label
    return [
        "Write a short superhero story for a young child that includes a ridiculous red mess and a kind ending.",
        f"Tell a comic story where {h} faces {v}'s {t} and uses {p} instead of getting angry.",
        "Write a brave but funny rescue story where helping is better than fighting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["hero"].id
    s = f["sidekick"].id
    v = f["villain"].id
    p = f["power"].label
    t = f["trouble"].label
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {h}, and {s} helped as the sidekick.",
        ),
        QAItem(
            question=f"What did {v} cause at {place}?",
            answer=f"{v} caused a big comic-book gore mess with the {t}, which splattered red goop everywhere.",
        ),
        QAItem(
            question=f"How did {h} fix the problem?",
            answer=f"{h} used {p} and then chose kindness, which cleaned the mess and calmed everyone down.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The scary-looking mess was gone, the crowd was laughing, and the villain was helping clean up instead of causing trouble.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero usually for?",
            answer="A superhero is usually someone who protects others, solves trouble, and helps people stay safe.",
        ),
        QAItem(
            question="Why can jokes help in a hard moment?",
            answer="Jokes can help because they lower fear, make people breathe easier, and help everyone think more clearly.",
        ),
        QAItem(
            question="Why is kindness important when someone makes a mistake?",
            answer="Kindness matters because it helps fix the mistake without making the person feel hopeless or scared.",
        ),
        QAItem(
            question="What is a mess?",
            answer="A mess is something spilled, broken, or left out of order that needs cleaning or fixing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("power_tag", pid, p.tag))
        lines.append(asp.fact("cleanup", pid, p.cleanup))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        lines.append(asp.fact("zone", tid, t.zone))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Power, Trouble) :- setting(Place), power(Power), trouble(Trouble),
    affords(Place, blast), mess_of(Trouble, gore), power_tag(Power, Tag),
    Tag = humor; Tag = kindness.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for power in POWERS:
            for trouble in TROUBLES:
                if POWERS[power].tag in {"humor", "kindness"} and TROUBLES[trouble].mess == "gore":
                    combos.append((place, power, trouble))
    return combos


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="city", power="foam", trouble="tomato_blaster", hero="Nova", sidekick="Bean", villain="Dr. Splash"),
    StoryParams(place="rooftop", power="bandage_ray", trouble="paint_sneeze", hero="Sky", sidekick="Dot", villain="Captain Chuckle"),
    StoryParams(place="lab", power="giggle_smoke", trouble="berry_bomb", hero="Mira", sidekick="Pip", villain="The Crimson Prank"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid combos:")
        for item in vals:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} vs {p.villain} at {p.place} ({p.power} / {p.trouble})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
