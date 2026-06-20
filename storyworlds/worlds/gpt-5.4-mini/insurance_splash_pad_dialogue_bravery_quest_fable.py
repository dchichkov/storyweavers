#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini/insurance_splash_pad_dialogue_bravery_quest_fable.py
=====================================================================================

A small fable-like storyworld set at a splash pad: a child wants to start a quest,
talks with a cautious helper, shows bravery, and learns why insurance matters when
things can break.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- simulated state drives the prose
- dialogue appears in the story
- the quest has a clear beginning, turn, and ending image

The seed words and features are treated as constraints and motifs:
- insurance
- splash pad
- dialogue
- bravery
- quest
- fable style

Run it
------
    python storyworlds/worlds/gpt_5_4_mini/insurance_splash_pad_dialogue_bravery_quest_fable.py
    python storyworlds/worlds/gpt_5_4_mini/insurance_splash_pad_dialogue_bravery_quest_fable.py --all
    python storyworlds/worlds/gpt_5_4_mini/insurance_splash_pad_dialogue_bravery_quest_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt_5_4_mini/insurance_splash_pad_dialogue_bravery_quest_fable.py --verify
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
class Place:
    id: str
    scene: str
    detail: str

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
class Quest:
    id: str
    goal: str
    clue: str
    ending: str
    requires_bravery: int = 1
    risk: str = "spray"
    damage: str = "wet shoes"
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
class Insurance:
    id: str
    label: str
    promise: str
    coverage: str
    comfort: str
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
class Choice:
    id: str
    sense: int
    fix: str
    fail: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    pad = world.entities.get("pad")
    if not child or not pad:
        return out
    if child.meters["spray"] < THRESHOLD:
        return out
    sig = ("soak",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["wet"] += 1
    child.memes["surprise"] += 1
    world.get("pad").meters["splashed"] += 1
    out.append("__soak__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    guide = world.entities.get("guide")
    if not child or not guide:
        return out
    if child.memes["bravery"] < THRESHOLD or guide.memes["hope"] < THRESHOLD:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["resolve"] += 1
    out.append("__brave__")
    return out


CAUSAL_RULES = [Rule("soak", "physical", _r_soak), Rule("bravery", "social", _r_bravery)]


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


def splash_risk(quest: Quest, place: Place) -> bool:
    return "splash" in place.id or "pad" in place.id or quest.risk == "spray"


def sensible_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= 2]


def best_choice() -> Choice:
    return max(CHOICES.values(), key=lambda c: c.sense)


def would_ask_for_help(bravery: int, guide_kind: str) -> bool:
    return bravery <= 2 and guide_kind in {"mother", "father", "guardian"}


def _do_quest(world: World, child: Entity, quest: Quest, narrate: bool = True) -> None:
    child.meters["spray"] += 1
    child.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def story_open(world: World, child: Entity, guide: Entity, place: Place, quest: Quest) -> None:
    child.memes["joy"] += 1
    guide.memes["hope"] += 1
    world.say(
        f"At the splash pad, {child.id} and {guide.id} came to the bright fountains "
        f"like two travelers at the mouth of a friendly river. {place.detail}"
    )
    world.say(
        f'"I seek {quest.goal}," said {child.id}. "I must find the clue before the water '
        f"can wash it away."
    )


def dialogue(world: World, child: Entity, guide: Entity, quest: Quest, ins: Insurance) -> None:
    child.memes["desire"] += 1
    guide.memes["worry"] += 1
    world.say(
        f'"Will my shoes be ruined?" asked {child.id}. "{ins.label} will help if they are," '
        f"{guide.id} answered. \"{ins.promise}.\""
    )
    world.say(
        f'"Then I can be brave," said {child.id}, standing a little straighter.'
    )
    if would_ask_for_help(int(child.memes["bravery"]), guide.type):
        world.say(f'"And if the splash gets too wild, I will call for you," {child.id} added.')
    else:
        world.say(f'"I can handle the first step," {child.id} said, with a shaky smile.')


def start_quest(world: World, child: Entity, quest: Quest) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} stepped into the rushing spray and began the quest. The water leapt up "
        f"to {quest.damage}, but the little traveler kept going."
    )
    _do_quest(world, child, quest)


