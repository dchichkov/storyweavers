#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/strife_surprise_animal_story.py
===============================================================

A small story world built from the seed word "strife" with a Surprise beat in
an Animal Story style.

Premise
-------
A few barnyard friends are planning a little surprise for one animal, but a bit
of strife breaks out over who should lead the plan. The disagreement grows until
a grown-up animal notices the trouble, gently settles it, and reveals the
surprise: a cozy, cheerful treat that turns the argument into a shared laugh.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate over valid story combinations
- a Python gate plus an inline ASP twin
- story-grounded QA and world-knowledge QA
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "cow"}
        male = {"boy", "father", "dad", "man", "rooster", "bull"}
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
class AnimalSetting:
    id: str
    scene: str
    place_line: str
    gathering: str
    surprise_goal: str
    cozy_image: str
    ending_move: str

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
class Surprise:
    id: str
    label: str
    object_name: str
    where: str
    revealed_by: str
    makes_noise: bool = False
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
class StrifeSource:
    id: str
    label: str
    issue: str
    spark_line: str
    escalates: bool
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
class Calmer:
    id: str
    label: str
    action: str
    result: str
    power: int
    sense: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_strife(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("strife_started") and not world.facts.get("strife_embedded"):
        sig = ("strife",)
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("friend1", "friend2"):
                world.get(eid).memes["worry"] += 1
                world.get(eid).memes["hurt"] += 1
            world.get("field").meters["tension"] += 1
            out.append("__strife__")
    return out


CAUSAL_RULES = [Rule("strife", "social", _r_strife)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for strife_id, strife in STRIFES.items():
            for surprise_id, surprise in SURPRISES.items():
                if strife.escalates and surprise.makes_noise:
                    combos.append((setting, strife_id, surprise_id))
                elif not surprise.makes_noise:
                    combos.append((setting, strife_id, surprise_id))
    return combos


def sensible_calmer() -> list[Calmer]:
    return [c for c in CALMERS.values() if c.sense >= SENSE_MIN]


def best_calmer() -> Calmer:
    return max(CALMERS.values(), key=lambda c: c.sense)


def strife_severity(strife: StrifeSource, delay: int) -> int:
    return 1 + delay + (1 if strife.escalates else 0)


def calm_strength(calmer: Calmer) -> int:
    return calmer.power


def can_settle(calmer: Calmer, strife: StrifeSource, delay: int) -> bool:
    return calm_strength(calmer) >= strife_severity(strife, delay)


def predict_strife(world: World) -> dict:
    sim = world.copy()
    sim.facts["strife_started"] = True
    propagate(sim, narrate=False)
    return {"tension": sim.get("field").meters["tension"]}


def trigger_strife(world: World, a: Entity, b: Entity, strife: StrifeSource) -> None:
    world.facts["strife_started"] = True
    a.memes["defiance"] += 1
    b.memes["defiance"] += 1
    world.say(
        f"{a.id} and {b.id} were planning something kind, but then they both wanted to do it their own way."
    )
    world.say(
        f'"{a.id} should lead," said {a.id}. "{b.id} should lead," said {b.id}. '
        f"Pretty soon there was real strife."
    )
    world.say(strife.spark_line)
    propagate(world, narrate=False)


def surprise_reveal(world: World, setting: AnimalSetting, surprise: Surprise) -> None:
    world.say(
        f"Just then, {surprise.revealed_by} lifted the lid and revealed {surprise.object_name} {surprise.where}."
    )
    world.say(
        f"It was the surprise {setting.surprise_goal}, and the whole barn went quiet for one happy blink."
    )


def calm_and_fix(world: World, parent: Entity, calmer: Calmer, a: Entity, b: Entity, surprise: Surprise) -> None:
    a.memes["worry"] = 0
    b.memes["worry"] = 0
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"{parent.id} stepped in calmly and {calmer.action}, so the two friends stopped arguing."
    )
    world.say(
        f"{parent.id} {calmer.result}, and {a.id} and {b.id} finally looked together instead of apart."
    )
    surprise_reveal(world, world.facts["setting"], surprise)
    world.say(
        f"At the end, {a.id} and {b.id} shared the surprise and laughed side by side in the {world.facts['setting'].scene}."
    )


def tell(setting: AnimalSetting, strife: StrifeSource, surprise: Surprise, calmer: Calmer) -> World:
    world = World()
    a = world.add(Entity("Pip", kind="character", type="rabbit", role="planner"))
    b = world.add(Entity("Milo", kind="character", type="mouse", role="planner"))
    parent = world.add(Entity("Mina", kind="character", type="goat", role="grownup"))
    helper = world.add(Entity("Bram", kind="character", type="horse", role="helper"))
    field = world.add(Entity("field", type="place", label="the field"))
    world.facts.update(setting=setting, strife=strife, surprise=surprise, calmer=calmer)

    world.say(
        f"In {setting.scene}, {setting.place_line}."
    )
    world.say(
        f"{a.id} and {b.id} were getting ready for {setting.gathering}, because they wanted to make {setting.surprise_goal} for everyone."
    )
    world.say(
        f"{setting.cozy_image}"
    )

    world.para()
    trigger_strife(world, a, b, strife)

    world.para()
    if can_settle(calmer, strife, 0):
        calm_and_fix(world, parent, calmer, a, b, surprise)
    else:
        world.say(
            f"{parent.id} hurried over, but the argument was too loud and everyone needed a moment to breathe first."
        )
        world.say(
            f"After a little pause, {helper.id} helped, and then the surprise could be opened with a smile."
        )
        surprise_reveal(world, setting, surprise)
        world.say(
            f"Then the friends made peace, and the barn felt warm again."
        )

    world.facts.update(
        friend1=a,
        friend2=b,
        parent=parent,
        helper=helper,
        field=field,
        outcome="resolved",
        tension=world.get("field").meters["tension"],
    )
    return world


SETTINGS = {
    "barn": AnimalSetting(
        "barn",
        "the old red barn",
        "The sun was warm on the wooden boards, and the hens were pecking near the door.",
        "a tiny surprise party",
        "a basket of sweet hay cakes",
        "the barn smelled of straw and apples",
        "They settled into a cozy group under the loft beam",
    ),
    "meadow": AnimalSetting(
        "meadow",
        "the sunny meadow",
        "The grass waved like green ribbons, and the bees hummed softly nearby.",
        "a cheerful picnic",
        "a blanket full of berries",
        "the meadow was bright and open",
        "They tucked into a happy circle beneath the flower patch",
    ),
    "pond": AnimalSetting(
        "pond",
        "the quiet pond",
        "The water was still and blue, and the ducks drifted like little boats.",
        "a little welcome surprise",
        "a crate of crunchy carrots",
        "the pond glittered in the light",
        "They leaned together on the soft bank to share the treat",
    ),
}

STRIFES = {
    "who_leads": StrifeSource(
        "who_leads",
        "a who-leads argument",
        "a debate about who should carry the basket",
        "The basket wobbled as the two friends tugged and talked over each other.",
        True,
        tags={"strife", "argument"},
    ),
    "who_opens": StrifeSource(
        "who_opens",
        "a who-opens argument",
        "a squabble about who should open the lid",
        "The lid nearly popped off as they both reached for it at once.",
        True,
        tags={"strife", "argument"},
    ),
}

SURPRISES = {
    "cakes": Surprise(
        "cakes",
        "the hay cakes",
        "a basket of sweet hay cakes",
        "on a checkered cloth",
        "Mina",
        makes_noise=False,
        tags={"surprise", "treat"},
    ),
    "carrots": Surprise(
        "carrots",
        "the carrots",
        "a crate of crunchy carrots",
        "under a blue cloth",
        "Mina",
        makes_noise=False,
        tags={"surprise", "treat"},
    ),
}

CALMERS = {
    "soft_voice": Calmer("soft_voice", "a soft voice", "spoke gently to both of them", "picked up the basket with a smile", 2, 3, {"calm"}),
    "count_to_three": Calmer("count_to_three", "counting to three", "counted to three and asked them to breathe", "held up one hoof and waited", 3, 3, {"calm"}),
    "show_surprise": Calmer("show_surprise", "showing the surprise", "pointed to the covered basket and smiled", "let the surprise do the talking", 4, 4, {"calm", "surprise"}),
}

GIRL_NAMES = ["Pip", "Mina", "Luna", "Tia"]
BOY_NAMES = ["Milo", "Bram", "Otis", "Ben"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    strife: str
    surprise: str
    calmer: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "strife" and ends with a surprise treat.',
        f"Tell a barnyard story where {f['friend1'].id} and {f['friend2'].id} have a little strife, then discover a surprise together.",
        f'Write a gentle surprise story about animals arguing over a small job, and then making up when the hidden treat is revealed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    setting = f["setting"]
    strife = f["strife"]
    surprise = f["surprise"]
    calmer = f["calmer"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {a.id} and {b.id}, two animal friends who wanted to do a kind surprise for everyone."
        ),
        QAItem(
            question="Why did they have strife?",
            answer=f"They had strife because they both wanted to lead the plan their own way. That made the basket wobbly and turned their nice idea into an argument."
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{f['parent'].id} helped calm them down, and then the surprise {setting.surprise_goal} was revealed. After that, the friends shared it and smiled together."
        ),
        QAItem(
            question="What did the surprise change?",
            answer=f"It changed the story from an argument into a happy shared moment. The treat made both friends remember they were on the same side."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is strife?",
            answer="Strife means a disagreement or trouble between people or animals. It is the kind of problem that can make a happy plan feel tense."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something hidden until the right moment. When it is revealed, it can make someone feel excited and happy."
        ),
        QAItem(
            question="Why do animal stories often have animals talk?",
            answer="Animal stories often let animals talk so they can act like little people in the story. That makes the lesson easy for children to understand."
        ),
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("barn", "who_leads", "cakes", "show_surprise"),
    StoryParams("meadow", "who_opens", "carrots", "soft_voice"),
]


def explain_rejection() -> str:
    return "(No story: this tiny animal world only supports a strife-and-surprise turn, and no valid combination matched the request.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid in STRIFES:
        lines.append(asp.fact("strife", sid))
        lines.append(asp.fact("escalates", sid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for sid, c in CALMERS.items():
        lines.append(asp.fact("calmer", sid))
        lines.append(asp.fact("sense", sid, c.sense))
        lines.append(asp.fact("power", sid, c.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(C) :- calmer(C), sense(C, S), sense_min(M), S >= M.
valid(S, T, U) :- setting(S), strife(T), surprise(U).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {k for k, v in CALMERS.items() if v.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible calmers")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, strife=None, surprise=None, calmer=None, seed=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed and smoke test succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with strife and a surprise reveal.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--strife", choices=STRIFES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--calmer", choices=CALMERS)
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
              and (args.strife is None or c[1] == args.strife)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, strife, surprise = rng.choice(sorted(combos))
    calmer = args.calmer or rng.choice(sorted(CALMERS))
    return StoryParams(setting, strife, surprise, calmer, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], STRIFES[params.strife], SURPRISES[params.surprise], CALMERS[params.calmer])
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    return sample


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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print(" ", t)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
