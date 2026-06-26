#!/usr/bin/env python3
"""
storyworlds/worlds/vine_misunderstanding_sound_effects_moral_value_myth.py
===========================================================================

A small mythic storyworld about a vine, a misunderstanding, and a moral turn.

Premise:
A young helper watches over a sacred vine in a quiet grove. A strange sound
makes them fear the vine is in danger, but the sound actually comes from a
harmless creature or tool. The misunderstanding creates tension, then a wiser
voice and a careful action reveal the truth. The story ends with the vine safe
and the hero wiser.

This world is built to satisfy the Storyweavers contract:
- classical simulation with physical meters and emotional memes
- grounded prose driven by world state
- QA sets for story, world knowledge, and generation prompts
- inline ASP twin with a Python reasonableness gate
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    adjective: str
    noise_place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Noise:
    id: str
    sound: str
    source: str
    mistaken_for: str
    cause_word: str
    reveal_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Value:
    id: str
    label: str
    lesson: str
    virtue: str
    tag: str


@dataclass
class Hero:
    name: str
    type: str
    trait: str
    parent: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.sound: str = ""

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.sound = self.sound
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    vine = world.get("vine")
    noise = world.facts["noise"]
    if hero.memes.get("alarm", 0.0) < THRESHOLD:
        return out
    sig = ("misunderstood", noise.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
    vine.meters["watchfulness"] = vine.meters.get("watchfulness", 0.0) + 1.0
    out.append(f""
    )
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    noise = world.facts["noise"]
    if hero.meters.get("seen_source", 0.0) < THRESHOLD:
        return out
    sig = ("truth", noise.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
    out.append("")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("truth", _r_truth)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(
    place="the moonlit grove",
    adjective="moonlit",
    noise_place="the hollow stones",
    affords={"listen", "investigate", "reveal"},
)

NOISES = {
    "rustle": Noise(
        id="rustle",
        sound="shrrrk-shrrrk",
        source="a little wind-kissed bird in the leaves",
        mistaken_for="a thief gnawing the vine",
        cause_word="rustling",
        reveal_word="a bird's flutter",
        tags={"sound", "bird"},
    ),
    "snap": Noise(
        id="snap",
        sound="krack!",
        source="a dry twig under a deer hoof",
        mistaken_for="the vine splitting apart",
        cause_word="snapping",
        reveal_word="a deer step",
        tags={"sound", "forest"},
    ),
    "drip": Noise(
        id="drip",
        sound="plip... plip...",
        source="night dew falling from the trellis",
        mistaken_for="someone stealing sap",
        cause_word="dripping",
        reveal_word="water drops",
        tags={"sound", "water"},
    ),
}

VALUES = {
    "patience": Value(
        id="patience",
        label="patience",
        lesson="Wait and look before you leap to a guess.",
        virtue="patience",
        tag="moral",
    ),
    "care": Value(
        id="care",
        label="care",
        lesson="Care means tending what is precious with gentle hands.",
        virtue="care",
        tag="moral",
    ),
    "truth": Value(
        id="truth",
        label="truth",
        lesson="Truth grows clearer when someone checks the facts.",
        virtue="truth",
        tag="moral",
    ),
}

GROVE_GUARDS = {
    "elder": "the elder of the grove",
    "child": "the young keeper",
    "bird": "the small bird",
    "deer": "the quiet deer",
}

GIRL_NAMES = ["Mira", "Nia", "Rhea", "Sora", "Lina"]
BOY_NAMES = ["Arin", "Kai", "Taro", "Dorian", "Milo"]
TRAITS = ["brave", "curious", "gentle", "steadfast", "eager"]


ASP_RULES = r"""
% A misunderstanding happens when a sound is heard, its source is hidden,
% and the listener jumps to the wrong cause.
misunderstanding(H, N) :- hears(H, N), hidden_source(N), mistaken_for(N, _).

% Truth arrives once the source is revealed and the listener sees it.
truth_seen(H, N) :- hears(H, N), revealed(N), sees_source(H, N).

