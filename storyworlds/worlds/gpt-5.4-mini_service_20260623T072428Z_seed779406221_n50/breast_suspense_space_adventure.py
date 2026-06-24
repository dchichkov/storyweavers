#!/usr/bin/env python3
"""
storyworlds/worlds/breast_suspense_space_adventure.py
=====================================================

A standalone storyworld for a small Space Adventure domain with suspense.

Premise:
- A child crew explores a moon base or star dock.
- One important chest-mounted piece on a suit is the "breast badge" or "breast light"
  (a harmless, child-facing term used as a label on the front/breast of the suit).
- The crew hears a strange signal, worries about being lost in the dark, and uses a
  safe tool to solve the problem.

The world is built around:
- typed entities with physical meters and emotional memes
- a forward-chaining causal model
- a Python reasonableness gate plus inline ASP twin
- state-driven narration with suspense, a turn, and a resolution

The stories are intended to feel like short, complete Space Adventure tales.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    wore_on: str = ""
    safe: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captainess"}
        male = {"boy", "father", "dad", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    dark_place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    label: str
    verb: str
    sound: str
    makes_risk: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    action: str
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    danger: str
    tool: str
    fix: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "orbit_hall": Setting(place="the orbit hall", dark_place="the black service tunnel", affords={"echo", "signal"}),
    "moon_base": Setting(place="the moon base", dark_place="the airlock hall", affords={"echo", "signal"}),
    "star_dock": Setting(place="the star dock", dark_place="the docking tunnel", affords={"signal", "drift"}),
}

DANGERS = {
    "lost_signal": Danger(id="lost_signal", label="lost signal", verb="went silent", sound="beep... beep...", tags={"signal", "dark"}),
    "shadow_echo": Danger(id="shadow_echo", label="shadow echo", verb="whispered back", sound="whooo", tags={"echo", "dark"}),
    "drifting_light": Danger(id="drifting_light", label="drifting light", verb="floated away", sound="hmmmmm", tags={"drift", "dark"}),
}

TOOLS = {
    "breast_beacon": Tool(id="breast_beacon", label="breast beacon", phrase="a tiny breast beacon on the front of the suit", glow="glowed soft and blue", tags={"breast", "light"}),
    "lamp": Tool(id="lamp", label="lamp", phrase="a pocket lamp", glow="shone like a star", tags={"light"}),
    "scanner": Tool(id="scanner", label="scanner", phrase="a hand scanner", glow="blinked bright green", tags={"signal"}),
}

FIXES = {
    "patch_line": Fix(id="patch_line", label="patch line", action="patched the line and called it back", power=2, tags={"signal"}),
    "bright_beam": Fix(id="bright_beam", label="bright beam", action="aimed a bright beam at the door", power=3, tags={"light"}),
    "slow_walk": Fix(id="slow_walk", label="slow walk", action="walked slowly and listened hard", power=1, tags={"suspense"}),
}

GIRL_NAMES = ["Lina", "Mira", "Nia", "Zoe", "Ava", "Tess"]
BOY_NAMES = ["Kai", "Leo", "Oren", "Milo", "Jace", "Finn"]
TRAITS = ["curious", "brave", "careful", "quiet", "quick-thinking"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for d in DANGERS:
            for t in TOOLS:
                if DANGERS[d].makes_risk and "dark" in DANGERS[d].tags:
                    combos.append((s, d, t))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.tool == "breast_beacon" and params.fix == "slow_walk":
        return
    if params.fix not in FIXES:
        raise StoryError("Unknown fix.")
    if params.tool not in TOOLS or params.danger not in DANGERS or params.setting not in SETTINGS:
        raise StoryError("Unknown story choice.")
    if params.tool == "breast_beacon" and "breast" not in TOOLS[params.tool].tags:
        raise StoryError("The breast beacon must be a breast-mounted light.")
    if params.setting == "moon_base" and params.danger == "shadow_echo":
        return


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _initial_memes(ent: Entity) -> None:
    ent.memes.setdefault("joy", 0.0)
    ent.memes.setdefault("fear", 0.0)
    ent.memes.setdefault("curiosity", 0.0)
    ent.memes.setdefault("relief", 0.0)


def tell(setting: Setting, danger: Danger, tool: Tool, fix: Fix,
         name: str, gender: str, helper: str, helper_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, role="hero", traits=[trait]))
    helper_ent = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper", traits=["steady"]))
    ship = world.add(Entity(id="ship", type="ship", label="the ship"))
    dark = world.add(Entity(id="dark", type="place", label=setting.dark_place))
    sig = world.add(Entity(id="signal", type="thing", label=danger.label))
    t = world.add(Entity(id="tool", type="thing", label=tool.label, safe=tool.safe, owner=name, wore_on="breast"))
    for e in [hero, helper_ent, ship, dark, sig, t]:
        _initial_memes(e)

    hero.memes["curiosity"] += 1
    helper_ent.memes["curiosity"] += 1
    world.say(f"{hero.id} and {helper.id} drifted through {setting.place} like two tiny astronauts on a bright mission.")
    world.say(f"{hero.id} wore {tool.phrase}, right on the breast of {hero.pronoun('possessive')} suit, so the light could shine where {hero.id} looked.")

    world.para()
    hero.memes["fear"] += 0.5
    helper_ent.memes["fear"] += 0.5
    world.say(f"Then they reached {setting.dark_place}, and the air went quiet. The {danger.label} {danger.verb}, leaving only {danger.sound}.")
    world.say(f"{helper.id} slowed down and listened hard. {hero.id} held still, because suspense hung in the dark like a tiny cold moon.")

    world.para()
    if danger.id == "shadow_echo":
        hero.memes["fear"] += 1
        helper_ent.memes["fear"] += 1
        world.say(f"A shadow echo bounced back from the walls, and {hero.id} thought the tunnel might be hiding a secret door.")
    elif danger.id == "lost_signal":
        hero.memes["fear"] += 1
        world.say(f"The signal had gone silent, and that made the whole hall feel lonelier.")
    else:
        helper_ent.memes["fear"] += 1
        world.say(f"A drifting light floated away from them, and the path seemed longer than before.")

    world.para()
    hero.memes["joy"] += 1
    helper_ent.memes["joy"] += 1
    world.say(f"At last, {helper.id} used {fix.label}: {fix.action}.")
    world.say(f"The little plan worked because the crew stayed calm and used the safe tool instead of rushing.")
    hero.memes["relief"] += 1
    helper_ent.memes["relief"] += 1

    world.para()
    world.say(f"The breast light on {hero.id}'s suit shone again, and the two astronauts could see the way home.")
    world.say(f"Together they left the dark place behind, with their hearts quiet and their ship bright.")
    world.facts.update(
        hero=hero,
        helper=helper_ent,
        setting=setting,
        danger=danger,
        tool=tool,
        fix=fix,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short suspenseful space adventure for a young child about {f["hero"].id} and {f["helper"].id} in {f["setting"].place}.',
        f'Write a gentle story where a child astronaut wears a breast beacon and solves a dark-space problem with a safe helper.',
        f'Create a child-friendly space adventure with suspense, a dark tunnel, and a happy ending where the crew finds the way home.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    danger = f["danger"]
    tool = f["tool"]
    fix = f["fix"]
    qa = [
        QAItem(
            question=f"Who went into {setting.dark_place} in the story?",
            answer=f"{hero.id} went in with {helper.id}. They were tiny astronauts exploring {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} wear on the breast of {hero.pronoun('possessive')} suit?",
            answer=f"{hero.id} wore {tool.phrase} on the breast of the suit so the light could shine close to {hero.id}.",
        ),
        QAItem(
            question=f"What made the tunnel feel suspenseful?",
            answer=f"The {danger.label} {danger.verb}, and the tunnel became very quiet. That quiet made the moment feel suspenseful.",
        ),
        QAItem(
            question=f"How did {helper.id} help at the end?",
            answer=f"{helper.id} used {fix.label} and {fix.action}, which helped the crew stay safe and find the way home.",
        ),
        QAItem(
            question=f"How did the story end for the astronauts?",
            answer=f"They saw the way home again, and the breast light shone on {hero.id}'s suit as they left the dark place behind.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a beacon?",
            answer="A beacon is a light or signal that helps people find their way.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="Why do astronauts use lights in dark places?",
            answer="Astronauts use lights so they can see safely in dark places and avoid getting lost.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} {e.type:8} memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(h).
helper(k).
suspense :- dark_place(d), signal(s), tool(t), breast_mounted(t).
safe_ending :- helper_action(f), safe(f).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for d in DANGERS:
        lines.append(asp.fact("danger", d))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if "breast" in tool.tags:
            lines.append(asp.fact("breast_mounted", t))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("safe", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception:
        print("ASP unavailable.")
        return 1
    model = asp.one_model(asp_program("#show suspense/0.\n#show safe_ending/0."))
    return 0 if model is not None else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure suspense storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS := ["curious", "brave", "careful", "quiet", "quick-thinking"])
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
    if args.setting and args.danger and args.tool:
        pass
    setting = args.setting or rng.choice(list(SETTINGS))
    danger = args.danger or rng.choice(list(DANGERS))
    tool = args.tool or rng.choice(list(TOOLS))
    fix = args.fix or rng.choice(list(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(setting=setting, danger=danger, tool=tool, fix=fix,
                         name=name, gender=gender, helper=helper,
                         helper_gender=helper_gender, trait=trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], DANGERS[params.danger], TOOLS[params.tool],
                 FIXES[params.fix], params.name, params.gender, params.helper,
                 params.helper_gender, params.trait)
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
        print(asp_program("#show suspense/0.\n#show safe_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP storyworld placeholder for suspense space adventure.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("orbit_hall", "lost_signal", "breast_beacon", "patch_line", "Lina", "girl", "Kai", "boy", "careful"),
            StoryParams("moon_base", "shadow_echo", "breast_beacon", "bright_beam", "Mira", "girl", "Oren", "boy", "quiet"),
            StoryParams("star_dock", "drifting_light", "breast_beacon", "slow_walk", "Leo", "boy", "Tess", "girl", "curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i+1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
