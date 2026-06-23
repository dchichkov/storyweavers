#!/usr/bin/env python3
"""
storyworlds/worlds/uniform_fashion_humor_superhero_story.py
===========================================================

A small storyworld about superhero uniforms, fashion, and a funny fix.

Premise:
- A child superhero loves fashion and wants to show off a uniform.
- A tiny problem makes the uniform look silly at the worst moment.
- A helper or grown-up finds a humorous, sensible fix.
- The ending proves the uniform and fashion problem changed in the world.

This script follows the Storyweavers storyworld contract:
- stdlib-only prose engine
- shared results import eagerly
- lazy ASP helper import
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python reasonableness gate plus inline ASP twin
- grounded prompts, story QA, and world knowledge QA
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

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

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "traits": list(e.traits), "role": e.role,
            "owner": e.owner, "caretaker": e.caretaker, "worn_by": e.worn_by,
            "plural": e.plural, "tags": set(e.tags), "attrs": dict(e.attrs),
            "meters": defaultdict(float, e.meters), "memes": defaultdict(float, e.memes)
        }) for k, e in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = [dict(x) for x in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Setting:
    place: str
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Outfit:
    id: str
    label: str
    phrase: str
    wear: str
    region: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    label: str
    effect: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    outfit: str
    mishap: str
    fix: str
    hero: str
    hero_type: str
    partner: str
    partner_type: str
    seed: Optional[int] = None


SETTINGS = {
    "city_plaza": Setting(place="the city plaza", vibe="bright and busy", affords={"parade", "show"}),
    "school_stage": Setting(place="the school stage", vibe="crowded and giggly", affords={"show"}),
    "roof_garden": Setting(place="the roof garden", vibe="windy and sunny", affords={"parade", "show"}),
}

OUTFITS = {
    "cape": Outfit(id="cape", label="cape", phrase="a red cape", wear="wore", region="back", style="dramatic", tags={"cape", "fashion"}),
    "boots": Outfit(id="boots", label="boots", phrase="shiny boots", wear="wore", region="feet", style="flashy", tags={"boots", "fashion"}),
    "mask": Outfit(id="mask", label="mask", phrase="a starry mask", wear="wore", region="face", style="fancy", tags={"mask", "fashion"}),
    "suit": Outfit(id="suit", label="uniform", phrase="a bright uniform", wear="wore", region="torso", style="heroic", tags={"uniform", "fashion"}),
}

MISHAPS = {
    "spaghetti": Mishap(id="spaghetti", label="spaghetti sauce", effect="splashed", mess="red sauce", risk="stain", tags={"food", "mess"}),
    "confetti": Mishap(id="confetti", label="confetti cannon", effect="popped", mess="sticky confetti", risk="scraps", tags={"party", "mess"}),
    "goop": Mishap(id="goop", label="slime bucket", effect="slid", mess="green goop", risk="slime", tags={"slime", "mess"}),
}

FIXES = {
    "smock": Fix(id="smock", label="smock", phrase="a spare smock", action="put on", result="covered the stain", power=2, tags={"cloth", "fashion"}),
    "soap": Fix(id="soap", label="soap and water", phrase="soap and water", action="washed with", result="made the mess vanish", power=3, tags={"clean", "help"}),
    "tape": Fix(id="tape", label="tape star", phrase="a giant sticker star", action="covered it with", result="made the uniform look even sillier and better", power=1, tags={"funny", "fashion"}),
}

GIRL_NAMES = ["Maya", "Nina", "Zoe", "Ava", "Lila", "Rosa"]
BOY_NAMES = ["Ben", "Kai", "Leo", "Noah", "Finn", "Eli"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for s in SETTINGS:
        for o in OUTFITS:
            for m in MISHAPS:
                for f in FIXES:
                    if outfit_at_risk(OUTFITS[o], MISHAPS[m]) and fix_helps(FIXES[f], OUTFITS[o], MISHAPS[m]):
                        combos.append((s, o, m, f))
    return combos


def outfit_at_risk(outfit: Outfit, mishap: Mishap) -> bool:
    if outfit.region == "back" and mishap.id == "spaghetti":
        return True
    if outfit.region == "feet" and mishap.id == "goop":
        return True
    if outfit.region == "face" and mishap.id == "confetti":
        return True
    if outfit.label == "uniform":
        return True
    return mishap.id in {"spaghetti", "confetti", "goop"}


def fix_helps(fix: Fix, outfit: Outfit, mishap: Mishap) -> bool:
    if fix.id == "soap":
        return mishap.id in {"spaghetti", "goop"}
    if fix.id == "smock":
        return outfit.region in {"back", "torso"}
    if fix.id == "tape":
        return outfit.label == "cape" and mishap.id == "confetti"
    return False


def explain_rejection(outfit: Outfit, mishap: Mishap) -> str:
    return f"(No story: {mishap.label} is not a believable problem for {outfit.phrase} in this setup.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Humorous superhero fashion storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--outfit", choices=OUTFITS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-type", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
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
    if args.outfit and args.mishap:
        if not outfit_at_risk(OUTFITS[args.outfit], MISHAPS[args.mishap]):
            raise StoryError(explain_rejection(OUTFITS[args.outfit], MISHAPS[args.mishap]))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.outfit is None or c[1] == args.outfit)
              and (args.mishap is None or c[2] == args.mishap)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, outfit, mishap, fix = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_type)
    partner = args.partner or _pick_name(rng, partner_type)
    if partner == hero:
        partner = _pick_name(rng, partner_type)
    return StoryParams(setting=setting, outfit=outfit, mishap=mishap, fix=fix, hero=hero, hero_type=hero_type, partner=partner, partner_type=partner_type)


def story_can_read(params: StoryParams) -> bool:
    return params.outfit in OUTFITS and params.mishap in MISHAPS and params.fix in FIXES and params.setting in SETTINGS


def tell(params: StoryParams) -> World:
    if not story_can_read(params):
        raise StoryError("Invalid story params.")
    world = World()
    setting = SETTINGS[params.setting]
    outfit = OUTFITS[params.outfit]
    mishap = MISHAPS[params.mishap]
    fix = FIXES[params.fix]

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero", traits=["funny", "brave"]))
    partner = world.add(Entity(id=params.partner, kind="character", type=params.partner_type, role="partner", traits=["helpful", "cheery"]))
    costume = world.add(Entity(id="outfit", type="thing", label=outfit.label, phrase=outfit.phrase, owner=hero.id, worn_by=hero.id, tags=set(outfit.tags)))
    trouble = world.add(Entity(id="mishap", type="thing", label=mishap.label, phrase=mishap.label, tags=set(mishap.tags)))
    repair = world.add(Entity(id="fix", type="thing", label=fix.label, phrase=fix.phrase, tags=set(fix.tags)))

    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.facts.update(setting=setting, outfit=outfit, mishap=mishap, fix=fix, hero=hero, partner=partner, costume=costume, trouble=trouble, repair=repair)

    world.say(f"{hero.id} loved fashion almost as much as saving the day, and {partner.id} loved laughing at the results.")
    world.say(f"At {setting.place}, the two of them planned a superhero show. {hero.id} put on {outfit.phrase}, and {partner.id} cheered at the dramatic pose.")
    world.say(f"Everything looked heroic until {mishap.label} {mishap.effect} right onto the {outfit.label}. Suddenly the {outfit.label} looked very serious, very sticky, and a little bit embarrassed.")

    world.para()
    hero.memes["embarrassment"] += 1
    world.say(f"{partner.id} blinked. \"That is either a fashion emergency or a new trend,\" {partner.id} said.")
    world.say(f"{hero.id} gasped, then laughed. The problem was messy, but the joke landed on its feet.")

    world.para()
    if fix.id == "soap":
        repair.meters["power"] += 1
        costume.meters["clean"] += 1
        world.say(f"{partner.id} came back with {fix.phrase} and {fix.action} the {outfit.label}. In moments, the mess {fix.result}.")
        world.say(f"{hero.id} struck a pose in the shiny clean {outfit.label}. It still looked like a superhero uniform, only now it smelled like bubbles.")
    elif fix.id == "smock":
        costume.meters["covered"] += 1
        world.say(f"{partner.id} grabbed {fix.phrase} and {fix.action} the stained {outfit.label}. The smock {fix.result}, and the costume looked ready for a very silly museum exhibit.")
        world.say(f"{hero.id} declared, \"This is high fashion for heroes who spill lunch.\"")
    else:
        costume.meters["sticky"] += 1
        world.say(f"{partner.id} peeled on {fix.phrase} and {fix.action} the spot. It {fix.result}, which made both of them laugh even harder.")
        world.say(f"{hero.id} marched on anyway, with a uniform that now had the personality of a joke book.")
    world.say(f"By the end, the superhero fashion show was a hit, the {outfit.label} was fixed or improved, and the whole crowd agreed that laughter was the best accessory.")

    world.event("story_end", setting=setting.place, outfit=outfit.label, mishap=mishap.label, fix=fix.label)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a funny superhero story about {f['hero'].id} in a {f['outfit'].label} who has a fashion problem at {f['setting'].place}. Include the words uniform and fashion.",
        f"Tell a humorous superhero story where {f['partner'].id} helps fix a messy costume problem with {f['fix'].label}.",
        f"Write a short child-friendly story about a superhero fashion show, a silly mishap, and a cheerful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    outfit = f["outfit"]
    mishap = f["mishap"]
    fix = f["fix"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {hero.id} and {partner.id}. They tried to have a superhero fashion show at {setting.place}, and that is where the funny trouble started."
        ),
        QAItem(
            question=f"What happened to the {outfit.label}?",
            answer=f"{mishap.label.capitalize()} made a mess on it, so the outfit looked silly instead of perfect. That turned the costume into part of the joke, which kept the story playful."
        ),
        QAItem(
            question=f"How did they fix the problem?",
            answer=f"They used {fix.phrase} to solve it, and the result was funny but helpful. The uniform ended the story looking neat enough for the show, with everyone laughing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["outfit"].tags) | set(f["mishap"].tags) | set(f["fix"].tags)
    out: list[QAItem] = []
    if "uniform" in tags:
        out.append(QAItem("What is a uniform?", "A uniform is a matching outfit that shows someone belongs to a team, job, or group. People often wear uniforms so they look the same and are easy to recognize."))
    if "fashion" in tags:
        out.append(QAItem("What is fashion?", "Fashion means the clothes people like to wear and how they style them. It can be fun, silly, fancy, or practical."))
    if "clean" in tags:
        out.append(QAItem("Why do people clean clothes?", "People clean clothes to wash away dirt, stains, and sticky messes. Clean clothes feel fresh and are easier to wear again."))
    if "funny" in tags:
        out.append(QAItem("Why can a costume problem be funny?", "It can be funny because the hero expected to look amazing, but the mess made things awkward in a harmless way. A joke can make a small mistake feel light instead of scary."))
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  history events: {len(world.history)}")
    return "\n".join(lines)


ASP_RULES = r"""
outfit_at_risk(O,M) :- outfit(O), mishap(M), risky(O,M).
fix_helps(F,O,M) :- fix(F), outfit(O), mishap(M), helps(F,O,M).
valid(S,O,M,F) :- setting(S), outfit(O), mishap(M), fix(F), outfit_at_risk(O,M), fix_helps(F,O,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OUTFITS.items():
        lines.append(asp.fact("outfit", oid))
        if o.label == "uniform":
            lines.append(asp.fact("is_uniform", oid))
        for t in sorted(o.tags):
            lines.append(asp.fact("tag", oid, t))
    for mid, m in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for t in sorted(f.tags):
            lines.append(asp.fact("tag", fid, t))
    for s, o, m, f in valid_combos():
        lines.append(asp.fact("risky", o, m))
        lines.append(asp.fact("helps", f, o, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid combos.")
        print("only in python:", sorted(py - cl))
        print("only in asp:", sorted(cl - py))
    else:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"ERROR: generate() smoke test failed: {exc}")
        ok = False
    return 0 if ok else 1


def valid_combo_filter(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = valid_combos()
    return [c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.outfit is None or c[1] == args.outfit)
            and (args.mishap is None or c[2] == args.mishap)
            and (args.fix is None or c[3] == args.fix)]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(setting="city_plaza", outfit="suit", mishap="spaghetti", fix="soap", hero="Maya", hero_type="girl", partner="Ben", partner_type="boy"),
    StoryParams(setting="school_stage", outfit="cape", mishap="confetti", fix="tape", hero="Leo", hero_type="boy", partner="Ava", partner_type="girl"),
    StoryParams(setting="roof_garden", outfit="mask", mishap="goop", fix="smock", hero="Nina", hero_type="girl", partner="Kai", partner_type="boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combo_filter(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, outfit, mishap, fix = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_type)
    partner = args.partner or _pick_name(rng, partner_type)
    if partner == hero:
        partner = _pick_name(rng, partner_type)
    return StoryParams(setting=setting, outfit=outfit, mishap=mishap, fix=fix, hero=hero, hero_type=hero_type, partner=partner, partner_type=partner_type)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.partner}: {p.outfit} / {p.mishap} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