def turn(world: World, child: Entity, guide: Entity, quest: Quest, ins: Insurance, choice: Choice) -> None:
    if child.meters["wet"] >= THRESHOLD:
        world.say(
            f"Then the fountain splashed harder than expected, and {child.id} stopped short. "
            f"{guide.id} pointed at the sign for {ins.label} and said, \"A wise traveler is not "
            f"ashamed to be protected.\""
        )
    if choice.id == "cover":
        child.memes["relief"] += 1
        world.say(
            f"{child.id} hid the small token in a dry pocket and smiled. {choice.fix}."
        )
    elif choice.id == "borrow":
        guide.memes["care"] += 1
        world.say(
            f"{guide.id} offered a towel and a steady hand. {choice.fix}."
        )
    elif choice.id == "retry":
        child.memes["resolve"] += 1
        world.say(
            f"{child.id} took one breath, squared {child.pronoun('possessive')} shoulders, and tried again more carefully. {choice.fix}."
        )
    else:
        world.say(choice.fix)


def ending(world: World, child: Entity, guide: Entity, quest: Quest, ins: Insurance) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    guide.memes["pride"] += 1
    world.say(
        f"At last {child.id} found the clue: {quest.clue}. {quest.ending} "
        f"{ins.coverage}."
    )
    world.say(
        f"The splash pad glittered behind them, and {child.id}'s shoes were no worse for the journey. "
        f"{guide.id} smiled as if {child.id} had grown a little taller in a single afternoon."
    )


def tell(place: Place, quest: Quest, ins: Insurance, choice: Choice,
         child_name: str = "Mina", child_gender: str = "girl",
         guide_name: str = "Aunt June", guide_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="hero"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_gender, role="guide"))
    pad = world.add(Entity(id="pad", type="place", label="the splash pad"))
    child.memes["bravery"] = 1.0
    guide.memes["hope"] = 1.0
    world.facts["place"] = place
    world.facts["quest"] = quest
    world.facts["insurance"] = ins
    world.facts["choice"] = choice

    story_open(world, child, guide, place, quest)
    world.para()
    dialogue(world, child, guide, quest, ins)
    start_quest(world, child, quest)
    world.para()
    turn(world, child, guide, quest, ins, choice)
    ending(world, child, guide, quest, ins)
    world.facts.update(child=child, guide=guide, pad=pad, wet=child.meters["wet"] >= THRESHOLD)
    return world


PLACES = {
    "splash_pad": Place("splash_pad", "a splash pad", "The fountains danced in circles and the stones shone like glass."),
    "fountain_lane": Place("fountain_lane", "a splash pad", "The water shot up in silver ribbons, bright as a little river."),
}

QUESTS = {
    "token": Quest("token", "the blue token", "a blue token tucked near the biggest fountain", "It glittered like a tiny moon in a puddle of light.", 1, "spray", "wet socks", {"token"}),
    "shell": Quest("shell", "the shiny shell", "a shell that waited beside the rainbow arch", "It rested in the child’s palm like a small promise.", 1, "spray", "wet sleeves", {"shell"}),
}

INSURANCES = {
    "policy": Insurance("policy", "insurance", "If something gets ruined, grown-ups can help make it right.", "it can help replace what is lost", "That made the child feel safer.", {"insurance"}),
    "card": Insurance("card", "insurance card", "This little card tells us how to ask for help if we need it.", "it can help pay for repairs or replacement", "That made the child breathe easier.", {"insurance"}),
}

