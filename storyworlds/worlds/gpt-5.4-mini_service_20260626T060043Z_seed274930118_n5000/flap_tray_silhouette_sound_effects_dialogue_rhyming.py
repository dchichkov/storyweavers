#!/usr/bin/env python3
"""
Stand-alone storyworld: flap, tray, silhouette, sound effects, dialogue, rhyming story.

Premise:
A small child notices a lost silhouette-shaped kite flap caught in a bakery tray rack.
They want to fix it before the evening show, but the tray is too high and the flap keeps
slipping. A helper suggests a careful, rhyming rescue.

The world is simulated through physical meters and emotional memes:
- the flap can shake, catch, and straighten
- the tray can rattle, tilt, and drop crumbs
- the silhouette can be seen, hidden, or returned
- sound effects and dialogue are narrated as state changes

The story ends when the flap is restored and the silhouette is made clear again.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self) -> None:
        for k in ("balance", "height", "noise", "mess", "visible", "safe", "flapness"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "joy", "curiosity", "relief", "frustration"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def subj(self) -> str:
        return self.pronoun("subject")

    def obj(self) -> str:
        return self.pronoun("object")

    def pos(self) -> str:
        return self.pronoun("possessive")


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Problem:
    flap_label: str
    tray_label: str
    silhouette_label: str
    sound1: str
    sound2: str
    rhymes: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        current: list[str] = []
        for line in self.lines:
            if line == "":
                if current:
                    chunks.append(" ".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            chunks.append(" ".join(current))
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    seed: Optional[int] = None


SETTINGS = {
    "bakery": Setting(place="the bakery", detail="Warm buns sat on shelves, and a silver tray rack waited near the wall."),
    "theater": Setting(place="the little theater", detail="Curtains hung soft and red, and the stage lamp made every corner glow."),
    "attic": Setting(place="the attic", detail="Dust danced in the beams, and old trays leaned beside a toy trunk."),
}

PROBLEMS = {
    "bakery": Problem(
        flap_label="paper flap",
        tray_label="silver tray",
        silhouette_label="dark silhouette",
        sound1="flip-flip",
        sound2="clink-clink",
        rhymes="slap and tap, flap and lap",
    ),
    "theater": Problem(
        flap_label="curtain flap",
        tray_label="prop tray",
        silhouette_label="stage silhouette",
        sound1="swish-swish",
        sound2="tap-tap",
        rhymes="glide and slide, hide and sigh",
    ),
    "attic": Problem(
        flap_label="dusty flap",
        tray_label="old tray",
        silhouette_label="moon silhouette",
        sound1="creak-creak",
        sound2="clatter-clatter",
        rhymes="peek and seek, squeak and tweak",
    ),
}

HERO_NAMES = ["Mina", "Pip", "Nora", "Toby", "Luna", "Arlo"]
HELPER_NAMES = ["Moe", "June", "Bea", "Finn", "Ivy", "Ollie"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld about a flap, a tray, and a silhouette.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    prob = PROBLEMS[params.place]
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="person", label=params.helper_name))
    flap = world.add(Entity(id="flap", type="flap", label=prob.flap_label, phrase=prob.flap_label))
    tray = world.add(Entity(id="tray", type="tray", label=prob.tray_label, phrase=prob.tray_label))
    silhouette = world.add(Entity(id="silhouette", type="silhouette", label=prob.silhouette_label, phrase=prob.silhouette_label))
    world.facts.update(hero=hero, helper=helper, flap=flap, tray=tray, silhouette=silhouette, prob=prob)
    return world


def simulate(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    flap: Entity = world.facts["flap"]  # type: ignore[assignment]
    tray: Entity = world.facts["tray"]  # type: ignore[assignment]
    silhouette: Entity = world.facts["silhouette"]  # type: ignore[assignment]
    prob: Problem = world.facts["prob"]  # type: ignore[assignment]

    world.say(f"In {world.setting.place}, {hero.label} saw a {prob.silhouette_label} near a {prob.tray_label}.")
    world.say(f"{hero.label} whispered, 'What is that shape?'")
    world.say(f"'{prob.sound1}! {prob.sound2}!' went the {prob.flap_label} as the tray gave a tiny shake.")
    hero.memes["curiosity"] += 1
    tray.meters["noise"] += 1
    flap.meters["flapness"] += 1
    silhouette.meters["visible"] += 0.4
    silhouette.meters["height"] += 0.2

    world.para()
    world.say(f"{hero.label} tried to reach it, but the tray was high and the flap kept slipping away.")
    hero.memes["worry"] += 1
    hero.memes["frustration"] += 1
    tray.meters["balance"] += 0.3
    flap.meters["flapness"] += 0.5
    world.say(f"'{prob.sound2},' said the tray. 'Too high, too high!' sighed {hero.label}.")

    world.para()
    world.say(f"Then {helper.label} came near and smiled. '{prob.rhymes},' {helper.label} said with a grin.")
    world.say(f"{helper.label} held the tray steady while {hero.label} eased the flap straight and slow.")
    tray.meters["balance"] += 1.0
    flap.meters["flapness"] -= 0.8
    silhouette.meters["visible"] += 0.7
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.para()
    world.say(f"'{prob.sound1}... {prob.sound2}...' whispered the room, but now it sounded soft, not wild.")
    world.say(f"The silhouette stood clear at last, and the flap lay smooth beside the tray.")
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    silhouette.meters["visible"] = 1.0
    flap.meters["safe"] = 1.0
    tray.meters["safe"] = 1.0

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    prob: Problem = world.facts["prob"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        f"Write a rhyming story about a {prob.flap_label}, a {prob.tray_label}, and a {prob.silhouette_label}.",
        f"Tell a child-friendly story with sound effects and dialogue where {hero.label} fixes a tricky {prob.flap_label}.",
        f"Create a short rhyme about {world.setting.place}, a noisy tray, and a silhouette that becomes clear again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    prob: Problem = world.facts["prob"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.label} see in {world.setting.place}?",
            answer=f"{hero.label} saw a {prob.silhouette_label} near a {prob.tray_label}.",
        ),
        QAItem(
            question=f"What sound did the flap and tray make at first?",
            answer=f"They made the sounds '{prob.sound1}' and '{prob.sound2}'.",
        ),
        QAItem(
            question=f"Who helped make the silhouette clear again?",
            answer=f"{helper.label} helped {hero.label} hold the tray steady and fix the flap.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The flap lay smooth, the tray stayed steady, and the silhouette stood clear at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    prob: Problem = world.facts["prob"]  # type: ignore[assignment]
    return [
        QAItem(question="What is a silhouette?", answer="A silhouette is a dark shape you can see when light is behind something."),
        QAItem(question="What does a tray do?", answer="A tray carries things and helps keep them together."),
        QAItem(question="What is a flap?", answer="A flap is a piece that can swing, flutter, or move back and forth."),
        QAItem(question="Why do sound effects matter in stories?", answer="Sound effects help the story feel lively and let readers hear what is happening."),
        QAItem(question=f"Which rhyming words fit this story's style?", answer=f"The story uses playful rhyme like {prob.rhymes}."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.label or e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% place(P). hero(H). helper(X). flap(F). tray(T). silhouette(S).
% makes_sound(F, A). makes_sound(T, B). visible(S, 0/1).

can_fix(H, X, F, T, S) :- hero(H), helper(X), flap(F), tray(T), silhouette(S), has_sound(F), has_sound(T).
resolved(S) :- can_fix(_, _, _, _, S).

#show can_fix/5.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("place", "scene"))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("flap", "flap"))
    lines.append(asp.fact("tray", "tray"))
    lines.append(asp.fact("silhouette", "silhouette"))
    lines.append(asp.fact("has_sound", "flap"))
    lines.append(asp.fact("has_sound", "tray"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:  # pragma: no cover
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program())
    resolved = asp.atoms(model, "resolved")
    if resolved:
        print("OK: ASP program resolves the story's central problem.")
        return 0
    print("MISMATCH: ASP program did not resolve as expected.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    simulate(world)
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


CURATED = [
    StoryParams(place="bakery", hero_name="Mina", hero_type="girl", helper_name="Moe"),
    StoryParams(place="theater", hero_name="Pip", hero_type="boy", helper_name="June"),
    StoryParams(place="attic", hero_name="Nora", hero_type="girl", helper_name="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
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
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
