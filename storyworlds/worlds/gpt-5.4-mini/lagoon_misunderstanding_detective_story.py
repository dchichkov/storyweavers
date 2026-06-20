#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lagoon_misunderstanding_detective_story.py
========================================================================

A standalone story world for a tiny detective tale set at a lagoon.

Premise:
- A child detective notices a strange clue near the lagoon.
- A misunderstanding makes the case look suspicious.
- The detective follows physical evidence and emotional clues to discover the truth.
- A calm helper explains what really happened, and the ending proves the change.

This world keeps the story small and classical: one location, a handful of typed
entities, physical meters and emotional memes, a causal turn, and a resolution.
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
    detail: str
    sound: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    truth: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Misunderstanding:
    id: str
    suspicion: str
    false_story: str
    correction: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Helper:
    id: str
    label: str
    action: str
    explanation: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("")
    return out


def _r_clear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("truth_told") and "detective" in world.entities:
        det = world.get("detective")
        sig = ("clear", det.id)
        if sig not in world.fired:
            world.fired.add(sig)
            det.memes["relief"] += 1
            det.meters["mystery"] = 0
            out.append("")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("clear", "social", _r_clear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(clue: Clue, misunderstanding: Misunderstanding) -> bool:
    return clue.truth == "innocent" and "lagoon" in clue.tags and "misunderstanding" in misunderstanding.tags


def _predict(world: World, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("detective").meters["mystery"] += 1
    sim.get("detective").memes["worry"] += 1
    return {"worry": sim.get("detective").memes["worry"]}


def introduce(world: World, detective: Entity, sidekick: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon at the {setting.place}, {detective.id} and {sidekick.id} "
        f"looked for clues. {setting.detail}"
    )
    world.say(
        f"{detective.id} was a careful little detective, and {sidekick.id} carried a notebook "
        f"and a pencil."
    )


def clue_seen(world: World, detective: Entity, clue: Clue, setting: Setting) -> None:
    detective.meters["mystery"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        f"Near the water, {detective.id} spotted {clue.phrase} {clue.where}. "
        f"It looked strange at first, like it had been left there on purpose."
    )


def misunderstanding_beat(world: World, detective: Entity, helper: Entity, clue: Clue,
                           misunderstanding: Misunderstanding) -> None:
    pred = _predict(world, clue)
    detective.memes["worry"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"{misunderstanding.suspicion}," {detective.id} whispered. '
        f'"That {clue.label} must mean {misunderstanding.false_story}."'
    )
    world.say(
        f"{helper.id} frowned, because the clue sounded guilty even though nobody had proof."
    )


def investigate(world: World, detective: Entity, clue: Clue, helper: Helper) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} did not rush. {detective.pronoun().capitalize()} looked again at {clue.phrase}, "
        f"then checked the muddy edge of the path."
    )
    world.say(
        f"{helper.id} {helper.action}, and the real answer became clear."
    )


def truth_revealed(world: World, detective: Entity, sidekick: Entity, clue: Clue,
                   misunderstanding: Misunderstanding, helper: Helper) -> None:
    detective.memes["relief"] += 2
    sidekick.memes["relief"] += 1
    world.facts["truth_told"] = True
    propagate(world, narrate=False)
    world.say(
        f"It turned out {clue.label} was only {clue.truth}. {misunderstanding.correction} "
        f"{helper.explanation}"
    )
    world.say(
        f"{detective.id} smiled and wrote the true answer in the notebook, proud that the case had been solved by looking carefully."
    )


def ending_image(world: World, detective: Entity, sidekick: Entity, setting: Setting) -> None:
    world.say(
        f"As the sun went lower over the {setting.place}, {detective.id} and {sidekick.id} "
        f"walked home with the notebook tucked safely under an arm, the lagoon quiet behind them."
    )


