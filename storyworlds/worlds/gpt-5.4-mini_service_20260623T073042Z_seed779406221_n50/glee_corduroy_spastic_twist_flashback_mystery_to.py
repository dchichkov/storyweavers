#!/usr/bin/env python3
"""
storyworlds/worlds/glee_corduroy_spastic_twist_flashback_mystery_to.py
======================================================================

A small superhero-style storyworld about a sidekick, a corduroy costume,
an embarrassing spastic glitch, a Twist, a Flashback, and a Mystery to Solve.

Seed tale:
---
Captain Glee loved wearing a corduroy jacket that made a neat rustle when she
moved. One day, while helping in the city, her suit started acting spastic: a
clip snagged, the sleeve twisted, and her cape kept flipping over her eyes.
She and her kid sidekick chased the mystery back through a flashback to the
last repair visit. There, they discovered the wrong thread had been used in a
hidden seam. The Twist was that the strange glitch was not a villain's trick at
all, but a simple mistake. With the seam fixed, Glee flew again, and the city
cheered.

World model:
- Physical meters track costume damage, twist, and repair.
- Emotional memes track glee, worry, confidence, and relief.
- A flashback reveals the cause; a twist changes what the heroes think; the
  mystery is solved by a concrete repair.

The prose stays child-facing and concrete, with a superhero-story feel.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hero:
    id: str
    label: str
    type: str
    costume: str
    power: str
    keyword: str


@dataclass
class Glitch:
    id: str
    label: str
    symptom: str
    cause: str
    fix: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    method: str
    tool: str
    solves: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_glitch(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    suit = world.get("costume")
    if hero.meters["twist"] < THRESHOLD or suit.meters["snag"] < THRESHOLD:
        return out
    sig = ("glitch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    suit.meters["damage"] += 1
    hero.memes["worry"] += 1
    out.append("The costume snagged and the hero's move went all spastic.")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    if world.get("hero").memes["flashback"] < THRESHOLD:
        return out
    if world.get("clue").meters["seen"] < THRESHOLD:
        return out
    sig = ("reveal",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The flashback revealed a hidden seam with the wrong thread.")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    if world.get("tool").meters["used"] < THRESHOLD or world.get("clue").meters["seen"] < THRESHOLD:
        return out
    sig = ("solve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("costume").meters["damage"] = 0
    world.get("hero").memes["relief"] += 1
    out.append("The repair fixed the seam and the mystery was solved.")
    return out


CAUSAL_RULES = [
    Rule("glitch", "physical", _r_glitch),
    Rule("reveal", "story", _r_reveal),
    Rule("solve", "physical", _r_solve),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def flashback_possible(world: World) -> bool:
    return world.get("hero").meters["twist"] >= THRESHOLD and world.get("clue").meters["seen"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "patrol" not in setting.affords:
            continue
        for hid in HEROS:
            for gid in GLITCHES:
                if hid == "glee" and gid == "spastic":
                    combos.append((place, hid, gid))
    return combos


@dataclass
class StoryParams:
    place: str
    hero: str
    glitch: str
    sidekick: str
    repair: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: glee, corduroy, spastic, twist, flashback, mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROS)
    ap.add_argument("--glitch", choices=GLITCHES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
              if (args.place is None or c[0] == args.place)
              and (args.hero is None or c[1] == args.hero)
              and (args.glitch is None or c[2] == args.glitch)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hero, glitch = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        hero=hero,
        glitch=glitch,
        sidekick=args.sidekick or rng.choice(SIDEKICKS),
        repair=args.repair or rng.choice(list(REPAIRS)),
    )


def tell(setting: Setting, hero_cfg: Hero, glitch: Glitch, repair: Repair, sidekick: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id="hero", kind="character", type="girl", label=hero_cfg.label, role="hero"))
    kid = w.add(Entity(id="sidekick", kind="character", type="boy", label=sidekick, role="sidekick"))
    costume = w.add(Entity(id="costume", label=hero_cfg.costume))
    clue = w.add(Entity(id="clue", label=glitch.clue))
    tool = w.add(Entity(id="tool", label=repair.tool))
    for e in (hero, kid, costume, clue, tool):
        e.meters["init"] = 1
        e.memes["init"] = 0
    hero.memes["glee"] += 1
    kid.memes["glee"] += 1
    costume.meters["corduroy"] += 1
    costume.meters["snag"] += 1
    hero.meters["twist"] += 1
    w.say(f"{hero_cfg.label} loved her {hero_cfg.costume}, and its corduroy ribs made a cheerful rustle when she moved.")
    w.say(f"One bright day at {setting.place}, {hero_cfg.label} and {sidekick} were on patrol when a {glitch.label} changed her stride.")
    w.para()
    w.say(f"The move felt spastic and strange. {sidekick} pointed at the {glitch.symptom}, and {hero_cfg.label} frowned because a mystery had started.")
    clue.meters["seen"] += 1
    hero.memes["flashback"] += 1
    w.say("Then a flashback came back to her: the last repair visit, the hidden seam, and the wrong thread nobody had noticed.")
    propagate(w)
    w.para()
    w.say(f'"We can solve it," said {sidekick}. {hero_cfg.label} used the {repair.tool} and followed the {repair.method}.')
    tool.meters["used"] += 1
    propagate(w)
    if w.get("costume").meters["damage"] <= 0:
        hero.memes["glee"] += 1
        kid.memes["relief"] += 1
        w.say(f"At last, the corduroy suit was smooth again. {hero_cfg.label} smiled wide, and the city felt safe under her watch.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, sidekick, glitch, repair = f["hero"], f["sidekick"], f["glitch"], f["repair"]
    return [
        f'Write a superhero story for a young child where {hero.label} has a corduroy costume and a {glitch.label} causes a mystery to solve.',
        f"Tell a bright hero story in which {hero.label} and {sidekick} use a flashback to find out why the suit went {glitch.symptom}.",
        f'Write a child-friendly superhero tale that includes the words "glee", "corduroy", and "spastic", and ends with {repair.method}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, sidekick, glitch, repair = f["hero"], f["sidekick"], f["glitch"], f["repair"]
    return [
        QAItem(question=f"What kind of costume did {hero.label} wear?", answer=f"{hero.label} wore a corduroy costume that rustled when she moved."),
        QAItem(question=f"What problem started the mystery?", answer=f"A {glitch.label} made her movement feel {glitch.symptom}, so the heroes had to solve the mystery."),
        QAItem(question=f"What did the flashback show?", answer="It showed the last repair visit and the hidden seam with the wrong thread."),
        QAItem(question=f"How was the mystery solved?", answer=f"They used the {repair.tool} and followed the {repair.method}, which fixed the seam."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is corduroy?", answer="Corduroy is a cloth with soft ridges, and it can make a neat rustling sound."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a moment when the story remembers something from earlier."),
        QAItem(question="What does a mystery to solve mean?", answer="It means there is a problem or clue that the characters must figure out."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combo doesn't produce the superhero twist/flashback mystery pattern.)"


HEROS = {
    "glee": Hero(id="glee", label="Captain Glee", type="girl", costume="corduroy jacket", power="bright flight", keyword="glee"),
}
GLITCHES = {
    "spastic": Glitch(id="spastic", label="spastic glitch", symptom="spastic", cause="wrong thread", fix="repair the seam", clue="hidden seam", tags={"spastic", "mystery"}),
}
REPAIRS = {
    "stitch": Repair(id="stitch", label="stitch kit", method="stitch the hidden seam", tool="stitch kit", solves="seam", tags={"repair"}),
    "patch": Repair(id="patch", label="patch kit", method="patch the torn sleeve", tool="patch kit", solves="sleeve", tags={"repair"}),
}
SIDEKICKS = ["Kid Flash", "Bolt", "Pip", "Dash"]
SETTINGS = {
    "rooftop": Setting(place="the rooftop", vibe="windy", affords={"patrol"}),
    "alley": Setting(place="the sunny alley", vibe="busy", affords={"patrol"}),
    "bridge": Setting(place="the bridge", vibe="bright", affords={"patrol"}),
}


ASP_RULES = r"""
valid(P,H,G) :- setting(P), hero(H), glitch(G), hero_glitch_pair(H,G).
hero_glitch_pair(glee,spastic).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for h in HEROS:
        lines.append(asp.fact("hero", h))
    for g in GLITCHES:
        lines.append(asp.fact("glitch", g))
    lines.append(asp.fact("hero_glitch_pair", "glee", "spastic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROS or params.glitch not in GLITCHES or params.repair not in REPAIRS:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.place], HEROS[params.hero], GLITCHES[params.glitch], REPAIRS[params.repair], params.sidekick)
    world.facts.update(hero=world.get("hero"), sidekick=world.get("sidekick"), glitch=GLITCHES[params.glitch], repair=REPAIRS[params.repair], setting=SETTINGS[params.place])
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(place=p, hero="glee", glitch="spastic", sidekick=s, repair="stitch")) for p in SETTINGS for s in SIDEKICKS[:1]]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
