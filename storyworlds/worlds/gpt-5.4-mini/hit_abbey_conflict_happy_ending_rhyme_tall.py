#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hit_abbey_conflict_happy_ending_rhyme_tall.py
=============================================================================

A standalone storyworld for a tiny tall-tale domain: a child, a risky dare,
a clash of pride, and a happy ending that lands in a rhyme. The seed words
"hit" and "abbey" are built into the world model as the story's central motion:
a bell-ringer tries to hit the abbey bell too hard, conflict rises, and a calm
fix restores the bell tower and the mood.

This world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- reasonableness gate
- inline ASP twin
- three QA sets grounded in simulated world state
- complete story output with premise, turn, and ending image

The tone is tall-tale-ish: a little larger than life, but still child-facing,
clear, and concrete.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nun"}
        male = {"boy", "father", "dad", "man", "monk"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "nun": "sister", "monk": "brother"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    tall: bool
    rhyme: str
    bell_name: str
    risky_spot: str
    safe_help: str
    echo: str

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
class Action:
    id: str
    verb: str
    rhyme: str
    force: int
    risky: bool
    clap: str
    lesson: str

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
    power: int
    calm: str
    rhyme: str
    sound: str

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


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


def _r_shake(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["rung"] < THRESHOLD:
            continue
        sig = ("shake", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "abbey" in world.entities:
            world.get("abbey").meters["shudder"] += 1
        for name in ("child", "guide"):
            if name in world.entities:
                world.get(name).memes["fear"] += 1
        out.append("__bell__")
    return out


def _r_mend(world: World) -> list[str]:
    out: list[str] = []
    abbey = world.entities.get("abbey")
    if not abbey or abbey.meters["shudder"] < THRESHOLD:
        return out
    sig = ("mend", "abbey")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    abbey.meters["shudder"] = 0
    abbey.meters["whole"] += 1
    out.append("The abbey stood steady again.")
    return out


CAUSAL_RULES = [
    Rule("shake", "physical", _r_shake),
    Rule("mend", "physical", _r_mend),
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


def risky_hit(action: Action, place: Place) -> bool:
    return action.risky and place.tall


def fix_succeeds(action: Action, fix: Fix) -> bool:
    return fix.power >= action.force


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, action in ACTIONS.items():
            for fid, fix in FIXES.items():
                if risky_hit(action, place):
                    combos.append((pid, aid, fid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    action: str
    fix: str
    child: str
    child_type: str
    guide: str
    guide_type: str
    elder: str
    elder_type: str
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
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: abbey bell trouble, conflict, rhyme, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--guide")
    ap.add_argument("--elder")
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
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.tall:
            lines.append(asp.fact("tall", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("force", aid, a.force))
        if a.risky:
            lines.append(asp.fact("risky", aid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,F) :- place(P), action(A), fix(F), tall(P), risky(A).
success(A,F) :- force(A,FA), power(F,FP), FP >= FA.
ending(happy) :- valid(P,A,F), success(A,F).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        print("  only in asp:", sorted(a - b))
        print("  only in python:", sorted(b - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    fix = FIXES[params.fix]

    child = world.add(Entity(params.child, kind="character", type=params.child_type, role="child", traits=["bold"]))
    guide = world.add(Entity(params.guide, kind="character", type=params.guide_type, role="guide", traits=["steady"]))
    elder = world.add(Entity(params.elder, kind="character", type=params.elder_type, role="elder", traits=["calm"]))
    abbey = world.add(Entity("abbey", kind="place", type="place", label="the abbey"))

    child.memes["pride"] = 1
    guide.memes["warning"] = 1

    world.say(
        f"At {place.label}, where the towers rose tall as a tale, {child.id} and {guide.id} stood before {place.label_word}."
    )
    world.say(
        f'"Hear me now," said {guide.id}, "that bell is old, and the abbey is not a drum to hit."'
    )

    world.para()
    child.memes["desire"] += 1
    world.say(
        f"But {child.id} had a dare in {child.pronoun('possessive')} chest and a grin like a kite in a gale. "
        f'"I can {action.verb} it!" {child.id} sang. "I can hit the bell clean and keen!"'
    )
    world.say(
        f"{guide.id} warned that a hard hit could shake the stones, and the old abbey might not stay bright and neat."
    )

    if action.risky and place.tall:
        child.memes["defiance"] += 1
        world.say(
            f'"I will not quit," {child.id} said, and {child.pronoun()} gave the rope a mighty hit.'
        )
        child.meters["rung"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"The bell boomed, the tower shivered, and dust danced like bees in a jar."
        )
        if fix_succeeds(action, fix):
            abbey.meters["whole"] += 1
            child.memes["fear"] += 1
            world.say(
                f"Then {elder.id} came quick as a creek in spring. {elder.pronoun().capitalize()} laid a steady hand on the rope and used {fix.calm}."
            )
            world.say(
                f'The old bell rang again, but softer this time, with {fix.sound} and a kinder tune.'
            )
            world.say(
                f"{guide.id} and {child.id} looked up at the abbey, and the tall stone stayed true."
            )
            world.para()
            world.say(
                f"In the end, {child.id} learned that a brave heart need not strike so hard, for a wise hand makes a bell sing farther than force."
            )
            world.say(
                f"So they went home with a rhyme on their lips: 'A gentler hit keeps the abbey fit.'"
            )
        else:
            world.say(
                f"But the fix came too weak, and the abbey shook like a leaf in a storm."
            )
            world.say(
                f"The happy ending could not hold, so this world refuses the tale."
            )
            raise StoryError("Chosen fix cannot safely resolve the bell strike.")
    else:
        world.say(
            f"{child.id} rang the bell lightly, and the abbey answered with a soft and sunny chime."
        )
        world.say(
            f"The child laughed, the guide smiled, and the old stones never needed mending."
        )

    world.facts.update(
        place=place,
        action=action,
        fix=fix,
        child=child,
        guide=guide,
        elder=elder,
        outcome="happy",
        hit=True,
    )
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a child that includes the words "hit" and "abbey" and ends happily with a rhyme.',
        f"Tell a story where {f['child'].id} wants to hit the abbey bell too hard, a conflict rises, and a wise helper calms everyone down.",
        f'Write a child-friendly tall tale with the abbey, a noisy mistake, and a gentle rhyme at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guide, elder = f["child"], f["guide"], f["elder"]
    place, fix = f["place"], f["fix"]
    return [
        QAItem(
            question="Why did the conflict start?",
            answer=f"The conflict started because {child.id} wanted to hit the abbey bell too hard. {guide.id} warned {child.pronoun('object')} that the old stones should be treated gently.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{elder.id} stepped in and used {fix.calm}, which was strong enough to keep the abbey steady. That turned the noisy trouble into a safe, happy ending.",
        ),
        QAItem(
            question="What did the ending prove?",
            answer="It proved that a softer touch can work better than a reckless one. The bell sang, the abbey stayed whole, and the rhyme made the lesson easy to remember.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an abbey?",
            answer="An abbey is an old church building where monks or nuns may live or pray. In stories, abbeys are often tall, quiet, and full of stone rooms.",
        ),
        QAItem(
            question="What does it mean to hit something too hard?",
            answer="It means to strike with more force than is safe or needed. Too much force can break things, scare people, or make a problem bigger.",
        ),
        QAItem(
            question="Why do rhymes fit tall tales?",
            answer="Rhymes make tall tales sound playful and easy to remember. They can turn a lesson into something that feels like a song.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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


def valid_combo_selected(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combo_selected(args)
    if not combos:
        raise StoryError("No valid story combination matches the given options.")

    place, action, fix = rng.choice(sorted(combos))
    child_type = rng.choice(["girl", "boy"])
    guide_type = "woman" if child_type == "girl" else "man"
    elder_type = rng.choice(["woman", "man", "nun", "monk"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["Mabel", "Wren", "Bess", "Otis", "Glen"])
    elder = args.elder or rng.choice(["Sister May", "Brother Ben", "Aunt June", "Uncle Joe"])
    return StoryParams(place, action, fix, child, child_type, guide, guide_type, elder, elder_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


PLACES = {
    "abbey": Place("abbey", "the abbey", True, "tall", "bell", "stone steps", "a steady hand", "a long echo"),
    "bell_tower": Place("bell_tower", "the bell tower", True, "bright", "bell", "railing", "a calming rope", "a rolling chime"),
    "chapel_yard": Place("chapel_yard", "the chapel yard", False, "small", "hand bell", "yard stones", "a soft song", "a warm ring"),
}

ACTIONS = {
    "hit": Action("hit", "hit the bell", "fit", 3, True, "boom", "A gentle hit is better than a wild swing."),
    "strike": Action("strike", "strike the bell", "bright", 2, True, "clang", "Too much force can shake old stone."),
    "tap": Action("tap", "tap the bell", "nap", 1, False, "ting", "A careful tap keeps things safe."),
}

FIXES = {
    "steady_hand": Fix("steady_hand", "a steady hand", 3, "a steady hand", "well", "thrum"),
    "softer_rope": Fix("softer_rope", "a softer rope", 2, "a softer rope", "near", "hum"),
    "calm_breath": Fix("calm_breath", "a calm breath", 1, "a calm breath", "light", "song"),
}

GIRL_NAMES = ["Mina", "June", "Lena", "Tess", "Ada", "Nora"]
BOY_NAMES = ["Finn", "Evan", "Bram", "Noel", "Hugo", "Perry"]

CURATED = [
    StoryParams("abbey", "hit", "steady_hand", "Mina", "girl", "Mabel", "woman", "Brother Ben", "monk"),
    StoryParams("bell_tower", "strike", "softer_rope", "Finn", "boy", "Wren", "woman", "Sister May", "nun"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify_story() -> int:
    rc = 0
    if set(asp_valid()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate and Python gate differ.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify_story())
    if args.asp:
        print(f"{len(asp_valid())} compatible combos:")
        for p, a, f in asp_valid():
            print(f"  {p:12} {a:8} {f}")
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} at {p.place} ({p.action}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
