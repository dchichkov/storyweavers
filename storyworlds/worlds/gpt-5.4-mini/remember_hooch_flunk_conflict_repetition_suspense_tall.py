#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/remember_hooch_flunk_conflict_repetition_suspense_tall.py
==========================================================================================

A standalone storyworld for a tall-tale-style tiny domain built from the seed
words **remember**, **hooch**, and **flunk**, with **Conflict**, **Repetition**,
and **Suspense** woven into the simulated state.

Domain:
- A child on a dusty frontier wants to help at a county fair.
- They forget a needed bottle of sweet hooch for the pie table.
- The omission creates a conflict with a worried grown-up.
- Repetition builds suspense as the child retraces their steps.
- A simple fix proves what changed in the ending image.

This file follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
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
    breeze: str
    prop: str
    trail: str
    dark_spot: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Need:
    id: str
    label: str
    phrase: str
    place: str
    use: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Trouble:
    id: str
    label: str
    severity: int
    delay_limit: int
    text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    label: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self) -> None:
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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("hero")
    parent = world.entities.get("parent")
    if not child or not parent:
        return out
    if child.memes["defiance"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["friction"] += 1
    parent.memes["worry"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(setting: Setting, need: Need, trouble: Trouble, fix: Fix) -> bool:
    return need.place == setting.place and trouble.severity <= fix.power


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for nid in NEEDS:
            for tid in TROUBLES:
                for fid in FIXES:
                    if reasonableness_ok(SETTINGS[sid], NEEDS[nid], TROUBLES[tid], FIXES[fid]):
                        combos.append((sid, nid, tid, fid))
    return combos


def predict_delay(world: World, trouble: Trouble, delay: int) -> bool:
    return delay <= trouble.delay_limit


def setup(world: World, hero: Entity, parent: Entity, setting: Setting, need: Need) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"On a wide and windy morning, {hero.id} and {parent.id} reached {setting.place}. "
        f"The {setting.breeze} whispered over the boards, and {setting.prop} stood ready by the lane."
    )
    world.say(
        f"{hero.id} was the sort of child who could remember a tune after one hearing, "
        f"and today {hero.pronoun()} meant to help with {need.phrase}."
    )


def conflict_start(world: World, hero: Entity, parent: Entity, need: Need, trouble: Trouble) -> None:
    hero.memes["want"] += 1
    world.say(
        f"Then came the trouble: {hero.id} looked at the table and felt a cold jolt. "
        f'The little bottle of {need.label} was gone.'
    )
    world.say(
        f'"I remember it!" {hero.id} said. "I remember it, I remember it, I remember it!" '
        f'But remembering was not the same as holding {need.phrase} in {hero.pronoun("possessive")} hands.'
    )
    world.say(
        f"{parent.label_word.capitalize()} frowned. \"Without {need.label}, the pie will {trouble.label}. "
        f"You said you would bring it.\""
    )


def search(world: World, hero: Entity, need: Need) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"{hero.id} ran one way, then the other, then back again. "
        f"{hero.id} checked the porch, the wagon, and the barn door."
    )
    world.say(
        f"\"Not there,\" {hero.id} muttered. \"Not there, not there, not there.\" "
        f"The words came like hoofbeats in the dust."
    )


def remember_and_find(world: World, hero: Entity, need: Need, delay: int) -> None:
    hero.memes["remembered"] += 1
    if delay > 0:
        world.say(
            f"At last {hero.id} remembered the last place {hero.pronoun()} had set the bottle down: "
            f"beside {need.place}, tucked under a flour sack all along."
        )
    else:
        world.say(
            f"At last {hero.id} remembered the last place {hero.pronoun()} had set the bottle down: "
            f"right beside {need.place}, safe and waiting."
        )
    world.say(
        f"{hero.id} snatched it up and hurried back, the bottle sloshing like a tiny creek in a glass hill."
    )


