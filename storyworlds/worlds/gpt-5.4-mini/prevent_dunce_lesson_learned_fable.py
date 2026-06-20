#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prevent_dunce_lesson_learned_fable.py
======================================================================

A small fable-style storyworld about a clever little animal, a boastful dunce,
and a lesson learned in a village garden.  The domain is intentionally tiny:
a risky shortcut, a preventable mishap, a calm fix, and a moral ending that
feels like a fable instead of an event log.

The story keeps the seed words "prevent" and "dunce", and its prose leans toward
classic animal-fable rhythms: a beginning with a simple rule, a middle with a
mistake, and an ending image proving the lesson learned.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/prevent_dunce_lesson_learned_fable.py
    python storyworlds/worlds/gpt-5.4-mini/prevent_dunce_lesson_learned_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/prevent_dunce_lesson_learned_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/prevent_dunce_lesson_learned_fable.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "hen"}
        male = {"boy", "father", "king", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    virtue: str
    caution: str

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
class Temptation:
    id: str
    label: str
    act: str
    risk: str
    hint: str
    makes_mess: str

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
    action: str
    power: int
    sense: int
    finish: str
    qa_text: str

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


def _r_mess(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spilled"] >= THRESHOLD and ("mess", e.id) not in world.fired:
            world.fired.add(("mess", e.id))
            out.append(f"{e.label_word.capitalize()} got muddy from the spill.")
    return out


def _r_spirit(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["spilled"] >= THRESHOLD and e.role == "hero":
            sig = ("spirit", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("spirit", _r_spirit)]


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


def reasonable_fix(fix: Fix) -> bool:
    return fix.sense >= 2


def valid_combo(setting: Setting, temptation: Temptation, fix: Fix) -> bool:
    return "spill" in temptation.risk and reasonable_fix(fix)


def lesson_moral(lesson_learned: bool) -> str:
    return "They learned that wisdom grows when vanity is prevented." if lesson_learned else "They forgot the lesson."


def predict_spill(world: World, temptation: Temptation) -> bool:
    sim = world.copy()
    sim.get("hero").meters["spilled"] += 1
    propagate(sim, narrate=False)
    return sim.get("hero").meters["spilled"] >= THRESHOLD


def begin(world: World, setting: Setting, hero: Entity, fool: Entity) -> None:
    hero.memes["pride"] += 1
    fool.memes["brag"] += 1
    world.say(
        f"At {setting.place}, {hero.id} lived by a simple rule: a kind hand can prevent trouble before it grows."
    )
    world.say(
        f"Nearby lived {fool.id}, a boastful dunce who thought rules were only for smaller minds."
    )


def desire(world: World, hero: Entity, temptation: Temptation, setting: Setting) -> None:
    world.say(
        f"One bright morning, {hero.id} wished to {temptation.act}, because the old path looked easy and quick."
    )
    world.say(
        f"But {setting.scene} had a hidden {temptation.risk}, and {temptation.hint}."
    )


def warn(world: World, hero: Entity, fool: Entity, temptation: Temptation) -> None:
    if predict_spill(world, temptation):
        world.say(
            f'{hero.id} said, "{temptation.label} will make a spill. We should prevent that before it stains the trail."'
        )
        world.say(
            f'But {fool.id} laughed and called {hero.pronoun("object")} a dunce for being careful.'
        )


def ignore(world: World, fool: Entity, temptation: Temptation) -> None:
    fool.memes["defiance"] += 1
    world.say(
        f'"Nonsense," said {fool.id}. "I know better than that dunce warning me."'
    )
    world.say(
        f"So {fool.id} ran ahead to {temptation.act}, and the path answered with a bad splash."
    )


def accident(world: World, hero: Entity, fool: Entity, temptation: Temptation) -> None:
    hero.meters["spilled"] += 1
    fool.meters["spilled"] += 1
    propagate(world)
    world.say(
        f"The {temptation.label} tipped at once, and {temptation.makes_mess}."
    )
    world.say(
        f"{hero.id} stepped back, while {fool.id} stood still, looking every bit the dunce."
    )


def fix_it(world: World, fix: Fix, hero: Entity, fool: Entity) -> None:
    hero.memes["calm"] += 1
    fool.memes["shame"] += 1
    world.say(
        f"Then {hero.id} brought {fix.label} and {fix.action}."
    )
    world.say(
        f"The mess was gone, and the path looked neat again."
    )


def lesson(world: World, hero: Entity, fool: Entity, fix: Fix) -> None:
    hero.memes["lesson"] += 1
    fool.memes["lesson"] += 1
    world.say(
        f"{fool.id} lowered {fool.pronoun('possessive')} head and learned the lesson at last."
    )
    world.say(
        f'"{fix.qa_text}," whispered {fool.id}. {lesson_moral(True)}'
    )
    world.say(
        f"From then on, {fool.id} listened before rushing, and the garden stayed safe."
    )


def tell(setting: Setting, temptation: Temptation, fix: Fix, hero_name: str, fool_name: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type="fox", label=hero_name, role="hero"))
    fool = world.add(Entity(fool_name, kind="character", type="crow", label=fool_name, role="dunce"))
    path = world.add(Entity("path", type="path", label="the path"))
    world.facts["setting"] = setting
    world.facts["temptation"] = temptation
    world.facts["fix"] = fix
    world.facts["hero"] = hero
    world.facts["fool"] = fool
    world.facts["path"] = path

    begin(world, setting, hero, fool)
    world.para()
    desire(world, hero, temptation, setting)
    warn(world, hero, fool, temptation)
    ignore(world, fool, temptation)
    world.para()
    accident(world, hero, fool, temptation)
    fix_it(world, fix, hero, fool)
    world.para()
    lesson(world, hero, fool, fix)
    return world


SETTINGS = {
    "orchard": Setting("orchard", "the orchard", "the apple trees and soft grass", "kindness", "careful steps"),
    "village": Setting("village", "the village green", "the lane by the well and cart ruts", "patience", "watching first"),
    "garden": Setting("garden", "the garden", "the hedge, the stone path, and the bean rows", "prudence", "slow feet"),
}

TEMPTATIONS = {
    "shortcut": Temptation("shortcut", "the shortcut", "cross the wet ditch", "spill", "it looked harmless from far away", "the shoes and paws splashed into mud"),
    "berries": Temptation("berries", "the berry basket", "reach for the high berries", "spill", "the ladder leaned too close to the puddle", "the basket tumbled and stained the ground"),
    "paint": Temptation("paint", "the paint pot", "carry the paint across the yard", "spill", "the lid sat loose and wobbly", "blue paint poured over the stones"),
}

FIXES = {
    "brush": Fix("brush", "a little broom", "swept the mud away", 4, 3, "swept the mud away", "A little broom and steady paws can clean a small mess"),
    "cloth": Fix("cloth", "a dry cloth", "wiped the spill away", 3, 2, "wiped the spill away", "A dry cloth can help when the spill is still small"),
    "water": Fix("water", "a bucket of clean water", "washed the path clean", 2, 2, "washed the path clean", "Clean water can help when a stain is fresh"),
}

CURATED = [
    ("orchard", "shortcut", "brush", "Amber", "Milo"),
    ("village", "berries", "cloth", "Pip", "Clem"),
    ("garden", "paint", "water", "Fenn", "Bram"),
]

@dataclass
class StoryParams:
    setting: str
    temptation: str
    fix: str
    hero: str
    fool: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS.values():
        for t in TEMPTATIONS.values():
            for f in FIXES.values():
                if valid_combo(s, t, f):
                    combos.append((s.id, t.id, f.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable storyworld with prevent, dunce, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--fool")
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
              and (args.temptation is None or c[1] == args.temptation)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, temptation, fix = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Swift", "Nimble", "Wren", "Clover"])
    fool = args.fool or rng.choice(["Brag", "Blurt", "Caw", "Crack"])
    return StoryParams(setting, temptation, fix, hero, fool)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story that includes the word "prevent" and the word "dunce".',
        f"Tell a short lesson-learned story where {f['hero'].id} tries to avoid trouble, but {f['fool'].id} acts like a dunce and makes a spill.",
        f"Write a gentle animal tale with a clear moral about how to prevent a mess before it starts.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, fool, setting, temp, fix = f["hero"], f["fool"], f["setting"], f["temptation"], f["fix"]
    return [
        QAItem(
            question="Who are the main characters?",
            answer=f"The main characters are {hero.id}, the careful fox, and {fool.id}, the boastful dunce crow. One of them thinks first, and the other learns the hard way."
        ),
        QAItem(
            question="Why did the trouble happen?",
            answer=f"The trouble happened because {fool.id} ignored the warning and rushed into {temp.act}. That choice made the {temp.label} spill before anyone could prevent it."
        ),
        QAItem(
            question="How was the mess fixed?",
            answer=f"{hero.id} brought {fix.label} and {fix.action}. That cleaned the path and showed that calm work is better than foolish rushing."
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson learned was to prevent problems early and to listen before acting. The story says a dunce may laugh first, but wisdom lasts longer."
        ),
    ]


KNOWLEDGE = {
    "prevent": [("What does prevent mean?",
                 "To prevent something means to stop it before it happens.")],
    "dunce": [("What is a dunce?",
               "A dunce is a silly, foolish person in an old-fashioned story. It means someone is not thinking carefully.")],
    "lesson": [("What is a lesson in a fable?",
                "A lesson in a fable is the idea the story teaches you, like being careful or kind.")],
    "fox": [("What are foxes like in fables?",
              "Foxes in fables are often clever animals who think quickly and use smart ideas.")],
    "crow": [("What are crows like in fables?",
              "Crows are often shown as clever birds, and they can talk in fables just like people.")],
    "spill": [("Why is a spill a problem?",
                "A spill can make things messy, slippery, or hard to clean.")],
}
KNOWLEDGE_ORDER = ["prevent", "dunce", "lesson", "fox", "crow", "spill"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"prevent", "dunce", "lesson", "fox", "crow", "spill"}
    out = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(q, a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.id))
    for t in TEMPTATIONS.values():
        lines.append(asp.fact("temptation", t.id))
        lines.append(asp.fact("risk", t.id, "spill"))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
        lines.append(asp.fact("sense", f.id, f.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,F) :- setting(S), temptation(T), fix(F), risk(T, spill), sense(F, N), sense_min(M), N >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, temptation=None, fix=None, hero=None, fool=None), random.Random(777)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: smoke test crashed: {exc}")
        return 1
    if not ok:
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TEMPTATIONS[params.temptation], FIXES[params.fix], params.hero, params.fool)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c, hero="Swift", fool="Caw")) for c in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    StoryParams("orchard", "shortcut", "brush", "Swift", "Caw"),
    StoryParams("village", "berries", "cloth", "Nimble", "Blurt"),
    StoryParams("garden", "paint", "water", "Wren", "Crack"),
]


if __name__ == "__main__":
    main()
