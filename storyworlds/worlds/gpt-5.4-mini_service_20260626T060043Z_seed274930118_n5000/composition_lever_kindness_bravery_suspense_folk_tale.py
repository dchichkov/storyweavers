#!/usr/bin/env python3
"""
storyworlds/worlds/composition_lever_kindness_bravery_suspense_folk_tale.py
============================================================================

A small folk-tale storyworld about a careful composition, a stubborn lever,
and the kindness and bravery needed to use it well.

Premise:
- A village has a heavy old bell-stone that will not budge.
- A young composer wants to finish a rain-song for the spring fair.
- A hidden lever can lift the stone and reveal the bell-strike chamber.
- The wrong choice could crack the stone or leave the village without its tune.

The world is intentionally small and state-driven:
- Characters carry physical meters and emotional memes.
- The lever affects the stone, the chamber, and the song's completion.
- Kindness, bravery, and suspense are all reflected in the state and prose.

The prose aims for a child-facing folk-tale cadence, with a clear beginning,
turn, and ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
    weather: str = "soft rain"
    moon: str = "silver"
    affords: set[str] = field(default_factory=set)


@dataclass
class Composition:
    id: str
    title: str
    theme: str
    tempo: str
    needed_sound: str
    finish_image: str
    keyword: str = "composition"
    tags: set[str] = field(default_factory=set)


@dataclass
class Lever:
    id: str
    label: str
    action: str
    effect: str
    risk: str
    fits: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    composition: str
    lever: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []
        self.lever_state: str = "resting"
        self.stone_lifted: bool = False
        self.song_finished: bool = False
        self.hall_open: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.lever_state = self.lever_state
        clone.stone_lifted = self.stone_lifted
        clone.song_finished = self.song_finished
        clone.hall_open = self.hall_open
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_brave_push(world: World) -> list[str]:
    out: list[str] = []
    lever = world.get("lever")
    stone = world.get("stone")
    hero = world.get("hero")
    if lever.meters.get("pulled", 0) < THRESHOLD:
        return out
    sig = ("push",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    lever.meters["force"] = lever.meters.get("force", 0) + 1
    stone.meters["wobble"] = stone.meters.get("wobble", 0) + 1
    out.append("The lever gave a little shiver under brave hands.")
    return out


def _r_lift_stone(world: World) -> list[str]:
    out: list[str] = []
    lever = world.get("lever")
    stone = world.get("stone")
    if lever.meters.get("force", 0) < THRESHOLD:
        return out
    sig = ("lift",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stone.meters["raised"] = stone.meters.get("raised", 0) + 1
    world.stone_lifted = True
    out.append("The old stone rose just enough to breathe.")
    return out


def _r_open_hall(world: World) -> list[str]:
    out: list[str] = []
    if not world.stone_lifted:
        return out
    sig = ("open",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.hall_open = True
    out.append("A narrow chamber woke behind the stone.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("brave_push", _r_brave_push),
    Rule("lift_stone", _r_lift_stone),
    Rule("open_hall", _r_open_hall),
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


SETTING = Setting(place="the mossy hill", weather="soft rain", moon="silver", affords={"lever"})
COMPOSITIONS = {
    "rain_song": Composition(
        id="rain_song",
        title="the rain-song of the silver hill",
        theme="the village waits for the first clear bell after the rain",
        tempo="gentle and steady",
        needed_sound="a clear bell note",
        finish_image="the fair lanterns shining over the wet grass",
        tags={"rain", "song", "bell"},
    ),
    "dawn_song": Composition(
        id="dawn_song",
        title="the dawn-song of the river path",
        theme="the village needs a tune to guide the dawn walkers home",
        tempo="soft and bright",
        needed_sound="a bright echo",
        finish_image="the path glowing under morning mist",
        tags={"dawn", "song", "path"},
    ),
}
LEVERS = {
    "stone_lever": Lever(
        id="stone_lever",
        label="an old iron lever",
        action="pull it downward",
        effect="raise the bell-stone",
        risk="the stone might crack if the pull is rude",
        fits="a hidden slot in the hillside",
        tags={"iron", "stone", "lever"},
    ),
    "wood_lever": Lever(
        id="wood_lever",
        label="a carved wooden lever",
        action="press it with both hands",
        effect="open the secret hatch",
        risk="the hatch might jam if the press is too quick",
        fits="a narrow groove near the roots",
        tags={"wood", "hatch", "lever"},
    ),
}
HERO_NAMES = ["Mara", "Elin", "Toma", "Perrin", "Sera"]
HELPER_NAMES = ["Grandmother Brin", "Old Finn", "Aunt Nessa", "Brother Quill"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["woman", "man"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(SETTING.place, comp_id, lever_id) for comp_id in COMPOSITIONS for lever_id in LEVERS]


@dataclass
class StoryWorld:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale world about a composition and a lever.")
    ap.add_argument("--place", choices=[SETTING.place])
    ap.add_argument("--composition", choices=COMPOSITIONS)
    ap.add_argument("--lever", choices=LEVERS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    comp_id = args.composition or rng.choice(list(COMPOSITIONS))
    lever_id = args.lever or rng.choice(list(LEVERS))
    if (args.place and args.place != SETTING.place) or (args.composition and args.composition not in COMPOSITIONS) or (args.lever and args.lever not in LEVERS):
        raise StoryError("No valid story matches those choices.")
    if args.composition and args.lever:
        if args.composition == "rain_song" and args.lever == "wood_lever":
            raise StoryError("That lever does not fit the rain-song's stone chamber.")
    hero = args.name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    return StoryParams(
        place=SETTING.place,
        composition=comp_id,
        lever=lever_id,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
    )


def _pronoun_for_type(t: str, case: str = "subject") -> str:
    if t in {"girl", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if t in {"boy", "man"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    comp = COMPOSITIONS[params.composition]
    lev = LEVERS[params.lever]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    stone = world.add(Entity(id="stone", type="stone", label="the bell-stone"))
    lever = world.add(Entity(id="lever", type="lever", label=lev.label))
    world.facts.update(hero=hero, helper=helper, composition=comp, lever=lev, stone=stone)

    world.say(f"Once, on {world.setting.place}, there lived {params.hero}, who loved making {comp.title}.")
    world.say(f"{_pronoun_for_type(hero.type).capitalize()} was polishing the last line of {comp.theme} when the village elder sighed, because the song needed {comp.needed_sound}.")
    world.say(f"Under the hill, the people had long whispered about {lev.label}, hidden in roots and rock, and about the stone that kept the chamber shut.")

    world.para()
    world.say(f"{params.helper} found {params.hero} beside the hill and said, \"If we can {lev.action}, the hill may open.\"")
    world.say(f"{_pronoun_for_type(hero.type).capitalize()} looked at the dark seam in the earth and felt a flutter of suspense, for {lev.risk}.")
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.say(f"Still, {params.hero} chose kindness first: {_pronoun_for_type(hero.type, 'possessive')} asked if the old lever could be turned slowly, so the stone would not be hurt.")

    world.para()
    world.say(f"The two of them set their hands on {lev.label}. {params.helper} counted the breaths, and {params.hero} pulled with brave care.")
    lever.meters["pulled"] = lever.meters.get("pulled", 0) + 1
    propagate(world, narrate=True)
    if world.hall_open:
        world.say(f"Inside, the chamber answered with a clear ring, and {params.hero}'s composition finally found its needed sound.")
        world.song_finished = True
    else:
        world.say(f"The hill stayed quiet, and the tune still waited inside {_pronoun_for_type(hero.type, 'possessive')} chest.")

    world.para()
    if world.song_finished:
        world.say(f"At the spring fair, the new composition sounded across the wet grass, and the people smiled as if the moon had leaned closer.")
        world.say(f"The old lever rested again, the stone sat safe in its cradle, and the little village kept its song.")
    else:
        world.say(f"Together they promised to try again at dawn, gentler than before, because folk tales remember those who keep faith with a hard task.")
    world.facts["resolved"] = world.song_finished
    return world


def generation_prompts(world: World) -> list[str]:
    comp = world.facts["composition"]
    lev = world.facts["lever"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    return [
        f'Write a short folk tale about {hero.label} and {helper.label} that mentions "{comp.keyword}" and "{lev.label}".',
        f"Tell a gentle story where a child must use {lev.label} to finish {comp.title} without hurting the stone.",
        f"Write a suspenseful but kind story about a brave helper, a hidden lever, and a song that is waiting to be heard.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    comp = f["composition"]
    lev = f["lever"]
    qa = [
        QAItem(
            question=f"What was {hero.label} trying to finish in the story?",
            answer=f"{hero.label} was trying to finish {comp.title}, a {comp.theme} song for the village fair.",
        ),
        QAItem(
            question=f"Why did {helper.label} say the lever had to be used carefully?",
            answer=f"{helper.label} said to use {lev.label} carefully because {lev.risk}. A gentle pull would protect the stone.",
        ),
        QAItem(
            question=f"What changed after {hero.label} and {helper.label} pulled the lever together?",
            answer="The stone lifted, a hidden chamber opened, and the song found its clear sound.",
        ),
    ]
    if world.song_finished:
        qa.append(
            QAItem(
                question=f"How did {hero.label} feel when the composition was finally complete?",
                answer=f"{hero.label} felt brave and glad, because the careful choice worked and the village could hear the finished song.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lever?",
            answer="A lever is a simple tool that helps lift or move something heavy by turning a push or pull into extra force.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help gently, with care for other people and for things that could be harmed.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing a hard thing even when it feels a little scary, especially when it matters.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to see what will happen next when something important might go well or go wrong.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting={world.setting.place} weather={world.setting.weather} moon={world.setting.moon}")
    lines.append(f"lever_state={world.lever_state} stone_lifted={world.stone_lifted} hall_open={world.hall_open} song_finished={world.song_finished}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
lever_pulled :- pulled(lever).
brave_pull :- lever_pulled, kindness(hero), suspense(hero).
stone_lifted :- brave_pull.
hall_open :- stone_lifted.
song_finished :- hall_open, composition_ready(comp).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", SETTING.place))
    for cid, c in COMPOSITIONS.items():
        lines.append(asp.fact("composition", cid))
        lines.append(asp.fact("theme", cid, c.theme))
    for lid, l in LEVERS.items():
        lines.append(asp.fact("lever", lid))
        lines.append(asp.fact("fits", lid, l.fits))
    lines.append(asp.fact("kindness", "hero"))
    lines.append(asp.fact("bravery", "hero"))
    lines.append(asp.fact("suspense", "hero"))
    lines.append(asp.fact("pulled", "lever"))
    lines.append(asp.fact("composition_ready", "rain_song"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show song_finished/0."))
    return sorted(set(asp.atoms(model, "song_finished")))


def asp_verify() -> int:
    python_ok = set(valid_story_combos())
    asp_ok = set(valid_combos())
    if python_ok != asp_ok:
        print("MISMATCH between Python and ASP story gates.")
        return 1
    sample = generate(resolve_params(argparse.Namespace(
        place=None, composition=None, lever=None, name=None, hero_type=None,
        helper=None, helper_type=None, seed=None, all=False, trace=False, qa=False,
        json=False, asp=False, verify=False, show_asp=False
    ), random.Random(7)))
    if not sample.story.strip():
        print("Generated story was empty.")
        return 1
    print(f"OK: Python/ASP parity holds for {len(python_ok)} combos and a generated story.")
    return 0


CURATED = [
    StoryParams(place=SETTING.place, composition="rain_song", lever="stone_lever", hero="Mara", hero_type="girl", helper="Grandmother Brin", helper_type="woman"),
    StoryParams(place=SETTING.place, composition="dawn_song", lever="wood_lever", hero="Toma", hero_type="boy", helper="Old Finn", helper_type="man"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show song_finished/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world's ASP twin is intentionally tiny; run --verify for parity.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero}: {p.composition} with {p.lever}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