def tell(setting: Setting, clue: Clue, misunderstanding: Misunderstanding, helper: Helper,
         detective_name: str = "Milo", detective_gender: str = "boy",
         sidekick_name: str = "June", sidekick_gender: str = "girl",
         adult_name: str = "Mrs. Reed", adult_gender: str = "mother") -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="helper"))
    world.add(Entity(id="lagoon", type="place", label="the lagoon"))
    world.facts["adult"] = adult

    introduce(world, detective, sidekick, setting)
    world.para()
    clue_seen(world, detective, clue, setting)
    misunderstanding_beat(world, detective, adult, clue, misunderstanding)
    world.para()
    investigate(world, detective, clue, helper)
    world.para()
    truth_revealed(world, detective, sidekick, clue, misunderstanding, helper)
    ending_image(world, detective, sidekick, setting)

    world.facts.update(
        detective=detective, sidekick=sidekick, adult=adult,
        setting=setting, clue=clue, misunderstanding=misunderstanding, helper=helper,
        resolved=True, truth_told=True
    )
    return world


SETTINGS = {
    "lagoon": Setting(
        "lagoon",
        "the lagoon",
        "The reeds leaned over the water, and the dock creaked softly in the breeze.",
        "gulls called overhead",
    ),
    "dock": Setting(
        "dock",
        "the old dock by the lagoon",
        "The boards were sun-warm, and the water below made tiny silver flickers.",
        "waves tapped the posts",
    ),
    "reedbank": Setting(
        "reedbank",
        "the reedbank",
        "Tall reeds whispered together, and the muddy bank held small footprints.",
        "insects buzzed in the grass",
    ),
}

CLUES = {
    "bootprint": Clue(
        "bootprint", "bootprint", "a single bootprint", "near the reeds",
        "a fisher had stepped there earlier", {"lagoon", "mystery"},
    ),
    "shell": Clue(
        "shell", "shell", "a shiny shell", "by a rock",
        "the tide had carried it in", {"lagoon", "mystery"},
    ),
    "net": Clue(
        "net", "net", "a tangled net", "on the dock",
        "a sailor had left it to dry", {"lagoon", "mystery"},
    ),
}

MISUNDERSTANDINGS = {
    "stolen": Misunderstanding(
        "stolen", "This looks stolen", "someone sneaked here in the dark.",
        "But the mark was only from ordinary work, not a trick.",
        {"misunderstanding"},
    ),
    "hidden": Misunderstanding(
        "hidden", "Someone hid this on purpose", "a secret plan is going on.",
        "But the clue was simply dropped and forgotten.",
        {"misunderstanding"},
    ),
    "lost": Misunderstanding(
        "lost", "It must have been lost in a hurry", "someone ran away fast.",
        "But the clue belonged to a helper who had been working nearby.",
        {"misunderstanding"},
    ),
}

HELPERS = {
    "reedkeeper": Helper(
        "reedkeeper", "the reedkeeper", "pointed at the wet mud by the bank",
        "He showed a line of careful tracks that matched the real story.",
        {"truth", "lagoon"},
    ),
    "fisher": Helper(
        "fisher", "the fisher", "lifted a hand and explained the net",
        "She said the net was only drying after a long morning on the water.",
        {"truth", "lagoon"},
    ),
    "dockhand": Helper(
        "dockhand", "the dockhand", "knelt to brush aside the sand",
        "He explained that the shell had washed in with the tide at sunset.",
        {"truth", "lagoon"},
    ),
}

