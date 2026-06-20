#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/stub_repetition_quest_moral_value_nursery_rhyme.py
===================================================================================

A tiny storyworld for a nursery-rhyme-style quest built around repetition, a
small search, and a moral value. A child looks for a missing stubby wooden
toy, meets a few little obstacles, repeats a refrain while searching, and
learns a gentle lesson about patience and sharing.

The domain is intentionally small and classical:
- a child
- a helper or sibling
- a quest object
- a few places
- one moral ending

The story state drives the prose: the search progresses by places, the child
grows from worry to relief, and the ending image proves what changed.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
    opening: str
    ending: str

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
class Quest:
    id: str
    title: str
    refrain: str
    search_line: str
    found_line: str
    moral: str
    path: list[str] = field(default_factory=list)

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
class MoralValue:
    id: str
    label: str
    note: str
    helper_action: str

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["missing"] < THRESHOLD or ("worry", "child") in world.fired:
        return out
    world.fired.add(("worry", "child"))
    child.memes["worry"] += 1
    out.append("__worry__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.meters["missing"] < THRESHOLD or child.meters["searched"] >= THRESHOLD:
        return out
    if child.meters["searched"] < len(QUESTS[world.facts["quest"].id].path):
        child.meters["searched"] += 1
        helper.memes["help"] += 1
        out.append("__search__")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    quest = world.facts["quest"]
    if child.meters["searched"] >= len(quest.path) and child.meters["found"] < THRESHOLD:
        child.meters["found"] += 1
        child.meters["missing"] = 0.0
        child.memes["relief"] += 1
        out.append("__found__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("search", _r_search), Rule("found", _r_found)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def search_path(setting: Setting, quest: Quest) -> list[str]:
    return quest.path if quest.path else ["under the bed", "behind the chair", "by the window"]


def tell(setting: Setting, quest: Quest, moral: MoralValue,
         child_name: str = "Mimi", child_gender: str = "girl",
         helper_name: str = "Bobo", helper_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    stub = world.add(Entity(id="stub", type="thing", label="stub"))
    world.facts["quest"] = quest
    world.facts["setting"] = setting
    world.facts["moral"] = moral
    world.facts["stub"] = stub

    child.meters["missing"] = 1.0
    helper.memes["kindness"] = 1.0

    world.say(
        f"Little {child.id} went a-tip and a-tap, in {setting.scene} so bright."
        f" {setting.opening}"
    )
    world.say(
        f'"{quest.refrain}" sang {child.id}, and {helper.id} replied, '
        f'"I will help you search tonight."'
    )
    world.say(
        f"But the stub was not in the first sweet place, nor the second place, nor the little third place."
    )

    for place in search_path(setting, quest):
        world.para()
        child.meters["searched"] += 1
        world.say(f"They peeped {place}, and still no stub appeared.")
        if child.meters["searched"] < len(search_path(setting, quest)):
            world.say(f'"{quest.refrain}" said {child.id}, soft and near.')

    propagate(world, narrate=False)
    world.para()
    world.say(
        f"At last, {helper.id} found the stub {quest.found_line}, tucked where the smallest toy could hide."
    )
    world.say(
        f"{child.id} laughed with delight and tucked the stub into {child.pronoun('possessive')} hands."
    )
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.para()
    world.say(
        f"{moral.helper_action.capitalize()}, and {child.id} learned the moral of the day: "
        f"{moral.note}. {setting.ending}"
    )
    world.facts.update(child=child, helper=helper, quest=quest, setting=setting, moral=moral, outcome="found")
    return world


SETTINGS = {
    "nursery": Setting("nursery", "the nursery with a soft blue rug", "The lamp was warm, and the room was still.", "After that, the nursery felt cozy and kind."),
    "playroom": Setting("playroom", "the playroom with painted stars", "The cushions were piled up like little hills.", "After that, the playroom felt tidy and bright."),
    "attic": Setting("attic", "the attic with old trunks", "Dust motes danced in the sunbeam.", "After that, the attic seemed less lonely."),
}

QUESTS = {
    "bedtime": Quest("bedtime", "The Stubby Search", "Where, oh where, is the stub?", "under the bed", "beside an old sock", ["be patient", "look carefully", "ask kindly"]),
    "toybox": Quest("toybox", "The Little Treasure Hunt", "Where, oh where, is the stub?", "in the toybox", "beneath a felt frog", ["share the search", "keep trying", "speak gently"]),
    "blanket": Quest("blanket", "The Hidden Little Stub", "Where, oh where, is the stub?", "under the blanket", "near a pillow fort", ["use kind words", "help each other", "do not rush"]),
}

MORALS = {
    "patience": MoralValue("patience", "patience", "patient hearts find what hurried hands miss", "kindness made the search easier"),
    "sharing": MoralValue("sharing", "sharing", "sharing and helping make a small quest feel light", "sharing kept nobody lonely"),
    "care": MoralValue("care", "care", "careful eyes and kind words bring good endings", "care helped the stub come home"),
}

GIRL_NAMES = ["Mimi", "Lulu", "Nina", "Tia", "Ruby"]
BOY_NAMES = ["Bobo", "Pip", "Ollie", "Toby", "Remy"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, q, m) for s in SETTINGS for q in QUESTS for m in MORALS]


@dataclass
@dataclass
class StoryParams:
    setting: str
    quest: str
    moral: str
    child_name: str
    child_gender: str
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
    ap = argparse.ArgumentParser(description="Nursery-rhyme quest storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.moral is None or c[2] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, moral = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(setting, quest, moral, child_name, child_gender, helper_name, helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story that repeats "{f["quest"].refrain}" while a child looks for a stub.',
        f"Tell a gentle quest story where {f['child'].id} searches {f['setting'].scene} and learns {f['moral'].label}.",
        "Write a short rhyming story with a repeated line, a missing little toy, and a kindly ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, quest, moral = f["child"], f["helper"], f["quest"], f["moral"]
    return [
        QAItem(
            question="What was the child looking for?",
            answer="The child was looking for the stub. It was the little quest object that had gone missing."
        ),
        QAItem(
            question="Who helped with the search?",
            answer=f"{helper.id} helped with the search. {helper.id} kept looking until the stub was found."
        ),
        QAItem(
            question="What did the repeated line do in the story?",
            answer=f'It gave the story a singing, nursery-rhyme feel. The line "{quest.refrain}" came back again and again while the search went on.'
        ),
        QAItem(
            question="What did the child learn at the end?",
            answer=f"The child learned about {moral.label}. {moral.note.capitalize()}."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search or mission to find something or reach a goal. In stories, a quest gives the characters a reason to keep going."
        ),
        QAItem(
            question="Why do stories repeat a line in nursery rhyme style?",
            answer="Repeating a line makes a story feel sing-song and easy to remember. It also gives the listener a cozy pattern to enjoy."
        ),
        QAItem(
            question="What does patience mean?",
            answer="Patience means waiting calmly and keeping on without getting too upset. Patient characters try again instead of giving up too quickly."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Q, M) :- setting(S), quest(Q), moral(M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for m in MORALS:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import storyworlds.asp as aspmod  # noqa: F401
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, moral=None, name=None, helper=None, gender=None, helper_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        QUESTS[params.quest],
        MORALS[params.moral],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
    )
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


def tell(setting: Setting, quest: Quest, moral: MoralValue,
         child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    stub = world.add(Entity(id="stub", type="thing", label="stub"))
    child.meters["missing"] = 1.0
    quest.path = ["under the bed", "behind the chair", "by the window"]
    world.facts.update(child=child, helper=helper, quest=quest, setting=setting, moral=moral, stub=stub)

    world.say(f"{setting.scene.capitalize()} held a little hush, and {child.id} began a quest.")
    world.say(f'"{quest.refrain}" sang {child.id}, and {helper.id} joined the tune.')

    for i, place in enumerate(quest.path):
        world.para()
        world.say(f"They searched {place}, but the stub stayed hidden.")
        if i < len(quest.path) - 1:
            world.say(f'"{quest.refrain}" sang {child.id} once more, soft as rain.')

    child.meters["searched"] = float(len(quest.path))
    child.meters["found"] = 1.0
    child.meters["missing"] = 0.0
    child.memes["joy"] += 1
    child.memes["lesson"] += 1

    world.para()
    world.say(f"At last, {helper.id} found the stub {quest.found_line}.")
    world.say(f"{child.id} smiled, held it close, and thanked {helper.id}.")
    world.para()
    world.say(f"{moral.helper_action.capitalize()}, and {child.id} learned that {moral.note}.")
    world.say(setting.ending)
    return world


CURATED = [
    StoryParams("nursery", "bedtime", "patience", "Mimi", "girl", "Bobo", "boy"),
    StoryParams("playroom", "toybox", "sharing", "Pip", "boy", "Lulu", "girl"),
    StoryParams("attic", "blanket", "care", "Ruby", "girl", "Ollie", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for s, q, m in asp_valid_combos():
            print(f"  {s:8} {q:10} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and the stub ({p.setting}, {p.quest}, {p.moral})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
