#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sales_baptize_friendship_teamwork_misunderstanding_adventure.py
===============================================================================================

A standalone storyworld for a tiny adventure about friendship, teamwork, and a
misunderstanding around the words "sales" and "baptize".

Premise
-------
A pair of friends set up a little adventure stand to earn sales for a prize they
want. They also plan a small "baptize" moment for a new raft, boat, or flag
when the day's work is done. One child misunderstands the word baptize and
thinks it means to splash the goods or soak the sign. The friends must repair
the mix-up, work together, finish the sales, and end with a cheerful naming
ceremony.

The world is small and classical:
- typed entities with physical meters and emotional memes
- a forward causal model
- state-driven prose
- grounded QA from world state
- an inline ASP twin plus a Python reasonableness gate
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
class Locale:
    id: str
    scene: str
    adventure_name: str
    trail_word: str
    ending_image: str

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
class Item:
    id: str
    label: str
    phrase: str
    plural: bool = False
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
    mixup: str
    wrong_action: str
    fix_phrase: str
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
class Goal:
    id: str
    label: str
    price: int
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_confusion(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.meters["mixup"] < THRESHOLD:
            continue
        sig = ("confusion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        for other in world.characters():
            if other.id != e.id:
                other.memes["worry"] += 0.5
        out.append("__confusion__")
    return out


def _r_teamwork(world: World) -> list[str]:
    if sum(e.memes["helping"] for e in world.characters()) < 2:
        return []
    sig = ("teamwork",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("team").meters["progress"] += 1
    return ["__teamwork__"]


CAUSAL_RULES = [
    Rule("confusion", "social", _r_confusion),
    Rule("teamwork", "social", _r_teamwork),
]


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


def reasonable_combo(locale: Locale, misunderstanding: Misunderstanding, goal: Goal) -> bool:
    return locale.id in {"harbor", "market", "island"} and misunderstanding.id in {"baptize_mixup"} and goal.price >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(l.id, m.id, g.id) for l in LOCALES.values() for m in MISUNDERSTANDINGS.values() for g in GOALS.values()
            if reasonable_combo(l, m, g)]


def choose_response(goal: Goal, delay: int) -> bool:
    return goal.price + delay <= 3


def _do_misunderstanding(world: World, child: Entity, misunderstanding: Misunderstanding) -> None:
    child.meters["mixup"] += 1
    child.memes["embarrassment"] += 1
    propagate(world, narrate=False)


def _work_together(world: World, a: Entity, b: Entity) -> None:
    a.memes["helping"] += 1
    b.memes["helping"] += 1
    world.get("team").meters["progress"] += 1


def tell(locale: Locale, misunderstanding: Misunderstanding, goal: Goal,
         a_name: str = "Mia", a_gender: str = "girl",
         b_name: str = "Noah", b_gender: str = "boy",
         delay: int = 0, parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend", traits=["brave"]))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend", traits=["careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="adult", label="the grown-up"))
    team = world.add(Entity(id="team", label="the little team"))
    raft = world.add(Entity(id="raft", label="raft"))
    sign = world.add(Entity(id="sign", label="sales sign"))
    treasure = world.add(Entity(id="treasure", label=goal.label))

    a.memes["joy"] = 1
    b.memes["joy"] = 1

    world.say(
        f"On a bright adventure day, {a.id} and {b.id} turned {locale.scene} into a little base. "
        f"{locale.ending_image}"
    )
    world.say(
        f'They wanted to make sales for {goal.label}, and later they hoped to baptize the raft with a new name.'
    )

    world.para()
    world.say(
        f'{a.id} spread out the {sign.label} and called, "Sales! Sales for the trail!" '
        f'{b.id} sorted the ropes and counted the coins.'
    )
    world.say(
        f'When {a.id} heard the word baptize, {a.pronoun("subject")} imagined water splashing everywhere. '
        f"{a.id} looked at the goods and got mixed up."
    )

    world.para()
    _do_misunderstanding(world, a, misunderstanding)
    world.say(
        f'"Wait," said {b.id}. "Baptize does not mean soak the sales table. It means a naming moment after the work is done."'
    )
    world.say(
        f'{b.id} pointed at the sign, and {a.id} took a breath. The two friends cleaned the mess together.'
    )
    _work_together(world, a, b)

    world.para()
    if choose_response(goal, delay):
        parent.say = parent.say if False else None
        a.memes["joy"] += 1
        b.memes["joy"] += 1
        world.say(
            f"{parent.label_word.capitalize()} came by with a smile and helped them finish the sales. "
            f"With the table neat again, they counted enough coins for {goal.label}."
        )
        world.say(
            f"Then the friends baptized the raft by saying its new name aloud: {raft.label.capitalize()} Brightwing."
        )
        world.say(
            f"They set off on {locale.trail_word}, proud of their teamwork and the way the misunderstanding had turned into a good story."
        )
    else:
        world.say(
            f"The little stand lost too much time cleaning, so the sales came up short. "
            f"Still, {a.id} and {b.id} fixed the mistake together and decided to try again tomorrow."
        )
        world.say(
            f"Even without the prize, they baptized the raft with the new name and pushed it toward the water, side by side."
        )

    world.facts.update(
        locale=locale, misunderstanding=misunderstanding, goal=goal,
        a=a, b=b, parent=parent, team=team, raft=raft, sign=sign, treasure=treasure,
        outcome="success" if choose_response(goal, delay) else "short",
        delay=delay,
        baptized=True,
        sales_done=choose_response(goal, delay),
    )
    return world


LOCALES = {
    "harbor": Locale("harbor", "the harbor dock", "harbor adventure", "dock path", "the waves flashed like silver coins"),
    "market": Locale("market", "the market lane", "market adventure", "stone lane", "the stalls smelled of fruit and sea wind"),
    "island": Locale("island", "the island camp", "island adventure", "sandy path", "the palm trees swayed like watchful flags"),
}

MISUNDERSTANDINGS = {
    "baptize_mixup": Misunderstanding(
        "baptize_mixup",
        "baptize",
        "spill water on the sales stand",
        "say the new name after the work is done",
        tags={"baptize", "misunderstanding"},
    )
}

GOALS = {
    "map": Goal("map", "a treasure map", 2, tags={"sales"}),
    "lantern": Goal("lantern", "a small lantern", 3, tags={"sales"}),
    "compass": Goal("compass", "a brass compass", 2, tags={"sales"}),
}


@dataclass
@dataclass
class StoryParams:
    locale: str
    misunderstanding: str
    goal: str
    a_name: str
    a_gender: str
    b_name: str
    b_gender: str
    parent: str
    delay: int = 0
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
        f'Write an adventure story for a young child that includes the words "sales" and "baptize".',
        f"Tell a friendship story where {f['a'].id} and {f['b'].id} run a tiny sales stand, misunderstand the word baptize, and fix the problem together.",
        f"Write a teamwork story with a small mistake, a calm repair, and a happy naming moment for a raft.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, loc, goal = f["a"], f["b"], f["locale"], f["goal"]
    items = [
        QAItem(
            question="What were the friends trying to do?",
            answer=f"They were trying to make sales so they could buy {goal.label}. After that, they wanted to baptize their raft with a new name.",
        ),
        QAItem(
            question="What did one friend misunderstand?",
            answer=f"{a.id} misunderstood the word baptize and thought it meant soaking the sales stand. The mix-up made the day messy, but it also gave the story its turn.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"{a.id} and {b.id} cleaned the stand together and kept working as a team. That teamwork helped them finish the day in a better way.",
        ),
    ]
    if f["outcome"] == "success":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"They made enough sales, named the raft, and headed down the trail feeling proud. The ending shows friendship and teamwork winning over the misunderstanding.",
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer="They were still proud of each other even though they did not earn quite enough that day. The friends agreed to try the sales again tomorrow and keep the raft naming for later.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are sales?",
            answer="Sales are when people offer things and buy them, often by paying coins or money. In a story, sales can help someone earn enough for a goal.",
        ),
        QAItem(
            question="What does baptize mean here?",
            answer="Here, baptize means giving something a special name in a small ceremony. It is not the same as spilling water on everything.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because two people can share the work and fix problems faster. When friends work together, a mistake can become easier to solve.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "baptize_mixup", "map", "Mia", "girl", "Noah", "boy", "mother", 0),
    StoryParams("market", "baptize_mixup", "compass", "Ava", "girl", "Leo", "boy", "father", 0),
    StoryParams("island", "baptize_mixup", "lantern", "Eli", "boy", "Nora", "girl", "mother", 1),
]


def valid_story(params: StoryParams) -> bool:
    return (
        params.locale in LOCALES
        and params.misunderstanding in MISUNDERSTANDINGS
        and params.goal in GOALS
        and reasonable_combo(LOCALES[params.locale], MISUNDERSTANDINGS[params.misunderstanding], GOALS[params.goal])
    )


def explain_rejection() -> str:
    return "(No story: this combination does not support a good adventure-sized misunderstanding with a repair and a naming moment.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about sales, baptize, friendship, teamwork, and misunderstanding.")
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--a-name")
    ap.add_argument("--b-name")
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
              if (args.locale is None or c[0] == args.locale)
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.goal is None or c[2] == args.goal)]
    if not combos:
        raise StoryError(explain_rejection())
    locale, misunderstanding, goal = rng.choice(sorted(combos))
    a_name = args.a_name or rng.choice(["Mia", "Ava", "Eli", "Noah", "Lena", "Zoe"])
    b_name = args.b_name or rng.choice([n for n in ["Mia", "Ava", "Eli", "Noah", "Lena", "Zoe"] if n != a_name])
    a_gender = "girl" if a_name in {"Mia", "Ava", "Lena", "Zoe"} else "boy"
    b_gender = "girl" if b_name in {"Mia", "Ava", "Lena", "Zoe"} else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    delay = 0 if args.goal != "lantern" else rng.randint(0, 1)
    return StoryParams(locale, misunderstanding, goal, a_name, a_gender, b_name, b_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCALES[params.locale], MISUNDERSTANDINGS[params.misunderstanding], GOALS[params.goal],
                 params.a_name, params.a_gender, params.b_name, params.b_gender, params.delay, params.parent)
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


ASP_RULES = r"""
valid(L, M, G) :- locale(L), misunderstanding(M), goal(G), allowed(L, M, G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for lid in LOCALES:
        lines.append(asp.fact("locale", lid))
        if lid in {"harbor", "market", "island"}:
            lines.append(asp.fact("allowed", lid, "baptize_mixup", "map"))
            lines.append(asp.fact("allowed", lid, "baptize_mixup", "lantern"))
            lines.append(asp.fact("allowed", lid, "baptize_mixup", "compass"))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for combo in combos:
            print(combo)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
