#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/mammoth_jargon_sari_lesson_learned_dialogue_adventure.py
===============================================================================================================================

A standalone storyworld about an adventure in a dusty discovery hall where a
child, a guide, a mammoth display, too much jargon, and a bright sari-shaped
mistake turn into a lesson about speaking plainly.

The world is small on purpose:
- typed entities with physical meters and emotional memes
- a few causal rules that change state before the final scene
- a reasonableness gate
- inline ASP facts and rules
- three Q&A sets grounded in the simulated story

Seed premise:
- An adventurous child follows a guide into a hidden archive.
- A giant mammoth exhibit makes the room feel exciting and mysterious.
- The guide speaks in jargon, which confuses the child.
- A sari is used as a dramatic, makeshift explorer wrap and then as part of a safer, clearer solution.
- The story ends with the lesson learned: say things plainly when others need help.

This script is stdlib-only except for the shared Storyweavers result API
(results.py) and the lazy ASP helper (asp.py) used only in ASP modes.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    can_cover: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    place: str
    indoors: bool
    danger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    gear: str
    name: str
    gender: str
    guide: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "archive": Setting(id="archive", place="the old museum archive", indoors=True, danger="dust", tags={"archive", "museum"}),
    "gallery": Setting(id="gallery", place="the fossil gallery", indoors=True, danger="echoes", tags={"gallery", "museum"}),
    "hall": Setting(id="hall", place="the discovery hall", indoors=True, danger="mystery", tags={"hall", "museum"}),
}

ACTIVITIES = {
    "explore": Activity(id="explore", verb="explore the hidden hall", gerund="exploring the hidden hall", rush="dash deeper into the hall", mess="dusty", zone={"torso", "legs"}, keyword="explore", tags={"explore", "adventure"}),
    "climb": Activity(id="climb", verb="climb the display steps", gerund="climbing the display steps", rush="run up the steps", mess="scratched", zone={"feet", "legs"}, keyword="climb", tags={"climb", "adventure"}),
    "unwrap": Activity(id="unwrap", verb="unwrap the old crate", gerund="unwrapping the old crate", rush="pull at the cloth cover", mess="tangled", zone={"torso", "arms"}, keyword="unwrap", tags={"unwrap", "cloth"}),
}

PRIZES = {
    "map": Prize(id="map", label="field map", phrase="a folded field map", location="torso", tags={"map"}),
    "lantern": Prize(id="lantern", label="lantern", phrase="a brass lantern", location="torso", tags={"lantern"}),
    "badge": Prize(id="badge", label="badge", phrase="a shiny explorer badge", location="torso", tags={"badge"}),
}

GEAR = {
    "sari": Gear(id="sari", label="sari", phrase="a bright sari", covers={"torso", "arms"}, guards={"dusty", "tangled"}, tags={"sari", "cloth"}),
    "scarf": Gear(id="scarf", label="scarf", phrase="a long scarf", covers={"torso", "arms"}, guards={"dusty"}, tags={"scarf"}),
    "wrap": Gear(id="wrap", label="wrap", phrase="a soft wrap", covers={"torso"}, guards={"scratched", "dusty"}, tags={"wrap"}),
}

