#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/alpaca_loosen_pot_dim_magic_teamwork_adventure.py
===================================================================================

A standalone storyworld for a tiny adventure tale about teamwork and magic:
two kids find a stuck alpaca near a dim pot-shaped relic, then work together to
loosen the snag and guide the alpaca home.

Seed words:
- alpaca
- loosen
- pot-dim

Features:
- Magic
- Teamwork

Style:
- Adventure
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
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False
    magical: bool = False
    heavy: bool = False
    stuck: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Theme:
    id: str
    place: str
    adventure_frame: str
    quest: str
    ending: str
    scout_word: str
    relic_word: str


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    magic: bool = False
    teamwork: bool = False
    strength: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    needs: str
    danger: str
    can_be_loosened: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    tool1: str
    tool2: str
    problem: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    seed: Optional[int] = None


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


def _r_wait(world: World) -> list[str]:
    out = []
    alpaca = world.get("alpaca")
    if alpaca.meters["tangled"] >= THRESHOLD and ("wait",) not in world.fired:
        world.fired.add(("wait",))
        world.get("alpaca").memes["hope"] += 1
        out.append("__wait__")
    return out


def _r_team(world: World) -> list[str]:
    out = []
    h1 = world.get("hero1")
    h2 = world.get("hero2")
    if h1.memes["cooperate"] >= THRESHOLD and h2.memes["cooperate"] >= THRESHOLD and ("team",) not in world.fired:
        world.fired.add(("team",))
        h1.memes["brave"] += 1
        h2.memes["brave"] += 1
        out.append("__team__")
    return out


CAUSAL_RULES = [Rule("wait", _r_wait), Rule("team", _r_team)]


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


THEMES = {
    "trail": Theme(
        id="trail",
        place="a winding mountain trail",
        adventure_frame="an expedition through bright stone and wind",
        quest="find the lost bell path",
        ending="walked on together with the alpaca trotting happily beside them",
        scout_word="scouts",
        relic_word="pot-dim",
    ),
    "ruins": Theme(
        id="ruins",
        place="old jungle ruins",
        adventure_frame="a brave search through mossy arches",
        quest="find the hidden spring",
        ending="headed home with mud on their shoes and smiles on their faces",
        scout_word="explorers",
        relic_word="pot-dim",
    ),
}

TOOLS = {
    "glowstone": Tool("glowstone", "glowstone charm", "light", magic=True, strength=2, tags={"magic"}),
    "rope": Tool("rope", "rope", "pull", teamwork=True, strength=2, tags={"teamwork"}),
    "spell": Tool("spell", "sparkly spell", "magic", magic=True, teamwork=True, strength=3, tags={"magic", "teamwork"}),
}

PROBLEMS = {
    "vine": Problem("vine", "a coil of thorny vines", "loosening", "The vines held tight around the alpaca's leg.", tags={"alpaca", "loosen"}),
    "knot": Problem("knot", "a stubborn knot", "loosening", "The knot kept the gate from opening.", tags={"loosen"}),
    "door": Problem("door", "a jammed stone door", "opening", "The stone door would not budge.", can_be_loosened=False, tags={"pot-dim"}),
}