CHOICES = {
    "cover": Choice("cover", 3, "The guide tucked the token into a dry pocket before the next splash arrived", "The child held the token high and hoped the water would be gentle", {"cover"}),
    "borrow": Choice("borrow", 3, "The guide borrowed a spare pouch from the nearby bench and the child carried the clue safely", "The child tried to hide the clue in a soaked sleeve", {"borrow"}),
    "retry": Choice("retry", 2, "The child tried again with steadier feet, and the clue stayed safe", "The child dashed ahead and the fountain splashed the clue from one hand to the other", {"retry"}),
    "ignore": Choice("ignore", 1, "The child laughed and ran, but the water was faster than pride", "The child ignored the warning and lost the clue to the spray", {"ignore"}),
}

GIRL_NAMES = ["Mina", "Lina", "Ivy", "Sora", "Maya", "Nora"]
BOY_NAMES = ["Oren", "Tavi", "Rafi", "Eli", "Noam", "Theo"]
GUIDES = [("Aunt June", "woman"), ("Dad", "father"), ("Mom", "mother"), ("Uncle Ben", "man")]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            for i in INSURANCES:
                for c in CHOICES:
                    if splash_risk(QUESTS[q], PLACES[p]) and CHOICES[c].sense >= 2:
                        combos.append((p, q, i, c))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    quest: str
    insurance: str
    choice: str
    child: str
    child_gender: str
    guide: str
    guide_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Splash-pad fable about bravery, a quest, and insurance.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--insurance", choices=INSURANCES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guide")
    ap.add_argument("--guide-gender", choices=["woman", "man", "mother", "father"])
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
    if args.choice and CHOICES[args.choice].sense < 2:
        raise StoryError("(Refusing a choice that is too foolish for a fable-style story.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.insurance is None or c[2] == args.insurance)
              and (args.choice is None or c[3] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, ins, choice = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guide_name, guide_gender = (args.guide, args.guide_gender) if args.guide else rng.choice(GUIDES)
    return StoryParams(place, quest, ins, choice, child, child_gender, guide_name or rng.choice(["Aunt June", "Dad", "Mom"]), guide_gender or "woman")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child that uses the word "insurance" and is set at a splash pad.',
        f"Tell a dialogue-driven quest story where {f['child'].id} at the splash pad learns bravery and asks about insurance.",
        f"Write a gentle fable about a child, a guide, a splash pad, and a small quest that ends with a wiser understanding of insurance.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guide, quest, ins = f["child"], f["guide"], f["quest"], f["insurance"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {guide.id}. {child.id} begins the quest, and {guide.id} helps {child.pronoun('object')} think bravely."),
        ("What did the child want?", f"{child.id} wanted {quest.goal}. The clue was part of a small quest at the splash pad."),
        ("What did they say about insurance?", f"They talked about {ins.label} because it can help if something gets ruined. That made the child feel safer before stepping into the water."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a splash pad?", "A splash pad is a place with fountains or sprays where children can play in the water without a deep pool."),
        ("What is insurance?", "Insurance is a plan that can help people pay for repairs or replacement when something goes wrong."),
        ("What does bravery mean?", "Bravery means doing something even when you feel a little afraid. It does not mean never being nervous."),
        ("What is a quest?", "A quest is a journey or mission to find something important or solve a problem."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
splash_risk(Q,P) :- quest(Q), place(P), risky(P).
sensible(C) :- choice(C), sense(C,S), S >= 2.
valid(P,Q,I,C) :- splash_risk(Q,P), insurance(I), sensible(C).
outcome(brave) :- child_brave.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if "pad" in pid:
            lines.append(asp.fact("risky", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for iid in INSURANCES:
        lines.append(asp.fact("insurance", iid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py == ax:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        assert sample.story
        print("OK: smoke test generated a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], INSURANCES[params.insurance],
                 CHOICES[params.choice], params.child, params.child_gender, params.guide, params.guide_gender)
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
    StoryParams("splash_pad", "token", "policy", "cover", "Mina", "girl", "Aunt June", "woman"),
    StoryParams("fountain_lane", "shell", "card", "borrow", "Oren", "boy", "Dad", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
