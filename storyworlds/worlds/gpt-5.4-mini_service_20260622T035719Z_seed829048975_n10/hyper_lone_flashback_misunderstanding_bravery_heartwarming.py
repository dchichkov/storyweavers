#!/usr/bin/env python3
"""
storyworlds/worlds/hyper_lone_flashback_misunderstanding_bravery_heartwarming.py
===============================================================================

A small storyworld about a hyper little helper, a lone porch, a flashback
misunderstanding, and a brave heartwarming fix.

Seed tale idea:
---
A hyper child named Jo is alone in a quiet garden shed with a lonely kite box.
They remember a flashback of being blamed for a broken lantern and worry that
a new misunderstanding will happen again. When the garden light goes out, Jo
bravely climbs a stool to fetch a spare bulb for Grandma, and the mistake turns
into a warm laugh and a hug.

The world model keeps both physical meters and emotional memes:
- meters: light, dark, broken, carried, reached
- memes: hyper, worry, bravery, misunderstanding, relief, warmth, love

The plot is state-driven:
1. Setup: Jo is hyper and lone, and the garden feels dim.
2. Flashback: Jo remembers an old misunderstanding and gets worried.
3. Turn: Grandma needs help; Jo chooses brave action despite worry.
4. Resolution: the light returns, the misunderstanding clears, and the ending
   image proves the change.

Contract notes:
- Stdlib only.
- Imports results eagerly and asp lazily in ASP helpers.
- Includes StoryParams, build_parser, resolve_params, generate, emit, main.
- Supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp.
"""

from __future__ import annotations

import argparse
import json
import os
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
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandpa", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            traits=list(v.traits), role=v.role, owner=v.owner, caretaker=v.caretaker,
            plural=v.plural, tags=set(v.tags), attrs=dict(v.attrs),
            meters=defaultdict(float, v.meters), memes=defaultdict(float, v.memes)
        ) for k, v in self.entities.items()}
        clone.facts = json.loads(json.dumps(self.facts, default=str))
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    clears: set[str]
    covers: set[str]
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    activity: str
    gift: str
    fix: str
    name: str
    gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"string", "lamp"}),
    "porch": Setting(place="the porch", indoor=False, affords={"string", "lamp"}),
    "shed": Setting(place="the little shed", indoor=True, affords={"string", "lamp"}),
}

ACTIVITIES = {
    "string": Activity(
        id="string",
        verb="untangle the kite string",
        gerund="untangling kite string",
        rush="run to the kite box",
        mess="tangled",
        soil="all tangled",
        zone={"hands"},
        keyword="string",
        tags={"kite", "string"},
    ),
    "lamp": Activity(
        id="lamp",
        verb="fix the little lamp",
        gerund="fixing the little lamp",
        rush="hurry to the lamp shelf",
        mess="dark",
        soil="too dark",
        zone={"hands", "torso"},
        keyword="lamp",
        tags={"lamp", "light"},
    ),
}

GIFTS = {
    "kite": Gift(
        id="kite",
        label="kite",
        phrase="a bright red kite",
        region="hands",
        plural=False,
        genders={"girl", "boy"},
    ),
    "lantern": Gift(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        region="hands",
        plural=False,
        genders={"girl", "boy"},
    ),
}

