#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cancel_blimp_cup_repetition_foreshadowing_tall_tale.py
======================================================================================

A standalone story world for a tall-tale-style tiny domain built from the seed
words: cancel, blimp, cup.

Premise:
- A small town plans a sky parade with a giant blimp.
- A child wants to win the town's biggest cup.

Tension:
- The blimp's little bell keeps ringing a warning that the wind is rising.
- The town repeats a chant, which acts as repetition and foreshadowing.

Turn:
- The captain notices the signs and cancels the blimp ride before trouble.

Resolution:
- The cup is awarded on the ground in a grand, silly, tall-tale ending.

The world uses typed entities with physical meters and emotional memes, a tiny
forward rule engine, a reasonableness gate, an inline ASP twin, and three Q&A
sets driven by world state.
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
WIND_WARNING = 2.0


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
    attrs: dict[str, str] = field(default_factory=dict)

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
        return self.label or self.type



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
    sky: str
    crowd: str

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
class Cup:
    id: str
    label: str
    phrase: str
    prize_line: str
    shiny: bool = True

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
class Blimp:
    id: str
    label: str
    phrase: str
    warning: str
    can_cancel: bool = True

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
class Plan:
    id: str
    title: str
    chant: str
    foreshadow: str
    tall_tale_end: str

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


