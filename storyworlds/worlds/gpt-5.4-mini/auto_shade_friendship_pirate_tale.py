#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/auto_shade_friendship_pirate_tale.py
=====================================================================

A standalone tiny storyworld for a friendship-and-adventure tale in a pirate
play frame. Two friends sail an auto-cart pirate rig on a sunny path, need shade
for a tired pet or snack, make a risky choice, then choose a sensible fix and
end with a bright shared solution.

Seed words:
- auto
- shade

Style:
- Pirate Tale
- Friendship
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
SENSE_MIN = 2


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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    breeze: str
    scene: str
    has_sun: bool = True


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    use: str
    at: str
    needs: str
    safe: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scorch(world: World) -> list[str]:
    out: list[str] = []
    shade = world.entities.get("shade")
    if not shade:
        return out
    if shade.meters["used"] < THRESHOLD:
        return out
    sig = ("scorch", shade.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shade.meters["tattered"] += 1
    for ch in world.characters():
        ch.memes["worry"] += 1
    out.append("__heat__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("shade") and world.entities["shade"].meters["fixed"] >= THRESHOLD:
        sig = ("relief", "shade")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for ch in world.characters():
            ch.memes["relief"] += 1
            ch.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("scorch", "physical", _r_scorch),
    Rule("relief", "social", _r_relief),
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


def risk_at_hand(risk: Thing, target: Thing) -> bool:
    return risk.safe and not target.safe


def sensible_risks() -> list[Risk]:
    return [r for r in RISKS.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Thing, delay: int) -> int:
    return 1 + delay if target.safe is False else 0


def is_safe_fix(risk: Risk, target: Thing, delay: int) -> bool:
    return risk.power >= fire_severity(target, delay)


def tell(setting: Setting, risk: Thing, target: Thing, fix: Risk,
         hero: str = "Mara", hero_gender: str = "girl",
         friend: str = "Finn", friend_gender: str = "boy",
         captain: str = "mother", delay: int = 0,
         pet: str = "", snack: str = "") -> World:
    world = World(setting)
    a = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    b = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=captain, role="parent", label="the parent"))
    auto = world.add(Entity(id="auto", type="thing", label=risk.label))
    shade_ent = world.add(Entity(id="shade", type="thing", label=target.label))
    a.memes["brave"] = 2
    b.memes["loyal"] = 2
    world.facts["pet"] = pet
    world.facts["snack"] = snack

    world.say(f"On a bright day, {hero} and {friend} turned the yard into {setting.scene}.")
    world.say(f"Their pirate auto rolled along like a tiny ship, and the breeze felt {setting.breeze}.")
    world.say(f'"We need {target.use}," said {friend}. "{target.needs} would be perfect for the crew."')

    world.para()
    a.memes["want"] += 1
    b.memes["care"] += 1
    world.say(f"{hero} spotted {risk.phrase} and grinned. " + f'"I know! We can use the {risk.label} for shade."')
    world.say(f"{friend} bit {friend}\'s lip. " + f'"{risk.label} makes real trouble near the sun," {friend} warned.')
    world.facts["warned"] = True

    if setting.has_sun and risk_at_hand(risk, target):
        if delay == 0:
            world.say(f"{hero} listened for a moment, but the shiny idea still tugged like a rope in the wind.")
            world.say(f"Then {hero} ran to the {risk.label} and pulled it into place over the {target.label}.")
            auto.meters["used"] += 1
            shade_ent.meters["used"] += 1
            propagate(world, narrate=False)
            world.para()
            world.say(f"{risk.id.capitalize()} slipped into place, but the sun crept under it and warmed the {target.label}.")
            if is_safe_fix(fix, target, delay):
                shade_ent.meters["fixed"] = 1
                world.say(f"{parent.label_word.capitalize()} came over at once and {fix.text.replace('{target}', target.label)}.")
                world.say(f"The little crew cheered when the {target.label} stayed cool again.")
                world.say(f"{hero} and {friend} sat in the new shade, side by side, like true pirate mates.")
                outcome = "fixed"
            else:
                world.say(f"{parent.label_word.capitalize()} came running, but {fix.fail.replace('{target}', target.label)}.")
                world.say(f"The shade flapped, the heat won, and the crew had to move away fast.")
                outcome = "bad"
        else:
            world.say(f"{hero} almost used the {risk.label}, but {friend} pointed to the sun and to the {target.label}.")
            world.say(f"{hero} thought again, nodded, and chose a safer plan before any trouble started.")
            shade_ent.meters["fixed"] = 1
            world.para()
            world.say(f"{parent.label_word.capitalize()} smiled and helped them set up the {target.label} the right way.")
            world.say(f"At last the pirates had cool shade, a happy crew, and no risky tricks at all.")
            outcome = "avoided"
    else:
        world.say(f"The sun hid behind clouds, so the {risk.label} never seemed like a real problem.")
        shade_ent.meters["fixed"] = 1
        outcome = "calm"

    world.facts.update(
        hero=a, friend=b, parent=parent, risk=risk, target_cfg=target, fix=fix,
        auto=auto, shade=shade_ent, outcome=outcome, delay=delay
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["hero"], f["friend"]
    risk, target = f["risk"], f["target_cfg"]
    return [
        f'Write a pirate-style friendship story for a young child that uses the words "auto" and "shade".',
        f"Tell a story where {a.id} and {b.id} want to make {target.label} for their pirate auto, but a risky idea about {risk.label} must be replaced with a safer one.",
        f'Write a gentle adventure story where friends choose safe shade instead of a dangerous shortcut and end happy together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["hero"], f["friend"], f["parent"]
    risk, target, fix = f["risk"], f["target_cfg"], f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two friends who were playing pirate crew together. {parent.label_word.capitalize()} was there too to help them stay safe."),
        ("What did they want to build?",
         f"They wanted {target.use} for their pirate auto. That would give the crew {target.needs} during their adventure."),
        (f"What risky idea did {a.id} have?",
         f"{a.id} wanted to use {risk.label} for shade, but that was not a safe idea. {b.id} warned that the sun and the {target.label} needed a real, safer fix."),
    ]
    if f["outcome"] in {"fixed", "avoided"}:
        qa.append((
            "How did they solve the problem?",
            f"They chose {fix.text.replace('{target}', target.label)}. That gave them shade without the risky shortcut, so the friends could keep playing together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the two friends safe and happy in the shade. Their pirate game could go on because they worked together and picked the sensible choice."
        ))
    else:
        qa.append((
            "What happened when the risky plan was tried?",
            f"The sun warmed the {target.label} and the crew had to move away quickly. {parent.label_word.capitalize()} had to come help them with a better fix."
        ))
    return qa


KNOWLEDGE = {
    "auto": [("What is an auto?",
              "An auto is a vehicle that can carry people from place to place. In a story, it can also be a pretend pirate ship on wheels.")],
    "shade": [("What is shade?",
               "Shade is a cool place out of the direct sun, often made by a tree, umbrella, or roof.")],
    "sun": [("Why do people look for shade on a hot day?",
             "Shade helps them feel cooler because it blocks some of the sun's warmth.")],
    "friendship": [("What does friendship mean?",
                    "Friendship means caring about someone, helping them, and having fun together.")],
    "umbrella": [("What does an umbrella do?",
                  "An umbrella can give shade or keep rain off people. It is a simple tool for protection.")],
}
KNOWLEDGE_ORDER = ["auto", "shade", "sun", "friendship", "umbrella"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["risk"].tags) | set(world.facts["target_cfg"].tags) | {"friendship"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for e in world.entities.values():
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


SETTINGS = {
    "harbor": Setting("harbor", "the harbor", "cool", "the harbor yard"),
    "deck": Setting("deck", "the deck", "salty", "the deck and pier"),
    "beach": Setting("beach", "the beach", "warm", "the beach road"),
}

THINGS = {
    "auto_shade": Thing("auto_shade", "striped cloth", "a striped cloth", "use for shade", "the sun", "real shade", tags={"shade"}),
    "umbrella_shade": Thing("umbrella_shade", "big umbrella", "a big umbrella", "use for shade", "the sun", "real shade", tags={"shade", "umbrella"}),
    "canopy": Thing("canopy", "canvas canopy", "a canvas canopy", "use for shade", "the sun", "cool shade", tags={"shade"}),
}

RISKS = {
    "fast_wheel": Risk("fast_wheel", 3, 3,
                       "spotted a loose wheel on the auto and tried to fix it with a sailcloth shortcut",
                       "could not fix the wheel in time",
                       "used the quick wheel fix",
                       tags={"auto"}),
    "shade_net": Risk("shade_net", 3, 2,
                      "grabbed the shade net and tied it between poles",
                      "could not keep the shade net steady",
                      "tied the shade net in place",
                      tags={"shade"}),
    "sail": Risk("sail", 2, 2,
                 "raised the little sail cloth over the cart",
                 "could not hold the sail cloth steady",
                 "raised the sail cloth safely",
                 tags={"auto", "shade"}),
}

FIXES = {
    "canopy": Risk("canopy", 3, 4,
                   "lashed the canopy to the poles and stretched it tight",
                   "could not lash the canopy tight enough",
                   "lashed the canopy tight",
                   tags={"shade"}),
    "park_tree": Risk("park_tree", 3, 3,
                      "moved the auto under the nearest tree",
                      "could not get the auto under the tree soon enough",
                      "moved under the tree",
                      tags={"shade"}),
}

CURATED = [
    ("harbor", "sail", "canopy"),
    ("deck", "shade_net", "park_tree"),
    ("beach", "fast_wheel", "canopy"),
]

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, risk in RISKS.items():
            for fid, fix in FIXES.items():
                if risk_at_hand(risk, THINGS["auto_shade"]) and is_safe_fix(fix, THINGS["auto_shade"], 0):
                    combos.append((sid, rid, fid))
    return combos


@dataclass
class StoryParams:
    setting: str
    risk: str
    fix: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-friendship storyworld with auto and shade.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              and (args.risk is None or c[1] == args.risk)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, risk, fix = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting, risk=risk, fix=fix,
        hero=args.name or rng.choice(["Mara", "Lina", "Pip", "Tess"]),
        hero_gender="girl",
        friend=args.friend or rng.choice(["Finn", "Noah", "Jace", "Milo"]),
        friend_gender="boy",
        parent=args.parent or rng.choice(["mother", "father"]),
        delay=0,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], THINGS["auto_shade"], THINGS["umbrella_shade"], RISKS[params.risk],
                 hero=params.hero, hero_gender=params.hero_gender, friend=params.friend,
                 friend_gender=params.friend_gender, captain=params.parent, delay=params.delay)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,R,F) :- setting(S), risk(R), fix(F).
sensible(R) :- risk(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_risks()}:
        rc = 1
        print("MISMATCH in sensible risks")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, risk=None, fix=None, parent=None, name=None, friend=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def sensible_risks() -> list[Risk]:
    return [r for r in RISKS.values() if r.sense >= SENSE_MIN]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"sensible risks: {', '.join(asp_sensible())}")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(s, r, f, "Mara", "girl", "Finn", "boy", "mother")) for s, r, f in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
