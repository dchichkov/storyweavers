#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ultra_sophomore_mid_moral_value_humor_nursery.py
=================================================================================

A small standalone storyworld for a nursery-rhyme style tale with a moral turn
and a little humor. The world models a tiny barnyard game where three helpers
must decide whether to share a treat, tell the truth, and fix a silly mess.

Seed words: ultra, sophomore, mid

Design goals:
- Nursery-rhyme cadence with child-facing language.
- Clear moral value: honesty and sharing beat greed.
- Gentle humor: a bumbling spill, a proud boast, a comical fix.
- State-driven story: emotions and physical state change the ending.
- Inline ASP twin plus Python reasonableness gate and parity check.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORAL_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "tired": 0.0, "shine": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "guilt": 0.0, "kindness": 0.0, "worry": 0.0}

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    sweetness: int = 1
    sticky: bool = False
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
class Fix:
    id: str
    label: str
    phrase: str
    power: int
    kind: str = "clean"
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mess"] < THRESHOLD:
            continue
        sig = ("mess", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        for ch in list(world.entities.values()):
            if ch.kind == "character":
                ch.memes["worry"] += 0.5
        out.append("The little floor got messy, and everybody looked a bit woolly.")
    return out


def _r_guilt(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["guilt"] < THRESHOLD:
            continue
        sig = ("guilt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["kindness"] += 1
        out.append(f"{e.id} felt small inside, but also ready to do right.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("guilt", _r_guilt)]


@dataclass
class StoryParams:
    setting: str
    trio: str
    treat: str
    fix: str
    hero: str
    helper: str
    parent: str
    flaw: str
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


SETTINGS = {
    "barn": "a cozy little barn",
    "kitchen": "a sunny little kitchen",
    "garden": "a tiny moonlit garden",
}

TRIOS = {
    "barn": {
        "hero": ("Benny", "boy"),
        "helper": ("Pip", "boy"),
        "parent": ("Moo", "mother"),
    },
    "kitchen": {
        "hero": ("Luna", "girl"),
        "helper": ("Nell", "girl"),
        "parent": ("Nan", "mother"),
    },
    "garden": {
        "hero": ("Toby", "boy"),
        "helper": ("May", "girl"),
        "parent": ("Dad", "father"),
    },
}

TREATS = {
    "jam_tart": Treat("jam_tart", "jam tart", "a jam tart", sweetness=2, sticky=True, tags={"food", "jam"}),
    "honey_cup": Treat("honey_cup", "honey cup", "a honey cup", sweetness=3, sticky=True, tags={"food", "honey"}),
    "berry_bun": Treat("berry_bun", "berry bun", "a berry bun", sweetness=2, sticky=False, tags={"food", "berry"}),
}

FIXES = {
    "napkin": Fix("napkin", "napkin", "a big napkin", power=2, kind="clean", tags={"clean"}),
    "cloth": Fix("cloth", "cloth", "a soft cloth", power=1, kind="clean", tags={"clean"}),
    "soap": Fix("soap", "soap", "a little soap bowl", power=3, kind="clean", tags={"clean"}),
}

GENDERS = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for treat in TREATS:
            for fix in FIXES:
                if TREATS[treat].sticky and FIXES[fix].power >= 2:
                    out.append((setting, treat, fix))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with a moral and a chuckle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.fix:
        if not (TREATS[args.treat].sticky and FIXES[args.fix].power >= 2):
            raise StoryError("That treat and fix do not make a sensible little problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treat is None or c[1] == args.treat)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treat, fix = rng.choice(sorted(combos))
    trio = setting
    hero_name, hero_gender = TRIOS[setting]["hero"]
    helper_name, helper_gender = TRIOS[setting]["helper"]
    parent_name, parent_gender = TRIOS[setting]["parent"]
    _ = helper_gender
    _ = parent_gender
    flaw = "greedy"
    return StoryParams(setting=setting, trio=trio, treat=treat, fix=fix,
                       hero=hero_name, helper=helper_name, parent=parent_name, flaw=flaw)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type="boy" if params.hero in {"Benny", "Toby"} else "girl",
                            role="hero", traits=["bright"], attrs={"flaw": params.flaw}))
    helper = world.add(Entity(id=params.helper, kind="character", type="boy" if params.helper in {"Pip"} else "girl",
                              role="helper", traits=["kind"]))
    parent = world.add(Entity(id=params.parent, kind="character", type="mother" if params.parent in {"Moo", "Nan"} else "father",
                              role="parent", label="the parent"))
    floor = world.add(Entity(id="floor", type="floor", label="the floor"))
    treat = TREATS[params.treat]
    fix = FIXES[params.fix]

    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"In {SETTINGS[params.setting]}, {hero.id} and {helper.id} played a merry little game.")
    world.say(f"They found {treat.phrase}, and {hero.id} said, 'Oh my stars, what a nice surprise!'")
    world.say(f"But {hero.id} was a bit too proud and wanted the whole treat all at once.")
    world.para()

    world.say(f"{helper.id} whispered, 'Let's share. A full belly is not the same as a good one.'")
    hero.memes["worry"] += 1
    if treat.sticky:
        hero.meters["mess"] += 1
        propagate(world, narrate=True)
        world.say(f"{hero.id} got sticky fingers and the treat plopped onto the {floor.label_word}.")
        world.say(f"The {floor.label_word} looked like a funny little pudding with manners.")
        hero.memes["guilt"] += 1
        propagate(world, narrate=True)
        world.para()
        world.say(f"{parent.label_word.capitalize()} came along, not cross but calm.")
        world.say(f"{parent.pronoun().capitalize()} gave them {FIXES[params.fix].phrase} and a tea towel, and together they cleaned the mess.")
        world.say(f"{hero.id} said sorry, {helper.id} shared, and the snack was split in three neat smiles.")
        world.say("The tiniest lesson sat there bright and round: sharing makes room for everyone.")
    else:
        world.say(f"The treat was tidy, and there was no mess at all; they shared it straight away.")
        world.say(f"{parent.label_word.capitalize()} laughed and said the best snack is the one that makes every mouth glad.")

    world.facts.update(params=params, hero=hero, helper=helper, parent=parent,
                       treat=treat, fix=fix, setting=params.setting)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that includes the words "ultra", "sophomore", and "mid".',
        f"Tell a short moral story where {f['hero'].id} learns to share instead of being greedy, with a funny sticky mishap.",
        f"Write a gentle rhyming tale about a snack, a spill, and a kind helper who fixes the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    treat = f["treat"]
    fix = f["fix"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, {helper.id}, and {parent.label_word}. They are the little helpers at the center of the rhyme."),
        ("What went wrong?",
         f"{hero.id} wanted too much of {treat.label}, and the sticky treat made a mess. That funny spill is what turned the story toward its lesson."),
        ("How was the problem fixed?",
         f"{parent.label_word.capitalize()} brought {fix.phrase}, and they cleaned up together. Then {hero.id} said sorry and shared the snack fairly."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    treat = f["treat"]
    fix = f["fix"]
    out = []
    if treat.sticky:
        out.append(("Why can sticky food make trouble?",
                    "Sticky food can smear onto hands, tables, and floors. That makes extra work, which is why sharing carefully is better than grabbing greedily."))
    out.append((f"What is {fix.label} for?",
                f"{fix.phrase.capitalize()} helps clean up little spills and sticky spots. It is handy when a small mess needs a gentle fix."))
    out.append(("What is the moral of the story?",
                "Sharing and telling the truth are kinder than grabbing everything for yourself. When someone helps and everyone cooperates, the little trouble becomes small again."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting(T), treat(F), fix(X)) :- sticky(F), clean_power(X,P), P >= 2.
"""


def asp_facts() -> str:
    import asp
    parts: list[str] = []
    for sid in SETTINGS:
        parts.append(asp.fact("setting", sid))
    for tid, t in TREATS.items():
        parts.append(asp.fact("treat", tid))
        if t.sticky:
            parts.append(asp.fact("sticky", tid))
    for xid, x in FIXES.items():
        parts.append(asp.fact("fix", xid))
        parts.append(asp.fact("clean_power", xid, x.power))
    return "\n".join(parts)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _r
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python combo gates differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, treat=None, fix=None), _r.Random(7)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {e}")
    print("OK: parity check passed." if rc == 0 else "Parity check failed.")
    return rc


def explain_rejection(treat: Treat, fix: Fix) -> str:
    return f"(No story: {fix.label} is too weak for this sticky little treat.)"


def resolve_params_checked(args: argparse.Namespace) -> None:
    pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.fix and not (TREATS[args.treat].sticky and FIXES[args.fix].power >= 2):
        raise StoryError(explain_rejection(TREATS[args.treat], FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treat is None or c[1] == args.treat)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treat, fix = rng.choice(sorted(combos))
    trio = setting
    hero_name, helper_name, parent_name = TRIOS[setting]["hero"][0], TRIOS[setting]["helper"][0], TRIOS[setting]["parent"][0]
    return StoryParams(setting=setting, trio=trio, treat=treat, fix=fix, hero=hero_name, helper=helper_name, parent=parent_name, flaw="greedy")


CURATED = [
    StoryParams(setting="barn", trio="barn", treat="jam_tart", fix="napkin", hero="Benny", helper="Pip", parent="Moo", flaw="greedy", seed=1),
    StoryParams(setting="kitchen", trio="kitchen", treat="honey_cup", fix="soap", hero="Luna", helper="Nell", parent="Nan", flaw="greedy", seed=2),
    StoryParams(setting="garden", trio="garden", treat="berry_bun", fix="napkin", hero="Toby", helper="May", parent="Dad", flaw="greedy", seed=3),
]


def valid_combo_check() -> list[tuple[str, str, str]]:
    return valid_combos()


def generate_and_bundle(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = rng_base + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
