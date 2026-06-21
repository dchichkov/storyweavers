#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/technology_opponent_teamwork_superhero_story.py
===============================================================================

A standalone storyworld about a superhero team, a piece of technology, and an
opponent who causes trouble. The story is built from a small causal simulation:
heroes coordinate, a device is used, the opponent creates a problem, teamwork
resolves it, and the ending proves what changed.

The world keeps:
- physical meters: charge, damage, trapped, secure
- emotional memes: courage, worry, trust, teamwork, pride

The seed words are honored directly in the story text: technology, opponent.
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
TECH_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    name: str
    scene: str
    dark_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tech:
    id: str
    label: str
    phrase: str
    function: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Opponent:
    id: str
    label: str
    move: str
    weakness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TeamPlan:
    id: str
    opener: str
    split_task: str
    combine_task: str
    ending: str
    tags: set[str] = field(default_factory=set)


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_teamup(world: World) -> list[str]:
    out: list[str] = []
    if world.get("team").memes["teamwork"] < THRESHOLD:
        return out
    if world.get("device").meters["charge"] < THRESHOLD:
        return out
    sig = ("teamup",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("device").meters["secure"] += 1
    world.get("opponent").meters["trap"] = max(0.0, world.get("opponent").meters["trap"] - 1)
    out.append("__team__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.get("device").meters["secure"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("base").meters["damage"] = max(0.0, world.get("base").meters["damage"] - 1)
    out.append("The team steadied the technology and kept it working.")
    return out


CAUSAL_RULES = [Rule("teamup", _r_teamup), Rule("repair", _r_repair)]


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


def predict_opponent(world: World) -> dict:
    sim = world.copy()
    sim.get("device").meters["charge"] += 0.5
    sim.get("opponent").meters["trap"] += 1
    propagate(sim, narrate=False)
    return {
        "secure": sim.get("device").meters["secure"] >= THRESHOLD,
        "damage": sim.get("base").meters["damage"],
    }


def team_introduce(world: World, hero1: Entity, hero2: Entity, setting: Setting, plan: TeamPlan) -> None:
    hero1.memes["courage"] += 1
    hero2.memes["trust"] += 1
    world.say(
        f"On a bright night in {setting.name}, {hero1.id} and {hero2.id} stood "
        f"ready beside {setting.scene}. {plan.opener}"
    )


def show_device(world: World, tech: Tech) -> None:
    world.say(
        f"They brought {tech.phrase}, a piece of technology that could {tech.function}."
    )


def opponent_strikes(world: World, opp: Opponent, setting: Setting) -> None:
    world.get("opponent").meters["trap"] += 1
    world.get("base").meters["damage"] += 1
    world.get("device").meters["charge"] -= 0.2
    world.say(
        f"Then {opp.label} swooped in with {opp.move}, and the {setting.dark_spot} "
        f"began to shake."
    )


def split_team(world: World, hero1: Entity, hero2: Entity, plan: TeamPlan) -> None:
    hero1.memes["teamwork"] += 1
    hero2.memes["teamwork"] += 1
    world.say(
        f"{hero1.id} took {plan.split_task}, while {hero2.id} handled {plan.combine_task}."
    )


def use_tech(world: World, tech: Tech, hero1: Entity, hero2: Entity) -> None:
    world.get("device").meters["charge"] += 1
    world.say(
        f"{hero1.id} powered up the {tech.label}, and {hero2.id} held it steady "
        f"so the signal stayed strong."
    )
    propagate(world, narrate=True)


def defeat_opponent(world: World, opp: Opponent, plan: TeamPlan) -> None:
    world.get("opponent").meters["trap"] = 0.0
    world.get("opponent").memes["frustration"] += 1
    world.say(
        f"With a final push, they used {opp.weakness} against {opp.label}. {plan.ending}"
    )


def ending_image(world: World, setting: Setting, tech: Tech, hero1: Entity, hero2: Entity) -> None:
    world.say(
        f"At the end, {setting.name} was calm again. {tech.label_word if hasattr(tech, 'label_word') else tech.label} "
        f"glowed softly, and {hero1.id} and {hero2.id} smiled because their teamwork had saved the day."
    )


def tell(setting: Setting, tech: Tech, opp: Opponent, plan: TeamPlan,
         hero1_name: str = "Nova", hero2_name: str = "Spark",
         hero1_type: str = "girl", hero2_type: str = "boy") -> World:
    world = World()
    hero1 = world.add(Entity(id=hero1_name, kind="character", type=hero1_type, role="hero", traits=["brave"]))
    hero2 = world.add(Entity(id=hero2_name, kind="character", type=hero2_type, role="hero", traits=["quick"]))
    world.add(Entity(id="team", kind="character", type="group", role="team"))
    world.add(Entity(id="device", kind="thing", type="device", label=tech.label))
    world.add(Entity(id="opponent", kind="character", type="villain", label=opp.label))
    world.add(Entity(id="base", kind="thing", type="base", label="the base"))
    world.get("team").memes["teamwork"] = 1.0
    world.get("device").meters["charge"] = 1.0
    world.get("device").meters["secure"] = 0.0
    world.get("base").meters["damage"] = 0.0

    team_introduce(world, hero1, hero2, setting, plan)
    show_device(world, tech)
    world.para()
    opponent_strikes(world, opp, setting)
    world.say("The heroes looked at each other and knew they had to work as one.")
    split_team(world, hero1, hero2, plan)
    use_tech(world, tech, hero1, hero2)
    defeat_opponent(world, opp, plan)
    world.para()
    ending_image(world, setting, tech, hero1, hero2)

    world.facts.update(
        setting=setting, tech=tech, opponent=opp, plan=plan,
        hero1=hero1, hero2=hero2,
        secure=world.get("device").meters["secure"] >= THRESHOLD,
        damage=world.get("base").meters["damage"],
        charge=world.get("device").meters["charge"],
    )
    return world


SETTINGS = {
    "city": Setting(id="city", name="Star City", scene="the rooftop beacon", dark_spot="skyline"),
    "harbor": Setting(id="harbor", name="Blue Harbor", scene="the watchtower", dark_spot="dock"),
    "museum": Setting(id="museum", name="Moon Museum", scene="the glass hall", dark_spot="main gallery"),
}

TECHS = {
    "scanner": Tech(id="scanner", label="signal scanner", phrase="a signal scanner", function="find hidden trouble"),
    "glider": Tech(id="glider", label="glider pack", phrase="a glider pack", function="reach far places fast"),
    "shield": Tech(id="shield", label="power shield", phrase="a power shield", function="hold back danger"),
}

OPPONENTS = {
    "mist": Opponent(id="mist", label="Mist Wolf", move="a cloud of sneaky fog", weakness="bright teamwork"),
    "buzz": Opponent(id="buzz", label="Captain Buzz", move="a swarm of buzzing drones", weakness="careful coordination"),
    "glow": Opponent(id="glow", label="Night Glow", move="a flash of blinding sparks", weakness="steady hands"),
}

PLANS = {
    "scan": TeamPlan(id="scan", opener="They nodded and split up the job.", split_task="scanning the shadows", combine_task="watching the doors", ending="The danger vanished in the light."),
    "lift": TeamPlan(id="lift", opener="They made a quick plan together.", split_task="lifting the beam", combine_task="guiding the device", ending="The barrier popped open at once."),
    "lock": TeamPlan(id="lock", opener="They whispered, then agreed on a team move.", split_task="holding the corners", combine_task="locking the latch", ending="The trap closed before the opponent could escape."),
}


@dataclass
class StoryParams:
    setting: str
    tech: str
    opponent: str
    plan: str
    hero1: str
    hero1_type: str
    hero2: str
    hero2_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TECHS:
            for o in OPPONENTS:
                for p in PLANS:
                    combos.append((s, t, o, p))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero teamwork story world with technology and an opponent.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tech", choices=TECHS)
    ap.add_argument("--opponent", choices=OPPONENTS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--type1", choices=["girl", "boy"])
    ap.add_argument("--type2", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid combinations.")
    filtered = [c for c in combos
                if args.setting in (None, c[0])
                and args.tech in (None, c[1])
                and args.opponent in (None, c[2])
                and args.plan in (None, c[3])]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tech, opponent, plan = rng.choice(filtered)
    return StoryParams(
        setting=setting,
        tech=tech,
        opponent=opponent,
        plan=plan,
        hero1=args.name1 or rng.choice(["Nova", "Mira", "Luna", "Vex"]),
        hero1_type=args.type1 or rng.choice(["girl", "boy"]),
        hero2=args.name2 or rng.choice(["Spark", "Pulse", "Comet", "Dash"]),
        hero2_type=args.type2 or rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.tech not in TECHS or params.opponent not in OPPONENTS or params.plan not in PLANS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], TECHS[params.tech], OPPONENTS[params.opponent], PLANS[params.plan],
                 hero1_name=params.hero1, hero2_name=params.hero2,
                 hero1_type=params.hero1_type, hero2_type=params.hero2_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story that includes the words technology and opponent, and shows teamwork in {f['setting'].name}.",
        f"Tell a child-friendly superhero adventure where two heroes use {f['tech'].label} to stop an opponent.",
        f"Write a bright story where teamwork helps heroes beat an opponent and keep their technology working.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero1, hero2 = f["hero1"], f["hero2"]
    tech, opp, setting = f["tech"], f["opponent"], f["setting"]
    return [
        ("Who are the story heroes?", f"The story is about {hero1.id} and {hero2.id}, who worked together like a team."),
        ("What piece of technology did they use?", f"They used {tech.phrase}, which helped them handle the trouble."),
        ("Who caused the problem?", f"{opp.label} caused the trouble by attacking {setting.name} and making the place shake."),
        ("How did they win?", f"They won by using teamwork and {tech.label} together, so the opponent could not keep going."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is technology?", "Technology is a tool or machine people use to help solve a problem or do a job."),
        ("What does teamwork mean?", "Teamwork means people work together, share the job, and help each other finish."),
        ("What is an opponent?", "An opponent is someone who is on the other side and causes a challenge or a contest."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
    StoryParams(setting="city", tech="scanner", opponent="mist", plan="scan", hero1="Nova", hero1_type="girl", hero2="Spark", hero2_type="boy"),
    StoryParams(setting="harbor", tech="shield", opponent="buzz", plan="lock", hero1="Mira", hero1_type="girl", hero2="Dash", hero2_type="boy"),
    StoryParams(setting="museum", tech="glider", opponent="glow", plan="lift", hero1="Luna", hero1_type="girl", hero2="Pulse", hero2_type="boy"),
]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
tech(T) :- tech_fact(T).
opponent(O) :- opponent_fact(O).
plan(P) :- plan_fact(P).
valid(S,T,O,P) :- setting(S), tech(T), opponent(O), plan(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for t in TECHS:
        lines.append(asp.fact("tech_fact", t))
    for o in OPPONENTS:
        lines.append(asp.fact("opponent_fact", o))
    for p in PLANS:
        lines.append(asp.fact("plan_fact", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
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
