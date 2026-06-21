#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/christmas_friday_bread_conflict_quest_superhero_story.py
========================================================================================

A small superhero-style storyworld built from the seed words:

- christmas
- friday
- bread

and the requested narrative instruments:

- Conflict
- Quest

The world is a child-facing, state-driven simulation about a kid hero, a helper,
a missing bread delivery, a holiday errand, and a conflict that is solved through
a quest rather than a frozen paragraph with swapped nouns.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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


@dataclass
class Hero:
    id: str
    title: str
    outfit: str
    power: str
    symbol: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    source: str
    risk: str
    conflict_line: str
    quest_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestTool:
    id: str
    label: str
    phrase: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
    hero_title: str
    problem: str
    tool: str
    resolution: str
    setting: str
    holiday: str = "christmas"
    day: str = "friday"
    seed: Optional[int] = None


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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_anxiety(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("trouble", 0.0) < THRESHOLD:
            continue
        sig = ("anxiety", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["worry"] = ent.memes.get("worry", 0.0) + 1
        out.append("__anxiety__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_anxiety,):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonable(problem: Problem, tool: QuestTool, resolution: Resolution) -> bool:
    return "quest" in problem.tags and "conflict" in problem.tags and resolution.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                for rid, r in RESOLUTIONS.items():
                    if reasonable(p, t, r):
                        out.append((sid, pid, tid))
    return out


def hero_name_text(hero: Entity) -> str:
    return f"{hero.id}, the {hero.attrs.get('title', 'hero')}"


def tell(setting: dict, hero_cfg: Hero, helper_name: str, helper_gender: str,
         adult_name: str, adult_gender: str, problem: Problem, tool: QuestTool,
         resolution: Resolution, holiday: str, day: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_cfg.id, kind="character", type=hero_cfg.attrs.get("gender", "boy") if False else hero_cfg.tags and "girl" or "boy",
        label=hero_cfg.id, role="hero", traits=["brave", "kind"],
        attrs={"title": hero_cfg.title, "setting": setting["label"]},
    ))
    hero.type = hero_cfg.attrs["gender"]
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_gender, label=helper_name,
        role="helper", traits=["smart", "loyal"], attrs={"setting": setting["label"]},
    ))
    adult = world.add(Entity(
        id=adult_name, kind="character", type=adult_gender, label=adult_name,
        role="adult", traits=["calm"], attrs={"setting": setting["label"]},
    ))
    bread = world.add(Entity(id="bread", kind="thing", type="thing", label="bread", attrs={"fresh": True}, meters={}))
    world.add(bread)

    hero.memes["hope"] = 1
    helper.memes["teamwork"] = 1
    adult.memes["care"] = 1

    world.say(
        f"It was {day} in {setting['label']}, and {holiday} lights were glowing in the windows."
    )
    world.say(
        f"{hero.id} was a {hero_cfg.title} with a {hero_cfg.outfit}. {helper.id} called "
        f"{hero.id} to a new quest."
    )
    world.say(
        f'Their mission was to find the missing bread for the holiday table, '
        f'but the trail led to a noisy conflict near the market.'
    )

    world.para()
    world.say(
        f"{problem.conflict_line} {helper.id} pointed at the clues and said, "
        f'"This is our quest."'
    )
    world.say(
        f"{hero.id} felt the tug of the problem because {problem.risk}."
    )
    world.say(
        f'"We can fix this," said {adult.id}, "but we must do it the safe way."'
    )

    world.para()
    helper.meters["courage"] = helper.meters.get("courage", 0.0) + 1
    world.say(
        f"{helper.id} packed {tool.phrase}. It {tool.helps}, and that made the next step possible."
    )
    world.say(
        f"{problem.quest_line}"
    )
    bread.meters["missing"] = 1
    bread.meters["found"] = 0

    world.para()
    if resolution.power >= 2:
        bread.meters["missing"] = 0
        bread.meters["found"] = 1
        adult.meters["trouble"] = 0
        world.say(
            f"{adult.id} used {resolution.success}."
        )
        world.say(
            f"The bread was safe again, and the conflict cooled like snow on a roof."
        )
        world.say(
            f"By the time they went home, the table was ready for christmas supper."
        )
    else:
        bread.meters["missing"] = 1
        world.get(helper.id).memes["worry"] = helper.memes.get("worry", 0.0) + 1
        world.say(
            f"{adult.id} tried {resolution.fail}."
        )
        world.say(
            f"The quest had to pause, but they kept searching together."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        adult=adult,
        bread=bread,
        problem=problem,
        tool=tool,
        resolution=resolution,
        setting=setting,
        holiday=holiday,
        day=day,
        outcome="found" if bread.meters.get("found", 0.0) >= THRESHOLD else "searching",
    )
    return world


SETTINGS = {
    "kitchen": {"label": "the kitchen", "tags": {"christmas", "bread", "quest"}},
    "bakery": {"label": "the bakery street", "tags": {"bread", "quest"}},
    "town": {"label": "the snowy town square", "tags": {"christmas", "friday", "bread", "quest"}},
}

PROBLEMS = {
    "missing_bread": Problem(
        id="missing_bread",
        label="missing bread",
        source="bread",
        risk="the family could not finish the holiday meal",
        conflict_line="The bread was gone, and everyone had a different guess about where it went.",
        quest_line="The three of them followed crumbs and footprints through the snowy air.",
        tags={"conflict", "quest", "bread"},
    ),
    "baker_mixup": Problem(
        id="baker_mixup",
        label="bakery mix-up",
        source="bread",
        risk="the wrong basket had been packed for the christmas table",
        conflict_line="At the bakery, a mix-up caused a clash of voices and worried faces.",
        quest_line="They checked every basket until the right loaf turned up.",
        tags={"conflict", "quest", "bread", "christmas"},
    ),
}