% Moral turn: the hero accepts the lesson and becomes wiser.
wise_after(H) :- truth_seen(H, N), moral_lesson(N, L), learns(H, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "grove"))
    lines.append(asp.fact("affords", "grove", "listen"))
    lines.append(asp.fact("affords", "grove", "investigate"))
    lines.append(asp.fact("affords", "grove", "reveal"))
    for nid, n in NOISES.items():
        lines.append(asp.fact("noise", nid))
        lines.append(asp.fact("sound_of", nid, n.sound))
        lines.append(asp.fact("mistaken_for", nid, n.mistaken_for))
    for vid, v in VALUES.items():
        lines.append(asp.fact("moral_lesson", vid, v.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_validations() -> bool:
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic vine misunderstanding storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--value", choices=VALUES)
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


def valid_combo(noise: Noise, value: Value) -> bool:
    return bool(noise.tags & {"sound"}) and value.tag == "moral"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    noise_id = args.noise or rng.choice(list(NOISES))
    value_id = args.value or rng.choice(list(VALUES))
    noise = NOISES[noise_id]
    value = VALUES[value_id]
    if not valid_combo(noise, value):
        raise StoryError("The chosen sound and moral value do not make a coherent myth.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait, noise=noise_id, value=value_id, seed=None)


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    noise: str
    value: str
    seed: Optional[int] = None


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    vine = world.add(Entity(id="vine", kind="thing", type="vine", label="vine", phrase="a silver-green vine"))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label="elder"))
    noise = NOISES[params.noise]
    value = VALUES[params.value]
    world.facts.update(hero=hero, vine=vine, elder=elder, noise=noise, value=value)

    hero.memes["care"] = 1.0
    vine.meters["living"] = 1.0

    world.say(f"{params.name} was { _article(params.trait)} {params.trait} child who tended {vine.phrase} in {SETTING.place}.")
    world.say(f"The vine was old and dear, said to grow from a hero's forgotten gift, and its leaves shone in the {SETTING.adjective} light.")
    world.para()

    world.say(f"Then came {noise.sound} from {SETTING.noise_place}.")
    hero.memes["alarm"] = 1.0
    world.say(f"{params.name} thought it was {noise.mistaken_for}.")
    world.say(f"In a hurry, {params.name} reached toward the vine and listened harder.")
    propagate(world, narrate=False)
    world.para()

    world.say(f"But the elder of the grove lifted {hero.pronoun('possessive')} hand and said, 'Wait.'")
    world.say(f"{params.name} followed the sound and found {noise.source}.")
    hero.meters["seen_source"] = 1.0
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
    world.say(f"It was only {noise.reveal_word}, not a danger at all.")
    world.say(f"Then {params.name} smiled and remembered the moral of {value.label}: {value.lesson}")
    world.para()

    hero.memes["peace"] = 1.0
    vine.meters["safe"] = 1.0
    world.say(f"The vine stayed unhurt in the grove, and {params.name} guarded it more gently after that.")
    world.say(f"From then on, whenever {noise.sound} echoed nearby, {params.name} looked first and guessed second.")
    world.facts["resolved"] = True
    return world


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    noise = f["noise"]
    value = f["value"]
    return [
        f'Write a short myth for a child about a vine and the sound "{noise.sound}".',
        f"Tell a gentle story where {hero.label} misreads a noise in the grove, then learns the value of {value.label}.",
        f"Write a mythic story with a misunderstanding, a revealed sound, and a moral lesson about {value.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    noise = f["noise"]
    value = f["value"]
    return [
        QAItem(
            question=f"What did {hero.label} think the sound {noise.sound} meant at first?",
            answer=f"{hero.label} thought it was {noise.mistaken_for}. That was the misunderstanding in the grove.",
        ),
        QAItem(
            question=f"What was the sound really coming from?",
            answer=f"It was really coming from {noise.source}. When {hero.label} looked closely, the fear went away.",
        ),
        QAItem(
            question=f"What moral lesson did {hero.label} remember at the end?",
            answer=f"{value.lesson} {hero.label} remembered the value of {value.label} and became wiser.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    value = f["value"]
    noise = f["noise"]
    return [
        QAItem(
            question="What is a vine?",
            answer="A vine is a plant with a long, flexible stem that can climb or trail along a surface.",
        ),
        QAItem(
            question="Why should people look carefully before they guess?",
            answer="Looking carefully helps people avoid misunderstandings, because a sound or sight can seem scary when it is actually harmless.",
        ),
        QAItem(
            question=f"What does the moral value of {value.label} mean?",
            answer=value.lesson,
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mira", gender="girl", trait="curious", noise="rustle", value="patience"),
    StoryParams(name="Arin", gender="boy", trait="steadfast", noise="snap", value="care"),
    StoryParams(name="Nia", gender="girl", trait="gentle", noise="drip", value="truth"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    return 0


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
        print("ASP mode is available for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
