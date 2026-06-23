#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/rip_ado_whosejigger_problem_solving_moral_value.py
=============================================================================================================

A small standalone storyworld about a tall-tale repair job: a rip in a banner,
an ado at the market, and a mysterious whosejigger that helps solve the trouble
with humor and moral value.

The domain is intentionally narrow and state-driven:
- A banner or sail gets a rip.
- A helper looks for the right whosejigger in a workshop or wagon.
- The problem is solved with a repair that proves the change physically.
- The ending keeps the tone tall, warm, and a little funny.

Words required by the seed are used in the story space:
- rip
- ado
- whosejigger

Features emphasized:
- Problem Solving
- Moral Value
- Humor
- Tall-tale style

The story generator produces several compatible combinations across settings,
problems, helpers, and tools. It uses a world model with physical meters and
emotional memes, plus a small ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    helper_for: str = ""
    tool_for: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    key: str
    label: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Problem:
    key: str
    name: str
    noun: str
    verb: str
    at_risk: str
    damage: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    key: str
    label: str
    phrase: str
    use: str
    fixs: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    humor: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    key: str
    label: str
    type: str
    talking_style: str
    moral_style: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    helper: str
    name: str
    gender: str
    partner_name: str
    partner_gender: str
    seed: Optional[int] = None


PLACES = {
    "harbor": Place("harbor", "the harbor", "saltwind", {"banner", "sail"}),
    "market": Place("market", "the market square", "bustle", {"banner", "awning"}),
    "barn": Place("barn", "the red barn", "haydust", {"sack", "banner"}),
    "fair": Place("fair", "the county fair", "music", {"banner", "kite"}),
}

PROBLEMS = {
    "banner_rip": Problem(
        "banner_rip", "a rip in the banner", "banner", "mended",
        "the banner", "the banner flapped and tore wider", "cloth",
        tags={"rip", "banner"},
    ),
    "sail_rip": Problem(
        "sail_rip", "a rip in the sail", "sail", "patched",
        "the sail", "the sail snapped in the wind", "cloth",
        tags={"rip", "sail"},
    ),
    "sack_rip": Problem(
        "sack_rip", "a rip in the sack", "sack", "stitched",
        "the sack", "the apples rolled out", "cloth",
        tags={"rip", "sack"},
    ),
    "awning_rip": Problem(
        "awning_rip", "a rip in the awning", "awning", "sewn",
        "the awning", "the rain slipped through", "cloth",
        tags={"rip", "awning"},
    ),
}

TOOLS = {
    "whosejigger": Tool(
        "whosejigger",
        "a whosejigger",
        "a little whosejigger",
        "tighten the tear",
        fixs={"cloth"},
        covers={"cloth"},
        humor="It looked like a spoon and a corkscrew had a polite argument.",
        tags={"whosejigger"},
    ),
    "needle_spool": Tool(
        "needle_spool",
        "a needle and spool",
        "a needle and a spool of thread",
        "stitch the rip",
        fixs={"cloth"},
        covers={"cloth"},
        humor="The spool rolled once, like it was hurrying to help.",
        tags={"needle"},
    ),
    "patch_kit": Tool(
        "patch_kit",
        "a patch kit",
        "a patch kit with sticky cloth",
        "cover the tear",
        fixs={"cloth"},
        covers={"cloth"},
        humor="It came in a tin that jingled like tiny bells.",
        tags={"patch"},
    ),
}