GIRL_NAMES = ["Mina", "Lina", "Tara", "Asha", "Nina", "Ria", "Sana", "Leela"]
BOY_NAMES = ["Arin", "Nico", "Rey", "Kian", "Milo", "Dev", "Owen", "Samir"]
TRAITS = ["curious", "bold", "careful", "bright", "spirited"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("hero")
    guide = world.entities.get("guide")
    if not child or not guide:
        return out
    if child.memes["confusion"] < THRESHOLD:
        return out
    sig = ("confusion", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    guide.memes["pressure"] += 1
    out.append("The words tangled up the plan.")
    return out


CAUSAL_RULES = [_r_confusion]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(activity: Activity, prize: Prize, gear: Gear) -> bool:
    if activity.id == "unwrap" and gear.id != "sari":
        return False
    if prize.location not in gear.covers:
        return False
    if activity.mess not in gear.guards:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for act_id, act in ACTIVITIES.items():
            for prize_id, prize in PRIZES.items():
                for gear_id, gear in GEAR.items():
                    if reasonableness_gate(act, prize, gear):
                        combos.append((place, act_id, prize_id))
    uniq = sorted(set(combos))
    return uniq


def introduce(world: World, hero: Entity, guide: Entity) -> None:
    world.say(f"{hero.id} loved adventure and followed {guide.id} into {world.setting.place}.")
    world.say(f"At the center of the room stood a giant mammoth, and its tall tusks seemed to guard every shadow.")


def setup_dialogue(world: World, hero: Entity, guide: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["excitement"] += 1
    guide.memes["certainty"] += 1
    world.say(f'"Let\'s {activity.verb}," {hero.id} said.')
    world.say(f'"Careful," {guide.id} replied, "that is a lot of jargon for a small hall."')
    world.say(f"{hero.id} frowned because the jargon made the plan feel slippery.")
    hero.memes["confusion"] += 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} held the {prize.label} close and tried to guess the next step.")


def warn_with_lesson(world: World, hero: Entity, guide: Entity, activity: Activity, prize: Entity) -> None:
    world.say(f'"Say it plainly," {hero.id} said. "I can help better when I understand."')
    guide.memes["regret"] += 1
    world.say(f'"You are right," {guide.id} said. "Plain words make a better path than fancy jargon."')
    world.say(f"The mammoth watched like a quiet teacher while the two of them slowed down and listened.")


def apply_gear(world: World, hero: Entity, guide: Entity, gear: Gear, prize: Entity) -> None:
    outfit = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, phrase=gear.phrase, can_cover=True, covers=set(gear.covers), tags=set(gear.tags)))
    outfit.worn_by = hero.id
    hero.memes["confidence"] += 1
    guide.memes["relief"] += 1
    world.say(f'{guide.id} helped {hero.id} put on {gear.phrase}, and the new wrap covered the dusty places.')
    world.say(f"With the {gear.label} in place, the {prize.label} stayed safe while they worked.")


