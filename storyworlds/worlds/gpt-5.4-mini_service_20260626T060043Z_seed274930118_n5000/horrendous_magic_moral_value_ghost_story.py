#!/usr/bin/env python3
"""
storyworlds/worlds/horrendous_magic_moral_value_ghost_story.py
==============================================================

A small ghost-story world with a magical haunting and a clear moral choice.

Premise:
- A child wanders into a quiet old room at night.
- A ghost is upset because a magic keepsake was borrowed and not returned.
- The situation turns "horrendous" in a child-friendly way: spooky noises, cold air,
  and a rattling spell that makes the room feel wrong.
- The child must choose between keeping the shiny thing and doing the kind, honest thing.
- The ending proves the moral value changed the world: the ghost calms, the magic settles,
  and the room becomes warm and peaceful.

This script follows the Storyweavers world contract with:
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- eager shared results import
- lazy ASP import inside helper functions only
- a Python reasonableness gate plus an inline ASP_RULES twin
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, --seed, -n
"""

from __future__ import annotations

import argparse
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
    held_by: Optional[str] = None
    is_magic: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    moonlit: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class MagicThing:
    id: str
    label: str
    phrase: str
    effect: str
    scares: str
    value: str
    is_magic: bool = True


@dataclass
class GhostMood:
    id: str
    label: str
    tremble_word: str
    calm_word: str
    moral_value: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_cold(world: World) -> list[str]:
    out = []
    if world.facts.get("haunt_started") and not world.facts.get("ghost_calm"):
        sig = ("cold")
        if sig not in world.fired:
            world.fired.add(sig)
            for e in world.entities.values():
                if e.kind == "character":
                    e.memes["unease"] = e.memes.get("unease", 0.0) + 1
            out.append("The room felt cold and wrong.")
    return out


