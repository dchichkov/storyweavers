#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/vestibule_dapper_shine_teamwork_detective_story.py
==================================================================================

A small detective storyworld about teamwork, a vestibule, and a dapper shine.

Premise:
- Two children and a helper adult investigate a small mystery in a vestibule.
- A shiny item goes missing from a dapper coat stand.
- They team up, notice clues, and solve it together.

The story stays child-facing, concrete, and state-driven: clues are physical,
feelings change over time, and the ending proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REQUIRED_WORDS = ("vestibule", "dapper", "shine")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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


@dataclass
class Clue:
    id: str
    label: str
    text: str
    shine: bool = False
    hidden: bool = False


@dataclass
class DetectiveTool:
    id: str
    label: str
    help_text: str
    reveals_hidden: bool = False
    sorts_teamwork: bool = False


@dataclass
class StoryParams:
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    helper: str
    helper_gender: str
    object_name: str
    object_label: str
    clue1: str
    clue2: str
    tool: str
    seed: Optional[int] = None


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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    team = world.get("team")
    if team.memes.get("teamwork", 0.0) >= THRESHOLD and "solved" not in world.fired:
        world.fired.add(("solved",))
        team.meters["progress"] = team.meters.get("progress", 0.0) + 1
        out.append("__solve__")
    return out


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("object")
    if obj.meters.get("found", 0.0) >= THRESHOLD and ("shine_seen",) not in world.fired:
        world.fired.add(("shine_seen",))
        out.append("__shine__")
    return out


RULES = [Rule("teamwork", _r_teamwork), Rule("shine", _r_shine)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_risk(clue: Clue) -> bool:
    return clue.shine


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for o in OBJECTS:
        for c1 in CLUES:
            for c2 in CLUES:
                if c1 != c2 and clue_risk(CLUES[c1]) and clue_risk(CLUES[c2]):
                    combos.append((o, c1, c2))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective teamwork storyworld.")
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].reveal and not args.clue1 and not args.clue2:
        pass
    combos = [c for c in valid_combos()
              if (args.object_name is None or c[0] == args.object_name)
              and (args.clue1 is None or c[1] == args.clue1)
              and (args.clue2 is None or c[2] == args.clue2)]
    if not combos:
        raise StoryError("(No valid detective mystery matches those options.)")
    obj, c1, c2 = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    hero1, g1 = pick_name(rng)
    hero2, g2 = pick_name(rng, avoid=hero1)
    helper, hg = pick_name(rng)
    return StoryParams(hero1=hero1, hero1_gender=g1, hero2=hero2, hero2_gender=g2,
                       helper=helper, helper_gender=hg, object_name=obj,
                       object_label=OBJECTS[obj], clue1=c1, clue2=c2, tool=tool)


def pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def tell(params: StoryParams) -> World:
    if params.object_name not in OBJECTS or params.clue1 not in CLUES or params.clue2 not in CLUES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    if params.clue1 == params.clue2:
        raise StoryError("The two clues must be different.")
    world = World()
    a = world.add(Entity(id=params.hero1, kind="character", type=params.hero1_gender, role="detective", memes={"curious": 1.0}))
    b = world.add(Entity(id=params.hero2, kind="character", type=params.hero2_gender, role="detective", memes={"curious": 1.0}))
    h = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", label="the helper"))
    team = world.add(Entity(id="team", kind="group", type="team", label="the team", memes={"teamwork": 0.0}))
    obj = world.add(Entity(id="object", label=params.object_label, meters={"found": 0.0}, memes={"missing": 1.0}))
    clue1 = world.add(Entity(id="clue1", label=CLUES[params.clue1].label, attrs={"text": CLUES[params.clue1].text}, meters={"shine": 1.0 if CLUES[params.clue1].shine else 0.0}))
    clue2 = world.add(Entity(id="clue2", label=CLUES[params.clue2].label, attrs={"text": CLUES[params.clue2].text}, meters={"shine": 1.0 if CLUES[params.clue2].shine else 0.0}))
    tool = world.add(Entity(id="tool", label=TOOLS[params.tool].label, attrs={"help": TOOLS[params.tool].help_text}, meters={"used": 0.0}))
    world.say(f"In the vestibule, {a.id} and {b.id} found a dapper little mystery.")
    world.say(f"A polished {params.object_label} was missing, and a faint shine winked near the coat stand.")
    world.para()
    world.say(f"{h.id} knelt beside them and said, \"Let's solve it together.\"")
    world.say(f"{a.id} spotted {clue1.label}; {b.id} noticed {clue2.label}.")
    team.memes["teamwork"] = 1.0
    obj.meters["found"] = 1.0
    world.say(f"They used {tool.label} to check behind the umbrella rack and under the bench.")
    propagate(world, narrate=False)
    world.para()
    world.say(f"The final clue led to a small shine in a pocket, and the missing {params.object_label} turned up at last.")
    world.say(f"The team put it back where it belonged, and the vestibule looked dapper and bright again.")
    world.facts.update(hero1=a, hero2=b, helper=h, object=obj, tool=tool, clue1=clue1, clue2=clue2, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a detective story for a young child that includes the words "{REQUIRED_WORDS[0]}", "{REQUIRED_WORDS[1]}", and "{REQUIRED_WORDS[2]}".',
        f"Tell a teamwork mystery set in a vestibule where {p.hero1} and {p.hero2} solve a small missing-item case with help from a grown-up.",
        f"Write a child-friendly detective story about a dapper-looking place, a shine clue, and a team that works together to find what was lost.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(question="Where did the mystery happen?",
               answer="It happened in the vestibule, right by the coat stand and the bench. That mattered because the clue had to be found in the same small place where the item went missing."),
        QAItem(question="How did the children solve the case?",
               answer=f"They worked as a team: {p.hero1} noticed one clue, {p.hero2} noticed another, and the helper showed them how to check the hidden spots. Together they followed the shine and found the missing object."),
        QAItem(question="How did the story end?",
               answer=f"It ended with the missing {p.object_label} back in its proper place, and the vestibule looking dapper and bright again. The team’s teamwork changed the place from puzzling to peaceful."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a vestibule?",
               answer="A vestibule is a small entry area by a door. It is a useful place for coats, shoes, and quick little mysteries."),
        QAItem(question="What does dapper mean?",
               answer="Dapper means neat, stylish, and nicely put together. A dapper place or person looks especially tidy and smart."),
        QAItem(question="What can shine mean?",
               answer="Shine means to give off light or look bright and glossy. A shiny clue can catch your eye right away."),
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this mystery needs at least two different shine clues.)"