FIXES = {
    "steady": Fix(
        id="steady",
        label="steady stool",
        prep="bring over the steady stool",
        tail="brought the stool over and stood safely on it",
        clears={"dark"},
        covers={"hands"},
        plural=False,
        tags={"brave", "help"},
    ),
    "bulb": Fix(
        id="bulb",
        label="spare bulb",
        prep="fetch the spare bulb from the cupboard",
        tail="fetched the bulb and screwed it in",
        clears={"dark"},
        covers={"hands", "torso"},
        plural=False,
        tags={"light", "help"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Noa", "Tia", "Ivy", "Zoe"]
BOY_NAMES = ["Owen", "Jude", "Eli", "Nico", "Leo", "Sam"]
HELPERS = ["grandma", "grandpa"]
TRAITS = ["hyper", "lone", "quiet", "brave", "curious"]

CURATED = [
    StoryParams(setting="garden", activity="lamp", gift="lantern", fix="bulb",
                name="Jo", gender="girl", helper="grandma", helper_gender="girl"),
    StoryParams(setting="porch", activity="string", gift="kite", fix="steady",
                name="Milo", gender="boy", helper="grandpa", helper_gender="boy"),
    StoryParams(setting="shed", activity="lamp", gift="lantern", fix="steady",
                name="Pia", gender="girl", helper="grandma", helper_gender="girl"),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for g in GIFTS:
                for f in FIXES:
                    if "dark" in FIXES[f].clears and a == "lamp":
                        out.append((s, a, g, f))
                    if "help" in FIXES[f].tags and a == "string":
                        out.append((s, a, g, f))
    return out


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this combination does not create a believable misunderstanding and brave fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld: hyper, lone, flashback, misunderstanding, bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.gift is None or c[2] == args.gift)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, gift, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    helper_gender = "girl" if helper == "grandma" else "boy"
    return StoryParams(setting=setting, activity=activity, gift=gift, fix=fix,
                       name=name, gender=gender, helper=helper,
                       helper_gender=helper_gender)


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] += 1
    hero.memes["hyper"] += 1
    hero.memes["worry"] += 1
    world.event("activity", hero=hero.id, activity=activity.id)


def _flashback(world: World, hero: Entity) -> None:
    hero.memes["misunderstanding"] += 1
    hero.memes["worry"] += 1
    world.event("flashback", hero=hero.id)
    world.say(f"{hero.id} paused, and a flashback flickered up in {hero.head if hasattr(hero, 'head') else 'memory'}")


def tell(setting: Setting, activity: Activity, gift: Gift, fix: Fix,
         name: str, gender: str, helper: str, helper_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, role="hero",
                            traits=["hyper", "lone"], attrs={"helper": helper}))
    adult = world.add(Entity(id=helper.title(), kind="character", type=helper_gender,
                             label=f"the {helper}", role="helper"))
    item = world.add(Entity(id="gift", type=gift.id, label=gift.label, phrase=gift.phrase,
                            owner=hero.id, caretaker=adult.id, region=gift.region,
                            plural=gift.plural, genders=set(gift.genders)))
    tool = world.add(Entity(id=fix.id, type="tool", label=fix.label, phrase=fix.label, attrs={"kind": fix.id}))
    hero.memes["hyper"] = 1
    hero.memes["bravery"] = 0
    hero.memes["misunderstanding"] = 0
    world.facts.update(setting=setting, activity=activity, gift=item, fix=tool, helper=adult,
                       hero=hero, misheard=False, resolved=False)
    world.say(f"{hero.id} was a hyper little {gender} who felt lone on {setting.place}.")
    world.say(f"{hero.id} liked {activity.gerund}, but {setting.place} looked oddly quiet.")
    world.para()
    world.say(f"One day, {hero.id} spotted {item.ref()} and wanted to {activity.verb}.")
    world.say(f"Then a flashback returned: once, {helper} had sounded worried about a broken lamp, and {hero.id} had thought it was blame.")
    hero.memes["misunderstanding"] += 1
    hero.memes["worry"] += 1
    world.event("misunderstanding", hero=hero.id, helper=helper)
    world.para()
    world.say(f"{hero.id} remembered that old misunderstanding and felt very small for a moment.")
    world.say(f"But when {helper} called for help, {hero.id} saw there was no blame at all, only a dark little job to do.")
    hero.memes["bravery"] += 1
    world.say(f"With a brave breath, {hero.id} chose to help anyway.")
    world.para()
    if fix.id == "bulb":
        world.say(f"{hero.id} {fix.prep} and {fix.tail}.")
    else:
        world.say(f"{hero.id} {fix.prep} and {fix.tail}.")
    hero.meters["reached"] += 1
    hero.memes["relief"] += 1
    world.say(f"The lamp glowed again, and {helper} smiled because the little problem was fixed together.")
    world.say(f"{helper.title()} gave {hero.id} a warm hug, and the room felt cozy and safe.")
    hero.memes["love"] += 1
    world.facts.update(misheard=False, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    return [
        f'Write a heartwarming story about a hyper, lone child named {hero.id} in {setting.place}.',
        f'Write a story that includes the words "hyper" and "lone" and ends with kindness after a misunderstanding.',
        f"Tell a gentle story where a flashback makes {hero.id} worry, but bravery helps set things right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    activity: Activity = f["activity"]
    item: Entity = f["gift"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel worried in {setting.place}?",
            answer=f"{hero.id} remembered an old misunderstanding and thought the same trouble might happen again. That flashback made {hero.id} feel lone and uneasy until help arrived.",
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do for {helper.id.title()}?",
            answer=f"{hero.id} climbed up and fixed the little problem instead of hiding from it. That brave choice turned the dark moment into a warm one.",
        ),
        QAItem(
            question=f"What was the ending image in the story?",
            answer=f"The lamp glowed again, {helper.id} hugged {hero.id}, and the room felt cozy. The ending shows that the misunderstanding was cleared and kindness won.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the helpful thing even when you feel nervous or small. It does not mean having no fear; it means choosing to act kindly anyway.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first. Once people talk and explain, the mix-up can be fixed.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory that comes back into your mind as if you are seeing it again. Stories use flashbacks to show why a character feels a certain way now.",
        ),
    ]


ASP_RULES = r"""
is_hyper(H) :- hyper(H).
is_lone(H) :- lone(H).
misunderstanding(H) :- flashback(H), worry(H).
brave(H) :- misunderstanding(H), help_needed(H).
heartwarming(H) :- brave(H), resolved(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show is_hyper/1.\n#show is_lone/1."))
    atoms = set(asp.atoms(model, "is_hyper")) | set(asp.atoms(model, "is_lone"))
    if atoms == {("hyper",), ("lone",)}:
        print("OK: ASP twin loads and produces the expected registry facts.")
        # smoke test normal generation
        sample = generate(CURATED[0])
        assert sample.story and sample.prompts
        return 0
    print("MISMATCH in ASP twin.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.activity not in ACTIVITIES or params.gift not in GIFTS or params.fix not in FIXES:
        raise StoryError("(Invalid parameters.)")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("(Invalid gender.)")
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], GIFTS[params.gift],
                 FIXES[params.fix], params.name, params.gender, params.helper, params.helper_gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        for item in sample.prompts:
            print(item)
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show is_hyper/1.\n#show is_lone/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
