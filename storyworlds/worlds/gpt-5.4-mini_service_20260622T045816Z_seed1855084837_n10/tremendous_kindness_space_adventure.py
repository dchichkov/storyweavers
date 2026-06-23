#!/usr/bin/env python3
"""
storyworlds/worlds/tremendous_kindness_space_adventure.py
=========================================================

A compact storyworld about a child astronaut, a drifting spacecraft problem,
and a tremendous act of kindness that turns the mission around.

The tale stays small on purpose: one live world model, a few registries, a
forward rule for physical and emotional state, and a state-driven renderer.
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
from pathlib import Path
from typing import Optional

# Robust path setup: walk upward until we find the repo-side results.py.
_HERE = Path(__file__).resolve()
for _parent in [_HERE.parent, *_HERE.parents]:
    if (_parent / "results.py").exists():
        sys.path.insert(0, str(_parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Ship:
    id: str
    name: str
    place: str
    hazard: str
    rescue_tool: str
    rescue_method: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    at_risk: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperTool:
    id: str
    label: str
    phrase: str
    power: int
    help_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

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
        c.facts = copy.deepcopy(self.facts)
        c.trace = list(self.trace)
        return c


@dataclass
class StoryParams:
    ship: str
    problem: str
    helper: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


SHIPS = {
    "starport": Ship(
        id="starport",
        name="the bright starport",
        place="a busy starport",
        hazard="tremendous darkness",
        rescue_tool="beacon",
        rescue_method="shone the beacon",
        lesson="kindness can light the way",
        tags={"space", "port"},
    ),
    "moonbase": Ship(
        id="moonbase",
        name="the little moon base",
        place="a moon base",
        hazard="a big power drop",
        rescue_tool="panel",
        rescue_method="fixed the panel",
        lesson="kindness can keep a team calm",
        tags={"space", "moon"},
    ),
    "cometlab": Ship(
        id="cometlab",
        name="the comet lab ship",
        place="a tiny lab ship",
        hazard="a drifting supply crate",
        rescue_tool="magnet",
        rescue_method="pulled the crate back",
        lesson="kindness makes brave helpers",
        tags={"space", "lab"},
    ),
}

PROBLEMS = {
    "darkness": Problem(
        id="darkness",
        label="darkness",
        phrase="a tremendous patch of darkness",
        risk="could not see the dock door",
        at_risk="the landing path",
        severity=1,
        tags={"dark", "beacon"},
    ),
    "powerdrop": Problem(
        id="powerdrop",
        label="power drop",
        phrase="a sudden power drop",
        risk="the guidance screen went black",
        at_risk="the control panel",
        severity=2,
        tags={"panel", "power"},
    ),
    "crate": Problem(
        id="crate",
        label="crate drift",
        phrase="a drifting supply crate",
        risk="the snack locker would get bumped",
        at_risk="the docking rail",
        severity=1,
        tags={"crate", "magnet"},
    ),
}

HELPERS = {
    "beacon": HelperTool(
        id="beacon",
        label="beacon",
        phrase="a small rescue beacon",
        power=1,
        help_text="shone a warm beam across the dock",
        tags={"beacon", "light"},
    ),
    "panel": HelperTool(
        id="panel",
        label="panel key",
        phrase="a tiny panel key",
        power=2,
        help_text="brought the ship panel back to life",
        tags={"panel", "repair"},
    ),
    "magnet": HelperTool(
        id="magnet",
        label="magnet",
        phrase="a gentle magnet tool",
        power=1,
        help_text="pulled the crate away without a bump",
        tags={"magnet", "pull"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Lyra", "Ivy", "Zara", "Pia", "Aria", "Luna"]
BOY_NAMES = ["Orion", "Kai", "Rex", "Noah", "Tate", "Juno", "Eli", "Finn"]
TRAITS = ["curious", "brave", "gentle", "quick-thinking", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship_id, ship in SHIPS.items():
        for problem_id, problem in PROBLEMS.items():
            for helper_id, helper in HELPERS.items():
                if helper.label in problem.tags or helper.id in problem.tags:
                    combos.append((ship_id, problem_id, helper_id))
    return combos


def explain_rejection(problem: Problem, helper: HelperTool) -> str:
    return f"(No story: {helper.label} does not fit the needs of {problem.label} here.)"


def _predict(world: World, hero: Entity, helper: HelperTool) -> dict:
    sim = world.copy()
    _use_helper(sim, sim.get(hero.id), helper, narrate=False)
    return {
        "fixed": sim.facts.get("fixed", False),
        "kindness": sim.get(hero.id).memes.get("kindness", 0),
    }


def _use_helper(world: World, hero: Entity, helper: HelperTool, narrate: bool = True) -> None:
    hero.meters["help"] += 1
    world.facts["fixed"] = True
    if narrate:
        world.say(f"{hero.id} used {helper.phrase} and it {helper.help_text}.")


def _spread_kindness(world: World, hero: Entity, friend: Entity, ship: Ship) -> None:
    hero.memes["kindness"] += 1
    friend.memes["relief"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"{hero.id} shared a tremendous kindness and held {friend.id}'s hand while the ship drifted."
    )
    world.say(
        f"That calm helped them both stay brave inside {ship.name}."
    )


def _resolve(world: World, hero: Entity, friend: Entity, ship: Ship, problem: Problem, helper: HelperTool) -> None:
    world.say(
        f"Then {hero.id} found {helper.phrase}, and {friend.id} pointed to {problem.at_risk}."
    )
    _use_helper(world, hero, helper, narrate=True)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Together they fixed the trouble, and the ship became safe again."
    )
    world.say(
        f"At the end, {hero.id} and {friend.id} watched {ship.place} glow softly, proud of their teamwork."
    )


def tell(ship: Ship, problem: Problem, helper: HelperTool, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, trait: str = "kind") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", attrs={"trait": trait}))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    world.add(Entity(id=ship.id, kind="thing", type="ship", label=ship.name, attrs={"place": ship.place}))
    world.add(Entity(id=problem.id, kind="thing", type="problem", label=problem.label, attrs={"at_risk": problem.at_risk}))
    world.add(Entity(id=helper.id, kind="thing", type="tool", label=helper.label, attrs={"help_text": helper.help_text}))

    hero.memes["kindness"] = 1.0
    friend.memes["worry"] = 1.0
    world.say(
        f"On {ship.name}, {hero.id} and {friend.id} were exploring {ship.place} when {problem.phrase} appeared."
    )
    world.say(
        f"{friend.id} worried because {problem.risk}, but {hero.id} had a kind plan."
    )
    world.para()
    _spread_kindness(world, hero, friend, ship)
    pred = _predict(world, hero, helper)
    world.facts.update(predicted_fixed=pred["fixed"])

    world.para()
    _resolve(world, hero, friend, ship, problem, helper)
    world.facts.update(
        hero=hero,
        friend=friend,
        ship=ship,
        problem=problem,
        helper=helper,
        trait=trait,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ship, problem, helper = f["ship"], f["problem"], f["helper"]
    return [
        f'Write a space adventure for a young child that includes the word "tremendous" and shows kindness on {ship.name}.',
        f"Tell a short story where {f['hero'].id} and {f['friend'].id} meet {problem.label} and use {helper.label} to help each other.",
        f"Write a gentle spaceship story where a tremendous problem is solved by kindness and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    ship = f["ship"]
    problem = f["problem"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who were the story's two children aboard {ship.name}?",
            answer=f"The story was about {hero.id} and {friend.id}. They were exploring {ship.place} when the trouble appeared.",
        ),
        QAItem(
            question=f"What problem did they face on {ship.name}?",
            answer=f"They faced {problem.phrase}. It made the mission hard because {problem.risk}.",
        ),
        QAItem(
            question=f"How did {hero.id} help {friend.id} through the trouble?",
            answer=f"{hero.id} showed a tremendous kindness and stayed calm with {friend.id}. That helped them work together until the problem was fixed.",
        ),
        QAItem(
            question=f"What tool helped them solve the problem?",
            answer=f"They used {helper.phrase}. It was the right tool for this space problem, so the ship could become safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ship = f["ship"]
    helper = f["helper"]
    out = [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being caring and helpful to someone else. It can make scary moments feel smaller.",
        ),
        QAItem(
            question="What is a space adventure?",
            answer="A space adventure is a story about traveling through space, solving problems, and exploring new places.",
        ),
    ]
    if "space" in ship.tags:
        out.append(QAItem(
            question="Why do space crews need tools?",
            answer="Space crews need tools because small problems on a ship can stop the mission. The right tool helps fix trouble safely.",
        ))
    if helper.id == "beacon":
        out.append(QAItem(
            question="What does a beacon do?",
            answer="A beacon sends out a bright signal or light so people can notice it and find their way.",
        ))
    if helper.id == "magnet":
        out.append(QAItem(
            question="What does a magnet tool do?",
            answer="A magnet can pull some metal things closer without needing to push them. That makes it useful for gentle rescue jobs.",
        ))
    return out


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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={dict((k, v) for k, v in e.attrs.items() if v)}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
good_combo(S,P,H) :- ship(S), problem(P), helper(H), helper_fits(H,P).
resolved :- chosen(S,P,H), good_combo(S,P,H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("problem_tag", pid, t))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_fits", hid, h.id))
        for t in sorted(h.tags):
            lines.append(asp.fact("helper_tag", hid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
        print("  only in ASP:", sorted(cl - py))
        print("  only in Python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(ship=None, problem=None, helper=None), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld about kindness.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
              if (args.ship is None or c[0] == args.ship)
              and (args.problem is None or c[1] == args.problem)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, problem, helper = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    friend_name = args.friend or rng.choice([n for n in friend_pool if n != hero_name] or friend_pool)
    return StoryParams(
        ship=ship,
        problem=problem,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ship not in SHIPS or params.problem not in PROBLEMS or params.helper not in HELPERS:
        raise StoryError("Invalid StoryParams.")
    world = tell(
        SHIPS[params.ship],
        PROBLEMS[params.problem],
        HELPERS[params.helper],
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(ship="starport", problem="darkness", helper="beacon", hero_name="Nova", hero_gender="girl", friend_name="Orion", friend_gender="boy"),
    StoryParams(ship="moonbase", problem="powerdrop", helper="panel", hero_name="Kai", hero_gender="boy", friend_name="Mira", friend_gender="girl"),
    StoryParams(ship="cometlab", problem="crate", helper="magnet", hero_name="Lyra", hero_gender="girl", friend_name="Finn", friend_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
