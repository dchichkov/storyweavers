#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/advice_friendship_conflict_rhyming_story.py
===========================================================================

A small story world for a rhyming friendship tale with advice and conflict.

Premise
-------
Two friends want to build something together, but they disagree about how to do
it. One friend gives advice that sounds wise, the conflict cools, and they find
a better way that leaves them smiling at the end.

The world is simulation-driven: typed entities carry physical meters and emotional
memes, and state changes drive the prose, Q&A, and ASP twin.
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
MOOD_GOOD = 2.0


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
    weather: str
    rhyme_a: str
    rhyme_b: str
    sound: str
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
class BuildPlan:
    id: str
    name: str
    raw_goal: str
    rhyme_goal: str
    materials: list[str]
    size: str
    conflict_reason: str
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
class Advice:
    id: str
    line: str
    action: str
    kindness: str
    result: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["conflict"] < THRESHOLD:
            continue
        if ("soften", e.id) in world.fired:
            continue
        world.fired.add(("soften", e.id))
        e.memes["worry"] += 1
        out.append("")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["together"] < THRESHOLD:
            continue
        if ("fix", e.id) in world.fired:
            continue
        world.fired.add(("fix", e.id))
        e.memes["joy"] += 1
        e.memes["conflict"] = 0.0
        out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in (_r_soften, _r_fix):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if s])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for bid, plan in PLANS.items():
            for aid, advice in ADVICES.items():
                if plan.size == "small" and advice.action == "push":
                    continue
                if setting.weather == "windy" and plan.name == "kite":
                    continue
                combos.append((sid, bid, aid))
    return combos


def _simulate_conflict(world: World, a: Entity, b: Entity, plan: BuildPlan, advice: Advice) -> None:
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(
        f"In {world.setting.place}, {a.id} and {b.id} played with a bright little sway. "
        f"{a.id} wanted a {plan.rhyme_goal}, a fine thing to make and play."
    )
    world.say(
        f"But the plan met a bump and a grumble, a snag in the sunny day; "
        f"{b.id} saw the trouble and started to say what words might lead the way."
    )
    b.memes["conflict"] += 1
    world.say(
        f'"{advice.line}," said {b.id}, with care in {b.pronoun("possessive")} voice, '
        f'"for friends can stay kind when they pause and make a wise choice."'
    )
    a.memes["conflict"] += 1
    world.say(
        f"{a.id} frowned for a moment, then looked at the plan in sight, "
        f"for {advice.kindness} words can cool a storm and turn a wrong to right."
    )


def _resolve(world: World, a: Entity, b: Entity, plan: BuildPlan, advice: Advice) -> None:
    a.meters["together"] += 1
    b.meters["together"] += 1
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"So they slowed right down and listened, and the air grew calm and light; "
        f"{advice.result} {plan.name} together, and the idea felt bright."
    )
    world.say(
        f"They tied the string and straightened the ring, then laughed at the happy view; "
        f"{a.id} and {b.id} stayed close as can be, a pair of friends tried and true."
    )


def _ending(world: World, a: Entity, b: Entity, plan: BuildPlan) -> None:
    world.say(
        f"By dusk they had finished the little {plan.name}, with {plan.materials[0]} and "
        f"{plan.materials[1]} in tune; their friendship shone like a lantern glow, warm as a silver moon."
    )
    world.say(
        f"{a.id} smiled at {b.id}, and {b.id} smiled back, their quarrel now out of sight; "
        f"with advice and care, they made it work, and the ending felt just right."
    )


def tell(setting: Setting, plan: BuildPlan, advice: Advice,
         a_name: str = "Mia", a_gender: str = "girl",
         b_name: str = "Noah", b_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting)
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend", traits=["bright"]))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend", traits=["kind"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))

    world.say(
        f"{a.id} and {b.id} were friends in {setting.place}, where {setting.sound} went by. "
        f"The day wore a {setting.weather} cloak, and the clouds floated high."
    )
    world.say(
        f"They wanted to build a {plan.name} that could rise and sing, "
        f"{plan.raw_goal} as if it knew how to take wing."
    )

    world.para()
    _simulate_conflict(world, a, b, plan, advice)

    if plan.size == "small":
        world.say(
            f"But {b.id} noticed the little {plan.name} was top-heavy and wobbled with fright; "
            f"{advice.action} would help the whole thing stand up tall and tight."
        )
    else:
        world.say(
            f"{b.id} noticed the bigger build needed a steadier start; "
            f"{advice.action} would keep it from falling apart."
        )

    world.para()
    _resolve(world, a, b, plan, advice)
    _ending(world, a, b, plan)

    world.facts.update(
        setting=setting,
        plan=plan,
        advice=advice,
        a=a,
        b=b,
        parent=parent,
        together=True,
        conflict=True,
        resolved=True,
    )
    return world


