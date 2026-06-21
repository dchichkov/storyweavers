#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/march_suspense_comedy.py
========================================================

A small storyworld about a neighborhood march with a comic suspense beat:
someone thinks the parade is in trouble, a harmless mystery grows tense, and
then the truth turns out funny and safe.

The seed word is "march". The style leans comedic, but the middle should still
carry suspense from the world state: missing props, odd noises, a mistaken alarm,
and a final reveal that changes the ending image.
"""

from __future__ import annotations

import argparse
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class MarchSetting:
    id: str
    place: str
    crowd: str
    sound: str
    visual: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    useful_for: str
    can_miss: bool = False
    can_rattle: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    clue: str
    risk: int
    harmless: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    action: str
    reveal: str
    sense: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    prop: str
    problem: str
    fix: str
    march_word: str = "march"
    hero: str = "Mila"
    hero_type: str = "girl"
    friend: str = "Noah"
    friend_type: str = "boy"
    adult: str = "Aunt Poppy"
    adult_type: str = "aunt"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        import copy
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "town_square": MarchSetting("town_square", "the town square", "a cheering crowd", "a soft drumbeat", "strings of paper flags"),
    "school_yard": MarchSetting("school_yard", "the school yard", "a line of parents and kids", "a bouncy whistle", "bright hand-painted signs"),
    "park_path": MarchSetting("park_path", "the park path", "a curious crowd", "a tap-tap rhythm", "balloons tied to stroller handles"),
}

PROPS = {
    "drum": Prop("drum", "drum", "a little drum", "keep the beat", can_rattle=True, tags={"sound", "march"}),
    "banner": Prop("banner", "banner", "a tall paper banner", "make the march look serious", can_miss=True, tags={"visual", "march"}),
    "bells": Prop("bells", "bells", "a ring of bells", "make a cheerful surprise", can_rattle=True, tags={"sound", "march"}),
}

PROBLEMS = {
    "lost_banner": Problem("lost_banner", "lost banner", "the banner slipped behind a bench", 2, tags={"lost", "visual"}),
    "mystery_rattle": Problem("mystery_rattle", "mystery rattle", "something kept rattling in a bag", 1, tags={"sound", "mystery"}),
    "tied_shoelace": Problem("tied_shoelace", "tied shoelace", "one shoelace had snuck under a shoe", 1, tags={"small", "funny"}),
    "wind_gust": Problem("wind_gust", "wind gust", "a gust of wind kept nudging the props", 2, tags={"wind", "visual"}),
}

FIXES = {
    "peek": Fix("peek", "peek around", "peek around the bench", "it was only the banner blowing against a trash can", 3, tags={"reveal", "comedy"}),
    "shake": Fix("shake", "shake the bag", "shake the bag gently", "out popped a tiny squeaky toy", 2, tags={"reveal", "comedy"}),
    "tie": Fix("tie", "tie the lace", "tie the shoelace in a big bow", "the scary pause turned into a silly bow", 2, tags={"reveal", "comedy"}),
    "pin": Fix("pin", "pin the paper", "pin the paper banner to a clipboard", "the banner stopped fluttering like a worried bird", 2, tags={"fix", "comedy"}),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prop in PROPS.items():
            for prob_id, prob in PROBLEMS.items():
                if sid == "town_square" and prob_id == "wind_gust":
                    combos.append((sid, pid, prob_id))
                elif prop.can_rattle and prob_id in {"mystery_rattle", "tied_shoelace"}:
                    combos.append((sid, pid, prob_id))
                elif prop.can_miss and prob_id in {"lost_banner", "wind_gust"}:
                    combos.append((sid, pid, prob_id))
                elif prop.id == "bells" and prob_id == "mystery_rattle":
                    combos.append((sid, pid, prob_id))
    return combos


def is_reasonable_combo(setting: str, prop: str, problem: str) -> bool:
    return (setting, prop, problem) in set(valid_combos())


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def resolve_problem(problem: Problem, fix: Fix) -> bool:
    return fix.sense >= problem.risk


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny suspense-comedy march storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    options = [x for x in pool if x != avoid]
    return rng.choice(options)


GIRL_NAMES = ["Mila", "Nina", "Luna", "Zoe", "Aria", "Pia"]
BOY_NAMES = ["Noah", "Eli", "Milo", "Toby", "Rex", "Finn"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.prop and args.problem and not is_reasonable_combo(args.setting, args.prop, args.problem):
        raise StoryError("(No story: that prop would not plausibly create that kind of suspense in that setting.)")
    if args.fix and args.problem and not resolve_problem(PROBLEMS[args.problem], FIXES[args.fix]):
        raise StoryError("(No story: that fix is too weak for the problem, so the suspense would never resolve.)")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prop is None or c[1] == args.prop)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, problem = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    hero_type = rng.choice(["girl", "boy"])
    friend_type = "boy" if hero_type == "girl" else "girl"
    hero = args.name or _pick_name(rng, GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or _pick_name(rng, BOY_NAMES if friend_type == "boy" else GIRL_NAMES, avoid=hero)
    return StoryParams(
        setting=setting,
        prop=prop,
        problem=problem,
        fix=fix,
        hero=hero,
        hero_type=hero_type,
        friend=friend,
        friend_type=friend_type,
        adult=rng.choice(["Aunt Poppy", "Uncle Ben", "Mom", "Dad"]),
        adult_type=rng.choice(["aunt", "uncle", "mother", "father"]),
    )


def aspire(world: World, hero: Entity, friend: Entity, setting: MarchSetting, prop: Prop) -> None:
    hero.memes["excitement"] += 1
    friend.memes["excitement"] += 1
    world.say(f"On a bright day, {hero.id} and {friend.id} joined the {setting.place} {setting.crowd}.")
    world.say(f"They wanted to {prop.useful_for} during the {setting.id.replace('_', ' ')} march.")
    world.say(f"{setting.visual.capitalize()} glittered above them, and the {setting.sound} kept everyone smiling.")


def suspense(world: World, hero: Entity, friend: Entity, problem: Problem, prop: Prop) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.para()
    world.say(f"Then {problem.clue}.")
    world.say(f'"Wait," {friend.id} whispered. "{prop.label.capitalize()}? Where did it go?"')
    world.say(f"{hero.id} looked left, then right, and the funny little crowd went very quiet.")


def reveal(world: World, adult: Entity, fix: Fix, problem: Problem) -> None:
    adult.memes["calm"] += 1
    world.para()
    world.say(f"{adult.id} came over, smiling like the answer was hiding in plain sight.")
    world.say(f'"Let\'s {fix.action}," {adult.id} said.')
    world.say(f"At once, the truth came out: {fix.reveal}.")
    world.say(f"The scary pause turned into a joke everybody could share.")


def finish(world: World, hero: Entity, friend: Entity, prop: Prop, setting: MarchSetting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.para()
    world.say(f"{hero.id} picked up {prop.phrase} again, grinning now instead of gulping.")
    world.say(f"The march started up once more, and this time the beat sounded extra brave.")
    world.say(f"By the end, {setting.visual} waved overhead while {hero.id} and {friend.id} marched on, laughing at the whole tiny mystery.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    prop = PROPS[params.prop]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, role="friend"))
    adult = world.add(Entity(id=params.adult, kind="character", type=params.adult_type, role="adult"))
    world.add(Entity(id="prop", label=prop.label, role="prop", tags=set(prop.tags)))
    world.facts.update(setting=setting, prop=prop, problem=problem, fix=fix, hero=hero, friend=friend, adult=adult)
    aspire(world, hero, friend, setting, prop)
    suspense(world, hero, friend, problem, prop)
    reveal(world, adult, fix, problem)
    finish(world, hero, friend, prop, setting)
    world.facts["outcome"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child that includes the word "march" and a small suspenseful mystery in {f["setting"].place}.',
        f'Tell a funny story where {f["hero"].id} notices a problem during a march, worries for a moment, and then discovers a silly explanation.',
        f'Write a march story with suspense, a harmless surprise, and a happy ending image of people laughing together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    prop = f["prop"]
    problem = f["problem"]
    setting = f["setting"]
    fix = f["fix"]
    return [
        ("What kind of story is this?",
         f"It is a march story that starts with a little suspense and ends like a comedy. The mystery is small enough to be funny once it is solved."),
        ("What worried the children?",
         f"They thought {problem.clue}. That made them pause in the middle of the march and look around very carefully."),
        ("Who helped solve the mystery?",
         f"{adult.id} helped by staying calm and suggesting that they {fix.action}. That turned the tense moment into a joke instead of a disaster."),
        ("How did the story end?",
         f"It ended with {hero.id} and {friend.id} marching again and laughing. The {setting.visual} stayed overhead, so the last image is cheerful and safe."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a march?",
         "A march is a way of walking together in a steady beat, usually for a parade or a fun group event."),
        ("Why can suspense be funny in a comedy?",
         "Suspense makes you wonder what is happening, and comedy can turn that worry into a surprising joke."),
        ("What should you do when something small seems scary?",
         "Stop, look carefully, and ask a grown-up or helper before guessing. That usually helps the mystery make sense."),
    ]


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="town_square", prop="banner", problem="lost_banner", fix="peek", hero="Mila", hero_type="girl", friend="Noah", friend_type="boy", adult="Aunt Poppy", adult_type="aunt"),
    StoryParams(setting="school_yard", prop="bells", problem="mystery_rattle", fix="shake", hero="Eli", hero_type="boy", friend="Zoe", friend_type="girl", adult="Mom", adult_type="mother"),
    StoryParams(setting="park_path", prop="drum", problem="tied_shoelace", fix="tie", hero="Luna", hero_type="girl", friend="Finn", friend_type="boy", adult="Dad", adult_type="father"),
    StoryParams(setting="town_square", prop="banner", problem="wind_gust", fix="pin", hero="Toby", hero_type="boy", friend="Pia", friend_type="girl", adult="Uncle Ben", adult_type="uncle"),
]


ASP_RULES = r"""
valid(S,P,Pr) :- setting(S), prop(P), problem(Pr), combo(S,P,Pr).
resolved(Fx,Pr) :- fix(Fx), problem(Pr), fix_sense(Fx,S), problem_risk(Pr,R), S >= R.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if p.can_miss:
            lines.append(asp.fact("can_miss", pid))
        if p.can_rattle:
            lines.append(asp.fact("can_rattle", pid))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("problem_risk", prid, pr.risk))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_sense", fid, fx.sense))
    for s, p, pr in valid_combos():
        lines.append(asp.fact("combo", s, p, pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    try:
        py = set(valid_combos())
        cl = set(asp_valid_combos())
        if py == cl:
            print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        else:
            rc = 1
            print("MISMATCH in valid combos:")
            if cl - py:
                print("  only in clingo:", sorted(cl - py))
            if py - cl:
                print("  only in python:", sorted(py - cl))
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print("VERIFY FAILED:", exc)
        traceback.print_exc()
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.prop not in PROPS:
        raise StoryError(f"Unknown prop: {params.prop}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.fix not in FIXES:
        raise StoryError(f"Unknown fix: {params.fix}")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, p, pr in combos:
            print(f"  {s:12} {p:8} {pr}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
