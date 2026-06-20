#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distinguish_bile_damp_problem_solving_mystery_to.py
====================================================================================

A standalone storyworld for a tall-tale-flavored mystery:
a child and a grown-up must distinguish one strange clue from another, solve a
small problem, and heed a cautionary lesson about a damp, swampy place.

Seed words:
- distinguish
- bile
- damp

Story ingredients:
- Problem Solving
- Mystery to Solve
- Cautionary
- Tall Tale style
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
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    label: str
    damp: bool = False
    mystery: str = ""

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
class Clue:
    id: str
    label: str
    smell: str
    taste_note: str
    likely_source: str
    safe: bool = True
    carries_bile: bool = False
    dampness: float = 0.0

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
class Tool:
    id: str
    label: str
    purpose: str
    helps_distinguish: bool = False
    helps_solve: bool = False
    safe: bool = True

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
        self.trace: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    place: str
    clue1: str
    clue2: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    cautionary: bool = True
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


PLACES = {
    "swamp": Place("swamp", "the wide swamp", damp=True, mystery="a croaking mystery"),
    "dock": Place("dock", "the river dock", damp=True, mystery="a lost barrel mystery"),
    "kitchen": Place("kitchen", "the ranch kitchen", damp=False, mystery="a supper mystery"),
}

CLUES = {
    "bile_mud": Clue("bile_mud", "a bitter green smear", "sharp and swampy", "a bile-like bitterness", "the frog pond", safe=False, carries_bile=True, dampness=1.0),
    "reed_sap": Clue("reed_sap", "a green reed stain", "fresh and grassy", "a damp grassy taste", "the reed bed", safe=True, carries_bile=False, dampness=0.7),
    "lamp_oil": Clue("lamp_oil", "a slick dark drip", "oily and smoky", "a greasy taste", "the lantern", safe=False, carries_bile=False, dampness=0.2),
    "spring_water": Clue("spring_water", "a clear wet drop", "cool and clean", "just plain wet", "the spring", safe=True, carries_bile=False, dampness=1.0),
}

TOOLS = {
    "nose": Tool("nose", "a sharp nose", "sniff clues", helps_distinguish=True, safe=True),
    "ledger": Tool("ledger", "a big notebook", "compare clues", helps_distinguish=True, helps_solve=True, safe=True),
    "lantern": Tool("lantern", "a lantern", "light the way", helps_solve=True, safe=True),
}

GIRL_NAMES = ["Mabel", "Lena", "Dora", "Nell", "Pearl", "Annie"]
BOY_NAMES = ["Otis", "Bram", "Hank", "Jules", "Rufus", "Cal"]


def _rule(smoke: str, sig: tuple, world: World) -> bool:
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.trace.append(smoke)
    return True


