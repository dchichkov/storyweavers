#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/chant_begin_pogo_classroom_dialogue_conflict_problem.py
==============================================================================================================

A small classroom adventure storyworld built from the seed words
"chant", "begin", and "pogo".

Premise:
- A child in a classroom wants to begin a pogo-style chant.
- The teacher worries because the energetic bouncing could shake a fragile
  classroom problem object.
- Dialogue creates the conflict.
- Problem solving finds a safe way to keep the chant, the energy, and the
  classroom calm.

The domain is intentionally narrow: one setting, one core conflict, and one
reasonable resolution. The story still varies through names, roles, and the
specific classroom object at risk.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "teacher"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male and self.type != "teacher":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the classroom"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    noise: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))


@dataclass
class Rule:
    name: str
    apply: callable


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("pogo", 0.0) < THRESHOLD:
            continue
        sig = ("noise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if actor.meters.get("noise", 0.0) < THRESHOLD:
            actor.meters["noise"] = actor.meters.get("noise", 0.0) + 1
        out.append(f"{actor.id}'s pogo steps made a lively patter through the classroom.")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("pogo", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing":
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("wobble", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wobble"] = item.meters.get("wobble", 0.0) + 1
            item.meters["risk"] = item.meters.get("risk", 0.0) + 1
            out.append(f"The {item.label} started to wobble.")
    return out


CAUSAL_RULES = [Rule("noise", _r_noise), Rule("wobble", _r_wobble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
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


def risk_at_problem(activity: Activity, problem: Problem) -> bool:
    return problem.region in activity.zone


def select_tool(activity: Activity, problem: Problem) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.id in tool.guards and problem.region in tool.covers:
            return tool
    return None


def predict_problem(world: World, actor: Entity, activity: Activity, problem_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    problem = sim.get(problem_id)
    return {"wobble": problem.meters.get("wobble", 0.0) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That action does not fit this classroom story.")
    world.zone = set(activity.tags)
    actor.meters["pogo"] = actor.meters.get("pogo", 0.0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('traits', [])), 'curious')} "
        f"{hero.type} who loved a good classroom adventure."
    )


def loves(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.verb} and to {activity.keyword} "
        f"the words so they felt like a game."
    )


def begin_chant(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"At the start of the day, {hero.id} wanted to begin a chant."
        f' "{activity.keyword}! {activity.keyword}! {activity.keyword}!" {hero.pronoun()} sang.'
    )


def teacher_warns(world: World, teacher: Entity, hero: Entity, problem: Problem, activity: Activity) -> bool:
    pred = predict_problem(world, hero, activity, problem.id)
    if not pred["wobble"]:
        return False
    teacher.memes["worry"] = teacher.memes.get("worry", 0.0) + 1
    world.say(
        f'"If we pogo right here, the {problem.label} could tip," {teacher.label_word} said.'
    )
    return True


def conflict_dialogue(world: World, hero: Entity, teacher: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f'"But I want to begin now," {hero.id} said. '
        f'"The chant sounds brave when it jumps!"'
    )
    world.say(
        f'{teacher.label_word} shook {teacher.pronoun("possessive")} head and said, '
        f'"Brave is good. Safe is better."'
    )


def choose_tool(world: World, teacher: Entity, hero: Entity, activity: Activity, problem: Problem) -> Optional[Tool]:
    tool_def = select_tool(activity, problem)
    if tool_def is None:
        return None
    tool = world.add(Entity(
        id=tool_def.id,
        label=tool_def.label,
        kind="thing",
        protective=True,
        covers=set(tool_def.covers),
    ))
    tool.worn_by = hero.id
    if predict_problem(world, hero, activity, problem.id)["wobble"]:
        tool.worn_by = None
        del world.entities[tool.id]
        return None
    world.say(
        f'{teacher.label_word} pointed to {tool_def.label} and smiled. '
        f'"How about we {tool_def.prep}?"'
    )
    return tool_def


def resolve(world: World, hero: Entity, teacher: Entity, activity: Activity, problem: Problem, tool_def: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["stubborn"] = 0.0
    world.say(
        f'"Yes!" {hero.id} said, and {hero.pronoun()} grinned at {teacher.label_word}.'
    )
    world.say(
        f"They {tool_def.tail}. Soon {hero.id} could {activity.verb} in place, "
        f"{problem.label} steady and safe, while the class joined the chant in a bright, small rhythm."
    )


def tell(
    setting: Setting,
    activity: Activity,
    problem_cfg: Problem,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    teacher_name: str = "Ms. Reed",
) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        memes={"traits": ["brave", "curious"], "want": 0.0},
    ))
    teacher = world.add(Entity(
        id=teacher_name,
        kind="character",
        type="teacher",
        label="the teacher",
    ))
    problem = world.add(Entity(
        id=problem_cfg.id,
        kind="thing",
        label=problem_cfg.label,
        phrase=problem_cfg.phrase,
        region=problem_cfg.region,
    ))

    intro(world, hero)
    loves(world, hero, activity)
    world.say(
        f"The classroom was quiet and sunlit, with {problem.label} waiting on the shelf."
    )
    world.para()
    begin_chant(world, hero, activity)
    teacher_warns(world, teacher, hero, problem, activity)
    conflict_dialogue(world, hero, teacher, activity)
    world.para()
    tool_def = choose_tool(world, teacher, hero, activity, problem)
    if tool_def:
        resolve(world, hero, teacher, activity, problem, tool_def)

    world.facts.update(
        hero=hero,
        teacher=teacher,
        problem=problem,
        problem_cfg=problem_cfg,
        activity=activity,
        tool=tool_def,
        resolved=tool_def is not None,
    )
    return world


SETTINGS = {
    "classroom": Setting(place="the classroom", indoors=True, affords={"chant", "pogo", "begin"}),
}

ACTIVITIES = {
    "chant": Activity(
        id="chant",
        verb="chant",
        gerund="chanting",
        rush="step faster",
        noise="bright chanting",
        keyword="chant",
        tags={"sound"},
    ),
    "pogo": Activity(
        id="pogo",
        verb="pogo",
        gerund="pogoing",
        rush="bounce harder",
        noise="bouncy patter",
        keyword="pogo",
        tags={"bounce", "sound"},
    ),
    "begin": Activity(
        id="begin",
        verb="begin",
        gerund="beginning",
        rush="start at once",
        noise="a quick start",
        keyword="begin",
        tags={"sound"},
    ),
}

PROBLEMS = {
    "tower": Problem(
        id="tower",
        label="tower of books",
        phrase="a tall tower of books",
        region="bookshelf",
        risk="toppling",
        zone={"bounce"},
        tags={"books"},
    ),
    "jar": Problem(
        id="jar",
        label="jar of crayons",
        phrase="a bright jar of crayons",
        region="desk",
        risk="spilling",
        zone={"bounce"},
        tags={"colors"},
    ),
    "planet": Problem(
        id="planet",
        label="paper planet model",
        phrase="a paper planet model",
        region="shelf",
        risk="shaking loose",
        zone={"bounce"},
        tags={"space"},
    ),
}

TOOLS = [
    Tool(
        id="rug",
        label="the rug circle",
        prep="move to the rug circle and keep the chant bouncy but tiny",
        tail="moved to the rug circle",
        covers={"bookshelf", "desk", "shelf"},
        guards={"pogo"},
    ),
    Tool(
        id="stomp",
        label="soft stomping steps",
        prep="turn the pogo into soft stomping steps",
        tail="swapped the big jumps for soft stomps",
        covers={"bookshelf", "desk", "shelf"},
        guards={"pogo"},
    ),
]

NAMES = ["Mina", "Toby", "Iris", "Noah", "Lena", "Eli"]
TEACHERS = ["Ms. Reed", "Mr. Fox", "Ms. Vale"]
TRAITS = ["brave", "curious", "lively", "spirited"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for pid, problem in PROBLEMS.items():
                if risk_at_problem(act, problem) and select_tool(act, problem):
                    combos.append((place, act_id, pid))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    problem: str
    name: str
    teacher: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Classroom adventure: chant, begin, pogo, dialogue, conflict, problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--teacher", choices=TEACHERS)
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(activity: Activity, problem: Problem) -> str:
    return f"(No story: {activity.verb} would not reasonably threaten {problem.label} in this classroom.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.problem is None or c[2] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, problem = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    teacher = args.teacher or rng.choice(TEACHERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, problem=problem, name=name, teacher=teacher, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short classroom adventure story that includes the words "chant", "begin", and "pogo".',
        f"Tell a gentle story where {f['hero'].id} wants to begin a pogo chant, but {f['teacher'].label_word} worries about the {f['problem'].label}.",
        f"Write an adventure-style classroom story about a child, a conflict, and a problem-solving compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    teacher: Entity = f["teacher"]
    problem: Entity = f["problem"]
    activity: Activity = f["activity"]
    tool = f["tool"]

    return [
        QAItem(
            question=f"What did {hero.id} want to begin in the classroom?",
            answer=f"{hero.id} wanted to begin a {activity.keyword} chant, because {hero.pronoun()} liked the lively rhythm.",
        ),
        QAItem(
            question=f"Why did {teacher.label_word} worry about the {problem.label}?",
            answer=f"{teacher.label_word} worried because pogoing in that spot could make the {problem.label} wobble and tip.",
        ),
        QAItem(
            question=f"How did the classroom problem get solved?",
            answer=f"They used {tool.label if tool else 'a careful plan'} so {hero.id} could keep the chant going without shaking the {problem.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a classroom?", answer="A classroom is a room where children learn, talk, read, and do school activities together."),
        QAItem(question="What does a teacher do?", answer="A teacher helps children learn, keeps them safe, and guides the class."),
        QAItem(question="What is a chant?", answer="A chant is a short set of words that people repeat together in a steady rhythm."),
        QAItem(question="What does pogo mean?", answer="To pogo means to bounce up and down in place, like a small jumpy dance."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:12} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "",
             "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in sorted(SETTINGS[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for z in sorted(p.zone):
            lines.append(asp.fact("risk_zone", pid, z))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- affords(S,A), activity(A), problem(P), tag(A,bounce), risk_zone(P,bounce).
fix(A,P) :- risk(A,P), tool(T), guards(T,A), problem(P), covers(T,R), worn_on(P,R).
valid(S,A,P) :- affords(S,A), risk(A,P), fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PROBLEMS[params.problem], params.name, "girl" if params.name in {"Mina", "Iris", "Lena"} else "boy", params.teacher)
    # patch trait into facts for QA variety
    world.facts["hero"].memes.setdefault("traits", [])
    world.facts["hero"].memes["traits"] = [params.trait]
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
    StoryParams(place="classroom", activity="pogo", problem="tower", name="Mina", teacher="Ms. Reed", trait="brave"),
    StoryParams(place="classroom", activity="pogo", problem="jar", name="Toby", teacher="Mr. Fox", trait="curious"),
    StoryParams(place="classroom", activity="pogo", problem="planet", name="Iris", teacher="Ms. Vale", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos_asp()
        print(f"{len(combos)} compatible combos:")
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