TOOLS = {
    "map": QuestTool("map", "city map", "a folded city map", "showed the path between the clues", {"quest"}),
    "lantern": QuestTool("lantern", "lantern", "a small lantern", "shone on the crumbs", {"quest", "christmas"}),
    "notes": QuestTool("notes", "clue notes", "a page of clue notes", "kept the mission organized", {"quest"}),
}

RESOLUTIONS = {
    "steady_hands": Resolution("steady_hands", 3, 3, "careful hands to carry the recovered bread home", "a quick grab that did not help", {"quest"}),
    "ask_baker": Resolution("ask_baker", 3, 2, "a calm question to the baker, who smiled and pointed to the right shelf", "an angry shout that only made the crowd more confused", {"conflict"}),
    "follow_crumbs": Resolution("follow_crumbs", 2, 2, "the crumbs, step by step, until the loaf was found", "the wrong turn that lost the trail", {"quest"}),
}

HEROES = {
    "nova": Hero("Nova", "tiny shield hero", "a red cape and silver boots", "finding what is lost", {"hero"}),
    "spark": Hero("Spark", "young helper hero", "a bright scarf and a star badge", "picking the right clue", {"hero"}),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Ben", "Leo", "Max", "Tom", "Finn"]


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
    hero_title: str
    problem: str
    tool: str
    resolution: str
    setting: str
    holiday: str = "christmas"
    day: str = "friday"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with christmas, friday, bread, conflict, and quest.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--setting", choices=SETTINGS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    hero_key = args.hero or rng.choice(sorted(HEROES))
    hero = HEROES[hero_key]
    helper = rng.choice(GIRL_NAMES + BOY_NAMES)
    adult = rng.choice(["Mom", "Dad"])
    return StoryParams(
        hero=hero.id,
        hero_gender="boy",
        helper=helper,
        helper_gender="girl" if helper in GIRL_NAMES else "boy",
        adult=adult,
        adult_gender="girl" if adult == "Mom" else "boy",
        hero_title=hero.title,
        problem=problem,
        tool=tool,
        resolution=resolution,
        setting=setting,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story that includes the words "christmas", "friday", and "bread", with a conflict and a quest.',
        f"Tell a child-friendly superhero quest where {f['hero'].id} and {f['helper'].id} search for bread on friday before christmas dinner.",
        f"Write a short story about a hero, a conflict, and a quest to bring back bread for the holiday table.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bread = f["bread"]
    problem = f["problem"]
    answers = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id}, {helper.id}, and the missing bread. Together they faced a conflict and followed a quest to help the holiday meal.",
        ),
        QAItem(
            question="What was the conflict in the story?",
            answer=f"The conflict was that {problem.label} made everyone worried and gave them different ideas at once. They had to calm down and solve it together instead of arguing.",
        ),
        QAItem(
            question="What happened to the bread at the end?",
            answer=f"The bread was found again and got back to the table. That changed the ending from worry to a warm christmas supper.",
        ),
    ]
    if f["outcome"] == "found":
        answers.append(QAItem(
            question="How did the quest help?",
            answer=f"The quest gave them a clear path to follow, and {f['tool'].label} helped them read the clues. Because they stayed together, they could bring the bread home safely.",
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    if f["holiday"] == "christmas":
        out.append(QAItem(
            question="What is christmas?",
            answer="Christmas is a holiday that many families celebrate with lights, gifts, and a special meal together.",
        ))
    if f["day"] == "friday":
        out.append(QAItem(
            question="What is friday?",
            answer="Friday is the day near the end of the week before the weekend starts.",
        ))
    if f["bread"].label == "bread":
        out.append(QAItem(
            question="What is bread?",
            answer="Bread is a food made from dough. People often eat it warm with a meal.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.tool not in TOOLS or params.resolution not in RESOLUTIONS:
        raise StoryError("Invalid params for this storyworld.")
    hero = HEROES.get("nova" if params.hero == "Nova" else "spark")
    if hero is None:
        raise StoryError("Unknown hero.")
    world = tell(
        SETTINGS[params.setting],
        hero,
        params.helper,
        params.helper_gender,
        params.adult,
        params.adult_gender,
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        RESOLUTIONS[params.resolution],
        params.holiday,
        params.day,
    )
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
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes, e.attrs)
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), quest_problem(P), conflict_problem(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if "quest" in p.tags:
            lines.append(asp.fact("quest_problem", pid))
        if "conflict" in p.tags:
            lines.append(asp.fact("conflict_problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    import io
    from contextlib import redirect_stdout
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(hero=None, problem=None, tool=None, resolution=None, setting=None), random.Random(7)))
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: verify smoke test passed.")
    return rc


CURATED = [
    StoryParams(hero="Nova", hero_gender="boy", helper="Mia", helper_gender="girl", adult="Mom", adult_gender="girl", hero_title="tiny shield hero", problem="missing_bread", tool="map", resolution="steady_hands", setting="town"),
    StoryParams(hero="Spark", hero_gender="boy", helper="Leo", helper_gender="boy", adult="Dad", adult_gender="boy", hero_title="young helper hero", problem="baker_mixup", tool="lantern", resolution="ask_baker", setting="bakery"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
