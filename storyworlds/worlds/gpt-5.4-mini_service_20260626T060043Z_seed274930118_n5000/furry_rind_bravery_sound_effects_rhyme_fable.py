#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/furry_rind_bravery_sound_effects_rhyme_fable.py
===============================================================================================================

A compact fable-style storyworld about a furry little hero, a troublesome rind,
bravery, sound effects, and a rhyming turn toward kindness.

Premise seed:
- furry
- rind

Story shape:
- A small animal discovers a fruit rind on the path.
- The rind causes a problem: it is slippery, and someone timid needs help.
- Sound effects and rhyme are woven into the prose.
- Bravery changes the outcome: the hero chooses the helpful act instead of the boastful one.

The world model tracks both physical state in meters and emotional state in memes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    at: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"slip": 0.0, "safety": 0.0, "shine": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "bravery": 0.0, "joy": 0.0, "kindness": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the orchard"
    detail: str = "apple trees and a mossy path"
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    rhyme: str
    risk: str
    meter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    verb: str
    sound: str
    rhyme: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.problem: Optional[Problem] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.problem = self.problem
        return clone


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.meters["slip"] < THRESHOLD:
            continue
        if ("slip", c.id) in world.fired:
            continue
        world.fired.add(("slip", c.id))
        c.memes["fear"] += 1
        out.append(f"{c.id} wobbled on the rind: slip-slop!")
    return out


def _r_care(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.memes["bravery"] < THRESHOLD:
            continue
        if ("care", c.id) in world.fired:
            continue
        world.fired.add(("care", c.id))
        c.memes["kindness"] += 1
        c.meters["safety"] += 1
        out.append(f"{c.id} chose the kinder way, and the path felt steadier.")
    return out


CAUSAL_RULES = [
    _r_slip,
    _r_care,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tiny_rhyme(a: str, b: str) -> str:
    return f"{a} and {b}, a fable-sized pair"


def predicts_slip(world: World, actor: Entity, problem: Problem) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["slip"] += 1
    propagate(sim, narrate=False)
    return sim.get(actor.id).memes["fear"] >= THRESHOLD


def tell(setting: Setting, problem: Problem, aid: Aid,
         hero_name: str = "Pip", hero_type: str = "fox",
         friend_name: str = "Moss", friend_type: str = "hare") -> World:
    world = World(setting)
    world.problem = problem

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["furry", "small", "brave"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_type,
        traits=["timid", "gentle"],
    ))
    rind = world.add(Entity(
        id="rind",
        type="rind",
        label="orange rind",
        phrase="a bright orange rind",
        owner=hero.id,
    ))

    world.say(
        f"{hero.id} was a furry little {hero.type} who lived near {setting.place}, "
        f"where the {setting.detail} made every day feel like a tune."
    )
    world.say(
        f"{friend.id} was a soft-footed {friend.type} who loved to hum in a whisper."
    )
    world.say(
        f"One morning, {hero.id} found {rind.phrase} on the path and made a quick sound: "
        f"\"{problem.sound}!\""
    )
    world.say(
        f"{problem.rhyme.capitalize()}, {hero.id} said, trying to be bold and neat."
    )

    world.para()
    world.say(
        f"{friend.id} stepped forward, but the rind sat in the way like a shiny trap."
    )
    if predicts_slip(world, friend, problem):
        world.say(
            f"{friend.id} trembled. \"I do not think I can cross that,\" {friend.pronoun()} said."
        )
    world.say(
        f"{hero.id} heard the little worry and felt {hero.pronoun('possessive')} chest go tight."
    )
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"Still, {hero.id} took a breath and said, \"{problem.rhyme}.\""
    )
    world.say(
        f"Then {hero.id} nudged the rind aside with a careful paw: {problem.sound}!"
    )
    hero.meters["safety"] += 1
    prop = world.get("rind")
    prop.at = "beside the path"
    prop.meters["shine"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{friend.id} crossed safely at last, and {friend.id} laughed so softly it sounded like rain."
    )
    hero.memes["joy"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} smiled, not because {hero.id} had been the loudest, but because {hero.id} had been brave."
    )
    world.say(
        f"From then on, the path was clear, the rind was harmless, and the two friends shared the last bright peel of the day."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        rind=rind,
        problem=problem,
        aid=aid,
        setting=setting,
    )
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", detail="apple trees and a mossy path", affords={"slip"}),
    "meadow": Setting(place="the meadow", detail="wildflowers and a winding lane", affords={"slip"}),
    "garden": Setting(place="the garden", detail="bean rows and a sunny walk", affords={"slip"}),
}

