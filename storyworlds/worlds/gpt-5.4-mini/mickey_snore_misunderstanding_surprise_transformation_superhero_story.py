#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mickey_snore_misunderstanding_surprise_transformation_superhero_story.py
======================================================================================================

A standalone story world for a tiny superhero-style misunderstanding tale.

Seed words:
- mickey
- snore

Features:
- Misunderstanding
- Surprise
- Transformation

This world simulates a child hero, a sleepy sidekick, a mistaken alarm, and a
surprise transformation into a true rescue moment. It generates compact,
child-facing superhero stories with state-driven turns and endings that prove
what changed.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
class Scene:
    id: str
    place: str
    sky: str
    alarm_place: str
    dark_phrase: str
    hero_pose: str
    ending_pose: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Misunderstanding:
    id: str
    trigger: str
    mistaken_threat: str
    true_cause: str
    clue: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Surprise:
    id: str
    reveal: str
    helper_line: str
    gift: str
    sparkle: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Transformation:
    id: str
    from_state: str
    to_state: str
    power_name: str
    costume: str
    action: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_noise(world: World) -> list[str]:
    out = []
    if world.get("sidekick").meters["snoring"] >= THRESHOLD and ("noise",) not in world.fired:
        world.fired.add(("noise",))
        world.get("hero").memes["worry"] += 1
        world.get("hero").memes["misunderstanding"] += 1
        out.append("__alarm__")
    return out


def _r_truth(world: World) -> list[str]:
    out = []
    if world.get("sidekick").meters["snoring"] < THRESHOLD:
        return out
    if world.get("helper").memes["calm"] >= THRESHOLD and ("truth",) not in world.fired:
        world.fired.add(("truth",))
        world.get("hero").memes["understanding"] += 1
        out.append("__reveal__")
    return out


def _r_transform(world: World) -> list[str]:
    out = []
    if world.get("hero").memes["heroic"] >= THRESHOLD and ("transform",) not in world.fired:
        world.fired.add(("transform",))
        world.get("hero").meters["shining"] += 1
        world.get("hero").memes["confidence"] += 1
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("noise", "social", _r_noise),
    Rule("truth", "social", _r_truth),
    Rule("transform", "physical", _r_transform),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("sidekick").meters["snoring"] += 1
    propagate(sim, narrate=False)
    return {
        "misunderstanding": sim.get("hero").memes["misunderstanding"] >= THRESHOLD,
        "understanding": sim.get("hero").memes["understanding"] >= THRESHOLD,
    }


def setup(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["bravery"] += 1
    hero.memes["care"] += 1
    world.say(
        f"At {world.scene.place}, {hero.id} wore {world.scene.hero_pose} and watched over the city."
    )
    world.say(
        f"Beside {hero.id}, {sidekick.id} was curled up under {sidekick.pronoun('possessive')} blanket, making a soft {sidekick.attrs['sound']}."
    )


def alarm(world: World, hero: Entity, misunderstanding: Misunderstanding) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'Suddenly {hero.id} heard a {misunderstanding.trigger}. '
        f'"A villain!" {hero.id} shouted. "{misunderstanding.mistaken_threat}!"'
    )


def investigate(world: World, hero: Entity, helper: Entity, misunderstanding: Misunderstanding) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"{helper.id} hurried over and pointed at the {misunderstanding.clue}. "
        f'"Wait," {helper.id} said, "that sound comes from {misunderstanding.true_cause}."'
    )


def reveal(world: World, surprise: Surprise, transformation: Transformation, hero: Entity, sidekick: Entity) -> None:
    hero.memes["surprise"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"Then came a {surprise.reveal}. {surprise.helper_line}"
    )
    world.say(
        f'With a bright {surprise.sparkle}, {hero.id} pulled on {transformation.costume} and became {transformation.power_name}.'
    )


def rescue(world: World, transformation: Transformation, hero: Entity, sidekick: Entity, scene: Scene) -> None:
    hero.meters["shining"] += 1
    sidekick.meters["safe"] += 1
    world.say(
        f"{hero.id} {transformation.action}, and the whole room glowed with brave light."
    )
    world.say(
        f"The danger was only a misunderstanding, but the rescue was real: {sidekick.id} slept safe, and {hero.id} stood tall at {scene.ending_pose}."
    )


SCENES = {
    "rooftop": Scene("rooftop", "the rooftop", "a silver moon", "the alley below", "dark rooftops", "a red cape", "on the ledge"),
    "neighborhood": Scene("neighborhood", "the quiet street", "a starry sky", "the front porch", "shadowy trees", "a blue mask", "by the mailbox"),
    "tower": Scene("tower", "the tall clock tower", "a glowing sunset", "the stairs", "a dark hallway", "a green suit", "at the window"),
}