def reasonability_gate(place: Place, clue1: Clue, clue2: Clue, tool: Tool) -> Optional[str]:
    if clue1.id == clue2.id:
        return "Pick two different clues so there is something to distinguish."
    if not tool.helps_distinguish:
        return f"(No story: {tool.label} cannot help distinguish clues.)"
    if place.damp and not (clue1.dampness > 0 or clue2.dampness > 0):
        return "(No story: the place is damp, but neither clue is damp enough to matter.)"
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for c1 in CLUES.values():
            for c2 in CLUES.values():
                if c1.id == c2.id:
                    continue
                for tid, tool in TOOLS.items():
                    if reasonability_gate(place, c1, c2, tool) is None:
                        out.append((pid, c1.id, c2.id, tid))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.damp:
            lines.append(asp.fact("damp_place", pid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if c.carries_bile:
            lines.append(asp.fact("bile_clue", cid))
        if c.dampness > 0:
            lines.append(asp.fact("damp_clue", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.helps_distinguish:
            lines.append(asp.fact("distinguishes", tid))
    return "\n".join(lines)


ASP_RULES = r"""
needs_distinguish(P, C1, C2) :- place(P), clue(C1), clue(C2), C1 != C2.
ok_tool(T) :- tool(T), distinguishes(T).
ok_story(P, C1, C2, T) :- needs_distinguish(P, C1, C2), ok_tool(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show ok_story/4."))
    return sorted(set(asp.atoms(model, "ok_story")))


def tell(place: Place, clue1: Clue, clue2: Clue, tool: Tool, hero: Entity, helper: Entity) -> World:
    world = World()
    world.add(hero)
    world.add(helper)

    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1

    world.say(
        f"Out where the sky hung low and the crows talked like old judges, {hero.id} "
        f"and {helper.id} came to {place.label}. The ground there was damp, and the whole "
        f"bank smelled like a mystery waiting to be named."
    )
    world.say(
        f"{hero.id} found {clue1.label} beside {clue2.label}. \"I can {tool.purpose},\" "
        f"{hero.id} said, \"but first I must distinguish one clue from the other.\""
    )

    world.para()
    world.say(
        f"{helper.id} bent down, looked close, and used {tool.label} to compare the smell "
        f"and the feel. One clue came from {clue1.likely_source}, and the other came from "
        f"{clue2.likely_source}."
    )

    if clue1.carries_bile or clue2.carries_bile:
        world.say(
            f"One of the clues carried a bitter trace like bile. That was the old warning "
            f"sign: a smell can lie, but a careful nose can tell the truth."
        )
    else:
        world.say(
            f"Neither clue was wicked, but the dampness made them easy to mix up. That is "
            f"why the pair had to look again and think slow."
        )

    world.para()
    if clue1.carries_bile or clue2.carries_bile:
        world.say(
            f"At last they distinguished the harmless clue from the one that meant trouble. "
            f"The bitter smear was not food at all, but swamp muck that had reached the path."
        )
        world.say(
            f"{helper.id} swept it away and marked the safe trail with a lantern glow, so "
            f"{hero.id} would not follow the wrong sign in the dark."
        )
        hero.memes["relief"] += 1
        helper.memes["relief"] += 1
        world.facts["resolved"] = True
    else:
        world.say(
            f"They distinguished the two signs and solved the small mystery, but they also "
            f"learned the easy lesson: a damp place can fool a hurried mind, so slow eyes are "
            f"worth more than fast feet."
        )
        hero.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.facts["resolved"] = True

    world.say(
        f"By sunset the trail was straight as a fence post. {hero.id} tucked the notebook "
        f"under {hero.pronoun('possessive')} arm, and {helper.id} laughed that the swamp had "
        f"lost its riddle for another day."
    )

    world.facts.update(
        place=place,
        clue1=clue1,
        clue2=clue2,
        tool=tool,
        hero=hero,
        helper=helper,
        outcome="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale mystery story for a small child that includes the words '
        f'"distinguish", "{f["clue1"].label_word if hasattr(f["clue1"], "label_word") else f["clue1"].label}", and "damp".',
        f"Tell a cautionary story where {f['hero'].id} must distinguish one clue from another "
        f"at {f['place'].label}, and careful thinking solves the problem.",
        f"Write a short story in a tall-tale voice about a damp place, a mystery clue, and "
        f"a helper who uses a tool to solve the puzzle."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue1 = f["clue1"]
    clue2 = f["clue2"]
    place = f["place"]
    answer1 = (
        f"{hero.id} went with {helper.id} to {place.label} to solve a mystery. They "
        f"found two clues and had to distinguish which one mattered."
    )
    answer2 = (
        f"They used {f['tool'].label} and careful looking to tell the clues apart. "
        f"One clue carried a bitter trace like bile, which helped them spot the dangerous sign."
    )
    answer3 = (
        f"They solved the puzzle and left the trail safer than before. The damp ground "
        f"still stayed damp, but the confusing clue was cleared away."
    )
    return [
        QAItem("Who was the story about?", answer1),
        QAItem("How did they solve the mystery?", answer2),
        QAItem("What changed by the end?", answer3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does distinguish mean?",
               "To distinguish means to tell one thing from another by noticing what makes them different."),
        QAItem("What is bile?",
               "Bile is a bitter yellow-green liquid in the body. People usually say it tastes very bitter when they use the word in a story."),
        QAItem("What does damp mean?",
               "Damp means a little wet, like ground or cloth that has some water in it but is not soaking."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations exist.")

    def keep(c: tuple[str, str, str, str]) -> bool:
        return ((args.place is None or c[0] == args.place) and
                (args.clue1 is None or c[1] == args.clue1) and
                (args.clue2 is None or c[2] == args.clue2) and
                (args.tool is None or c[3] == args.tool))

    combos = [c for c in combos if keep(c)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue1, clue2, tool = rng.choice(sorted(combos))
    place_obj = PLACES[place]
    c1, c2, t = CLUES[clue1], CLUES[clue2], TOOLS[tool]

    if reasonability_gate(place_obj, c1, c2, t):
        raise StoryError(reasonability_gate(place_obj, c1, c2, t))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero])

    return StoryParams(place, clue1, clue2, tool, hero, hero_gender, helper, helper_gender, True)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place], CLUES[params.clue1], CLUES[params.clue2], TOOLS[params.tool],
        Entity(params.hero, kind="character", type=params.hero_gender, role="hero"),
        Entity(params.helper, kind="character", type=params.helper_gender, role="helper"),
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
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            bits = []
            if e.meters:
                bits.append(f"meters={dict(e.meters)}")
            if e.memes:
                bits.append(f"memes={dict(e.memes)}")
            if e.role:
                bits.append(f"role={e.role}")
            print(f"  {e.id}: {' '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


def asp_program_for_show() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show ok_story/4.\n"


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    rc = 0
    if py == clingo:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos.")
        print("only python:", sorted(py - clingo))
        print("only asp:", sorted(clingo - py))
        rc = 1

    # smoke test ordinary generation
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(777))
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    print("OK: default generation smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program_for_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos[:200]:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("swamp", "bile_mud", "spring_water", "ledger", "Mabel", "girl", "Otis", "boy"),
            StoryParams("dock", "lamp_oil", "reed_sap", "nose", "Bram", "boy", "Lena", "girl"),
            StoryParams("swamp", "reed_sap", "bile_mud", "ledger", "Nell", "girl", "Cal", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