GIRL_NAMES = ["Lila", "Mina", "Zoe", "Ava", "Nia", "Maya"]
BOY_NAMES = ["Taro", "Finn", "Noah", "Eli", "Jude", "Arin"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for tool1 in TOOLS:
            for tool2 in TOOLS:
                for problem in PROBLEMS:
                    if is_reasonable(TOOLS[tool1], TOOLS[tool2], PROBLEMS[problem]):
                        combos.append((theme, tool1, tool2, problem))
    return combos


def is_reasonable(t1: Tool, t2: Tool, prob: Problem) -> bool:
    if not prob.can_be_loosened and not (t1.magic or t2.magic):
        return False
    if prob.id == "vine" and not (t1.teamwork or t2.teamwork):
        return False
    return True


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about an alpaca, magic, and teamwork.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool1", choices=TOOLS)
    ap.add_argument("--tool2", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero1-gender", choices=["girl", "boy"])
    ap.add_argument("--hero2")
    ap.add_argument("--hero2-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.tool1 is None or c[1] == args.tool1)
              and (args.tool2 is None or c[2] == args.tool2)
              and (args.problem is None or c[3] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, tool1, tool2, problem = rng.choice(sorted(combos))
    g1 = args.hero1_gender or rng.choice(["girl", "boy"])
    g2 = args.hero2_gender or ("boy" if g1 == "girl" else "girl")
    return StoryParams(
        theme=theme,
        tool1=tool1,
        tool2=tool2,
        problem=problem,
        hero1=args.hero1 or _pick_name(rng, g1),
        hero1_gender=g1,
        hero2=args.hero2 or _pick_name(rng, g2),
        hero2_gender=g2,
    )


def predict_loosen(world: World) -> bool:
    return world.get("alpaca").meters["tangled"] >= THRESHOLD


def tell(theme: Theme, t1: Tool, t2: Tool, prob: Problem, hero1: str, g1: str, hero2: str, g2: str) -> World:
    w = World()
    h1 = w.add(Entity(id="hero1", kind="character", type=g1, label=hero1, role="helper"))
    h2 = w.add(Entity(id="hero2", kind="character", type=g2, label=hero2, role="helper"))
    alp = w.add(Entity(id="alpaca", kind="character", type="alpaca", label="the alpaca", stuck=True))
    relic = w.add(Entity(id="relic", type="thing", label="the pot-dim relic", magical=True))
    problem = w.add(Entity(id="problem", type="thing", label=prob.label, heavy=prob.id == "door", stuck=True))
    h1.memes["curious"] += 1
    h2.memes["curious"] += 1
    w.say(f"{hero1} and {hero2} set off on {theme.place}, following {theme.adventure_frame}.")
    w.say(f"Near an old {theme.relic_word} relic, they found {prob.label} and a small alpaca in trouble.")
    w.para()
    w.say(f'"Look," said {hero1}, "the alpaca is stuck."')
    w.say(f'"We can {prob.needs} it," said {hero2}, "if we work together."')
    h1.memes["cooperate"] += 1
    h2.memes["cooperate"] += 1
    if t1.magic or t2.magic:
        w.say(f"{hero1} lifted the {t1.label}, and {hero2} answered with the {t2.label}.')
    else:
        w.say(f"{hero1} took the {t1.label}, and {hero2} took the {t2.label}.")
    w.para()
    if prob.id == "vine":
        w.say("The charm gave the knot a tiny shine, and the rope pulled in a careful rhythm.")
        w.say("At last, the vines loosened and slid off the alpaca's leg.")
        alp.meters["tangled"] = 0
        alp.memes["relief"] += 1
        w.say("The alpaca shook its wool, then nuzzled both kids as if it knew they had helped.")
    elif prob.id == "knot":
        w.say("Magic tickled the knot while teamwork held the rope steady.")
        w.say("With one last tug, the knot loosened and the gate swung open.")
        problem.meters["open"] = 1
    else:
        w.say("They whispered the spell together, then pushed from both sides.")
        w.say("The stone door loosened with a groan and opened just enough for the light to pour in.")
        problem.meters["open"] = 1
    w.para()
    w.say(f"By sunset, {hero1} and {hero2} had {theme.ending}, and the little alpaca was safe.")
    w.facts.update(theme=theme, tool1=t1, tool2=t2, problem=prob, hero1=h1, hero2=h2, alpaca=alp, relic=relic)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write an adventure story that includes the words alpaca, loosen, and pot-dim.",
        f"Tell a story where {f['hero1'].label} and {f['hero2'].label} use magic and teamwork to loosen {f['problem'].label}.",
        f"Write a child-friendly adventure about a stuck alpaca near a pot-dim relic and a brave rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question="Who is the story about?", answer=f"It is about {f['hero1'].label} and {f['hero2'].label}, who go on an adventure and help an alpaca."),
        QAItem(question="What needed to be done?", answer=f"They needed to loosen {f['problem'].label} so the alpaca could be safe again. They did it by using magic and teamwork together."),
        QAItem(question="How did the story end?", answer=f"It ended with the alpaca safe and the two helpers walking away together after their brave fix. The pot-dim relic stayed behind as a quiet clue from the adventure."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an alpaca?", answer="An alpaca is a fluffy animal with long legs and a soft coat. People often keep them on farms or see them on trips."),
        QAItem(question="What does it mean to loosen something?", answer="To loosen something means to make it less tight. When something is loosened, it can move more easily."),
        QAItem(question="What is teamwork?", answer="Teamwork means working together to do one job. Each helper does a part, and together they can solve a bigger problem."),
        QAItem(question="What is magic in a story?", answer="In a story, magic is a special power that can make unusual things happen. It often helps the heroes in a wonderful way."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, A, B, P) :- theme(T), tool(A), tool(B), problem(P), reasonable(T, A, B, P).
reasonable(T, A, B, vine) :- magic_or_teamwork(A, B), theme(T).
reasonable(T, A, B, knot) :- magic_or_teamwork(A, B), theme(T).
reasonable(T, A, B, door) :- magic(A), magic(B), theme(T).
magic_or_teamwork(A, B) :- magic(A).
magic_or_teamwork(A, B) :- magic(B).
magic_or_teamwork(A, B) :- teamwork(A).
magic_or_teamwork(A, B) :- teamwork(B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if t.magic:
            lines.append(asp.fact("magic", t.id))
        if t.teamwork:
            lines.append(asp.fact("teamwork", t.id))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
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
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
    except Exception as e:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        t1 = TOOLS[params.tool1]
        t2 = TOOLS[params.tool2]
        prob = PROBLEMS[params.problem]
    except KeyError as e:
        raise StoryError(f"Invalid parameter: {e.args[0]}") from None
    world = tell(theme, t1, t2, prob, params.hero1, params.hero1_gender, params.hero2, params.hero2_gender)
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


CURATED = [
    StoryParams(theme="trail", tool1="glowstone", tool2="rope", problem="vine", hero1="Mina", hero1_gender="girl", hero2="Taro", hero2_gender="boy"),
    StoryParams(theme="ruins", tool1="spell", tool2="rope", problem="knot", hero1="Ava", hero1_gender="girl", hero2="Noah", hero2_gender="boy"),
    StoryParams(theme="trail", tool1="spell", tool2="glowstone", problem="door", hero1="Eli", hero1_gender="boy", hero2="Lila", hero2_gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