def _r_wind_grows(world: World) -> list[str]:
    out: list[str] = []
    blimp = world.entities.get("blimp")
    if not blimp:
        return out
    if blimp.meters["floating"] < THRESHOLD:
        return out
    sig = ("wind_grows",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("sky").meters["wind"] += 1
    world.get("crowd").memes["unease"] += 1
    out.append("__warning__")
    return out


def _r_cup_glitters(world: World) -> list[str]:
    cup = world.entities.get("cup")
    if not cup or cup.meters["claimed"] < THRESHOLD:
        return []
    sig = ("cup_glitters",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("cupstand").memes["pride"] += 1
    return ["The cup seemed to shine like a small moon in a biscuit tin sky."]


CAUSAL_RULES = [Rule("wind_grows", _r_wind_grows), Rule("cup_glitters", _r_cup_glitters)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                for s in sents:
                    if not s.startswith("__"):
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def forecast(world: World) -> dict:
    sim = world.copy()
    if "blimp" in sim.entities:
        sim.get("blimp").meters["floating"] += 1
        propagate(sim, narrate=False)
    return {
        "wind": sim.get("sky").meters["wind"],
        "unease": sim.get("crowd").memes["unease"],
    }


def can_story(plan: Plan, setting: Setting, cup: Cup, blimp: Blimp) -> bool:
    return bool(plan and setting and cup.shiny and blimp.can_cancel)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PLANS:
            for cid in CUPS:
                combos.append((sid, pid, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    plan: str
    cup: str
    child: str
    child_gender: str
    captain: str
    captain_gender: str
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


def parade_open(world: World, child: Entity, captain: Entity, plan: Plan, cup: Cup, blimp: Blimp) -> None:
    child.memes["wonder"] += 1
    captain.memes["pride"] += 1
    world.say(
        f"On parade day, {world.setting.place} was full of {world.setting.crowd}, "
        f"and the sky wore {world.setting.sky} like a blue blanket."
    )
    world.say(
        f"{child.id} had one wish: the {cup.phrase}. {captain.id} had one plan: the {blimp.phrase}."
    )
    world.say(
        f'The town kept chanting, "{plan.chant}" and the words rolled around the square again and again.'
    )


def foreshadow(world: World, child: Entity, captain: Entity, plan: Plan, blimp: Blimp) -> None:
    world.say(
        f"Then the {blimp.label} gave a tiny bell-ring. {plan.foreshadow}"
    )
    world.say(
        f'{child.id} frowned and listened. {captain.id} tipped {captain.pronoun("possessive")} hat and said, '
        f'"If that bell keeps talking, we may have to change our tune."'
    )


def cancel_ride(world: World, captain: Entity, blimp: Blimp) -> None:
    captain.memes["care"] += 1
    blimp.meters["canceled"] += 1
    world.say(
        f"Sure enough, the wind rose up like a barn cat on a fence rail, so {captain.id} canceled the blimp ride."
    )
    world.say(
        f"Nobody argued. The blimp stayed tied down, bobbing and patient, while the town looked up and nodded."
    )


def award_cup(world: World, child: Entity, cup: Cup, plan: Plan) -> None:
    child.memes["joy"] += 2
    world.get("cup").meters["claimed"] += 1
    world.say(
        f"Instead, the cup was awarded on the ground. {cup.prize_line}"
    )
    world.say(
        f"{child.id} held it high and laughed so hard the laugh flew almost as high as the blimp had been."
    )
    world.say(
        f"{plan.tall_tale_end}"
    )


def tell(setting: Setting, plan: Plan, cup: Cup, blimp: Blimp,
         child_name: str = "Milo", child_gender: str = "boy",
         captain_name: str = "Captain June", captain_gender: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_gender, role="captain"))
    world.add(Entity(id="sky", type="sky", label="the sky"))
    world.add(Entity(id="crowd", type="crowd", label="the crowd"))
    world.add(Entity(id="cupstand", type="stand", label="the stand"))
    world.add(Entity(id="cup", type="thing", label=cup.label))
    world.add(Entity(id="blimp", type="thing", label=blimp.label))

    parade_open(world, child, captain, plan, cup, blimp)
    world.para()
    foreshadow(world, child, captain, plan, blimp)

    # The blimp's presence makes the wind "matter" in the world state.
    world.get("blimp").meters["floating"] += 1
    propagate(world, narrate=True)

    world.para()
    if world.get("sky").meters["wind"] >= WIND_WARNING:
        cancel_ride(world, captain, blimp)
    else:
        world.say(
            f"The wind stayed kind, but {captain.id} still watched it like a hawk with a pocket watch."
        )

    world.para()
    award_cup(world, child, cup, plan)

    world.facts.update(
        child=child, captain=captain, cup=cup, blimp=blimp, plan=plan,
        setting=setting, canceled=world.get("blimp").meters["canceled"] >= THRESHOLD,
        wind=float(world.get("sky").meters["wind"]),
    )
    return world


SETTINGS = {
    "harbor": Setting("harbor", "Harbor Square", "high white clouds", "dockhands and sleepy geese"),
    "fair": Setting("fair", "County Fair", "striped bright clouds", "carnival folk and kite racers"),
    "hill": Setting("hill", "Hilltop", "wide blue sky", "picnickers and brass-band folks"),
}

PLANS = {
    "parade": Plan("parade", "the sky parade", "Up high, stay bright!", "The bell kept saying the wind was getting bigger.",
                   "And that is why the town remembered the day a cup was won without a single ounce of bluster."),
    "race": Plan("race", "the blimp race", "Up high, go long!", "The ropes began to tap as if they knew a storm song.",
                "And that is why the whole county cheered the smallest safe choice with the loudest hooray."),
    "delivery": Plan("delivery", "the midnight delivery", "Up high, be quick!", "The basket swung once, twice, and the lanterns blinked like sleepy eyes.",
                     "And that is why the story ended with a cup, a grin, and a blimp tied down like a good dog."),
}

CUPS = {
    "tin": Cup("tin", "tin cup", "a tin cup as big as a melon", "It was polished with a rag and handed over with a bow."),
    "golden": Cup("golden", "golden cup", "a golden cup bigger than a teacup and louder than a marching band", "It gleamed so bright it made the pigeons squint."),
    "blue": Cup("blue", "blue cup", "a blue cup with stars on the rim", "It flashed blue as a creek in moonlight."),
}

BLIMPS = {
    "red": Blimp("red", "blimp", "a red blimp with a bell on its belly", "The bell was a warning bell, and it had a mighty habit of ringing before trouble."),
    "striped": Blimp("striped", "blimp", "a striped blimp the size of a sleeping whale", "The ropes hummed, and that humming meant the wind was changing its mind."),
    "green": Blimp("green", "blimp", "a green blimp with brass fins", "The fins shivered, and everyone who knew better kept one eye on the sky."),
}

GIRL_NAMES = ["June", "Mabel", "Nell", "Ruby", "Iris"]
BOY_NAMES = ["Otis", "Wade", "Earl", "Jasper", "Toby"]


@dataclass
class StoryParams:
    setting: str
    plan: str
    cup: str
    child: str
    child_gender: str
    captain: str
    captain_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale-style story that includes the words "cancel", "blimp", and "cup".',
        f"Tell a folktale-like story where {f['captain'].id} cancels a blimp ride because the wind gives a warning, and {f['child'].id} still gets the cup at the end.",
        f"Write a repeated-phrase story with a foreshadowing sign in the sky, a canceled blimp, and a cup prize.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    captain = f["captain"]
    cup = f["cup"]
    plan = f["plan"]
    qa = [
        (
            "What was the big plan?",
            f"The town planned {plan.title}, with a blimp floating above the square and the cup waiting below. It was meant to be a grand day with plenty of sky and plenty of noise."
        ),
        (
            "What warned them that trouble might come?",
            f"The blimp's bell gave a little warning, and the chant kept repeating the same sky-high words. That was the foreshadowing, because the wind grew louder right after."
        ),
        (
            "What did the captain do when the wind rose?",
            f"{captain.id} canceled the blimp ride before anything could go wrong. The captain chose the safe answer and kept the town out of a sky-sized mess."
        ),
        (
            "How did the story end?",
            f"{child.id} got {cup.phrase} on the ground, and everyone cheered. The ending proves the change: the blimp stayed tied down, but the prize still came home."
        ),
    ]
    if f.get("canceled"):
        qa.append((
            "Why was cancel the right word for this story?",
            f"Because the plan was stopped before the blimp could take off. The captain saw the warning signs and chose not to continue."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = []
    items.append(QAItem(
        question="What is a blimp?",
        answer="A blimp is a big lighter-than-air airship that floats through the sky. It can carry banners or people and usually moves slowly and carefully."
    ))
    items.append(QAItem(
        question="What does cancel mean?",
        answer="Cancel means to stop a plan before it happens. People cancel when a choice is no longer safe or no longer makes sense."
    ))
    items.append(QAItem(
        question="What is a cup?",
        answer="A cup is a container used for drinking, and it can also be a prize or trophy. In stories, a cup can mean a small treasure to win."
    ))
    if f.get("canceled"):
        items.append(QAItem(
            question="Why did the bell matter?",
            answer="The bell mattered because it warned the town that the weather was changing. That warning helped the captain decide to cancel."
        ))
    return items


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "parade", "golden", "Milo", "boy", "Captain June", "girl"),
    StoryParams("fair", "race", "tin", "Ruby", "girl", "Captain Sol", "boy"),
    StoryParams("hill", "delivery", "blue", "Otis", "boy", "Captain Nell", "girl"),
]


def valid_for(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.plan in PLANS and params.cup in CUPS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.plan and args.plan not in PLANS:
        raise StoryError("Unknown plan.")
    if args.cup and args.cup not in CUPS:
        raise StoryError("Unknown cup.")
    if args.plan == "parade" and args.cup == "tin":
        pass
    choices = [p for p in CURATED if (args.setting is None or p.setting == args.setting)
               and (args.plan is None or p.plan == args.plan)
               and (args.cup is None or p.cup == args.cup)]
    if not choices:
        if args.setting or args.plan or args.cup:
            raise StoryError("(No valid combination matches the given options.)")
        choices = CURATED
    p = rng.choice(choices)
    return p


def generate(params: StoryParams) -> StorySample:
    if not valid_for(params):
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], PLANS[params.plan], CUPS[params.cup], BLIMPS["red"],
                 params.child, params.child_gender, params.captain, params.captain_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale blimp-and-cup storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--cup", choices=CUPS)
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


ASP_RULES = r"""
repeated(T) :- chant(T).
foreshadowing(T) :- warning(T).
windy :- warning(_).
cancelled :- windy.
winning_cup :- cup(_).
valid(S,P,C) :- setting(S), plan(P), cup(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("chant", pid))
        lines.append(asp.fact("warning", pid))
    for cid in CUPS:
        lines.append(asp.fact("cup", cid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH in valid combos.")
        if cl - py:
            print(" only in clingo:", sorted(cl - py))
        if py - cl:
            print(" only in python:", sorted(py - cl))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    print("OK: smoke test generated a story.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} / {p.plan} / {p.cup}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