def flunk_line(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["shame"] += 1
    world.say(
        f"For a second, {hero.id} thought {hero.pronoun()} had flunked the whole day. "
        f"The pie table needed the missing thing, and that mistake had felt as big as a thundercloud."
    )
    world.say(
        f"But {hero.id} kept going, because a tall-tale kid can flunk a moment and still save the morning."
    )


def fix_it(world: World, hero: Entity, parent: Entity, fix: Fix, need: Need, trouble: Trouble) -> None:
    world.say(
        f'{parent.label_word.capitalize()} took one look and said, "That is why we keep a spare." '
        f"Then {parent.pronoun()} used {fix.label} and settled the mess with a calm, sure hand."
    )
    world.say(
        f"The sweet hooch went into the pie filling, and the kitchen smelled like sugar, cinnamon, and long-ago fairs."
    )
    world.say(
        f"{fix.text}."
    )
    hero.memes["relief"] += 1
    parent.memes["relief"] += 1


def ending(world: World, hero: Entity, parent: Entity, setting: Setting, need: Need, fix: Fix) -> None:
    world.say(
        f"By sundown the pie had a golden top, the crowd had a grin, and {hero.id} stood straighter than a fence post."
    )
    world.say(
        f"{hero.id} remembered the lesson plain as daylight: if a thing is needed, say so early, look twice, and never lose hope."
    )
    world.say(
        f"That night the wind still sang over {setting.place}, but the bottle of {need.label} sat where everyone could see it, "
        f"and the day ended sweet instead of sour."
    )


def tell(setting: Setting, need: Need, trouble: Trouble, fix: Fix,
         hero_name: str = "Mabel", hero_gender: str = "girl",
         parent_name: str = "Aunt June", parent_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    world.facts["setting"] = setting
    world.facts["need"] = need
    world.facts["trouble"] = trouble
    world.facts["fix"] = fix
    world.facts["hero"] = hero
    world.facts["parent"] = parent

    setup(world, hero, parent, setting, need)
    world.para()
    conflict_start(world, hero, parent, need, trouble)
    search(world, hero, need)
    if not predict_delay(world, trouble, delay=1):
        world.say("The suspense stretched long as a rope bridge, and the clock kept ticking.")
    remember_and_find(world, hero, need, delay=1)
    hero.memes["defiance"] += 1
    propagate(world, narrate=True)
    world.para()
    flunk_line(world, hero, trouble)
    fix_it(world, hero, parent, fix, need, trouble)
    world.para()
    ending(world, hero, parent, setting, need, fix)
    world.facts["outcome"] = "recovered"
    return world


SETTINGS = {
    "fair": Setting("fair", "the county fair", "dry wind", "the pie tent", "down the main street", "the prize table"),
    "barn": Setting("barn", "the red barn", "hay-sweet wind", "the cider stand", "past the stalls", "the workbench"),
    "camp": Setting("camp", "the river camp", "cool evening wind", "the cookfire", "up the creek path", "the kettle"),
}

NEEDS = {
    "hooch": Need("hooch", "hooch", "a bottle of sweet hooch", "the pie tent", "stir the filling", tags={"hooch", "sweet"}),
    "syrup": Need("syrup", "maple syrup", "a jug of maple syrup", "the cake table", "sweeten the batter", tags={"sweet"}),
    "spice": Need("spice", "cinnamon spice", "a tin of cinnamon spice", "the pudding bowl", "wake up the flavor", tags={"spice"}),
}

TROUBLES = {
    "flunk": Trouble("flunk", "flunk", 1, 1, "flunk", tags={"flunk"}),
    "mess": Trouble("mess", "mess up", 1, 1, "mess up", tags={"mess"}),
}

FIXES = {
    "spare": Fix("spare", "the spare bottle", 2, 2, "The spare bottle did the trick, and the pie tasted like a sunrise", "", tags={"spare"}),
    "backtrack": Fix("backtrack", "a quick backtrack", 1, 1, "The backtrack worked, and the missing bottle was found in a flash", "", tags={"search"}),
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    need = f["need"]
    return [
        f'Write a tall tale for a child that includes the words "remember", "{need.label}", and "flunk".',
        f"Tell a suspenseful story about {hero.id} who has to remember where {need.label} was left before the pie contest begins.",
        f"Write a story with repetition and conflict where a child keeps saying \"I remember\" until the missing {need.label} is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    need = f["need"]
    fix = f["fix"]
    trouble = f["trouble"]
    return [
        QAItem(
            question="What did the child keep trying to remember?",
            answer=f"{hero.id} kept trying to remember where the {need.label} had been left. The child needed it for the pie table, so remembering mattered a great deal."
        ),
        QAItem(
            question="Why was there a conflict?",
            answer=f"There was conflict because {hero.id} forgot the {need.label} and {parent.id} was worried the pie would {trouble.label}. The missing bottle made the whole morning tense until it was found."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended well after the missing {need.label} was found and the spare plan helped. The pie was finished, the worry faded, and {hero.id} did not flunk the day after all."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does remember mean?",
            answer="Remember means to keep something in your mind so you can find it or do it later. It helps a person not forget an important job."
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to see what will happen next. It makes a story feel tense and exciting for a little while."
        ),
        QAItem(
            question="What is a flunk?",
            answer="To flunk means to do so badly that you fail, like not passing a test or not finishing a job well enough."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: that combination doesn't make a believable tall-tale conflict.)"


ASP_RULES = r"""
valid(S, N, T, F) :- setting(S), need(N), trouble(T), fix(F),
                    need_place(N, S), fix_power(F, P), trouble_severity(T, S1), P >= S1.
outcome(recovered) :- valid(_, _, _, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_place", nid, n.place))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("trouble_severity", tid, t.severity))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_power", fid, f.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python.")
        return 1
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generation produced empty story.")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


@dataclass
@dataclass
class StoryParams:
    setting: str
    need: str
    trouble: str
    fix: str
    hero: str
    hero_gender: str
    parent: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with remember / hooch / flunk.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["woman", "man", "mother", "father"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    filtered = [c for c in combos
                if (args.setting is None or c[0] == args.setting)
                and (args.need is None or c[1] == args.need)
                and (args.trouble is None or c[2] == args.trouble)
                and (args.fix is None or c[3] == args.fix)]
    if not filtered:
        raise StoryError(explain_rejection())
    setting, need, trouble, fix = rng.choice(filtered)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    hero = args.hero or rng.choice(["Mabel", "Cal", "Ruby", "Toby", "Nell"])
    parent = args.parent or rng.choice(["Aunt June", "Uncle Jed", "Ma", "Pa"])
    if args.need == "hooch" and args.setting == "camp":
        hero = args.hero or "Mabel"
    return StoryParams(setting, need, trouble, fix, hero, hero_gender, parent, parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], NEEDS[params.need], TROUBLES[params.trouble], FIXES[params.fix],
                 params.hero, params.hero_gender, params.parent, params.parent_gender)
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
    StoryParams("fair", "hooch", "flunk", "spare", "Mabel", "girl", "Aunt June", "mother"),
    StoryParams("barn", "syrup", "mess", "backtrack", "Cal", "boy", "Uncle Jed", "father"),
    StoryParams("camp", "hooch", "flunk", "backtrack", "Nell", "girl", "Pa", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for combo in asp_valid_combos():
            print("  ", combo)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
