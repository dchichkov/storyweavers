#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spa_kindness_nursery_rhyme.py
==============================================================

A small storyworld about a tiny spa day, where children and helpers use gentle
care, kind words, and simple soothing actions. The tone aims at nursery-rhyme
softness: short, musical sentences, repeated beats, and a clear turn from a
small problem to a kind solution.

The seed words are "spa" and "kindness"; the story is built around those ideas.
A child feels grumpy, another child or helper notices, and the world changes
through patient care: warm water, towels, brushes, soap bubbles, and kind acts.
"""

from __future__ import annotations

import argparse
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
class Item:
    id: str
    label: str
    kind: str
    warm: bool = False
    wet: bool = False
    fragrant: bool = False
    kind_needed: int = 1
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SpaAction:
    id: str
    phrase: str
    gentle: str
    soothe: str
    targets: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Remedy:
    id: str
    phrase: str
    help_text: str
    strength: int
    tags: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    action: str
    remedy: str
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
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, item: Item) -> Item:
        self.items[item.id] = item
        return item

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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.items = copy.deepcopy(self.items)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["upset"] < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["comforted"] += 1
        out.append("__kindness__")
    return out


def _r_spa_relax(world: World) -> list[str]:
    out: list[str] = []
    for item in world.items.values():
        if item.meters["used"] < THRESHOLD:
            continue
        sig = ("spa", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["special"] += 1
        out.append("__spa__")
    return out


CAUSAL_RULES = [Rule("kindness", _r_kindness), Rule("spa", _r_spa_relax)]


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


def setting_line(setting: str) -> str:
    return {
        "spa": "The little spa was tucked behind a blue door, with soft towels and a shiny sink.",
        "garden_spa": "The garden spa smelled of mint, and a tiny fountain made the air sing.",
        "bathroom": "The bathroom was warm and bright, with bubbles waiting in the tub.",
    }.get(setting, "The little spa was warm and bright, with soft towels and a shiny sink.")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for action in ACTIONS:
            for remedy in REMEDIES:
                if action != "scrub" or remedy in {"towel", "bubble", "song"}:
                    combos.append((setting, action, remedy))
    return combos


def tell(setting: str, action: SpaAction, remedy: Remedy,
         hero: str = "Mina", hero_gender: str = "girl",
         helper: str = "Nora", helper_gender: str = "girl",
         parent: str = "mom") -> World:
    world = World()
    child = world.add_entity(Entity(id=hero, kind="character", type=hero_gender, role="hero",
                                    traits=["little", "gentle"]))
    pal = world.add_entity(Entity(id=helper, kind="character", type=helper_gender, role="helper",
                                  traits=["kind", "patient"]))
    grown = world.add_entity(Entity(id="Parent", kind="character", type=parent, role="parent",
                                    label="the parent"))
    bath = world.add_item(Item(id="spa", label="spa room", kind=setting))
    towel = world.add_item(Item(id="towel", label="soft towel", kind="towel", warm=True))
    bowl = world.add_item(Item(id="bowl", label="bubble bowl", kind="bowl", wet=True, fragrant=True))

    world.say(setting_line(setting))
    world.say(f"{hero} was there with {helper}, and both liked the word spa because it sounded like a soft little clap.")
    world.say(f"{hero} wanted to {action.phrase}, but {helper} noticed {hero} looked upset.")
    child.memes["upset"] += 1
    pal.memes["kindness"] += 1
    world.para()
    world.say(f'"Come along," said {helper}, "let us choose a kinder way."')
    world.say(f"{helper} offered {remedy.phrase}, and the little room grew calmer and warmer.")
    if remedy.id in {"towel", "bubble", "song"}:
        bath.meters["used"] += 1
        towel.meters["used"] += 1
        bowl.meters["used"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f"{grown.label_word.capitalize()} smiled and helped, too.")
    world.say(f"Then {hero} tried the {remedy.phrase} with {helper}, and the upset feeling went small.")
    child.memes["joy"] += 1
    child.memes["comforted"] += 1
    pal.memes["joy"] += 1
    world.say(f"The bath stayed tidy, the towels stayed soft, and the spa day ended in a hushy, happy hum.")

    world.facts.update(
        hero=child, helper=pal, parent=grown, setting=setting, action=action,
        remedy=remedy, bath=bath, towel=towel, bowl=bowl
    )
    return world


SETTINGS = {
    "spa": "spa",
    "garden_spa": "garden_spa",
    "bathroom": "bathroom",
}

ACTIONS = {
    "bubble": SpaAction(id="bubble", phrase="blow bubbles", gentle="bubbling", soothe="bubble"),
    "scrub": SpaAction(id="scrub", phrase="scrub too hard", gentle="scrubbing", soothe="towel"),
    "song": SpaAction(id="song", phrase="sing a soft song", gentle="singing", soothe="song"),
}

REMEDIES = {
    "towel": Remedy(id="towel", phrase="a warm towel", help_text="wrapped the child in warmth", strength=2),
    "bubble": Remedy(id="bubble", phrase="a bowl of bubbles", help_text="made the whole room feel playful", strength=1),
    "song": Remedy(id="song", phrase="a kind little song", help_text="turned the worry into a hum", strength=1),
}

CURATED = [
    StoryParams(hero="Mina", hero_gender="girl", helper="Nora", helper_gender="girl",
                parent="mother", action="scrub", remedy="towel", setting="spa"),
    StoryParams(hero="Eli", hero_gender="boy", helper="Mina", helper_gender="girl",
                parent="father", action="bubble", remedy="bubble", setting="bathroom"),
    StoryParams(hero="Luna", hero_gender="girl", helper="Pip", helper_gender="boy",
                parent="mother", action="song", remedy="song", setting="garden_spa"),
]


def explain_rejection(action: SpaAction, remedy: Remedy) -> str:
    return f"(No story: {action.phrase} needs a gentler fix than {remedy.phrase}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny nursery-rhyme spa storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.action and args.remedy:
        if (args.setting or "spa", args.action, args.remedy) not in combos:
            raise StoryError(explain_rejection(ACTIONS[args.action], REMEDIES[args.remedy]))
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, remedy = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Mina", "Luna", "Eli", "Noa"])
    helper = args.helper or rng.choice([n for n in ["Nora", "Pip", "Ivy", "Ola"] if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(hero=hero, hero_gender="girl" if hero in {"Mina", "Luna", "Nora", "Ivy", "Ola"} else "boy",
                       helper=helper, helper_gender="girl" if helper in {"Mina", "Luna", "Nora", "Ivy", "Ola"} else "boy",
                       parent=parent, action=action, remedy=remedy, setting=setting)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a nursery-rhyme style spa story that includes the word "spa" and shows kindness.',
        f"Tell a soft story where {f['hero'].id} feels grumpy at the spa, then {f['helper'].id} helps with a kinder choice.",
        f"Write a gentle story about a tiny spa day where {f['hero'].id} learns kindness from {f['helper'].id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    action, remedy = f["action"], f["remedy"]
    return [
        ("Who is the story about?", f"It is about {hero.id} and {helper.id}, with {parent.label_word} nearby to help."),
        ("What did {0} want to do?".format(hero.id), f"{hero.id} wanted to {action.phrase}, but that was not the kindest choice."),
        ("How did they solve the problem?", f"They chose {remedy.phrase} instead. That softer choice made the spa day calm and kind."),
        ("How did the story end?", "It ended with a happy hush, soft towels, and everyone feeling cared for."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a spa?", "A spa is a place where people wash, rest, and feel cared for with warm water and gentle help."),
        ("What is kindness?", "Kindness means choosing soft words, helpful actions, and care for someone else's feelings."),
        ("Why are towels useful?", "Towels dry wet skin and help a person feel warm again after water or bubbles."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(meters)} memes={dict(memes)} role={e.role}")
    for i in world.items.values():
        meters = {k: v for k, v in i.meters.items() if v}
        lines.append(f"  {i.id:8} (item   ) meters={dict(meters)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
needs_kindness(P) :- upset(P).
gets_soothed(P) :- needs_kindness(P), comfort(C), used(C).
valid(S,A,R) :- setting(S), action(A), remedy(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for r in REMEDIES:
        lines.append(asp.fact("comfort", r))
    lines.append(asp.fact("upset", "child"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as e:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {e}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.action not in ACTIONS or params.remedy not in REMEDIES:
        raise StoryError("Invalid parameters.")
    world = tell(params.setting, ACTIONS[params.action], REMEDIES[params.remedy],
                 hero=params.hero, hero_gender=params.hero_gender,
                 helper=params.helper, helper_gender=params.helper_gender,
                 parent=params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(f"{len(asp_valid_combos())} valid combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                p = resolve_params(args, random.Random(base + i))
            except StoryError as e:
                print(e)
                return
            p.seed = base + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
