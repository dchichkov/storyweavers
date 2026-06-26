#!/usr/bin/env python3
"""
storyworlds/worlds/banner_repetition_suspense_bad_ending_rhyming_story.py
========================================================================

A small standalone story world about a banner, repeated tries, a little
suspense, and a bad ending in a rhyming-story style.

Premise:
- A child and a helper try to hang a banner for a special day.
- The banner keeps slipping, snagging, or getting tugged by the wind.
- The world model tracks height, wind, tension, fray, and emotional worry.
- The story ends with the banner not making it to its happy spot.

This world is intentionally narrow: it favors a few plausible variants over many
weak ones. Invalid choices are rejected with StoryError.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
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
    wind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class BannerCfg:
    id: str
    phrase: str
    label: str = "banner"
    color: str = "bright"
    length: str = "long"
    fragile: bool = True


@dataclass
class ToolCfg:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turns: int = 0

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.turns = self.turns
        return clone


def _hero_name(gender: str) -> list[str]:
    return ["Mia", "Luna", "Nora", "Zoe", "Ivy"] if gender == "girl" else ["Leo", "Finn", "Theo", "Max", "Noah"]


TRAITS = ["brave", "patient", "busy", "cheery", "tiny"]
PLACES = {
    "yard": Setting(place="the yard", wind="a quick wind", affords={"hang"}),
    "hall": Setting(place="the hall", wind="no wind at all", affords={"hang"}),
    "porch": Setting(place="the porch", wind="a sly wind", affords={"hang"}),
}

BANNERS = {
    "party": BannerCfg(id="party", phrase="a bright party banner"),
    "welcome": BannerCfg(id="welcome", phrase="a welcome banner"),
    "festival": BannerCfg(id="festival", phrase="a long festival banner"),
}

TOOLS = [
    ToolCfg(id="tape", label="sticky tape", helps={"hold"}, prep="put on sticky tape", tail="stuck it up with sticky tape"),
    ToolCfg(id="rope", label="a short rope", helps={"lift"}, prep="tie on a short rope", tail="pulled it with a short rope"),
    ToolCfg(id="stool", label="a small stool", helps={"reach"}, prep="bring out a small stool", tail="stood up on the small stool"),
]


@dataclass
class StoryParams:
    place: str
    banner: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def banner_pronoun(hero: Entity, banner: Entity) -> str:
    return banner.it()


def rime(a: str, b: str) -> str:
    return f"{a} {b}"


def setting_line(world: World) -> str:
    if world.setting.wind == "no wind at all":
        return f"The {world.setting.place.removeprefix('the ')} was still and small, a calm little hall."
    return f"The air by {world.setting.place} was brisk and bright, with a wind that danced and darted in sight."


def select_tool(place: str, banner: BannerCfg) -> ToolCfg:
    if place == "hall":
        return TOOLS[2]
    if place == "porch":
        return TOOLS[1]
    return TOOLS[0]


def reasonableness_gate(place: str, banner: BannerCfg) -> bool:
    return place in PLACES and banner.id in BANNERS and "hang" in PLACES[place].affords


def _raise_if_invalid(args: argparse.Namespace) -> None:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.banner and args.banner not in BANNERS:
        raise StoryError("Unknown banner.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")
    if args.place and args.banner:
        if not reasonableness_gate(args.place, BANNERS[args.banner]):
            raise StoryError("That banner story cannot happen in that place.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about a banner, suspense, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--banner", choices=BANNERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["parent", "grandparent", "friend"])
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
    _raise_if_invalid(args)
    place = args.place or rng.choice(list(PLACES))
    banner = args.banner or rng.choice(list(BANNERS))
    if not reasonableness_gate(place, BANNERS[banner]):
        raise StoryError("That choice set does not make a workable banner story.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(_hero_name(gender))
    helper = args.helper or rng.choice(["parent", "grandparent", "friend"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, banner=banner, name=name, gender=gender, helper=helper, trait=trait)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    banner: Entity = f["banner"]
    tool: ToolCfg = f["tool"]
    return [
        QAItem(
            question=f"What were {hero.id} and {helper.label} trying to do?",
            answer=f"They were trying to hang {banner.phrase} so it could shine up high.",
        ),
        QAItem(
            question=f"Why did the banner story feel tense at {world.setting.place}?",
            answer=f"The banner kept slipping in the wind, so every try felt like a little wait and worry.",
        ),
        QAItem(
            question=f"How many tries did they make before the ending?",
            answer=f"They made three tries, and each try ended in a new hitch and a little more hush.",
        ),
        QAItem(
            question=f"What tool did they use to help with the banner?",
            answer=f"They used {tool.label}, which was meant to help them reach, hold, or lift the banner.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: the banner tore, slipped free, and never got to the happy spot.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banner?",
            answer="A banner is a long piece of cloth or paper with words or pictures on it, used to show a message or celebrate a special day.",
        ),
        QAItem(
            question="Why can wind be a problem for a banner?",
            answer="Wind can tug on a banner, make it flap, and pull it loose if it is not held well.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something might go wrong.",
        ),
        QAItem(
            question="What does repetition do in a story?",
            answer="Repetition repeats words or actions so a story can feel catchy, bouncy, or tense.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    banner: Entity = f["banner"]
    return [
        f'Write a short rhyming story with the word "banner" about {hero.id} trying to hang a celebration sign.',
        f"Tell a suspenseful children's story where {hero.id} and {hero.pronoun('possessive')} helper keep trying, trying, trying to lift {banner.phrase}.",
        "Write a simple repetitive story that ends badly when a banner will not stay up.",
    ]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid in BANNERS:
        lines.append(asp.fact("banner", bid))
    for tid in [t.id for t in TOOLS]:
        lines.append(asp.fact("tool", tid))
    for pid, p in PLACES.items():
        for a in p.affords:
            lines.append(asp.fact("affords", pid, a))
    for bid, b in BANNERS.items():
        lines.append(asp.fact("can_fail", bid))
    for t in TOOLS:
        for h in t.helps:
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B) :- place(P), banner(B), affords(P,hang), can_fail(B).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, b) for p in PLACES for b in BANNERS if reasonableness_gate(p, BANNERS[b]))
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_world(params: StoryParams) -> World:
    setting = PLACES[params.place]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, memes={"hope": 1.0}))
    helper_type = {"parent": "mother", "grandparent": "woman", "friend": "girl"}[params.helper]
    helper = world.add(Entity(id=params.helper, kind="character", type=helper_type, label=f"the {params.helper}", memes={"care": 1.0}))
    banner_cfg = BANNERS[params.banner]
    banner = world.add(Entity(id="banner", type="banner", label="banner", phrase=banner_cfg.phrase, owner=hero.id, caretaker=helper.id, meters={"height": 0.0, "tug": 0.0, "fray": 0.0}, memes={"hope": 0.0, "worry": 0.0}))
    tool = select_tool(params.place, banner_cfg)
    world.facts.update(hero=hero, helper=helper, banner=banner, tool=tool, params=params)
    return world


def narrate_attempt(world: World, hero: Entity, helper: Entity, banner: Entity, tool: ToolCfg, attempt: int) -> None:
    banner.memes["hope"] += 0.2
    banner.memes["worry"] += 0.3
    hero.memes["hope"] += 0.1
    world.say(f"Up they went, up they went, on attempt {attempt}, neat and bright.")
    if attempt == 1:
        world.say(f"{hero.id} held the {banner.label} while {helper.label} got {tool.label} in sight.")
        world.say(f"They {tool.prep}, and the banner rose a bit, but not quite right.")
        banner.meters["height"] += 0.5
        banner.meters["tug"] += 0.8
    elif attempt == 2:
        world.say(f"Again they tried, and again they sighed, with the wind at the banner's side.")
        world.say(f"The {tool.label} helped a touch, but a sneaky gust gave one strong slide.")
        banner.meters["height"] += 0.3
        banner.meters["tug"] += 1.0
        banner.meters["fray"] += 0.5
        banner.memes["worry"] += 0.5
    else:
        world.say(f"Once more, once more, they reached and rose, with hope in their hands and dust on their toes.")
        world.say(f"But the pull got mean, and the knot got weak; the little sign started to seek a fall.")
        banner.meters["tug"] += 1.3
        banner.meters["fray"] += 1.0
        banner.memes["worry"] += 1.0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    banner: Entity = world.facts["banner"]
    tool: ToolCfg = world.facts["tool"]

    world.say(f"{hero.id} had {banner.phrase}, a shiny little show.")
    world.say(f"{hero.id} and {helper.label} wanted to hang it high, so everyone could know.")
    world.say(setting_line(world))
    world.say(f"{hero.id} smiled, but the wind was quick; it made the banner twitch and blow.")

    world.para()
    world.say("Try one, try one, up they spun, and up it climbed a little way.")
    narrate_attempt(world, hero, helper, banner, tool, 1)
    world.say("Still it did not stay, stay, stay; it dipped again in a swaying play.")

    world.para()
    world.say("Try two, try two, not through, not through; they would not quit the task.")
    narrate_attempt(world, hero, helper, banner, tool, 2)
    world.say(f"{hero.id} peeked up high and held {hero.pronoun('possessive')} breath; the banner shook like a mask.")

    world.para()
    world.say("Try three, try three, it might not be free, but the sky kept all its jokes.")
    narrate_attempt(world, hero, helper, banner, tool, 3)
    banner.meters["height"] = max(0.0, banner.meters["height"] - 1.0)
    banner.meters["fray"] += 1.2
    banner.memes["worry"] += 1.0
    hero.memes["hope"] = 0.0
    helper.memes["care"] += 0.5

    world.say(f"Then came the bad part, sharp and stark: the string snapped short with a little dark.")
    world.say(f"The {banner.label} slipped from the hook, spun in the air, and fell with a flop into the yard.")
    world.say(f"Now the wall stood bare, and the day went by without the merry sign they had hoped to declare.")
    world.say(f"{hero.id} and {helper.label} stood still and sad, with a torn banner on the grass and a sigh in the air.")

    world.facts["ending_bad"] = True
    world.facts["attempts"] = 3
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="yard", banner="party", name="Mia", gender="girl", helper="parent", trait="brave"),
    StoryParams(place="porch", banner="welcome", name="Leo", gender="boy", helper="friend", trait="patient"),
    StoryParams(place="hall", banner="festival", name="Nora", gender="girl", helper="grandparent", trait="cheery"),
]


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
        vals = asp_valid()
        print(f"{len(vals)} compatible (place, banner) combos:\n")
        for p, b in vals:
            print(f"  {p:8} {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: banner at {p.place} ({p.banner})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