MISUNDERSTANDINGS = {
    "snore": Misunderstanding("snore", "deep snore", "the city was under attack", "a sleepy snore from the sidekick", "tiny rising blanket"),
}

SURPRISES = {
    "badge": Surprise("badge", "surprise", "The helper smiled and held up a shiny badge from the hero club.", "badge", "flash"),
}

TRANSFORMATIONS = {
    "hero": Transformation("hero", "worry", "confidence", "the true hero of the night", "hero cape", "used calm words instead of fear"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [("rooftop", "snore", "badge"), ("neighborhood", "snore", "badge"), ("tower", "snore", "badge")]


@dataclass
@dataclass
class StoryParams:
    scene: str
    misunderstanding: str
    surprise: str
    transformation: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero misunderstanding story world.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, U, T) :- scene(S), misunderstanding(M), surprise(U), transformation(T).
"""


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who was the story about?", f"It was about {f['hero'].id}, a little superhero, and {f['sidekick'].id}, who was fast asleep."),
        ("What did {0} think the noise was?".format(f["hero"].id), f"{f['hero'].id} thought the snore was a villain attack, because the sound was loud and surprising."),
        ("What did the helper explain?".format(), f"{f['helper'].id} explained that the sound came from {f['sidekick'].id}'s snore, not from a villain."),
        ("How did the story end?", f"It ended with {f['hero'].id} transformed into a brighter hero, while {f['sidekick'].id} slept safely nearby."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a snore?", "A snore is a breathing sound some people make when they are sleeping."),
        ("What does a superhero do?", "A superhero notices danger, stays brave, and helps others stay safe."),
        ("What is a misunderstanding?", "A misunderstanding happens when someone thinks the wrong thing at first."),
        ("What is a transformation?", "A transformation is a big change from one state into another."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a superhero story where Mickey hears a snore and mistakes it for danger.",
        "Tell a story with a misunderstanding, a surprise reveal, and a transformation into a real hero moment.",
        "Write a child-friendly superhero tale that includes the words mickey and snore.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    world = World(scene)
    hero = world.add(Entity(params.hero_name, kind="character", type=params.hero_gender, role="hero"))
    sidekick = world.add(Entity(params.sidekick_name, kind="character", type=params.sidekick_gender, role="sidekick", attrs={"sound": "snore"}))
    helper = world.add(Entity(params.helper_name, kind="character", type=params.helper_gender, role="helper"))

    hero.memes["heroic"] += 1
    sidekick.meters["snoring"] += 1

    setup(world, hero, sidekick)
    world.para()
    alarm(world, hero, MISUNDERSTANDINGS[params.misunderstanding])
    investigate(world, hero, helper, MISUNDERSTANDINGS[params.misunderstanding])
    world.para()
    reveal(world, SURPRISES[params.surprise], TRANSFORMATIONS[params.transformation], hero, sidekick)
    rescue(world, TRANSFORMATIONS[params.transformation], hero, sidekick, scene)
    world.facts.update(hero=hero, sidekick=sidekick, helper=helper, scene=scene)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    misunderstanding = args.misunderstanding or "snore"
    surprise = args.surprise or "badge"
    transformation = args.transformation or "hero"
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or "Mickey"
    sidekick_name = args.sidekick_name or rng.choice(["Pip", "Nora", "Benny", "Luna"])
    helper_name = args.helper_name or rng.choice(["Ava", "Milo", "Ruby", "Kai"])
    if args.misunderstanding and args.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    return StoryParams(scene, misunderstanding, surprise, transformation, hero_name, hero_gender, sidekick_name, sidekick_gender, helper_name, helper_gender)


CURATED = [
    StoryParams("rooftop", "snore", "badge", "hero", "Mickey", "boy", "Pip", "boy", "Ava", "girl"),
    StoryParams("neighborhood", "snore", "badge", "hero", "Mickey", "boy", "Luna", "girl", "Kai", "boy"),
    StoryParams("tower", "snore", "badge", "hero", "Mickey", "boy", "Benny", "boy", "Ruby", "girl"),
]


def valid_story_params(params: StoryParams) -> bool:
    return params.scene in SCENES and params.misunderstanding in MISUNDERSTANDINGS


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        print("MISMATCH in ASP/Python parity.")
        rc = 1
    else:
        print(f"OK: ASP/Python parity ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c} {d}" for a, b, c, d in asp_valid_combos()))
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
