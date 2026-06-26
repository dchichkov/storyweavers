#!/usr/bin/env python3
"""
Story world: shock-suspense-problem-solving quest in a small space-adventure domain.

A child-facing classical simulation where a crew is on a quest through space,
meets an unexpected shock, feels suspense, solves a practical problem, and
finishes with a changed world state.
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


@dataclass
class Vessel:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Site:
    id: str
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class QuestItem:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    fixed: bool = False


@dataclass
class StoryParams:
    ship: str
    crew_name: str
    helper_name: str
    quest: str
    problem: str
    site: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.vessels: dict[str, Vessel] = {}
        self.sites: dict[str, Site] = {}
        self.items: dict[str, QuestItem] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_vessel(self, v: Vessel) -> Vessel:
        self.vessels[v.id] = v
        return v

    def add_site(self, s: Site) -> Site:
        self.sites[s.id] = s
        return s

    def add_item(self, i: QuestItem) -> QuestItem:
        self.items[i.id] = i
        return i


SHIP_REGISTRY = {
    "Comet Kite": {"speed": 2.0, "spark": 1.0},
    "Star Pebble": {"speed": 1.0, "spark": 2.0},
    "Moon Lantern": {"speed": 1.5, "spark": 1.5},
}

SITE_REGISTRY = {
    "asteroid_gate": Site(id="asteroid_gate", name="the asteroid gate", kind="gate"),
    "silent_moon": Site(id="silent_moon", name="the silent moon", kind="moon"),
    "cloud_ring": Site(id="cloud_ring", name="the cloud ring", kind="ring"),
    "signal_cave": Site(id="signal_cave", name="the signal cave", kind="cave"),
}

QUEST_REGISTRY = {
    "starlight_key": QuestItem(id="starlight_key", label="starlight key", kind="key"),
    "map_chip": QuestItem(id="map_chip", label="map chip", kind="chip"),
    "glow_seed": QuestItem(id="glow_seed", label="glow seed", kind="seed"),
}

PROBLEMS = {
    "jammed_door": "a door that would not open",
    "dead_panel": "a quiet control panel with no light",
    "lost_signal": "a message that kept slipping away",
}

NAMES = ["Mina", "Taro", "Lia", "Niko", "Pia", "Ravi", "Zuri", "Oren"]
HELPERS = ["Ari", "Bo", "Cleo", "Dax", "Eli", "Faye", "Juno", "Kai"]


ASP_RULES = r"""
ship(S) :- ship_name(S).
site(T) :- site_name(T).
quest_item(Q) :- quest_item_name(Q).

shock(Site) :- signal(Site), unexpected(Site).
suspense(Crew) :- shock(_), crew(Crew).
problem(Crew) :- suspense(Crew), blocked(_).
solved(Crew) :- problem(Crew), fix(_, _).

