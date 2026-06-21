#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ashamed_inner_monologue_folk_tale.py
=====================================================================

A small folk-tale-style storyworld about a child, a mistake, an ashamed inner
monologue, and a kind repair.

Premise
-------
A child in a village does a small wrong thing, feels ashamed, argues with
themselves in inner monologue, then tells the truth and makes amends.

This world is deliberately tiny and classical:
- typed entities with physical meters and emotional memes
- state-driven story beats
- a Python reasonableness gate plus inline ASP twin
- three Q&A sets grounded in the simulated world
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother",
                "grandfather": "grandfather"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    opening: str
    ending: str

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
class Mistake:
    id: str
    action: str
    inner_voice: str
    risk: str
    consequence: str
    clue: str
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
class Repair:
    id: str
    method: str
    effect: str
    ending_image: str
    care_word: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

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


def _r_shame(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["broken"] >= THRESHOLD and not world.fired.intersection({("shame",)}):
        world.fired.add(("shame",))
        child.memes["ashamed"] += 1
        child.memes["fear"] += 0.5
        out.append("__shame__")
    return out


def _r_fear_to_silence(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes["ashamed"] >= THRESHOLD and not world.fired.intersection({("silence",)}):
        world.fired.add(("silence",))
        child.meters["silent"] += 1
        out.append("__silence__")
    return out


CAUSAL_RULES = [Rule("shame", _r_shame), Rule("silence", _r_fear_to_silence)]


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


def predict_repair(world: World, mistake: Mistake) -> dict:
    sim = world.copy()
    _do_mistake(sim, narrate=False)
    return {
        "broken": sim.get("child").meters["broken"],
        "ashamed": sim.get("child").memes["ashamed"],
    }


def _do_mistake(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    item = world.get("item")
    child.meters["broken"] += 1
    item.meters["broken"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, mistake: Mistake, repair: Repair,
         child_name: str = "Mara", child_gender: str = "girl",
         parent_name: str = "Mother", parent_gender: str = "woman",
         helper_name: str = "Old Fox", helper_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["small", "thoughtful"]))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender,
                              role="parent", label="the mother"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender,
                              role="helper", label="the old fox"))
    item = world.add(Entity(id="item", kind="thing", type="thing", label="the loaf"))
    world.facts.update(setting=setting, mistake=mistake, repair=repair,
                       child=child, parent=parent, helper=helper, item=item)

    world.say(
        f"Once, in {setting.place}, there lived a small child named {child.id}. "
        f"{setting.opening}"
    )
    world.say(
        f"{child.id} loved the warm smell of the village kitchen, but one day "
        f"{child.pronoun()} saw {item.label} left cooling on the sill."
    )
    world.say(
        f'In {child.id}\'s mind a little voice whispered, "{mistake.inner_voice}"'
    )

    world.para()
    child.memes["desire"] += 1
    child.memes["guilt"] += 0.5
    world.say(
        f"{child.id} reached out and did it anyway: {mistake.action}. "
        f"{mistake.clue}"
    )
    _do_mistake(world)
    world.say(
        f"{mistake.risk}. {child.id} stared at the damage and felt {mistake.consequence}."
    )

    world.para()
    if child.memes["ashamed"] >= THRESHOLD:
        world.say(
            f'Inside, {child.id} thought, "{child.id} should not hide. '
            f"{child.id} must tell the truth."
        )
    world.say(
        f"{child.id} walked to {parent.id} and confessed what happened."
    )
    child.memes["courage"] += 1
    parent.memes["care"] += 1

    world.para()
    world.say(
        f"{parent.id} listened kindly and did not scold {child.pronoun('object')} away."
    )
    world.say(
        f"Together they used {repair.method}, and {repair.effect}."
    )
    child.meters["broken"] = 0.0
    item.meters["broken"] = 0.0
    child.memes["ashamed"] = 0.0
    child.memes["relief"] += 1
    child.memes["love"] += 1

    world.para()
    world.say(
        f"At the end, {repair.ending_image}, and {setting.ending}."
    )
    if helper_name:
        helper.memes["wisdom"] += 1
        world.say(f"Even {helper.id} nodded, pleased by the honest child.")

    world.facts["outcome"] = "repaired"
    return world


SETTINGS = {
    "village": Setting(
        "village",
        "a little village by the green woods",
        "The chimneys puffed softly, and every door seemed to know every other door.",
        "The village went on shining under the evening stars.",
    ),
    "cottage": Setting(
        "cottage",
        "a small cottage at the edge of the hill",
        "A warm hearth glowed inside, and the wind sang over the roof.",
        "The cottage rested happily beneath the moon.",
    ),
    "market": Setting(
        "market",
        "a busy market lane",
        "Baskets of apples and cloth stalls lined the lane, and everyone greeted everyone else.",
        "The market quieted down when twilight came.",
    ),
}

MISTAKES = {
    "spilled_flour": Mistake(
        "spilled_flour",
        "spilled a whole bowl of flour across the floor",
        "Maybe nobody will notice if I stay very still.",
        "The white flour made a big mess on the boards",
        "and now the kitchen looked untidy",
        "A puff of flour rose like a tiny cloud.",
        tags={"kitchen", "mess"},
    ),
    "dropped_berries": Mistake(
        "dropped_berries",
        "dropped the berry basket and bruised the fruit",
        "It was only a little basket; perhaps I can hide it.",
        "The berries rolled away under the table",
        "and the fruit looked sad and squashed",
        "Red berries spun over the stones.",
        tags={"fruit", "mess"},
    ),
    "spilt_milk": Mistake(
        "spilt_milk",
        "spilled the milk pail on the doorstep",
        "If I am quiet, maybe the puddle will disappear.",
        "The milk ran in a pale stream across the step",
        "and the doorstep was slippery and sticky",
        "A white trail spread under the door.",
        tags={"milk", "mess"},
    ),
}

