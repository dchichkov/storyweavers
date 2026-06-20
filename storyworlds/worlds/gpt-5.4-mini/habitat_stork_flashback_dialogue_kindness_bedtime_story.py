#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/habitat_stork_flashback_dialogue_kindness_bedtime_story.py
==========================================================================================

A small standalone storyworld for a bedtime-style tale about a child, a stork,
a memory from earlier in the day, a kind act, and a soothing ending.

The world is built around:
- a cozy habitat
- a rescued or welcomed stork
- a flashback beat that explains how the evening began
- dialogue that carries the emotional turn
- kindness as the resolving action

The prose is state-driven: physical meters and emotional memes accumulate through
the simulation, and the renderer narrates the consequences of those state changes.
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
class Habitat:
    id: str
    label: str
    evening_sound: str
    shelter: str
    warm_place: str
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
class StorkNeed:
    id: str
    label: str
    reason: str
    risk: str
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
class KindAction:
    id: str
    label: str
    verb: str
    helper: str
    result: str
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


@dataclass
class World:
    habitat: Habitat
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
        clone = World(self.habitat)
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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["warmth"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["calm"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "emotional", _r_relief)]


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime stork story with flashback, dialogue, and kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--habitat", choices=HABITATS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--kindness", choices=KINDNESS_ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def setup(world: World, child: Entity, parent: Entity, stork: Entity, need: StorkNeed) -> None:
    child.memes["love"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"At bedtime, {child.id} and {parent.label_word} sat by the window and listened to the soft night sounds of the {world.habitat.label}."
    )
    world.say(
        f"Near the reeds, a quiet {stork.label} stood still, as if it had found a place that belonged to it."
    )
    world.say(
        f"{child.id} whispered, \"That {stork.label} looks tired.\" {parent.label_word.capitalize()} nodded and said, \"Maybe it needs help finding a safe place to rest.\""
    )
    world.facts["need"] = need.id


def flashback(world: World, child: Entity, stork: Entity, need: StorkNeed) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Earlier that afternoon, {child.id} had seen the {stork.label} on a windy path, looking confused and a little lonely."
    )
    world.say(
        f"The memory came back like a tiny lantern: the bird had been searching for {need.reason}."
    )


def dialogue(world: World, child: Entity, parent: Entity, stork: Entity, need: StorkNeed) -> None:
    child.memes["concern"] += 1
    world.say(
        f'"Can we help it?" {child.id} asked.'
    )
    world.say(
        f'"Yes," said {parent.label_word}. "Kindness is how we answer when someone is lost."'
    )
    world.say(
        f'{child.id} smiled at the {stork.label} and said, "Come with us. We will keep you safe."'
    )
    world.say(
        f"The {stork.label} blinked slowly, and the room felt gentler right away."
    )


def kindness(world: World, child: Entity, parent: Entity, stork: Entity, action: KindAction) -> None:
    child.memes["kindness"] += 1
    parent.memes["pride"] += 1
    stork.meters["comfort"] += 1
    stork.meters["warmth"] += 1
    world.say(
        f"{child.id} brought a soft towel and a shallow bowl of water, and {parent.label_word} helped move everything beside the window."
    )
    world.say(
        f"Then they {action.verb} for the {stork.label}: {action.helper}."
    )
    propagate(world, narrate=False)
    world.say(
        f"The {stork.label} settled in, and {action.result}."
    )


def ending(world: World, child: Entity, parent: Entity, stork: Entity, action: KindAction) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"By the time the moon climbed higher, the {stork.label} was safe and still, tucked into the cozy habitat they had made together."
    )
    world.say(
        f'{parent.label_word.capitalize()} kissed {child.id} goodnight and whispered, "You were very kind today."'
    )
    world.say(
        f'{child.id} looked at the calm {stork.label} one last time and smiled. Outside, the {world.habitat.label} sounded soft and bright, and inside, everyone was ready for sleep.'
    )


