#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pesky_reconciliation_superhero_story.py
=======================================================================

A standalone story world for a small superhero tale about a pesky disruption,
a worried team, and a reconciliation that makes the city feel safe again.

Premise
-------
A kid hero is working with a teammate in a tiny city scene. One teammate is
being pesky, the mission gets derailed, and the pair has to repair the hurt,
apologize, and reconcile before the final rescue.

The world uses typed entities with physical meters and emotional memes.
State drives the prose: a pesky action changes the scene, the team responds,
and reconciliation changes the ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/pesky_reconciliation_superhero_story.py
    python storyworlds/worlds/gpt-5.4-mini/pesky_reconciliation_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/pesky_reconciliation_superhero_story.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/pesky_reconciliation_superhero_story.py --verify
    python storyworlds/worlds/gpt-5.4-mini/pesky_reconciliation_superhero_story.py --json
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
    kind: str = "thing"          # character | thing | place
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
class Setting:
    id: str
    place: str
    scene: str
    danger_spot: str
    ending_image: str

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
class Mission:
    id: str
    action: str
    code: str
    danger: str
    repair: str
    keyword: str = "pesky"

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
class Fix:
    id: str
    action: str
    result: str
    comfort: str
    sense: int = 3
    power: int = 3

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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def chars(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    pest = world.get("partner")
    if pest.meters["pesky"] < THRESHOLD:
        return out
    sig = ("spoil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mission").meters["scattered"] += 1
    world.get("hero").memes["frustration"] += 1
    world.get("partner").memes["hurt"] += 1
    out.append("__spoil__")
    return out


def _r_reconcile(world: World) -> list[str]:
    hero = world.get("hero")
    partner = world.get("partner")
    if hero.memes["apology"] < THRESHOLD or partner.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["peace"] += 1
    partner.memes["peace"] += 1
    hero.memes["frustration"] = 0.0
    partner.memes["hurt"] = 0.0
    return ["__reconcile__"]


RULES = [Rule("spoil", _r_spoil), Rule("reconcile", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                produced.extend(m for m in msgs if not m.startswith("__"))
    if narrate:
        for msg in produced:
            world.say(msg)
    return produced


def compatible_combo(setting: Setting, mission: Mission, fix: Fix) -> bool:
    return mission.danger in {"noise", "mess", "delay"} and fix.power >= 3


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            for fid, fix in FIXES.items():
                if compatible_combo(setting, mission, fix):
                    out.append((sid, mid, fid))
    return out


def choose_fix() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 3]


def _do_mission(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    partner = world.get("partner")
    mission = world.get("mission")
    hero.meters["mission"] += 1
    partner.meters["pesky"] += 1
    partner.memes["mischief"] += 1
    world.say(
        f"In {world.setting.place}, {hero.id} and {partner.id} launched {mission.code}. "
        f"{world.setting.scene}"
    )
    world.say(
        f'“Let’s be superheroes!” {hero.id} said, and the two of them hurried toward '
        f'{world.setting.danger_spot}.'
    )
    propagate(world, narrate=narrate)


def predict_spoil(world: World) -> dict:
    sim = world.copy()
    _do_mission(sim, narrate=False)
    return {
        "spoiled": sim.get("mission").meters["scattered"] >= THRESHOLD,
        "frustration": sim.get("hero").memes["frustration"],
    }


def set_up(world: World, hero: Entity, partner: Entity) -> None:
    hero.memes["hope"] += 1
    partner.memes["hope"] += 1
    world.say(
        f"{hero.id} wore a bright cape, and {partner.id} wore a shiny mask. "
        f"They wanted to help {world.setting.place} feel safe."
    )


def pesky_turn(world: World, mission: Mission) -> None:
    world.say(
        f'But the {mission.keyword} idea got in the way. {world.get("partner").id} '
        f'kept making {mission.danger} on purpose, just to be silly.'
    )
    world.say(
        f"That was getting rather pesky, and {world.get('hero').id} could not finish "
        f"the rescue plan."
    )


def warn(world: World, hero: Entity, partner: Entity, mission: Mission) -> bool:
    pred = predict_spoil(world)
    if not pred["spoiled"]:
        return False
    hero.memes["worry"] += 1
    world.facts["predicted_frustration"] = pred["frustration"]
    world.say(
        f'"{partner.id}, please stop," {hero.id} said. "If you keep doing that '
        f'{mission.keyword} thing, the plan will break and our team will feel sad."'
    )
    return True


def apologize(world: World, hero: Entity, partner: Entity, mission: Mission) -> None:
    hero.memes["apology"] += 1
    partner.memes["forgiveness"] += 1
    world.say(
        f'{hero.id} took a deep breath. “I was upset,” {hero.pronoun()} said, '
        f'“but I still want to work with you.”'
    )
    world.say(
        f"{partner.id} looked down, then nodded. “I’m sorry for being pesky,” "
        f"{partner.id} whispered."
    )
    propagate(world, narrate=False)


def repair(world: World, hero: Entity, partner: Entity, fix: Fix, setting: Setting) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"Together they used {fix.action}. {fix.result.capitalize()}, and the city "
        f"grew quiet again."
    )
    world.say(
        f"{setting.ending_image} showed their teamwork: {hero.id} and {partner.id} "
        f"stood side by side, no longer cross, only calm."
    )


def tell(setting: Setting, mission: Mission, fix: Fix, hero_name: str, partner_name: str,
         hero_gender: str, partner_gender: str, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    parent = world.add(Entity(id="guide", kind="character", type=parent_type, role="guide", label="the guide"))
    mission_ent = world.add(Entity(id="mission", kind="thing", type="mission", label=mission.id))
    world.add(parent)

    set_up(world, hero, partner)
    world.para()
    _do_mission(world, narrate=False)
    pesky_turn(world, mission)
    warn(world, hero, partner, mission)
    if world.get("mission").meters["scattered"] >= THRESHOLD:
        world.para()
        apologize(world, hero, partner, mission)
        repair(world, hero, partner, fix, setting)
    else:
        world.say("Their plan stayed neat and quick.")
    world.facts.update(
        hero=hero, partner=partner, parent=parent, mission=mission, fix=fix, setting=setting,
        outcome="reconciled" if hero.memes["apology"] >= THRESHOLD else "steady",
    )
    return world


SETTINGS = {
    "rooftop": Setting("rooftop", "the rooftop", "The stars blinked above the tall buildings.", "the open skyline", "Their capes fluttered like flags in the wind."),
    "alley": Setting("alley", "the alley", "The alley was narrow, but the lanterns made it bright.", "the brick wall", "The wet pavement shone like a mirror."),
    "park": Setting("park", "the park", "The park was full of benches, trees, and a sleepy fountain.", "the fountain path", "The water sparkled under the moonlight."),
}

MISSIONS = {
    "signal": Mission("signal", "send a signal", "the signal mission", "noise", "reset the beacon"),
    "cleanup": Mission("cleanup", "clear the mess", "the cleanup mission", "mess", "sweep the sidewalk"),
    "search": Mission("search", "search for clues", "the search mission", "delay", "sort the clues"),
}

FIXES = {
    "breath": Fix("breath", "take a breath and listen", "the team remembered to talk first", "a little calmer"),
    "apology": Fix("apology", "say sorry and try again", "their voices softened", "kind and brave"),
    "hug": Fix("hug", "share a quick hug", "their hearts felt lighter", "warm and safe"),
}

HERO_NAMES = ["Maya", "Lina", "Noah", "Ben", "Ava", "Theo", "Zoe", "Eli"]
PARTNER_NAMES = ["Pip", "Rue", "Toby", "Nia", "Jax", "Milo", "Ivy", "Kai"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    mission: str
    fix: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a preschooler that includes the word "pesky" and ends with reconciliation.',
        f"Tell a small superhero story where {f['hero'].id} and {f['partner'].id} have a pesky disagreement during {f['mission'].id}, then make up and finish the mission.",
        f"Write a gentle superhero story about teamwork, apology, and reconciliation in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, partner, mission, fix = f["hero"], f["partner"], f["mission"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {partner.id}, two superheroes who try to work together. Their teamwork gets messy for a moment, but they fix it by talking."),
        ("What made the story pesky?",
         f"{partner.id} kept making {mission.danger} on purpose, which got in the way of the plan. That silly trouble made the mission feel pesky and hard to finish."),
        ("How did they make up?",
         f"{hero.id} and {partner.id} apologized, listened, and used {fix.action}. After that, they reconciled and felt calm again."),
    ]
    if f["outcome"] == "reconciled":
        qa.append((
            "How did the story end?",
            f"It ended with reconciliation. The heroes stood side by side, the problem was repaired, and the city looked safe and peaceful again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a superhero do?",
         "A superhero helps others, solves problems, and tries to keep people safe. Superheroes can work as a team, too."),
        ("What is reconciliation?",
         "Reconciliation is when people stop fighting, apologize, and become friendly again. It helps everyone feel better and work together."),
        ("Why should a pesky problem be handled with care?",
         "A pesky problem can make teamwork harder if nobody listens. Talking kindly and repairing hurt can turn it into a better ending."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this combination does not give a believable superhero reconciliation beat.)"


ASP_RULES = r"""
spoil :- pesky(P), P >= pesky_min.
reconcile :- apology(H), forgiveness(P), H >= 1, P >= 1.
valid(S, M, F) :- setting(S), mission(M), fix(F), mission_ok(M), fix_ok(F).
outcome(reconciled) :- spoil, reconcile.
outcome(steady) :- not spoil.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_ok", mid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_ok", fid))
    lines.append(asp.fact("pesky_min", 1))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("setting", params.setting),
        asp.fact("mission", params.mission),
        asp.fact("fix", params.fix),
        asp.fact("apology", 1),
        asp.fact("forgiveness", 1),
        asp.fact("pesky", 1),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    import json as _json
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print(_json.dumps({"python_only": sorted(py - cl), "asp_only": sorted(cl - py)}, indent=2))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero reconciliation story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--partner", choices=PARTNER_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mission is None or c[1] == args.mission)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mission, fix = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    partner = args.partner or rng.choice([n for n in PARTNER_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    hg = "girl" if hero in {"Maya", "Lina", "Ava", "Zoe"} else "boy"
    pg = "girl" if partner in {"Rue", "Nia", "Ivy"} else "boy"
    return StoryParams(setting, mission, fix, hero, hg, partner, pg, parent)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for mid in MISSIONS:
            for fid in FIXES:
                out.append((sid, mid, fid))
    return out


CURATED = [
    StoryParams("rooftop", "signal", "apology", "Maya", "girl", "Pip", "boy", "mother"),
    StoryParams("alley", "cleanup", "breath", "Noah", "boy", "Rue", "girl", "father"),
    StoryParams("park", "search", "hug", "Ava", "girl", "Kai", "boy", "mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MISSIONS[params.mission], FIXES[params.fix],
                 params.hero_name, params.partner_name, params.hero_gender,
                 params.partner_gender, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