HELPERS = {
    "ma": Helper("ma", "Ma", "mother", "gentle", "kind"),
    "uncle": Helper("uncle", "Uncle Jed", "father", "wry", "fair"),
    "neighbor": Helper("neighbor", "Neighbor Nell", "woman", "plain-spoken", "helpful"),
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    problem = world.facts["problem_cfg"]
    for ent in world.entities.values():
        if ent.id != "damaged":
            continue
        if ent.meters["torn"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["worse"] += 1
        world.facts["was_worse"] = True
        out.append(f"The {problem.noun} looked meaner by the minute.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    tool = world.facts["tool_cfg"]
    problem = world.facts["problem_cfg"]
    damaged = world.get("damaged")
    if damaged.meters["torn"] < THRESHOLD:
        return out
    if problem.zone not in tool.covers or problem.zone not in tool.fixs:
        return out
    sig = ("fix", tool.key, problem.key)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    damaged.meters["torn"] = 0
    damaged.meters["mended"] = 1
    helper = world.facts["helper_ent"]
    helper.memes["pride"] += 1
    out.append(f"The {tool.label} did its work, and the tear came out neat.")
    return out


RULES = [Rule("spread", _r_spread), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_at_risk(problem: Problem, tool: Tool) -> bool:
    return problem.zone in tool.fixs and problem.zone in tool.covers


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for prob in PROBLEMS:
            for tool in TOOLS:
                if problem_at_risk(PROBLEMS[prob], TOOLS[tool]):
                    combos.append((p, prob, tool))
    return combos


def _name_for(gender: str, rng: random.Random) -> str:
    names = {
        "girl": ["Ada", "Mabel", "Nina", "June", "Ivy", "Elsie"],
        "boy": ["Wes", "Hank", "Otis", "Bo", "Ezra", "Cal"],
    }
    return rng.choice(names[gender])


def intro(world: World, hero: Entity, partner: Entity, problem: Problem) -> None:
    world.say(
        f"Once, on {world.place.label}, {hero.id} and {partner.id} had their hands full "
        f"with {problem.name}."
    )
    world.say(
        f"They were good-hearted folk, and they hated to see a {problem.noun} in a fix."
    )


def add_ado(world: World, hero: Entity, partner: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    partner.memes["humor"] += 1
    world.say(
        f"With a little ado and a lot of sideways looks, {hero.id} said the {problem.noun} "
        f"ought not blow itself wider."
    )
    world.say(
        f"{helper.id} chuckled and said, \"Hold your horses and pass the {problem.noun}; "
        f"we'll see what the whosejigger can do.\""
    )


def attempt(world: World, helper: Entity, tool: Tool, problem: Problem) -> None:
    world.say(f"{tool.humor} {helper.id} set to work with {tool.phrase}.")
    damaged = world.get("damaged")
    damaged.meters["torn"] += 1
    propagate(world, narrate=True)


def resolve(world: World, hero: Entity, partner: Entity, helper: Entity, tool: Tool, problem: Problem) -> None:
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Before long, the {problem.noun} was straight as a church fence, and the "
        f"{world.place.label} could breathe again."
    )
    world.say(
        f"{hero.id} laughed so hard they nearly dropped the broom, and {partner.id} said "
        f"the whosejigger deserved a medal made of tin foil."
    )
    world.say(
        f"In the end, the patched {problem.noun} fluttered bravely in the breeze, "
        f"showing plain as day that a small good deed can mend a big bother."
    )


def tell(place: Place, problem: Problem, tool: Tool, helper_cfg: Helper,
         hero_name: str, hero_gender: str, partner_name: str, partner_gender: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender))
    helper = world.add(Entity(id=helper_cfg.label, kind="character", type=helper_cfg.type, label=helper_cfg.label))
    damaged = world.add(Entity(id="damaged", type=problem.noun))
    damaged.meters["torn"] = 0
    helper.memes["pride"] = 0
    world.facts = {
        "hero": hero,
        "partner": partner,
        "helper_ent": helper,
        "helper_cfg": helper_cfg,
        "problem_cfg": problem,
        "tool_cfg": tool,
        "place_cfg": place,
        "damaged": damaged,
        "resolved": False,
    }

    intro(world, hero, partner, problem)
    world.para()
    add_ado(world, hero, partner, helper, problem)
    attempt(world, helper, tool, problem)
    world.para()
    resolve(world, hero, partner, helper, tool, problem)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["problem_cfg"]
    t = f["tool_cfg"]
    place = f["place_cfg"]
    return [
        f'Write a tall-tale story for a young child about {p.name} at {place.label}, '
        f"using the word '{t.key}'.",
        f"Tell a funny problem-solving story where a rip gets fixed with {t.label} "
        f"and everybody keeps a calm head.",
        f"Write a moral tale set at {place.label} where {p.noun} is repaired with humor "
        f"and a trusty whosejigger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    partner: Entity = f["partner"]
    helper: Entity = f["helper_ent"]
    p: Problem = f["problem_cfg"]
    t: Tool = f["tool_cfg"]
    place: Place = f["place_cfg"]
    damaged: Entity = f["damaged"]
    qa = [
        QAItem(
            question=f"What problem did {hero.id} and {partner.id} find at {place.label}?",
            answer=f"They found {p.name}. The tear was small at first, but it was the kind of trouble that could grow if nobody paid it mind.",
        ),
        QAItem(
            question=f"Who came up with the fix for the {p.noun}?",
            answer=f"{helper.id} did. {helper.id} had the right calm for the job, and {t.label} fit the problem like a shoe on a Sunday horse.",
        ),
        QAItem(
            question=f"Why did the {p.noun} stop getting worse?",
            answer=f"Because the repair tool matched the cloth problem and the helper used it before the tear could widen. After that, the damage meter dropped back to zero.",
        ),
        QAItem(
            question=f"How did {hero.id} and {partner.id} feel after the repair?",
            answer=f"They felt relieved and amused. The whole business had been a grand ado, but the ending showed them that a steady head and a good helper can turn worry into a laugh.",
        ),
    ]
    if damaged.meters["mended"] >= THRESHOLD:
        qa.append(QAItem(
            question=f"What did the repaired {p.noun} look like at the end?",
            answer=f"It was mended clean and neat. It flapped in the breeze like it was proud to have survived its own trouble.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: Problem = f["problem_cfg"]
    t: Tool = f["tool_cfg"]
    out = [
        QAItem(
            question="What does a whosejigger mean?",
            answer="In a funny story, a whosejigger is a mystery tool name for a gadget whose exact shape you do not need to know. It is the sort of thing folks point at when the right little tool is the hero of the hour.",
        ),
        QAItem(
            question="What does it mean to have ado?",
            answer="Ado means a lot of fuss or excitement. People make ado when everybody is talking at once and the problem feels bigger than it really is.",
        ),
        QAItem(
            question="What is a rip?",
            answer="A rip is a tear in cloth or paper. It can grow bigger if nobody mends it.",
        ),
    ]
    if "whosejigger" in t.tags:
        out.append(QAItem(
            question="Why is a small tool useful in a repair story?",
            answer="A small tool is useful when it matches the job exactly. It can fix a small damage before the damage becomes a bigger mess.",
        ))
    if "rip" in p.tags:
        out.append(QAItem(
            question="Why should a rip be repaired quickly?",
            answer="Because a rip can spread when cloth flaps in the wind. Quick repair keeps the trouble small and the object useful.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, T) :- place(P), problem(Pr), tool(T), compatible(Pr, T).
compatibility(Pr, T) :- problem(Pr), tool(T), covers(T, cloth), fixs(T, cloth), rip_problem(Pr).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in PLACES:
        lines.append(asp.fact("place", key))
    for key, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", key))
        if "rip" in pr.tags:
            lines.append(asp.fact("rip_problem", key))
    for key, t in TOOLS.items():
        lines.append(asp.fact("tool", key))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", key, c))
        for f in sorted(t.fixs):
            lines.append(asp.fact("fixs", key, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    p = set(valid_combos())
    a = set(asp_valid_combos())
    ok = True
    if p != a:
        ok = False
        print("MISMATCH: python vs asp combos")
        print("python-only:", sorted(p - a))
        print("asp-only:", sorted(a - p))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, tool=None, helper=None, name=None, gender=None, partner_name=None, partner_gender=None, seed=None), random.Random(777)))
        _ = sample.story
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(p)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a rip, an ado, and a whosejigger.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
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
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, tool = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _name_for(gender, rng)
    partner_gender = args.partner_gender or ("boy" if gender == "girl" else "girl")
    partner_name = args.partner_name or _name_for(partner_gender, rng)
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        helper=helper,
        name=name,
        gender=gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.tool not in TOOLS or params.helper not in HELPERS:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    tool = TOOLS[params.tool]
    helper_cfg = HELPERS[params.helper]
    if not problem_at_risk(problem, tool):
        raise StoryError("This tool does not reasonably solve this rip problem.")
    world = tell(place, problem, tool, helper_cfg, params.name, params.gender, params.partner_name, params.partner_gender)
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
    StoryParams(place="harbor", problem="sail_rip", tool="whosejigger", helper="ma", name="Ada", gender="girl", partner_name="Wes", partner_gender="boy"),
    StoryParams(place="market", problem="banner_rip", tool="needle_spool", helper="neighbor", name="Mabel", gender="girl", partner_name="Bo", partner_gender="boy"),
    StoryParams(place="barn", problem="sack_rip", tool="patch_kit", helper="uncle", name="Otis", gender="boy", partner_name="June", partner_gender="girl"),
    StoryParams(place="fair", problem="awning_rip", tool="whosejigger", helper="neighbor", name="Elsie", gender="girl", partner_name="Cal", partner_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