CURATED = [
    StoryParams(hero1="Mina", hero1_gender="girl", hero2="Theo", hero2_gender="boy",
                helper="Aunt June", helper_gender="woman", object_name="badge",
                object_label="badge", clue1="button", clue2="sock", tool="magnifier"),
    StoryParams(hero1="Lena", hero1_gender="girl", hero2="Owen", hero2_gender="boy",
                helper="Mr. Bell", helper_gender="man", object_name="keyring",
                object_label="keyring", clue1="glint", clue2="feather", tool="notebook"),
    StoryParams(hero1="Nico", hero1_gender="boy", hero2="Ivy", hero2_gender="girl",
                helper="Grandma", helper_gender="woman", object_name="ring",
                object_label="ring", clue1="coin", clue2="ribbon", tool="flashlight"),
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Sage", "Ruby", "Nora", "Ada", "Mia"]
BOY_NAMES = ["Theo", "Owen", "Nico", "Eli", "Finn", "Jack", "Max", "Noah"]

OBJECTS = {
    "badge": "brass badge",
    "keyring": "small keyring",
    "ring": "silver ring",
    "locket": "tiny locket",
}

CLUES = {
    "button": Clue(id="button", label="a button with a shine", text="A button gleamed near the door.", shine=True),
    "glint": Clue(id="glint", label="a glint on the floor", text="A glint flashed under the bench.", shine=True),
    "coin": Clue(id="coin", label="a shiny coin", text="A coin shone by the umbrella stand.", shine=True),
    "feather": Clue(id="feather", label="a feather", text="A feather was caught in a coat pocket.", shine=False),
    "sock": Clue(id="sock", label="one lonely sock", text="A lonely sock sat by the shoe rack.", shine=False),
    "ribbon": Clue(id="ribbon", label="a ribbon", text="A ribbon hung from a hook.", shine=False),
}

TOOLS = {
    "magnifier": DetectiveTool(id="magnifier", label="a magnifying glass", help_text="It helps spot tiny clues.", reveals_hidden=True),
    "notebook": DetectiveTool(id="notebook", label="a notebook", help_text="It helps keep the clues in order.", sorts_teamwork=True),
    "flashlight": DetectiveTool(id="flashlight", label="a flashlight", help_text="It helps see shiny things in dark corners.", reveals_hidden=True),
}


def valid_tools() -> list[str]:
    return list(TOOLS)


def valid_clues() -> list[str]:
    return list(CLUES)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in OBJECTS:
        lines.append(asp.fact("object", k))
    for k, c in CLUES.items():
        lines.append(asp.fact("clue", k))
        if c.shine:
            lines.append(asp.fact("shiny", k))
    for k in TOOLS:
        lines.append(asp.fact("tool", k))
    return "\n".join(lines)


ASP_RULES = r"""
shine_clue(C) :- clue(C), shiny(C).
valid(O,C1,C2,T) :- object(O), shine_clue(C1), shine_clue(C2), C1 != C2, tool(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