PROBLEMS = {
    "rind-slip": Problem(
        id="rind-slip",
        verb="cross the path",
        gerund="crossing the path",
        rush="dash across",
        sound="slip-slop",
        rhyme="brave and calm, the path will be fine",
        risk="slippery",
        meter="slip",
        tags={"furry", "rind", "sound", "rhyme", "bravery"},
    ),
}

AIDS = {
    "paw-sweep": Aid(
        id="paw-sweep",
        label="a careful paw sweep",
        verb="sweep the rind aside",
        sound="swoosh",
        rhyme="brave and kind, clear the ground",
        protects={"slip"},
        tags={"bravery", "sound", "rhyme"},
    ),
}

HEROES = ["Pip", "Tansy", "Bram", "Nell", "Milo", "Poppy"]
FRIENDS = ["Moss", "Willow", "Fern", "Tuck", "Bibi", "Robin"]


@dataclass
class StoryParams:
    place: str
    problem: str
    aid: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable storyworld about furry bravery and a slippery rind.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--aid", choices=AIDS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    problem = args.problem or "rind-slip"
    aid = args.aid or "paw-sweep"
    hero_name = args.name or rng.choice(HEROES)
    friend_name = args.friend or rng.choice(FRIENDS)
    if hero_name == friend_name:
        raise StoryError("The hero and friend must be different characters.")
    return StoryParams(
        place=place,
        problem=problem,
        aid=aid,
        hero_name=hero_name,
        hero_type="fox",
        friend_name=friend_name,
        friend_type="hare",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short fable for children about a furry {hero.type} named {hero.id}, a rind, and bravery.',
        f"Tell a gentle story where {hero.id} helps {friend.id} cross a slippery path.",
        f'Write a rhyme-rich tale that includes the words "furry" and "rind" and ends with a brave choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Who is the furry hero in the story?",
            answer=f"The furry hero is {hero.id}, a small {hero.type} who lives near {setting.place}.",
        ),
        QAItem(
            question=f"What trouble did the rind cause on the path?",
            answer=f"The rind made the path slippery, so {friend.id} was afraid to cross it.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by carefully sweeping the rind aside instead of pretending it was not a problem.",
        ),
        QAItem(
            question=f"What sound did the story use when the hero moved the rind?",
            answer=f"The story used {problem.sound}, which is the little sound of the rind being nudged away.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the path was safe, {friend.id} could cross, and {hero.id} felt proud of being kind and brave.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rind?",
            answer="A rind is the outer skin or peel of some fruits, like an orange.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel nervous or afraid.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are little words that help you hear the action, like slap, swoosh, or plip-plop.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like light and night.",
        ),
        QAItem(
            question="Why do fables often end with a lesson?",
            answer="Fables often end with a lesson so readers can remember a simple truth about how to act well.",
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
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.at:
            bits.append(f"at={e.at}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A problem is at risk when it creates a slip meter on the path.
at_risk(P) :- problem(P), requires_slip(P).

% Bravery is the compatible response: the hero can help when they have bravery
% and the problem is genuinely at risk.
can_help(H, P) :- hero(H), problem(P), at_risk(P), brave(H).

valid_story(Place, Problem, Aid) :- setting(Place), problem(Problem), aid(Aid),
                                    at_risk(Problem), compatible(Aid, Problem).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("requires_slip", pid))
        lines.append(asp.fact("problem_sound", pid, p.sound))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for t in sorted(a.protects):
            lines.append(asp.fact("compatible", aid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = {(p, "rind-slip", "paw-sweep") for p in SETTINGS}
    got = set(asp_valid_stories())
    if got == expected:
        print(f"OK: clingo gate matches Python gate ({len(got)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  expected:", sorted(expected))
    print("  got:", sorted(got))
    return 1


def explain_rejection() -> str:
    return "(No story: this world only supports the clear fable of a furry hero, a slippery rind, and a brave helpful turn.)"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "rind-slip", "paw-sweep") for place in SETTINGS]


def resolve_story(params: StoryParams) -> tuple[Setting, Problem, Aid]:
    if params.problem not in PROBLEMS or params.aid not in AIDS or params.place not in SETTINGS:
        raise StoryError("Unknown world option.")
    return SETTINGS[params.place], PROBLEMS[params.problem], AIDS[params.aid]


def generate(params: StoryParams) -> StorySample:
    setting, problem, aid = resolve_story(params)
    world = tell(setting, problem, aid, params.hero_name, params.hero_type, params.friend_name, params.friend_type)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story triples:\n")
        for place, problem, aid in stories:
            print(f"  {place:10} {problem:10} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place=place, problem="rind-slip", aid="paw-sweep",
                        hero_name=hero, hero_type="fox", friend_name=friend, friend_type="hare")
            for place, hero, friend in [
                ("orchard", "Pip", "Moss"),
                ("meadow", "Tansy", "Willow"),
                ("garden", "Bram", "Fern"),
            ]
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