REPAIRS = {
    "broom": Repair(
        "broom",
        "swept the flour into a neat pan",
        "the floor was clean again after a few careful sweeps",
        "the floor shone clean by the fire",
        "cleanliness",
        tags={"broom"},
    ),
    "cloth": Repair(
        "cloth",
        "wiped the berries from the boards with a damp cloth",
        "the sticky juice was gone and the boards looked tidy again",
        "the basket sat filled with the rescued berries",
        "care",
        tags={"cloth"},
    ),
    "rag": Repair(
        "rag",
        "mopped the milk with a soft rag and sprinkled sand for safety",
        "the step was safe to walk on again",
        "the doorstep was dry and clear",
        "care",
        tags={"rag", "sand"},
    ),
}

TRAITS = ["careful", "curious", "gentle", "brave", "thoughtful", "quiet"]
CHILD_NAMES = ["Mara", "Sera", "Nina", "Tova", "Lina", "Elin"]
HELPERS = [("Old Fox", "man"), ("Grandmother", "woman"), ("Aunt Reed", "woman"), ("Old Bear", "man")]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mistake: str
    repair: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    helper_name: str
    helper_gender: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, m in MISTAKES.items():
            for rid, r in REPAIRS.items():
                if sid == "market" and mid == "spilt_milk":
                    combos.append((sid, mid, rid))
                elif sid == "cottage" and mid in {"spilled_flour", "spilt_milk"}:
                    combos.append((sid, mid, rid))
                elif sid == "village" and mid in {"spilled_flour", "dropped_berries"}:
                    combos.append((sid, mid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld with ashamed inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "woman", "man"])
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
              and (args.mistake is None or c[1] == args.mistake)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mistake, repair = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    parent_gender = args.parent or rng.choice(["woman", "man"])
    parent_name = "Mother" if parent_gender == "woman" else "Father"
    helper_name, helper_gender = rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, mistake, repair, child_name, child_gender,
                       parent_name, parent_gender, helper_name, helper_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the word "ashamed" and an inner monologue after a small mistake.',
        f"Tell a gentle village story where {f['child'].id} makes a mistake, feels ashamed, speaks to themselves in their head, and then tells the truth.",
        f"Write a short folk-tale style story about a child in {f['setting'].place} who does something wrong, confesses, and makes amends.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    mistake = f["mistake"]
    repair = f["repair"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, a small child who made a mistake and then told the truth."),
        ("What did {0} think in their head?".format(child.id),
         f"{child.id} had an ashamed inner monologue. {mistake.inner_voice} and then another thought told {child.pronoun('object')} to confess."),
        ("What happened after {0} made the mistake?".format(child.id),
         f"{child.id} saw the mess, felt ashamed, and went to {parent.id} to confess. That brave choice led to a kind repair instead of hiding."),
        ("How was the problem fixed?",
         f"They used {repair.method}, and {repair.effect}. The world became tidy and safe again."),
        ("How did the story end?",
         f"It ended with the damage repaired and {child.id} feeling relieved and loved. The village stayed warm and calm in the evening."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mistake"].tags) | set(world.facts["repair"].tags)
    out = []
    KNOWLEDGE = {
        "mess": [("What is a mess?", "A mess is when something gets scattered or dirty and needs cleaning up.")],
        "broom": [("What is a broom for?", "A broom sweeps dust or flour into a pile so the floor can be cleaned.")],
        "cloth": [("What is a cloth for?", "A cloth can wipe spills and sticky things off a table or floor.")],
        "rag": [("What is a rag for?", "A rag can soak up wet spills and help dry a surface.")],
        "sand": [("Why can sand help after a spill?", "Sand can help keep a wet floor from being slippery while it dries.")],
    }
    for key in ["mess", "broom", "cloth", "rag", "sand"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("village", "spilled_flour", "broom", "Mara", "girl", "Mother", "woman", "Grandmother", "woman", "thoughtful"),
    StoryParams("cottage", "spilt_milk", "rag", "Sera", "girl", "Father", "man", "Old Fox", "man", "quiet"),
    StoryParams("village", "dropped_berries", "cloth", "Nina", "girl", "Mother", "woman", "Aunt Reed", "woman", "gentle"),
]


def explain_rejection(setting: Setting, mistake: Mistake, repair: Repair) -> str:
    return ("(No story: this combination does not make a believable tiny folk-tale problem/repair.) "
            "Choose a setting and mistake that fit the repair well.")


def valid_story(params: StoryParams) -> bool:
    return (params.setting, params.mistake, params.repair) in valid_combos()


ASP_RULES = r"""
valid(S, M, R) :- setting(S), mistake(M), repair(R), compatible(S, M, R).
shame :- broken(child).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISTAKES:
        lines.append(asp.fact("mistake", mid))
    for rid in REPAIRS:
        lines.append(asp.fact("repair", rid))
    for s, m, r in valid_combos():
        lines.append(asp.fact("compatible", s, m, r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mistake=None, repair=None, name=None, gender=None, parent=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke-generated story.")
    except Exception as e:
        print(f"SMOKE FAILED: {e}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISTAKES[params.mistake], REPAIRS[params.repair],
                 params.child_name, params.child_gender, params.parent_name, params.parent_gender,
                 params.helper_name, params.helper_gender)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=[QAItem(q, a) for q, a in story_qa(world)],
                       world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
                       world=world)


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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(args.n * 40, 40):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