def ending(world: World, hero: Entity, guide: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    guide.memes["love"] += 1
    world.say(f'Together they finished the {activity.keyword} job, and the {prize.label} looked bright again.')
    world.say(f'{hero.id} smiled at the mammoth and said, "Adventure is better when everyone can understand the map."')


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, gear_cfg: Gear, hero_name: str, hero_gender: str, guide_name: str, parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="child", tags={"child"}))
    guide = world.add(Entity(id="guide", kind="character", type=parent, label=guide_name, role="guide", tags={"guide"}))
    prize = world.add(Entity(id="prize", kind="thing", type="object", label=prize_cfg.label, phrase=prize_cfg.phrase, location=prize_cfg.location, tags=set(prize_cfg.tags)))
    world.facts["activity"] = activity
    world.facts["prize"] = prize_cfg
    world.facts["gear"] = gear_cfg
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["setting"] = setting
    world.facts["trait"] = trait

    introduce(world, hero, guide)
    world.para()
    setup_dialogue(world, hero, guide, activity, prize)
    world.para()
    warn_with_lesson(world, hero, guide, activity, prize)
    world.para()
    apply_gear(world, hero, guide, gear_cfg, prize)
    world.para()
    ending(world, hero, guide, activity, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    activity: Activity = f["activity"]  # type: ignore[assignment]
    prize_cfg: Prize = f["prize"]  # type: ignore[assignment]
    gear_cfg: Gear = f["gear"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    guide: Entity = f["guide"]  # type: ignore[assignment]
    return [
        f'Write an adventure story for a child named {hero.label} that includes the words "mammoth", "jargon", and "sari".',
        f"Tell a dialogue-heavy tale where {hero.label} gets confused by jargon, then learns to ask for plain words while working near a mammoth exhibit.",
        f"Write a short adventure with a lesson learned: {guide.label} should stop using jargon, and {gear_cfg.label} should help keep {prize_cfg.label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity: Activity = f["activity"]  # type: ignore[assignment]
    prize_cfg: Prize = f["prize"]  # type: ignore[assignment]
    gear_cfg: Gear = f["gear"]  # type: ignore[assignment]
    hero: Entity = f["hero"]  # type: ignore[assignment]
    guide: Entity = f["guide"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went into {setting.place} on the adventure?",
            answer=f"{hero.label} and {guide.label} went there together. The room felt huge because the mammoth display stood right in the middle.",
        ),
        QAItem(
            question=f"Why did {hero.label} get stuck on the words the first time?",
            answer=f"{guide.label} used too much jargon, so the plan sounded slippery and hard to follow. {hero.label} needed plain words to understand what to do next.",
        ),
        QAItem(
            question=f"How did the {gear_cfg.label} help with {activity.verb}?",
            answer=f"It covered the dusty or tangled parts that could have caused trouble. That let {hero.label} keep working without ruining {prize_cfg.label}.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn from the dialogue?",
            answer=f"{hero.label} learned that plain words are kinder and easier to use in a real adventure. When people speak clearly, everyone can help and stay safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags: set[str] = set()
    for key in ("activity", "prize", "gear"):
        item = world.facts[key]
        if hasattr(item, "tags"):
            tags |= set(item.tags)
    out: list[QAItem] = []
    if "mammoth" not in tags:
        tags.add("mammoth")
    if "sari" in tags:
        out.append(QAItem(
            question="What is a sari?",
            answer="A sari is a long piece of cloth that some people wear as clothing. It can also be wrapped in creative ways when a story needs a colorful helper.",
        ))
    out.append(QAItem(
        question="What is jargon?",
        answer="Jargon is special language that can make a simple idea sound harder than it is. It is useful with experts, but children often need plainer words.",
    ))
    out.append(QAItem(
        question="What is a mammoth?",
        answer="A mammoth was a giant, woolly animal that lived long ago. People still talk about mammoths when they want something huge and impressive.",
    ))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.covers:
            parts.append(f"covers={sorted(e.covers)}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", activity="explore", prize="map", gear="sari", name="Mina", gender="girl", guide="Aunt Rhea", parent="woman", trait="curious"),
    StoryParams(place="gallery", activity="unwrap", prize="lantern", gear="sari", name="Arin", gender="boy", guide="Guide Nila", parent="woman", trait="bright"),
    StoryParams(place="archive", activity="climb", prize="badge", gear="sari", name="Sana", gender="girl", guide="Mr. Voss", parent="man", trait="spirited"),
]


def explain_rejection(args: argparse.Namespace) -> str:
    return "(No story: the chosen activity, prize, and gear do not make a sensible adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a mammoth, jargon, and a sari.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["woman", "man"])
    ap.add_argument("--guide")
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError(explain_rejection(args))
    place, activity, prize = rng.choice(sorted(combos))
    gear = args.gear or "sari"
    if gear != "sari":
        raise StoryError("This world expects the sari as the helpful wrap for the adventure.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["Guide Nila", "Aunt Rhea", "Mr. Voss"])
    parent = args.parent or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, gear=gear, name=name, gender=gender, guide=guide, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.activity not in ACTIVITIES or params.prize not in PRIZES or params.gear not in GEAR:
        raise StoryError("Invalid parameters for this world.")
    if params.gear != "sari":
        raise StoryError("The sari is the fixed helpful gear in this adventure world.")
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], GEAR[params.gear], params.name, params.gender, params.guide, params.parent, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(archive;gallery;hall).
activity(explore;climb;unwrap).
prize(map;lantern;badge).
gear(sari).

valid(P,A,R) :- place(P), activity(A), prize(R), gear(sari).
lesson_learned(P,A,R) :- valid(P,A,R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    lines.append(asp.fact("gear", "sari"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP valid-combos.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show lesson_learned/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        if len(samples) > 1 and not args.all:
            print(f"### variant {i + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.name}: {p.activity} at {p.place} with {p.gear}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
