#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/relevant_disconcert_jammies_cautionary_sound_effects_transformation.py
======================================================================================================

A standalone story world about an adventure night in jammies, where a curious
child hears a disconcerting sound, follows a cautionary lesson, and experiences
a playful transformation by the end.

This world is built around:
- the seed words: relevant, disconcert, jammies
- the features: Cautionary, Sound Effects, Transformation
- the style: Adventure

The domain is deliberately small: one child, one grown-up, one adventurous
setting, a worrying sound, a safe response, and a transformation that proves the
ending changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/relevant_disconcert_jammies_cautionary_sound_effects_transformation.py
    python storyworlds/worlds/gpt-5.4-mini/relevant_disconcert_jammies_cautionary_sound_effects_transformation.py --all
    python storyworlds/worlds/gpt-5.4-mini/relevant_disconcert_jammies_cautionary_sound_effects_transformation.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/relevant_disconcert_jammies_cautionary_sound_effects_transformation.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/relevant_disconcert_jammies_cautionary_sound_effects_transformation.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
class Setting:
    id: str
    label: str
    adventure: str
    dark_spot: str
    sound_place: str

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
class SoundSource:
    id: str
    label: str
    effect: str
    disconcerting: bool = True
    tags: set[str] = field(default_factory=set)

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
    label: str
    reveal: str
    sound: str
    mood: str
    tags: set[str] = field(default_factory=set)

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
class Response:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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


class World:
    def __init__(self) -> None:
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_disconcert(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    source = world.entities.get("sound")
    if not child or not source:
        return out
    sig = ("disconcert", child.id, source.id)
    if sig in world.fired:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    if source.meters["noise"] < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    out.append("__sound__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    if not child or not toy:
        return out
    sig = ("transform", toy.id)
    if sig in world.fired:
        return out
    if child.memes["safe"] < THRESHOLD:
        return out
    if toy.meters["changed"] < THRESHOLD:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("disconcert", "social", _r_disconcert),
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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def sound_risk(source: SoundSource) -> bool:
    return source.disconcerting


def can_transform(source: SoundSource, transform: Transformation) -> bool:
    return source.id in transform.tags or not transform.tags


@dataclass
@dataclass
class StoryParams:
    setting: str
    sound: str
    transform: str
    response: str
    child_name: str
    child_gender: str
    grownup: str
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


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    sound = SOUNDS[params.sound]
    transform = TRANSFORMS[params.transform]
    response = RESPONSES[params.response]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="hero"))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup, role="guide", label="the grown-up"))
    sound_ent = world.add(Entity(id="sound", kind="thing", type="sound", label=sound.label))
    toy = world.add(Entity(id="toy", kind="thing", type="thing", label=transform.label))
    child.memes["curiosity"] = 2.0
    child.memes["safe"] = 0.0
    child.meters["tired"] = 0.0
    sound_ent.meters["noise"] = 1.0
    toy.meters["changed"] = 0.0

    world.say(
        f"One night, {child.id} wore {child.pronoun('possessive')} jammies and tiptoed into "
        f"{setting.label}. It felt like an adventure because {setting.adventure}."
    )
    world.say(
        f"Then a {sound.label} went {sound.effect}, and that sound was so disconcert it made "
        f"{child.id} pause."
    )
    world.para()
    child.memes["curiosity"] += 1
    if sound_risk(sound):
        world.say(
            f'{child.id} whispered, "That sound is relevant to our quest, but it does not sound safe."'
        )
    world.say(
        f'{grownup.label_word.capitalize()} nodded and said, "First the cautionary part: do not go '
        f"toward strange noises alone."
    )
    world.say(
        f'{grownup.label_word.capitalize()} led {child.id} with a lantern toward {setting.sound_place}.'
    )
    child.memes["safe"] += 1
    world.para()

    if can_transform(sound, transform):
        toy.meters["changed"] += 1
        world.say(
            f"Under a small cloth, they found {transform.reveal}. It went {transform.sound}, "
            f"and the plain toy began to transform."
        )
        world.say(
            f"The surprise was not scary after all; it became a {transform.label} with a bright {transform.mood}."
        )
    else:
        world.say(
            f"They found only a quiet door, and the mystery stayed closed."
        )
    propagate(world, narrate=False)
    world.say(
        f"{child.id} smiled in {child.pronoun('possessive')} jammies, no longer disconcerted. "
        f"The adventure ended with {setting.label} feeling warm and safe."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        setting=setting,
        sound=sound,
        transform=transform,
        response=response,
        transformed=toy.meters["changed"] >= THRESHOLD,
    )
    return world


THEMES = {
    "cave": Setting("cave", "the cave", "shadowy tunnels and shiny stones", "the dark tunnel", "the echoing chamber"),
    "attic": Setting("attic", "the attic", "dusty beams and old trunks", "the creaky corner", "the back of the attic"),
    "forest": Setting("forest", "the forest camp", "twinkling trees and a lantern path", "the brambly hollow", "the piney clearing"),
}