def _r_magic_spike(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    charm = world.entities.get("charm")
    child = world.entities.get("child")
    if not ghost or not charm or not child:
        return out
    if ghost.memes.get("upset", 0) >= THRESHOLD and charm.held_by == child.id and not world.facts.get("returned"):
        sig = ("magic_spike")
        if sig not in world.fired:
            world.fired.add(sig)
            charm.meters["glow"] = charm.meters.get("glow", 0.0) + 1
            charm.meters["buzz"] = charm.meters.get("buzz", 0.0) + 1
            out.append("The magic charm buzzed and flashed in a horrendous little whirl.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    ghost = world.entities.get("ghost")
    charm = world.entities.get("charm")
    child = world.entities.get("child")
    if not ghost or not charm or not child:
        return out
    if world.facts.get("returned") and ghost.memes.get("upset", 0) >= THRESHOLD:
        sig = ("calm")
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.memes["upset"] = 0.0
            ghost.memes["warmth"] = ghost.memes.get("warmth", 0.0) + 1
            charm.meters["glow"] = 0.0
            out.append("The ghost's frown softened, and the magic settled like a blanket.")
    return out


CAUSAL_RULES = [Rule("cold", _r_cold), Rule("magic_spike", _r_magic_spike), Rule("calm", _r_calm)]


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


def tell(setting: Setting, magic: MagicThing, mood: GhostMood,
         child_name: str, child_type: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, traits=["curious", "kind"]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="a little ghost", traits=["lonely", "careful"]))
    charm = world.add(Entity(
        id="charm", kind="thing", type="charm", label=magic.label, phrase=magic.phrase,
        owner="ghost", held_by="child", is_magic=True
    ))
    ghost.memes["upset"] = 1.0
    ghost.memes["moral_value"] = 0.0
    world.facts.update(child=child, ghost=ghost, charm=charm, magic=magic, mood=mood)

    world.say(f"{child_name} was a curious child who liked quiet rooms and little mysteries.")
    world.say(f"One moonlit night, {child_name} found {magic.phrase} in {setting.place}.")
    world.say(f"Near the window drifted {ghost.label}, who looked worried and very sad.")
    world.say(f'"Please do not keep it," said the ghost. "It is my {magic.label}, and I need it back."')

    world.para()
    world.facts["haunt_started"] = True
    world.say(f"{child_name} heard a horrendous rattling sound as the {magic.label} began to glow.")
    propagate(world, narrate=True)
    world.say(f"The glow made shadows dance on the wall, but {child_name} noticed the ghost was not trying to frighten anyone.")

    world.para()
    world.say(f"{child_name} looked at the shining {magic.label} and then at the ghost's worried face.")
    world.say(f'Being honest felt small and brave at the same time. "{child_name} gave it back," {child_name} said.')

    world.facts["returned"] = True
    propagate(world, narrate=True)
    world.say(f"The ghost smiled, the room warmed, and the magic gave off a soft blue light instead of a horrendous flash.")
    world.say(f"{child_name} left {setting.place} feeling proud, because doing the kind thing had made the spooky room peaceful.")

    return world


SETTINGS = {
    "old_attic": Setting(place="the old attic", moonlit=True, affords={"find_charm"}),
    "quiet_hall": Setting(place="the quiet hall", moonlit=True, affords={"find_charm"}),
    "moon_garden": Setting(place="the moon garden", moonlit=True, affords={"find_charm"}),
}

MAGIC_THINGS = {
    "lantern": MagicThing(
        id="lantern",
        label="moon lantern",
        phrase="a moon lantern with silver stars",
        effect="glow",
        scares="horrendous rattling",
        value="kindness",
    ),
    "bell": MagicThing(
        id="bell",
        label="ghost bell",
        phrase="a ghost bell tied with a blue ribbon",
        effect="ring",
        scares="horrendous chime",
        value="honesty",
    ),
    "pebble": MagicThing(
        id="pebble",
        label="spell pebble",
        phrase="a spell pebble that shimmered like rain",
        effect="sparkle",
        scares="horrendous whisper",
        value="sharing",
    ),
}

GHOST_MOODS = {
    "lonely": GhostMood(id="lonely", label="lonely", tremble_word="worried", calm_word="peaceful", moral_value="kindness"),
    "sad": GhostMood(id="sad", label="sad", tremble_word="sad", calm_word="relieved", moral_value="honesty"),
    "restless": GhostMood(id="restless", label="restless", tremble_word="shivery", calm_word="still", moral_value="sharing"),
}

NAMES = ["Mina", "Ivy", "Nora", "Lila", "June", "Eva", "Pip", "Sana"]
TRAITS = ["curious", "gentle", "brave", "patient"]


@dataclass
class StoryParams:
    place: str
    magic: str
    mood: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def reasonableness(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Invalid setting for this ghost story.")
    if params.magic not in MAGIC_THINGS:
        raise StoryError("Unknown magic object.")
    if params.mood not in GHOST_MOODS:
        raise StoryError("Unknown ghost mood.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Invalid child gender.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    magic = f["magic"]
    mood = f["mood"]
    return [
        f'Write a gentle ghost story for a young child that includes the word "horrendous" and a magic {magic.label}.',
        f"Tell a moonlit story where {child.label} finds {magic.phrase} and helps a {mood.label} ghost with a moral choice.",
        f"Write a spooky-but-kind story about a child who returns a magical keepsake to a ghost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    magic = f["magic"]
    ghost = f["ghost"]
    mood = f["mood"]
    return [
        QAItem(
            question=f"Who found {magic.phrase} in {world.setting.place}?",
            answer=f"{child.label} found {magic.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the ghost look worried at first?",
            answer=f"The ghost looked worried because the {magic.label} belonged to the ghost and had not been returned yet.",
        ),
        QAItem(
            question="What kind choice did the child make at the end?",
            answer=f"{child.label} gave the magical keepsake back, and that honest choice helped the ghost feel calm again.",
        ),
        QAItem(
            question=f"How did the horrendous magic feel before it settled?",
            answer=f"It felt loud and spooky, with a horrendous flash and a rattling sound before it became quiet.",
        ),
        QAItem(
            question=f"What moral value mattered most in this story?",
            answer=f"Honesty and kindness mattered most, because they helped {ghost.label} relax and made the room peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in stories?",
            answer="A ghost is often a spooky spirit character in a story, but in gentle stories it can also be lonely, sad, or kind.",
        ),
        QAItem(
            question="What does a magic object do in a story?",
            answer="A magic object can glow, shimmer, or make strange things happen, which gives the story a little wonder.",
        ),
        QAItem(
            question="What is honesty?",
            answer="Honesty means telling the truth and doing the right thing even when it is hard.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.is_magic:
            bits.append("magic=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.moonlit:
            lines.append(asp.fact("moonlit", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MAGIC_THINGS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("value", mid, m.value))
        lines.append(asp.fact("scares", mid, m.scares))
    for gid, g in GHOST_MOODS.items():
        lines.append(asp.fact("ghost_mood", gid))
        lines.append(asp.fact("moral", gid, g.moral_value))
    return "\n".join(lines)


ASP_RULES = r"""
risk(M, G) :- magic(M), ghost_mood(G), moral(G, V), value(M, V).
honest_story(S, M, G) :- setting(S), risk(M, G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show honest_story/3."))
    asp_set = set(asp.atoms(model, "honest_story"))
    py_set = {
        (sid, mid, gid)
        for sid in SETTINGS
        for mid in MAGIC_THINGS
        for gid in GHOST_MOODS
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    print("clingo only:", sorted(asp_set - py_set))
    print("python only:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show honest_story/3."))
    return sorted(set(asp.atoms(model, "honest_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small magical ghost story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC_THINGS)
    ap.add_argument("--mood", choices=GHOST_MOODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    magic = args.magic or rng.choice(list(MAGIC_THINGS))
    mood = args.mood or rng.choice(list(GHOST_MOODS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, magic=magic, mood=mood, name=name, gender=gender, trait=trait)
    reasonableness(params)
    return params


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    magic = MAGIC_THINGS[params.magic]
    mood = GHOST_MOODS[params.mood]
    world = tell(setting, magic, mood, params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(place="old_attic", magic="lantern", mood="lonely", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="quiet_hall", magic="bell", mood="sad", name="Pip", gender="boy", trait="brave"),
    StoryParams(place="moon_garden", magic="pebble", mood="restless", name="Nora", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show honest_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for place, magic, mood in combos:
            print(f"  {place:12} {magic:8} {mood:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.place} / {p.magic} / {p.mood}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