success(Ship,Site,Q) :- ship_name(Ship), site_name(Site), quest_item_name(Q), solved(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for ship in SHIP_REGISTRY:
        lines.append(asp.fact("ship_name", ship))
    for site in SITE_REGISTRY.values():
        lines.append(asp.fact("site_name", site.id))
    for q in QUEST_REGISTRY.values():
        lines.append(asp.fact("quest_item_name", q.id))
    for site in SITE_REGISTRY.values():
        if site.kind in {"gate", "cave"}:
            lines.append(asp.fact("signal", site.id))
            lines.append(asp.fact("unexpected", site.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show success/3."))
    return sorted(set(asp.atoms(model, "success")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(cl - py))
    print("  only in Python:", sorted(py - cl))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for ship in SHIP_REGISTRY:
        for site in SITE_REGISTRY:
            for quest in QUEST_REGISTRY:
                if site in {"asteroid_gate", "signal_cave"}:
                    combos.append((ship, site, quest))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure with shock, suspense, and problem solving.")
    ap.add_argument("--ship", choices=SHIP_REGISTRY)
    ap.add_argument("--site", choices=SITE_REGISTRY)
    ap.add_argument("--quest", choices=QUEST_REGISTRY)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    if args.site:
        combos = [c for c in combos if c[1] == args.site]
    if args.ship:
        combos = [c for c in combos if c[0] == args.ship]
    if args.quest:
        combos = [c for c in combos if c[2] == args.quest]
    if not combos:
        raise StoryError("No valid space quest matches those choices.")
    ship, site, quest = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    problem = args.problem or rng.choice(list(PROBLEMS))
    return StoryParams(ship=ship, crew_name=name, helper_name=helper, quest=quest, problem=problem, site=site)


def _story_setup(world: World, params: StoryParams) -> None:
    ship = world.add_vessel(Vessel(id="ship", name=params.ship, role="home"))
    site = world.add_site(SITE_REGISTRY[params.site])
    quest = world.add_item(QuestItem(id=params.quest, label=QUEST_REGISTRY[params.quest].label, kind=QUEST_REGISTRY[params.quest].kind))
    crew = world.add_vessel(Vessel(id="crew", name=params.crew_name, role="captain"))
    helper = world.add_vessel(Vessel(id="helper", name=params.helper_name, role="helper"))

    ship.meters["power"] = 3.0
    crew.memes["hope"] = 1.0
    helper.memes["calm"] = 1.0

    world.facts.update(ship=ship, site=site, quest=quest, crew=crew, helper=helper, params=params)


def tell(params: StoryParams) -> World:
    world = World()
    _story_setup(world, params)
    ship: Vessel = world.facts["ship"]  # type: ignore[assignment]
    site: Site = world.facts["site"]  # type: ignore[assignment]
    quest: QuestItem = world.facts["quest"]  # type: ignore[assignment]
    crew: Vessel = world.facts["crew"]  # type: ignore[assignment]
    helper: Vessel = world.facts["helper"]  # type: ignore[assignment]

    world.say(f"{crew.name} rode in the {ship.name}, chasing a small quest to find the {quest.label}.")
    world.say(f"With {helper.name} beside {crew.name}, the ship slid toward {site.name} under quiet stars.")
    world.para()

    world.say(f"Then came a shock: {PROBLEMS[params.problem]}.")
    crew.memes["shock"] = 1.0
    crew.memes["suspense"] = 1.0
    world.say(f"{crew.name} held still and listened, because the next answer mattered.")
    world.say(f"{helper.name} peeked at the panel and kept a careful voice: the team would need a plan.")
    world.para()

    if params.problem == "jammed_door":
        world.say(f"{helper.name} found a small latch tool in the pocket box.")
        world.say(f"Together they lifted the stuck door, one tiny bit at a time.")
    elif params.problem == "dead_panel":
        world.say(f"{helper.name} traced the wires and tapped the spare glow cell into place.")
        world.say(f"The panel blinked awake, and the dark room turned soft and blue.")
    else:
        world.say(f"{helper.name} tuned the antenna toward the biggest metal rock nearby.")
        world.say(f"The message came back, clear and bright, like a star finally found.")
    crew.memes["problem_solving"] = 1.0
    world.para()

    quest.fixed = True
    ship.meters["power"] -= 0.5
    crew.memes["joy"] = 1.0
    world.say(f"At last, the {quest.label} was safe in {crew.name}'s hands.")
    world.say(f"Their quest was not over, but the worst surprise had turned into a brave little win.")
    world.say(f"On the way home, the {ship.name} glowed warm and steady, and {crew.name} smiled at {helper.name}.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]  # type: ignore[index]
    return [
        f"Write a short space adventure where {p.crew_name} meets a shock and solves a problem on the way to a quest.",
        f"Tell a child-friendly story about {p.crew_name}, {p.helper_name}, and a mission to find the {world.facts['quest'].label}.",
        f"Create a suspenseful but gentle story set near {world.facts['site'].name} with a clever fix and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    ship: Vessel = world.facts["ship"]  # type: ignore[assignment]
    site: Site = world.facts["site"]  # type: ignore[assignment]
    quest: QuestItem = world.facts["quest"]  # type: ignore[assignment]
    helper: Vessel = world.facts["helper"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who went on the quest in the {ship.name}?",
            answer=f"{p.crew_name} went on the quest in the {ship.name} with {helper.name} helping along the way.",
        ),
        QAItem(
            question=f"What was the shock in the story near {site.name}?",
            answer=f"The shock was {PROBLEMS[p.problem]}. That surprise made everyone pause and think carefully.",
        ),
        QAItem(
            question=f"What did {p.crew_name} and {helper.name} find at the end?",
            answer=f"They found the {quest.label} and kept it safe after solving the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or search for something important, often with a goal to reach and a problem to solve.",
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something is tricky or unexpected.",
        ),
        QAItem(
            question="Why do spaceships need careful checking?",
            answer="Spaceships need careful checking because even a tiny problem can make a trip harder, so the crew must solve it safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for v in world.vessels.values():
        lines.append(f"{v.id}: {v.name} role={v.role} meters={v.meters} memes={v.memes}")
    for s in world.sites.values():
        lines.append(f"{s.id}: {s.name} kind={s.kind}")
    for i in world.items.values():
        lines.append(f"{i.id}: {i.label} fixed={i.fixed}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify_and_solve() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show success/3."))
        return
    if args.verify:
        sys.exit(asp_verify_and_solve())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show success/3."))
        triples = sorted(set(asp.atoms(model, "success")))
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for ship, site, quest in valid_combos():
            params = StoryParams(
                ship=ship,
                crew_name=NAMES[0],
                helper_name=HELPERS[0],
                quest=quest,
                problem="dead_panel",
                site=site,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
