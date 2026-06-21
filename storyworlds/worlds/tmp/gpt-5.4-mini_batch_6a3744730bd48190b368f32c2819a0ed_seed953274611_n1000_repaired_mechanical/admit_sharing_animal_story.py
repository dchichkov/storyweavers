#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/admit_sharing_animal_story.py
=============================================================

A small animal storyworld about sharing, admitting a mistake, and making
amends. A child animal wants a treat, keeps it, admits the mistake, and then
shares so the friendship is repaired.

The world model uses typed entities with physical meters and emotional memes,
forward rules, a reasonableness gate, and an inline ASP twin.
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
    type: str = "animal"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "he", "male", "rabbit", "fox", "dog", "bear", "mouse", "lion", "cat"}
        female = {"girl", "she", "female", "deer", "bird", "duck", "squirrel"}
        t = self.type
        if t in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if t in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class CharacterSpec:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class TreatSpec:
    id: str
    label: str
    phrase: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SharingSpec:
    id: str
    title: str
    verb: str
    offering: str
    response: str
    repair: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    animal: str
    friend: str
    treat: str
    sharing: str
    setting: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["kept"] < THRESHOLD:
            continue
        sig = ("sad", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        friend = world.get("friend")
        friend.memes["hurt"] += 1
        e.memes["guilt"] += 1
        out.append("__sad__")
    return out


def _r_admit(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["admit"] < THRESHOLD:
            continue
        sig = ("admit", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        friend = world.get("friend")
        friend.memes["soften"] += 1
        e.memes["relief"] += 1
        out.append("__admit__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["share"] < THRESHOLD:
        return out
    sig = ("share", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["kind"] += 1
    friend.memes["kind"] += 1
    hero.meters["treats_shared"] += 1
    friend.meters["treats_shared"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("sad", "feeling", _r_sad), Rule("admit", "social", _r_admit), Rule("share", "social", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in ANIMALS:
        for f in ANIMALS:
            if a == f:
                continue
            for t in TREATS:
                if t.id in {"berry", "carrot"}:
                    combos.append((a.id, f.id, t.id))
    return combos


def reasonable_sharing(treat: TreatSpec) -> bool:
    return treat.id in {"berry", "carrot", "cookie"}


def admit_possible(animal: CharacterSpec, friend: CharacterSpec) -> bool:
    return animal.type != friend.type or animal.id != friend.id


def setting_line(setting: str) -> str:
    return {
        "forest": "The forest was soft and green, with a mossy log and a clear little path.",
        "pond": "The pond was still and blue, with reeds swaying in the breeze.",
        "meadow": "The meadow was wide and sunny, with flowers bobbing like tiny bells.",
    }[setting]


def predict_repair(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").memes["share"] += 1
    propagate(sim, narrate=False)
    return {"softened": sim.get("friend").memes["soften"] >= THRESHOLD, "kind": sim.get("friend").memes["kind"]}


def tell(animal: CharacterSpec, friend: CharacterSpec, treat: TreatSpec, sharing: SharingSpec, setting: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=animal.type, label=animal.label, traits=animal.traits))
    pal = world.add(Entity(id="friend", kind="character", type=friend.type, label=friend.label, traits=friend.traits))
    world.add(Entity(id="treat", label=treat.label, type="thing"))
    hero.memes["want"] = 1
    hero.memes["kept"] = 0
    pal.memes["hope"] = 1
    world.say(f"In the {setting}, {animal.id} found {treat.phrase}.")
    world.say(f"{animal.id} and {friend.id} were playing together, and the snack smelled so sweet.")
    world.say(setting_line(setting))
    world.para()
    world.say(f"{animal.id} wanted to keep it all for {animal.pronoun('object')}, even though {friend.id} was nearby.")
    hero.memes["kept"] += 1
    hero.memes["admit"] += 1
    propagate(world, narrate=False)
    world.say(f"{friend.id} looked sad and quiet.")
    world.say(f"Then {animal.id} decided to admit the mistake.")
    world.para()
    world.say(f"{animal.id} said, \"I was wrong. I should share.\"")
    hero.memes["share"] += 1
    propagate(world, narrate=False)
    world.say(f"So {animal.id} shared {treat.phrase} with {friend.id}.")
    world.say(f"{friend.id} smiled, and the two animals sat side by side to finish it together.")
    world.say(f"That was the best part of the day: a full belly, a kind heart, and a friend who felt better.")
    world.facts.update(hero=hero, friend=pal, treat=treat, sharing=sharing, setting=setting, admitted=True)
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "admit" and shows sharing.',
        f"Tell a gentle story where {f['hero'].id} admits a mistake and then shares {f['treat'].label} with a friend.",
        f'Write a short animal story about a snack, a sad friend, and a happy share at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What did the main animal admit?",
            answer=f"{f['hero'].id} admitted that {f['hero'].id} had kept the treat instead of sharing it. After that, the animal told the truth and tried to make it right."
        ),
        QAItem(
            question="How did the story get better?",
            answer=f"{f['hero'].id} shared {f['treat'].phrase} with {f['friend'].id}. That made the friend feel happy again, because sharing turned the trouble into a kind moment."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with both animals sitting together and enjoying the treat. The mistake was fixed, and their friendship felt warm again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Why should friends share treats?",
            answer="Sharing helps everyone feel included. It also keeps one friend from feeling left out or sad."
        ),
        QAItem(
            question="What does it mean to admit something?",
            answer="To admit something means to tell the truth about a mistake or a choice you made. It is honest and can help fix a problem."
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"  {e.id:8} ({e.kind:7}) meters={meters} memes={memes}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


ANIMALS = [
    CharacterSpec(id="bunny", type="rabbit", label="bunny", traits=["small", "quick"]),
    CharacterSpec(id="fox", type="fox", label="fox", traits=["bright", "fast"]),
    CharacterSpec(id="bear", type="bear", label="bear", traits=["gentle", "big"]),
    CharacterSpec(id="duck", type="duck", label="duck", traits=["silly", "happy"]),
]
TREATS = [
    TreatSpec(id="berry", label="berries", phrase="a bunch of red berries", plural=True),
    TreatSpec(id="carrot", label="carrot", phrase="a crunchy carrot", plural=False),
    TreatSpec(id="cookie", label="cookie", phrase="a tiny cookie", plural=False),
]
SHARINGS = {
    "share": SharingSpec(id="share", title="sharing", verb="share", offering="share it", response="feels better", repair="shared", tags={"share", "admit"}),
}
SETTINGS = ["forest", "pond", "meadow"]


def explain_rejection(treat: TreatSpec) -> str:
    return f"(No story: the treat {treat.label} does not fit the sharing-mistake pattern well enough.)"


def explain_params(args: argparse.Namespace) -> str:
    return "(No story: the chosen options do not describe a small sharing story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about admitting and sharing.")
    ap.add_argument("--animal", choices=[a.id for a in ANIMALS])
    ap.add_argument("--friend", choices=[a.id for a in ANIMALS])
    ap.add_argument("--treat", choices=[t.id for t in TREATS])
    ap.add_argument("--sharing", choices=list(SHARINGS))
    ap.add_argument("--setting", choices=SETTINGS)
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
    animals = {a.id: a for a in ANIMALS}
    treats = {t.id: t for t in TREATS}
    if args.treat and not reasonable_sharing(treats[args.treat]):
        raise StoryError(explain_rejection(treats[args.treat]))
    a = args.animal or rng.choice(list(animals))
    f = args.friend or rng.choice([x for x in animals if x != a])
    if a == f:
        raise StoryError("(No story: the animal and friend must be different.)")
    treat = args.treat or rng.choice([t.id for t in TREATS if reasonable_sharing(t)])
    sharing = args.sharing or "share"
    setting = args.setting or rng.choice(SETTINGS)
    return StoryParams(animal=a, friend=f, treat=treat, sharing=sharing, setting=setting)


def generate(params: StoryParams) -> StorySample:
    animals = {a.id: a for a in ANIMALS}
    treats = {t.id: t for t in TREATS}
    sharing = SHARINGS.get(params.sharing)
    if sharing is None:
        raise StoryError(f"(No story: unknown sharing mode '{params.sharing}'.)")
    if params.animal not in animals or params.friend not in animals:
        raise StoryError("(No story: unknown animal choice.)")
    if params.treat not in treats:
        raise StoryError("(No story: unknown treat choice.)")
    world = tell(animals[params.animal], animals[params.friend], treats[params.treat], sharing, params.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


ASP_RULES = r"""
animal(X) :- animal_id(X).
valid(A,B,T,S) :- animal(A), animal(B), A != B, treat(T), sharing(S), good_treat(T).
good_treat(berry).
good_treat(carrot).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal_id", a.id))
    for t in TREATS:
        lines.append(asp.fact("treat", t.id))
        if reasonable_sharing(t):
            lines.append(asp.fact("good_treat", t.id))
    for s in SHARINGS:
        lines.append(asp.fact("sharing", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP/Python valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(animal=None, friend=None, treat=None, sharing=None, setting=None), random.Random(1)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams(animal="bunny", friend="fox", treat="berry", sharing="share", setting="forest"),
    StoryParams(animal="duck", friend="bear", treat="carrot", sharing="share", setting="pond"),
    StoryParams(animal="fox", friend="duck", treat="berry", sharing="share", setting="meadow"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
