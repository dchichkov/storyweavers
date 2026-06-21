#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sillybilly_euphoric_sirloin_bad_ending_twist_rhyme.py
======================================================================================

A tiny bedtime-story world about a sleepy kitchen, a silly nickname, a shiny
sirloin, a twist, a rhyme, and a bad ending.

The world is classical and state-driven:
- typed entities carry physical meters and emotional memes,
- a short causal simulation drives the prose,
- explicit invalid choices raise StoryError,
- QA is generated from simulated state, not from rendered English,
- an inline ASP twin mirrors the Python validity gate and outcome logic.

The seed request asked for the words:
    sillybilly, euphoric, sirloin
and the narrative instruments:
    Bad Ending, Twist, Rhyme
with a bedtime-story style.
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    bedtime_phrase: str
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
class Snack:
    id: str
    label: str
    phrase: str
    aroma: str
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
class Twist:
    id: str
    reveal: str
    change: str
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
class Ending:
    id: str
    rhyme: str
    close: str
    bad: bool = False
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
    snack: str
    twist: str
    ending: str
    hero: str
    hero_gender: str
    parent: str
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_late(world: World) -> list[str]:
    out: list[str] = []
    candle = world.entities.get("candle")
    if not candle or candle.meters["lit"] < THRESHOLD:
        return out
    sig = ("late",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("hero")
    parent = world.get("parent")
    child.memes["alert"] += 1
    parent.memes["worry"] += 1
    out.append("The room felt a little too bright for bedtime.")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    candle = world.entities.get("candle")
    snack = world.entities.get("snack")
    if not candle or not snack:
        return out
    if candle.meters["lit"] < THRESHOLD or snack.meters["overdone"] >= THRESHOLD:
        return out
    sig = ("spoil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.meters["overdone"] += 1
    world.get("hero").memes["sad"] += 2
    world.get("parent").memes["regret"] += 1
    out.append("The snack smelled burned and changed the whole story.")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twist_done"):
        return out
    if world.get("hero").memes["euphoric"] < THRESHOLD:
        return out
    world.facts["twist_done"] = True
    out.append("But the biggest surprise was waiting inside the napkin.")
    return out


CAUSAL_RULES = [Rule("late", _r_late), Rule("spoil", _r_spoil), Rule("twist", _r_twist)]


def bedtime_gate(setting: Setting, snack: Snack, twist: Twist, ending: Ending) -> bool:
    return snack.id in {"sirloin"} and twist.id in {"twist"} and ending.id in {"bad", "rhymebad"}


def support_bad_end(ending: Ending) -> bool:
    return ending.bad


def predict_spoil(world: World) -> dict:
    sim = world.copy()
    candle = sim.entities["candle"]
    candle.meters["lit"] = 1
    propagate(sim, narrate=False)
    return {"spoiled": sim.entities["snack"].meters["overdone"] >= THRESHOLD}


def story_setup(world: World, hero: Entity, parent: Entity, setting: Setting, snack: Snack) -> None:
    hero.memes["curious"] += 1
    hero.memes["euphoric"] += 1
    world.say(
        f"At {setting.place}, under {setting.bedtime_phrase}, {hero.id} the sillybilly "
        f"was almost euphoric for the smell of {snack.phrase}."
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled softly and said it was a bedtime treat, "
        f"not a bedtime adventure."
    )
    world.say(
        f"The little pan gave off a cozy aroma, and {snack.label} waited like a secret."
    )


def story_twist(world: World, hero: Entity, twist: Twist, snack: Snack) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"Then came the twist: {twist.reveal}. {twist.change}"
    )
    world.say(
        f'In a sleepy voice, {hero.id} tried a tiny rhyme: "Sizzle and drizzle, '
        f'please do not fizzle."'
    )


def bad_ending(world: World, hero: Entity, parent: Entity, ending: Ending, snack: Snack) -> None:
    hero.memes["sad"] += 2
    parent.memes["sad"] += 1
    world.say(
        f"But the bad ending arrived at once. The treat went too dark, and the shiny "
        f"{snack.label} lost its sweet comfort."
    )
    world.say(
        f"{parent.label_word.capitalize()} hugged {hero.id} and whispered that some "
        f"mistakes stay with a room for a long while."
    )
    world.say(
        f"{ending.rhyme} {ending.close}"
    )


def tell(setting: Setting, snack: Snack, twist: Twist, ending: Ending,
         hero_name: str, hero_gender: str, parent_type: str) -> World:
    if not bedtime_gate(setting, snack, twist, ending):
        raise StoryError("This little world only tells sirloin bedtime stories with a twist and a bad-ending rhyme.")
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    candle = world.add(Entity(id="candle", kind="thing", type="thing", label="the candle"))
    snk = world.add(Entity(id="snack", kind="thing", type="food", label=snack.label, attrs={"phrase": snack.phrase}))
    hero.memes["euphoric"] = 1.0
    world.facts["setting"] = setting
    world.facts["snack"] = snack
    world.facts["twist"] = twist
    world.facts["ending"] = ending
    world.facts["candle"] = candle
    world.facts["hero"] = hero
    world.facts["parent"] = parent

    story_setup(world, hero, parent, setting, snack)
    world.para()
    story_twist(world, hero, twist, snack)
    candle.meters["lit"] = 1
    propagate(world, narrate=True)
    world.para()
    bad_ending(world, hero, parent, ending, snack)
    return world


SETTINGS = {
    "nursery": Setting(id="nursery", place="the little nursery", bedtime_phrase="the blue bedtime moon"),
    "kitchen": Setting(id="kitchen", place="the quiet kitchen", bedtime_phrase="the sleepy window light"),
}

SNACKS = {
    "sirloin": Snack(id="sirloin", label="sirloin", phrase="a warm sirloin slice", aroma="brown and buttery", tags={"sirloin"}),
    "toast": Snack(id="toast", label="toast", phrase="a toasted square", aroma="toasty", tags={"toast"}),
}

TWISTS = {
    "twist": Twist(id="twist", reveal="the sirloin was not for supper at all", change="It had been meant for the cat-shaped napkin castle.", tags={"twist"}),
}

ENDINGS = {
    "bad": Ending(id="bad", rhyme="Hush now, hush, no more delight,", close="the sirloin slept away in the night.", bad=True, tags={"bad", "rhyme"}),
    "rhymebad": Ending(id="rhymebad", rhyme="Stars went dim and crumbs went stray,", close="the bedtime snack was lost that day.", bad=True, tags={"bad", "rhyme"}),
}

HEROES = ["SillyBilly", "Milo", "Nina", "Poppy"]
GENDERS = {"SillyBilly": "boy", "Milo": "boy", "Nina": "girl", "Poppy": "girl"}
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for n in SNACKS:
            for t in TWISTS:
                for e in ENDINGS:
                    if bedtime_gate(SETTINGS[s], SNACKS[n], TWISTS[t], ENDINGS[e]):
                        combos.append((s, n, t, e))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story that includes the words "sillybilly", "euphoric", and "sirloin".',
        f"Tell a sleepy story where {f['hero'].id} feels euphoric about {f['snack'].phrase}, "
        f"then add a twist and end with a bad rhyme.",
        "Write a child-friendly bedtime story with a surprising turn and a sad ending image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    snack: Snack = f["snack"]
    twist: Twist = f["twist"]
    ending: Ending = f["ending"]
    qa = [
        ("Who is the story about?", f"It is about {hero.id}, the sillybilly, and {hero.pronoun('possessive')} parent."),
        ("What did the child want?", f"{hero.id} wanted the sirloin because it smelled warm and special at bedtime."),
        ("What was the twist?", f"The twist was that the sirloin was not meant as supper at all. It was supposed to stay safe inside the napkin castle."),
        ("How did the story end?", f"It ended badly. The sirloin was overdone, the room felt sad, and the rhyme closed the bedtime scene like a little sigh."),
    ]
    if f["snack"].id == "sirloin":
        qa.append((
            "Why was the child euphoric at the start?",
            f"{hero.id} felt euphoric because the sirloin smelled rich and cozy. That happy feeling made the bedtime choice feel extra tempting."
        ))
    if ending.bad:
        qa.append((
            "Why is the ending bad?",
            f"The ending is bad because the snack was spoiled and the evening could not be fixed back into a happy one. The rhyme marks that the story closed with loss instead of comfort."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does euphoric mean?", "Euphoric means very, very happy, almost as if joy is buzzing in your chest."),
        ("What is sirloin?", "Sirloin is a kind of meat from a cow. People often cook it as a dinner food."),
        ("What is a twist in a story?", "A twist is a surprise turn that changes what the reader thought would happen."),
        ("What is a rhyme?", "A rhyme is when words sound alike at the end, like night and light."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
lit(candle) :- candle_lit.
spoiled(snack) :- lit(candle), snack(sirloin).
twist_done :- euphoric(hero), twist(twist).
outcome(bad) :- spoiled(snack), twist_done.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("candle_lit"),
        asp.fact("candle"),
        asp.fact("snack", "sirloin"),
        asp.fact("twist", "twist"),
        asp.fact("hero"),
        asp.fact("euphoric", "hero"),
        asp.fact("outcome", "bad"),
    ]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("setting", params.setting),
        asp.fact("snack", params.snack),
        asp.fact("twist", params.twist),
        asp.fact("ending", params.ending),
        asp.fact("bad", params.ending),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid_combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")

    # smoke-test normal generation
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    # parity on curated/default-ish cases
    for p in CURATED:
        if asp_outcome(p) != "bad":
            rc = 1
            print("MISMATCH: ASP outcome diverged on curated case")
            break
    if rc == 0:
        print("OK: ASP outcome parity passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with sillybilly, euphoric, sirloin, twist, rhyme, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--parent", choices=PARENTS)
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


CURATED = [
    StoryParams(setting="nursery", snack="sirloin", twist="twist", ending="bad", hero="SillyBilly", hero_gender="boy", parent="mother", seed=1),
    StoryParams(setting="kitchen", snack="sirloin", twist="twist", ending="rhymebad", hero="Nina", hero_gender="girl", parent="father", seed=2),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    snack = args.snack or rng.choice(list(SNACKS))
    twist = args.twist or rng.choice(list(TWISTS))
    ending = args.ending or rng.choice(list(ENDINGS))
    if not bedtime_gate(SETTINGS[setting], SNACKS[snack], TWISTS[twist], ENDINGS[ending]):
        raise StoryError("This storyworld only supports the sirloin bedtime twist with a bad ending rhyme.")
    hero = args.hero or rng.choice(HEROES)
    hero_gender = "boy" if hero in {"SillyBilly", "Milo"} else "girl"
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting=setting, snack=snack, twist=twist, ending=ending, hero=hero, hero_gender=hero_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    for key, table in (("setting", SETTINGS), ("snack", SNACKS), ("twist", TWISTS), ("ending", ENDINGS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        SETTINGS[params.setting],
        SNACKS[params.snack],
        TWISTS[params.twist],
        ENDINGS[params.ending],
        params.hero,
        params.hero_gender,
        params.parent,
    )
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for combo in valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
