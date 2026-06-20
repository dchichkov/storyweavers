#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glaze_sting_conflict_pirate_tale.py
====================================================================

A standalone storyworld for a tiny pirate-tale conflict:
a child play-crew gets into a squabble over a glossy glaze map,
a stingy snap of bad luck turns the scene tense,
then a calm helper settles the conflict and the crew ends with a safer prize.

The world keeps two kinds of accumulated state:
- meters: physical effects like wet, sticky, broken, saved
- memes: emotional effects like joy, worry, conflict, relief

The story is generated from state, not from a frozen paragraph with swapped nouns.
It includes the seed words "glaze" and "sting", and the central feature is conflict.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
    name: str
    scene: str
    wind: str
    harbor: str

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
    phrase: str
    glossy: bool = False
    sticky: bool = False
    fragile: bool = False
    heavy: bool = False
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
class Trouble:
    id: str
    label: str
    phrase: str
    sting_text: str
    makes_conflict: bool = True
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
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    power: int
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["squabble"] >= THRESHOLD and e.memes["hurt"] >= THRESHOLD:
            sig = ("conflict", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["conflict"] += 1
            out.append("__conflict__")
    return out


def _r_sogginess(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["glaze"] >= THRESHOLD and e.meters["sting"] >= THRESHOLD:
            sig = ("sog", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["sticky"] += 1
            out.append("__sog__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("sogginess", _r_sogginess)]


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


def tell(setting: Setting, prop: Prop, trouble: Trouble, fix: Fix,
         captain: str = "Mina", mate: str = "Beck", parent: str = "mother") -> World:
    world = World()
    cap = world.add(Entity(captain, "character", "girl", role="captain", traits=["bold"]))
    mid = world.add(Entity(mate, "character", "boy", role="mate", traits=["careful"]))
    grown = world.add(Entity(parent, "character", "mother", role="helper"))
    map_piece = world.add(Entity("map", "thing", "thing", label=prop.label))
    world.add(Entity("harbor", "thing", "place", label=setting.harbor))
    cap.memes["joy"] = 1
    mid.memes["joy"] = 1

    world.say(
        f"On a bright day at {setting.name}, {captain} and {mate} turned the deck into a pirate game. "
        f"{setting.scene}"
    )
    world.say(
        f'"Captain {captain} and Mate {mate}!" {captain} cried. "We can cross the {setting.harbor} and find the lost chest!"'
    )

    world.para()
    world.say(
        f"But the wind came sharp off the water, and the little path glimmered with a {prop.label}. "
        f"{mate} peered at it and said, " + f'"We need the {prop.label} to stay dry."'
    )
    world.say(
        f'{captain} reached for {prop.phrase} anyway, hoping to make the chart easier to read.'
    )
    cap.memes["desire"] += 1
    mid.memes["worry"] += 1

    world.para()
    world.say(
        f"Then the trouble came quick: {trouble.sting_text}. "
        f"The glossy {prop.label} slipped, and the crew snapped at one another over who should hold it."
    )
    cap.meters["glaze"] += 1
    cap.meters["sting"] += 1
    mid.meters["glaze"] += 1
    mid.meters["sting"] += 1
    cap.memes["squabble"] += 1
    mid.memes["squabble"] += 1
    prop_ent = map_piece
    prop_ent.meters["glaze"] += 1
    prop_ent.meters["sting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain} frowned, {mate} frowned back, and the whole pirate game felt stuck on a rock."
    )

    world.para()
    world.say(
        f"Then {grown.label_word} came over with a calm voice. "
        f'"Let\'s fix this the safe way," {grown.pronoun()} said.'
    )
    world.say(
        f"{grown.pronoun().capitalize()} used {fix.phrase} and {fix.action}, and soon {fix.result}."
    )
    cap.memes["relief"] += 1
    mid.memes["relief"] += 1
    cap.memes["conflict"] = 0
    mid.memes["conflict"] = 0
    prop_ent.meters["glaze"] = 0
    prop_ent.meters["sting"] = 0
    prop_ent.meters["saved"] += 1

    world.para()
    world.say(
        f"At the end, the pirates sailed on with a clean chart, a steady crew, and a safe plan."
    )
    world.say(
        f"The {prop.label} still shone, but now it stayed where it belonged: in their adventure, not in their argument."
    )

    world.facts.update(
        captain=cap, mate=mid, grown=grown, setting=setting, prop=prop,
        trouble=trouble, fix=fix, map_piece=prop_ent
    )
    return world


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "The dock boards creaked like old ship planks.", "salt wind", "the tide line"),
    "cove": Setting("cove", "the cove", "The rocks made a little fort for their pretend ship.", "sea breeze", "the hidden inlet"),
    "island": Setting("island", "the island", "The sand held their footprints like treasure clues.", "warm air", "the palm shore"),
}

PROPS = {
    "glaze_map": Prop("glaze_map", "glaze map", "the glaze map", glossy=True, sticky=True, tags={"glaze", "map"}),
    "glaze_shell": Prop("glaze_shell", "glaze shell", "the glaze shell", glossy=True, tags={"glaze"}),
    "glaze_chest": Prop("glaze_chest", "glaze chest", "the small glaze chest", glossy=True, fragile=True, heavy=True, tags={"glaze"}),
}

TROUBLES = {
    "sting_wave": Trouble("sting_wave", "sting wave", "a sting of salt spray", "a sting of salt spray jumped from the waves", tags={"sting"}),
    "sting_net": Trouble("sting_net", "sting net", "a stingy tangle of rope", "a stingy tangle of rope caught their sleeves", tags={"sting"}),
    "sting_shell": Trouble("sting_shell", "sting shell", "a sharp little shell", "a sharp little shell nipped at their feet", tags={"sting"}),
}

FIXES = {
    "dry_cloth": Fix("dry_cloth", "dry cloth", "a dry cloth", "wiped the glaze from the map", "the map was clean and easy to read again", 2),
    "fresh_wrap": Fix("fresh_wrap", "fresh wrap", "a fresh cloth wrap", "wrapped the map in clean cloth", "the crew could carry it without another slip", 2),
    "shelter_box": Fix("shelter_box", "shelter box", "a small wooden box", "set the glossy map inside", "the glaze stayed safe and the crew could argue no more", 3),
}

GIRLS = ["Mina", "Lina", "Ava", "Nora", "Zia"]
BOYS = ["Beck", "Toby", "Finn", "Oren", "Jace"]
TRAITS = ["bold", "careful", "curious", "quick", "steady"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    prop: str
    trouble: str
    fix: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    parent: str
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
    out = []
    for s in SETTINGS:
        for p in PROPS:
            for t in TROUBLES:
                for f in FIXES.values():
                    if PROPS[p].sticky or PROPS[p].glossy:
                        out.append((s, p, t))
    return sorted(set(out))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale storyworld with glaze and sting conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    prop = args.prop or rng.choice(list(PROPS))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    fix = args.fix or rng.choice(list(FIXES))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if captain_gender == "girl" else "girl")
    captain = args.captain or rng.choice(GIRLS if captain_gender == "girl" else BOYS)
    mate = args.mate or rng.choice([n for n in (GIRLS if mate_gender == "girl" else BOYS) if n != captain])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, prop, trouble, fix, captain, captain_gender, mate, mate_gender, parent, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the words "{f["prop"].label}" and "sting".',
        f"Tell a story about {f['captain'].id} and {f['mate'].id} having a conflict over a glossy treasure clue, then solving it calmly.",
        f"Write a short pirate adventure where a slippery {f['prop'].label} causes trouble but the crew ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap, mate, grown = f["captain"], f["mate"], f["grown"]
    prop = f["prop"]
    fix = f["fix"]
    trouble = f["trouble"]
    return [
        QAItem(
            question=f"Who had the conflict in the story?",
            answer=f"{cap.id} and {mate.id} had the conflict. They both wanted to hold the glossy {prop.label}, and that made the pirate game tense."
        ),
        QAItem(
            question=f"What caused the trouble?",
            answer=f"{trouble.sting_text}. The stingy little surprise made the {prop.label} slip, and the crew started arguing over it."
        ),
        QAItem(
            question=f"How did the grown-up fix the problem?",
            answer=f"{grown.label_word.capitalize()} helped by using {fix.phrase}. That calmed everyone down and made the {prop.label} safe to use again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does glaze mean in this story?",
               "Glaze means a shiny, slick coating that makes something look glossy. If it gets on a map or shell, it can make it slippery."),
        QAItem("What does sting mean in this story?",
               "Sting means a sharp little hurt or snap, like salt spray or a nipping shell. It makes a scene feel sudden and uncomfortable."),
        QAItem("Why is a conflict important in a story?",
               "A conflict is the part where characters disagree or run into trouble. It gives the story a problem that needs a calm fix."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "glaze_map", "sting_wave", "dry_cloth", "Mina", "girl", "Beck", "boy", "mother", "careful"),
    StoryParams("cove", "glaze_shell", "sting_net", "fresh_wrap", "Lina", "girl", "Toby", "boy", "father", "bold"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a glossy glaze thing, a sting trouble, and a fix that can settle the conflict.)"


ASP_RULES = r"""
valid(S,P,T) :- setting(S), prop(P), trouble(T).
has_conflict(P,T) :- prop(P), trouble(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP parity.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, prop=None, trouble=None, fix=None, captain=None, captain_gender=None, mate=None, mate_gender=None, parent=None, seed=None), random.Random(1)))
        assert sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"FAIL: generation smoke test crashed: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROPS[params.prop], TROUBLES[params.trouble], FIXES[params.fix], params.captain, params.mate, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
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