def tell(setting: Habitat, need: StorkNeed, action: KindAction, name: str, parent_type: str) -> World:
    world = World(setting)
    child_gender = "girl" if name in GIRL_NAMES else "boy"
    child = world.add(Entity(id=name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    stork = world.add(Entity(id="Stork", kind="character", type="bird", label=setting.stork_label, role="visitor"))
    world.add(Entity(id="habitat", type="place", label=setting.label))
    setup(world, child, parent, stork, need)
    world.para()
    flashback(world, child, stork, need)
    world.para()
    dialogue(world, child, parent, stork, need)
    world.para()
    kindness(world, child, parent, stork, action)
    world.para()
    ending(world, child, parent, stork, action)
    world.facts.update(child=child, parent=parent, stork=stork, action=action, habitat=setting, need=need)
    return world


# Attach a couple of extra attributes after class definition for simplicity.
Habitat.stork_label = "stork"  # type: ignore[attr-defined]


SETTINGS = {
    "pond": Habitat("pond", "pond habitat", "frogs chirped", "reeds", "a nest of soft grass", {"water", "night"}),
    "marsh": Habitat("marsh", "marsh habitat", "the cattails whispered", "tall grass", "a patch of dry moss", {"water", "night"}),
    "garden": Habitat("garden", "garden habitat", "leaves rustled", "a little shed", "a warm blanket nest", {"land", "night"}),
}

HABITATS = SETTINGS

NEEDS = {
    "lost": StorkNeed("lost", "finding its way home", "it was lost after the wind blew hard", "cold and lonely", {"lost", "night"}),
    "tired": StorkNeed("tired", "resting before sunrise", "it was too tired to keep walking", "wobbly and sad", {"tired", "night"}),
    "rain": StorkNeed("rain", "staying dry for the night", "the rain had soaked its feathers", "shivery", {"rain", "night"}),
}

KINDNESS_ACTIONS = {
    "towel": KindAction("towel", "towel help", "offered a towel and a bowl of water", "the towel dried its feathers", "the stork looked calm and grateful", "the towel helped it feel warm and clean", {"kindness", "care"}),
    "nest": KindAction("nest", "nest help", "made a soft nest from grass and blankets", "the nest gave it a warm place to rest", "the stork tucked in with a sleepy sigh", "the nest turned the corner into a bedtime spot", {"kindness", "care"}),
    "light": KindAction("light", "light help", "carried a small lamp to guide it", "the little lamp made the path glow", "the stork found its safe place and settled", "the light showed a gentle path home", {"kindness", "care"}),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Finn", "Theo", "Noah", "Leo", "Ben", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for need in NEEDS:
            for action in KINDNESS_ACTIONS:
                combos.append((setting, need, action))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    habitat: str
    need: str
    kindness: str
    name: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the word "{f["habitat"].label}" and a gentle {f["stork"].label}.',
        f"Tell a bedtime story with a flashback, dialogue, and kindness where {f['child'].id} helps a {f['stork'].label} feel safe.",
        f'Write a cozy story about a {f["stork"].label} in a {f["habitat"].label} with a soft ending and spoken lines.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, stork, action, habitat, need = f["child"], f["parent"], f["stork"], f["action"], f["habitat"], f["need"]
    return [
        ("Who is the story about?", f"It is about {child.id}, {parent.label_word}, and a {stork.label} that needed help."),
        ("Why is there a flashback in the story?", f"It shows what {child.id} saw earlier and explains why the {stork.label} seemed worried. That memory helps the bedtime scene make sense."),
        ("How did they show kindness?", f"They used {action.verb} to help the {stork.label}, and that made the habitat feel safe and cozy."),
        ("How did the story end?", f"It ended with the {stork.label} resting peacefully in the {habitat.label}, while everyone got ready for sleep."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("What is a habitat?", "A habitat is the place where an animal lives and feels at home."),
        ("What is a stork?", "A stork is a tall bird with long legs and a long beak."),
        ("What does kindness mean?", "Kindness means helping gently, being caring, and trying to make someone feel safe."),
        ("What is a flashback?", "A flashback is when a story briefly goes back to something that happened earlier."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pond", "pond", "lost", "nest", "Maya", "mother"),
    StoryParams("marsh", "marsh", "tired", "towel", "Finn", "father"),
    StoryParams("garden", "garden", "rain", "light", "Lily", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not fit the cozy bedtime habitat tale.)"


ASP_RULES = r"""
valid(S, N, K) :- setting(S), need(N), kindness(K).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for n in NEEDS:
        lines.append(asp.fact("need", n))
    for k in KINDNESS_ACTIONS:
        lines.append(asp.fact("kindness", k))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.habitat is None or c[1] == args.habitat)
              and (args.need is None or c[2] == args.need)
              and (args.kindness is None or c[2] == args.kindness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, habitat, need, kindness = None, None, None, None
    setting, habitat, need = rng.choice(sorted(combos))
    kindness = args.kindness or rng.choice(sorted(KINDNESS_ACTIONS))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, habitat, need, kindness, name, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], NEEDS[params.need], KINDNESS_ACTIONS[params.kindness], params.name, params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