SETTINGS = {
    "field": Setting(
        id="field",
        place="the field",
        weather="breezy",
        rhyme_a="bright",
        rhyme_b="kite",
        sound="grass that whispered and swayed",
        tags={"outdoor", "breeze"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        weather="golden",
        rhyme_a="warm",
        rhyme_b="storm",
        sound="boards that creaked in a friendly hum",
        tags={"outdoor", "home"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden",
        weather="windy",
        rhyme_a="glow",
        rhyme_b="show",
        sound="leaves that fluttered and chimed",
        tags={"outdoor", "wind"},
    ),
}

PLANS = {
    "kite": BuildPlan(
        id="kite",
        name="kite",
        raw_goal="so it could flutter and fly",
        rhyme_goal="sparkly kite",
        materials=["paper", "string", "sticks"],
        size="small",
        conflict_reason="the tail kept slipping loose",
        tags={"kite", "air"},
    ),
    "tower": BuildPlan(
        id="tower",
        name="tower",
        raw_goal="so it could stand up proud and high",
        rhyme_goal="block tower",
        materials=["blocks", "glue", "cards"],
        size="big",
        conflict_reason="the top wanted to topple and sway",
        tags={"tower", "stack"},
    ),
    "boat": BuildPlan(
        id="boat",
        name="boat",
        raw_goal="so it could bob like a tiny little pearl",
        rhyme_goal="cardboard boat",
        materials=["box", "tape", "paper"],
        size="big",
        conflict_reason="the bow kept sagging down",
        tags={"boat", "craft"},
    ),
}

ADVICES = {
    "tie_more": Advice(
        id="tie_more",
        line="Let's tie it more, not ignore it before it can flop",
        action="tie the loose parts more snugly",
        kindness="gentle",
        result="They tied the strings a little more and shaped the pieces with care,",
        tags={"tie", "care"},
    ),
    "start_over": Advice(
        id="start_over",
        line="Let's stop and start over, so the wobble won't stay",
        action="start again with a steadier base",
        kindness="calm",
        result="They started again with a steadier base and set each piece just so,",
        tags={"restart", "care"},
    ),
    "ask_help": Advice(
        id="ask_help",
        line="Let's ask for help, and keep our friendship bright",
        action="ask the parent for a helping hand",
        kindness="kind",
        result="They asked the parent for a helping hand, and the whole idea took flight,",
        tags={"help", "care"},
    ),
}

NAMES = ["Mia", "Noah", "Ava", "Leo", "Zoe", "Eli", "Nora", "Theo"]


@dataclass
class StoryParams:
    setting: str
    plan: str
    advice: str
    a_name: str
    a_gender: str
    b_name: str
    b_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming friendship story world with advice and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--advice", choices=ADVICES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.plan is None or c[1] == args.plan)
              and (args.advice is None or c[2] == args.advice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, plan, advice = rng.choice(sorted(combos))
    a_gender = args.gender_a or rng.choice(["girl", "boy"])
    b_gender = args.gender_b or ("boy" if a_gender == "girl" else "girl")
    a_name = args.name_a or rng.choice(NAMES)
    b_name = args.name_b or rng.choice([n for n in NAMES if n != a_name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting, plan=plan, advice=advice,
        a_name=a_name, a_gender=a_gender, b_name=b_name, b_gender=b_gender,
        parent=parent,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child about friendship and conflict that includes the word "advice".',
        f"Tell a story where {f['a'].id} and {f['b'].id} disagree about a {f['plan'].name}, then a kind piece of advice helps them fix it.",
        f"Make a gentle rhyming tale in {f['setting'].place} where friends cool a conflict by listening to advice and ending with a happy scene.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, plan, advice = f["a"], f["b"], f["plan"], f["advice"]
    return [
        ("Who are the story friends?",
         f"The story is about {a.id} and {b.id}, two friends who care about each other and want to make something together."),
        ("What were they trying to do?",
         f"They were trying to build a {plan.name}. It started as a friendly plan, but they ran into conflict when the build got tricky."),
        ("What good advice helped them?",
         f"{b.id} gave advice that sounded calm and kind: {advice.line}. That helped them stop arguing and choose a better way."),
        ("How did the story end?",
         f"It ended happily, with the friends working together again and finishing the {plan.name}. Their friendship stayed strong after the conflict passed."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is advice?",
         "Advice is a helpful idea or suggestion that someone gives to make a choice easier or safer."),
        ("What is friendship?",
         "Friendship is when people care about each other, share, and try to help each other stay happy."),
        ("What is conflict?",
         "Conflict is a disagreement or problem between people, but it can be fixed when they listen and work it out."),
        ("What does it mean to work together?",
         "Working together means two or more people help one another to finish something as a team."),
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(field).
setting(porch).
setting(garden).

plan(kite).
plan(tower).
plan(boat).

advice(tie_more).
advice(start_over).
advice(ask_help).

valid(S,P,A) :- setting(S), plan(P), advice(A), not bad_combo(S,P,A).
bad_combo(garden,kite,_).
bad_combo(_,kite,ask_help) :- setting(garden).
bad_combo(_,tower,tie_more) :- plan(tower).

outcome(happy) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    for aid in ADVICES:
        lines.append(asp.fact("advice", aid))
    return "\n".join(lines)


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
        print("MISMATCH in valid combos.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, plan=None, advice=None, name_a=None, name_b=None,
            gender_a=None, gender_b=None, parent=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.plan not in PLANS or params.advice not in ADVICES:
        raise StoryError("(Invalid StoryParams values.)")
    world = tell(SETTINGS[params.setting], PLANS[params.plan], ADVICES[params.advice],
                 params.a_name, params.a_gender, params.b_name, params.b_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(setting="field", plan="kite", advice="tie_more", a_name="Mia", a_gender="girl",
                b_name="Noah", b_gender="boy", parent="mother"),
    StoryParams(setting="porch", plan="boat", advice="ask_help", a_name="Ava", a_gender="girl",
                b_name="Leo", b_gender="boy", parent="father"),
    StoryParams(setting="garden", plan="tower", advice="start_over", a_name="Zoe", a_gender="girl",
                b_name="Eli", b_gender="boy", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, plan, advice) combos:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.a_name} and {p.b_name}: {p.plan} ({p.setting}, {p.advice})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
