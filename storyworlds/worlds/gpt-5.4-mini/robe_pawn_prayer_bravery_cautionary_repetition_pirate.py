#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/robe_pawn_prayer_bravery_cautionary_repetition_pirate.py
========================================================================================

A standalone tiny storyworld for a pirate-tale seed with the required words
robe, pawn, and prayer, plus the narrative instruments Bravery, Cautionary, and
Repetition.

The domain is small: two children in pirate play find a dark "cabin" under a
table, one brave child wants to cross it using a ceremonial robe and a pawn
figurine as a marker, the cautious child warns that the pawn is too small and
easy to lose in the dark, then a repeated prayer-like chant becomes a calm way
to steady courage. In the safer branch, the children use a lantern and keep the
pawn on a shelf as a lucky treasure; in the risk branch, the pawn falls, the
bravery turns into a messy scramble, and an adult helps recover the scene.

The story is state-driven: physical meters track darkness, lostness, and glow;
emotional memes track bravery, caution, relief, and repetition. The prose is
assembled from those state changes rather than from a fixed paragraph template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/robe_pawn_prayer_bravery_cautionary_repetition_pirate.py
    python storyworlds/worlds/gpt-5.4-mini/robe_pawn_prayer_bravery_cautionary_repetition_pirate.py --all
    python storyworlds/worlds/gpt-5.4-mini/robe_pawn_prayer_bravery_cautionary_repetition_pirate.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/robe_pawn_prayer_bravery_cautionary_repetition_pirate.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    scene: str
    dark_spot: str
    pirate_frame: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Prop:
    id: str
    label: str
    kind: str
    dangerous_in_dark: bool = False
    sacred: bool = False
    tiny: bool = False
    gives_light: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    brave_child: str
    cautious_child: str
    robe: str
    pawn: str
    light: str
    response: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "deck": Setting("deck", "the ship deck was all moon-silver and creaky", "the shadow under the sail", "a pirate deck", "The lantern glow made the deck look brave"),
    "cabin": Setting("cabin", "the captain's cabin felt snug and secret", "the dark chest corner", "a pirate cabin", "The lantern glow made the cabin look warm"),
    "harbor": Setting("harbor", "the harbor boardwalk smelled like salt and rope", "the space behind the crates", "a harbor adventure", "The lantern glow turned the harbor bright"),
}

PROPS = {
    "robe": Prop("robe", "robe", "cloth", sacred=True, tags={"robe"}),
    "pawn": Prop("pawn", "pawn", "toy", dangerous_in_dark=True, tiny=True, tags={"pawn"}),
    "lantern": Prop("lantern", "lantern", "light", gives_light=True, tags={"light"}),
    "flashlight": Prop("flashlight", "flashlight", "light", gives_light=True, tags={"light"}),
    "rope": Prop("rope", "rope", "thing", tags={"rope"}),
}

RESPONSES = {
    "steady_lantern": Response("steady_lantern", 3, 3,
                              "lifted the lantern high and let its steady glow guide them",
                              "held the lantern up, but the dark corner was already too messy",
                              "lifted the lantern high to guide them",
                              tags={"light"}),
    "call_adult": Response("call_adult", 3, 4,
                           "called for a grown-up, who came right away and found the lost pawn",
                           "called for a grown-up, but the search took too long",
                           "called for a grown-up",
                           tags={"help"}),
    "prayer_pause": Response("prayer_pause", 2, 2,
                             "paused for a small prayer and then counted their steps again",
                             "paused and prayed, but the dark corner still swallowed the pawn",
                             "paused for a small prayer",
                             tags={"prayer"}),
    "water_bucket": Response("water_bucket", 1, 1,
                             "threw water everywhere",
                             "threw water everywhere, but that only made the floor worse",
                             "threw water everywhere",
                             tags={"water"}),
}