GIRL_NAMES = ["June", "Lina", "Mia", "Rose", "Nora"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Owen", "Leo"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    misunderstanding: str
    helper: str
    detective_name: str
    detective_gender: str
    sidekick_name: str
    sidekick_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    for s in SETTINGS:
        for c in CLUES:
            for m in MISUNDERSTANDINGS:
                if reasonableness_gate(CLUES[c], MISUNDERSTANDINGS[m]):
                    combos.append((s, c, m))
    return combos


KNOWLEDGE = {
    "lagoon": [("What is a lagoon?",
                "A lagoon is a shallow body of water that is partly separated from the sea or a lake.")],
    "clue": [("What is a clue?",
              "A clue is a small piece of information that can help solve a mystery.")],
    "misunderstanding": [("What is a misunderstanding?",
                         "A misunderstanding happens when someone thinks something means one thing, but it really means something else.")],
    "notebook": [("Why does a detective use a notebook?",
                  "A detective uses a notebook to remember clues, names, and careful thoughts.")],
    "careful": [("Why should a detective be careful?",
                 "A careful detective checks facts before deciding what happened.")],
    "tide": [("What does the tide do?",
              "The tide makes water rise and fall near the shore, and it can bring things in or carry them away.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "{f["clue"].label}" and takes place at a lagoon.',
        f"Tell a mystery story where {f['detective'].id} thinks {f['clue'].phrase} means something suspicious, but the real answer is harmless.",
        f'Write a gentle detective story about a misunderstanding at the lagoon that ends with the clue explained clearly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, s, a = f["detective"], f["sidekick"], f["adult"]
    c, m, h = f["clue"], f["misunderstanding"], f["helper"]
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{d.id} solved the mystery by looking carefully, and {s.id} helped by staying close and paying attention."
        ),
        QAItem(
            question="What did the strange clue turn out to mean?",
            answer=f"It turned out that {c.label} was only {c.truth}. At first it sounded suspicious, but the helper explained the harmless reason."
        ),
        QAItem(
            question="Why was there a misunderstanding?",
            answer=f"{d.id} thought {m.suspicion.lower()} and guessed the wrong story. The clue looked odd, but it was only a normal thing from near the lagoon."
        ),
        QAItem(
            question=f"What did {h.id} do to help?",
            answer=f"{h.id} {h.action} and explained the truth. That calm help showed everyone what the clue really meant."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags) | set(world.facts["misunderstanding"].tags) | {"lagoon", "clue", "misunderstanding", "notebook", "careful"}
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("lagoon", "bootprint", "stolen", "reedkeeper", "Milo", "boy", "June", "girl", "Mrs. Reed", "mother"),
    StoryParams("dock", "net", "hidden", "fisher", "Theo", "boy", "Lina", "girl", "Mr. Vale", "father"),
    StoryParams("reedbank", "shell", "lost", "dockhand", "Nora", "girl", "Finn", "boy", "Ms. Gray", "mother"),
]


def explain_rejection(clue: Clue, misunderstanding: Misunderstanding) -> str:
    return f"(No story: this clue is not a good mystery at the lagoon, or the misunderstanding is too weak to make a real detective turn.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for m in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", m))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,M) :- setting(S), clue(C), misunderstanding(M), lagoon_clue(C), misunderstood(M).
lagoon_clue(C) :- clue(C).
misunderstood(M) :- misunderstanding(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, misunderstanding=None, helper=None, detective_name=None, detective_gender=None, sidekick_name=None, sidekick_gender=None, adult_name=None, adult_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Lagoon detective story world with a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--adult")
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
              and (args.clue is None or c[1] == args.clue)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, misunderstanding = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    detective_gender = rng.choice(["boy", "girl"])
    sidekick_gender = "girl" if detective_gender == "boy" else "boy"
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    sidekick_name = args.sidekick or rng.choice(GIRL_NAMES if sidekick_gender == "girl" else BOY_NAMES)
    adult_gender = "mother" if rng.random() < 0.5 else "father"
    adult_name = args.adult or ("Mrs. Reed" if adult_gender == "mother" else "Mr. Reed")
    return StoryParams(setting, clue, misunderstanding, helper, detective_name, detective_gender, sidekick_name, sidekick_gender, adult_name, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], MISUNDERSTANDINGS[params.misunderstanding], HELPERS[params.helper], params.detective_name, params.detective_gender, params.sidekick_name, params.sidekick_gender, params.adult_name, params.adult_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