SOUNDS = {
    "rattle": SoundSource("rattle", "rattle", "clatter-clink", True, {"sound"}),
    "creak": SoundSource("creak", "creaking board", "eeek", True, {"sound"}),
    "hoot": SoundSource("hoot", "owl hoot", "whooo", True, {"sound"}),
}

TRANSFORMS = {
    "map": Transformation("map", "folded map", "a folded map under the cloth", "fwap!", "helpful", {"rattle"}),
    "lantern": Transformation("lantern", "lantern toy", "a little lantern toy", "plink!", "glowing", {"creak", "hoot"}),
    "badge": Transformation("badge", "adventure badge", "a badge with a star on it", "pop!", "brave", {"rattle", "creak", "hoot"}),
}

RESPONSES = {
    "listen": Response("listen", 3, "listened carefully and stayed with the grown-up", "The child listened carefully and stayed with the grown-up."),
    "call": Response("call", 3, "called for the grown-up and waited bravely", "The child called for the grown-up and waited bravely."),
    "torch": Response("torch", 1, "grabbed a torch and ran ahead alone", "The child grabbed a torch and ran ahead alone."),
}

NAMES_GIRL = ["Lina", "Maya", "Nora", "Ella", "Zoe"]
NAMES_BOY = ["Owen", "Finn", "Theo", "Milo", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in THEMES:
        for so in SOUNDS:
            for tr in TRANSFORMS:
                if sound_risk(SOUNDS[so]) and can_transform(SOUNDS[so], TRANSFORMS[tr]) and sensible_responses():
                    combos.append((s, so, tr))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child in jammies that includes the words "relevant" and "disconcert".',
        f"Tell a cautionary adventure where {f['child'].id} hears a strange sound in {f['setting'].label} and stays safe with a grown-up.",
        f"Write a transformation story where a noisy clue becomes a surprise treasure and the child ends happy and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    sound = f["sound"]
    transform = f["transform"]
    grown = f["grownup"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who went exploring in {child.pronoun('possessive')} jammies with a grown-up nearby."),
        ("Why did {0} feel disconcerted?".format(child.id), f"{child.id} felt disconcerted because {sound.label} made a strange {sound.effect} in {setting.label}. The noise was a warning that something might be worth checking carefully."),
        ("What happened at the end?", f"They found {transform.reveal}, and it transformed into a {transform.label}. That made the adventure turn from worrying to wonderful."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What are jammies?", "Jammies are soft clothes people wear for sleeping or resting. They help a child feel cozy at bedtime."),
        ("What should you do when a sound seems worrying?", "Stay with a grown-up and check safely instead of rushing ahead alone. That is the careful choice in an adventure."),
        ("What does transform mean?", "Transform means to change into something different. In stories, that change can make an ordinary thing feel magical."),
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
    lines.append("== (3) World knowledge questions ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world needs a disconcerting sound and a safe transformation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure story world with jammies, caution, sound effects, and transformation.")
    ap.add_argument("--setting", choices=THEMES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    choices = [c for c in combos
               if (args.setting is None or c[0] == args.setting)
               and (args.sound is None or c[1] == args.sound)
               and (args.transform is None or c[2] == args.transform)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, sound, transform = rng.choice(sorted(choices))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    grownup = args.grownup or rng.choice(["mother", "father"])
    return StoryParams(setting, sound, transform, response, name, gender, grownup)


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


CURATED = [
    StoryParams("cave", "rattle", "map", "listen", "Lina", "girl", "mother"),
    StoryParams("attic", "creak", "lantern", "call", "Owen", "boy", "father"),
    StoryParams("forest", "hoot", "badge", "listen", "Maya", "girl", "mother"),
]


ASP_RULES = r"""
sound_risk(S) :- sound(S), disconcerting(S).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(S, So, T) :- setting(S), sound(So), transform(T), sound_risk(So), transform_ok(So, T), sensible(_).
outcome(transformed) :- chosen_transform(T), transform(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in THEMES:
        lines.append(asp.fact("setting", sid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if s.disconcerting:
            lines.append(asp.fact("disconcerting", sid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    for tid, t in TRANSFORMS.items():
        for tag in sorted(t.tags):
            lines.append(asp.fact("transform_ok", tag, tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1.\n#show valid/3."))
    asp_sens = sorted(r for (r,) in asp.atoms(model, "sensible"))
    py_sens = sorted(r.id for r in sensible_responses())
    if asp_sens != py_sens:
        print("MISMATCH sensible responses:", asp_sens, py_sens)
        return 1
    # smoke test generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} valid combinations:")
        for row in asp_valid():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