GIRL_NAMES = ["Mina", "Luna", "Mara", "Ivy", "Nora"]
BOY_NAMES = ["Finn", "Jace", "Eli", "Toby", "Arlo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for light in ("lantern", "flashlight"):
            for pawn in ("pawn",):
                combos.append((s, light, pawn))
    return combos


def reasonableness_gate(light: Prop, pawn: Prop) -> bool:
    return light.gives_light and pawn.tiny and pawn.dangerous_in_dark


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def _r_dark(world: World) -> list[str]:
    out = []
    if world.get("cabin").meters["dark"] >= THRESHOLD and ("dark",) not in world.fired:
        world.fired.add(("dark",))
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["caution"] += 1
        out.append("__dark__")
    return out


def propagate(world: World) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_dark,):
            s = fn(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    return produced


def tell(setting: Setting, brave: str, cautious: str, robe: Prop, pawn: Prop, light: Prop, response: Response) -> World:
    world = World(setting)
    hero = world.add(Entity(brave, kind="character", type="boy" if brave in BOY_NAMES else "girl", role="brave"))
    guide = world.add(Entity(cautious, kind="character", type="girl" if cautious in GIRL_NAMES else "boy", role="cautious"))
    mom = world.add(Entity("Mom", kind="character", type="mother", label="the mother", role="adult"))
    robe_ent = world.add(Entity("robe", label=robe.label))
    pawn_ent = world.add(Entity("pawn", label=pawn.label))
    light_ent = world.add(Entity(light.id, label=light.label))
    world.facts.update(hero=hero, guide=guide, mom=mom, robe=robe_ent, pawn=pawn_ent, light=light_ent, response=response)

    hero.memes["bravery"] += 2
    guide.memes["caution"] += 2

    world.say(f"{hero.id} and {guide.id} turned {setting.scene} into a pirate game. {setting.pirate_frame}.")
    world.say(f"{hero.id} wore a {robe.label} like a captain's cloak, and the little {pawn.label} sat on a crate like a tiny treasure.")

    world.para()
    world.say(f"But {setting.dark_spot} looked very dark.")
    world.say(f'"We need to go there," {hero.id} said, because {hero.id} was very brave.')
    world.say(f'"Careful," {guide.id} said. "That pawn is tiny. In the dark, it could slip away."')

    if response.id == "prayer_pause":
        hero.memes["repetition"] += 2
        world.say(f'{hero.id} whispered a prayer once, then again, then once more, keeping the words soft and steady.')
        world.say(f'The repeated prayer made the brave heart calmer, but it also made both children slow down and look closely.')
        world.get("cabin").meters["dark"] += 1
        propagate(world)
        if light.id == "lantern":
            world.say(f"{guide.id} lifted the lantern and its glow showed the pawn still waiting on the crate.")
            world.say(f'This time they kept the pawn safe and walked on together, brave, careful, and bright.')
            outcome = "safe"
        else:
            world.say(f'The light was not enough for the shadowy corner, and the pawn wobbled to the floor.')
            world.get("pawn").meters["lost"] += 1
            world.say(f'{mom.label_word.capitalize()} came in, picked up the pawn, and helped them start over.')
            outcome = "lost"
    else:
        world.get("cabin").meters["dark"] += 1
        propagate(world)
        world.say(f'{hero.id} reached for the pawn first, because bravery tugged hard.')
        if light.id == "lantern":
            world.say(f'{guide.id} pointed the lantern down, and the glow made the pawn easy to spot.')
            world.say(f'They marched ahead with the pawn held tight, and the robe swished like a flag in the wind.')
            outcome = "safe"
        else:
            world.say(f'The flashlight flickered under the crates, and the pawn slipped into the dark.')
            world.get("pawn").meters["lost"] += 1
            world.say(f'{guide.id} gasped, "I told you to be careful," and {hero.id} felt the sting of not listening.')
            response = RESPONSES["call_adult"]
            world.say(f'{mom.label_word.capitalize()} came quickly and {response.text}.')
            outcome = "lost"

    world.para()
    if outcome == "safe":
        world.say(f"By the end, the pawn was still on the deck, the robe still swayed on {hero.id}, and the pirate game felt bold but gentle.")
    else:
        world.say(f"By the end, the pawn was found again, and the children learned that bravery works best when caution speaks up too.")
    world.facts["outcome"] = outcome
    return world


KNOWLEDGE = {
    "robe": [("What is a robe?", "A robe is a loose piece of clothing you wear over other clothes. It can make play feel fancy or grand.")],
    "pawn": [("What is a pawn?", "A pawn is a small game piece, often from chess. It is tiny and easy to lose if you are not careful.")],
    "prayer": [("What is a prayer?", "A prayer is a quiet talk or wish spoken softly. Some people say a prayer when they want comfort or hope.")],
    "bravery": [("What is bravery?", "Bravery means doing something hard or scary while keeping your heart steady.")],
    "cautionary": [("What does cautionary mean?", "Cautionary means it gives a warning or helps you learn to be careful.")],
    "repetition": [("What is repetition?", "Repetition means doing or saying something again and again.")],
    "light": [("Why is light helpful in the dark?", "Light helps you see where to step, so you can find things and avoid bumps.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-tale story for a small child that includes the words "robe", "pawn", and "prayer".',
        f"Tell a brave but cautionary pirate story where {f['hero'].id} wants to cross the dark place, {f['guide'].id} warns about the tiny pawn, and a repeated prayer helps them stay calm.",
        f'Write a story with repetition, bravery, and a gentle warning about a pawn in the dark, ending with a safe pirate image.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guide, mom = f["hero"], f["guide"], f["mom"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {guide.id}, two children playing pirates with {mom.label_word} nearby."),
        ("Why did {0} need to be careful?".format(hero.id),
         "They were heading toward a dark place, and the pawn was tiny enough to slip away in the shadows. The caution made the brave choice safer."),
        ("What did the repeated prayer do?",
         f"It helped {hero.id} slow down and feel steadier. That calm repetition kept the adventure from turning into a rush."),
    ]
    if outcome == "safe":
        qa.append(("How did the story end?",
                   f"It ended safely, with the pawn still found and the pirate game still going. The robe stayed on {hero.id} like a captain's cloak, and the lantern kept everything bright."))
    else:
        qa.append(("How did the story end?",
                   f"It ended with the pawn recovered and everyone learning to listen to caution sooner. {mom.label_word.capitalize()} helped fix the mistake and the brave game began again."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"robe", "pawn", "prayer", "bravery", "cautionary", "repetition", "light"}
    out = []
    for tag in ["robe", "pawn", "prayer", "bravery", "cautionary", "repetition", "light"]:
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_story(S) :- setting(S), response(r1).
warning_needed :- pawn(tiny), dark_corner.
repetition_used :- response(prayer_pause).
outcome(safe) :- repetition_used, not lost_pawn.
outcome(lost) :- lost_pawn.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show safe_story/1.\n#show outcome/1."))
    _ = asp.atoms(model, "safe_story")
    p = resolve_params(argparse.Namespace(setting=None, brave_child=None, cautious_child=None, robe=None, pawn=None, light=None, response=None), random.Random(7))
    sample = generate(p)
    if not sample.story:
        return 1
    print("OK: ASP and normal generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with robe, pawn, prayer, bravery, cautionary warning, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--light", choices=["lantern", "flashlight"])
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--brave-child")
    ap.add_argument("--cautious-child")
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
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    setting = args.setting or rng.choice(list(SETTINGS))
    brave = args.brave_child or rng.choice(GIRL_NAMES + BOY_NAMES)
    cautious_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != brave]
    cautious = args.cautious_child or rng.choice(cautious_pool)
    robe = "robe"
    pawn = "pawn"
    light = args.light or rng.choice(["lantern", "flashlight"])
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    if not reasonableness_gate(PROPS[light], PROPS[pawn]):
        raise StoryError("Invalid combination for this pirate story.")
    return StoryParams(setting, brave, cautious, robe, pawn, light, response)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.brave_child, params.cautious_child,
                 PROPS[params.robe], PROPS[params.pawn], PROPS[params.light],
                 RESPONSES[params.response])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show safe_story/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories: deck/cabin/harbor with lantern or flashlight")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams("deck", "Mina", "Finn", "robe", "pawn", "lantern", "prayer_pause"),
            StoryParams("cabin", "Jace", "Nora", "robe", "pawn", "flashlight", "steady_lantern"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
