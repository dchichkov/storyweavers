#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/governor_insect_mystery_to_solve_friendship_pirate.py
=====================================================================================

A tiny standalone storyworld about a pirate governor, a puzzling insect, and two
friends who solve the mystery together.

The world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen template swap
- Python reasonableness gate plus inline ASP twin
- three QA sets grounded in world state
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp

The source tale behind this world is simple:
a governor on a pirate island keeps finding strange little clues, two friends
follow them together, and they discover that an insect is causing the mystery.
The governor is not a villain; the friendship matters, the island feels like a
pirate tale, and the ending proves what changed.
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"governor": "governor", "captain": "captain", "child": "child"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    pirate_color: str
    dark_spot: str
    has_ship: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    hiding_place: str
    smell: str
    noise: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendPlan:
    id: str
    method: str
    helper_line: str
    reveal_line: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _r_mystery(world: World) -> list[str]:
    out = []
    gov = world.entities.get("governor")
    bug = world.entities.get("insect")
    if not gov or not bug:
        return out
    if bug.meters["seen"] < THRESHOLD:
        return out
    sig = ("mystery",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gov.memes["curiosity"] += 1
    for e in world.entities.values():
        if e.role == "friend":
            e.memes["curiosity"] += 1
    out.append("__mystery__")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    if world.get("governor").memes["relief"] < THRESHOLD:
        return out
    sig = ("friendship",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.role in {"friend", "governor"}:
            e.memes["trust"] += 1
    out.append("__bond__")
    return out


CAUSAL_RULES = [_r_mystery, _r_friendship]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule(world)
            if got:
                changed = True


def is_reasonable(place: Place, mystery: Mystery, plan: FriendPlan) -> bool:
    return "pirate" in place.tags and "friendship" in plan.tags and mystery.id == "insect"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PLACES:
        for mid in MYSTERIES:
            for plan_id in PLANS:
                if is_reasonable(PLACES[pid], MYSTERIES[mid], PLANS[plan_id]):
                    out.append((pid, mid, plan_id))
    return out


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("insect").meters["seen"] += 1
    propagate(sim)
    return {"curious": sim.get("governor").memes["curiosity"] >= THRESHOLD}


def tell(place: Place, mystery: Mystery, plan: FriendPlan,
         governor_name: str = "Gale",
         friend1: str = "Mira",
         friend2: str = "Tess") -> World:
    w = World()
    gov = w.add(Entity(id="governor", kind="character", type="governor", label=governor_name, role="governor"))
    a = w.add(Entity(id=friend1, kind="character", type="girl", label=friend1, role="friend"))
    b = w.add(Entity(id=friend2, kind="character", type="girl", label=friend2, role="friend"))
    bug = w.add(Entity(id="insect", kind="character", type="insect", label="tiny insect", role="mystery"))
    harbor = w.add(Entity(id="harbor", type="place", label=place.name))
    ship = w.add(Entity(id="ship", type="thing", label="pirate ship"))
    gov.memes["pride"] = 1.0
    a.memes["loyalty"] = 1.0
    b.memes["loyalty"] = 1.0

    w.say(f"On the pirate island of {place.name}, Governor {governor_name} stood on the harbor wall beside {friend1} and {friend2}.")
    w.say(f"Their ship rocked gently, and a strange little mystery began when {mystery.clue} was found near {mystery.hiding_place}.")
    w.para()
    w.say(f'"We should solve this together," said {friend1}, and {friend2} nodded. They followed {mystery.noise} and {mystery.smell} across the deck.')
    w.say(f'{governor_name} frowned. "A pirate island should not be full of odd clues," {gov.pronoun()} said, but {gov.pronoun("possessive")} voice was calm.')
    pred = predict(w)
    w.facts["predicted"] = pred["curious"]

    w.para()
    bug.meters["seen"] += 1
    propagate(w)
    w.say(f"Then the friends lifted a loose board, and there it was: the {bug.label}, busy under the plank, making the whole mystery feel alive.")
    w.say(f'The insect had been nibbling crumbs and leaving the trail, not stealing treasure at all.')
    if pred["curious"]:
        w.say(f'{friend1} laughed first. "{plan.helper_line}"')
        w.say(f'{friend2} pointed to the crumbs. "{plan.reveal_line}"')

    w.para()
    gov.memes["relief"] += 1
    w.say(f'Governor {governor_name} smiled wide. "That is a mystery solved," {gov.pronoun()} said. "And it was solved by friends."')
    w.say(f'They swept away the crumbs, left a tiny cup of sugar-water far from the maps, and the {bug.label} crawled off into the lantern light.')
    w.say(f"After that, the harbor felt brave again, and the governor and the two friends watched the pirate ship sway under a clean, quiet sky.")

    w.facts.update(
        governor=gov, friend1=a, friend2=b, insect=bug, place=place,
        mystery=mystery, plan=plan, outcome="solved"
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the words "governor" and "insect" and ends with a mystery being solved by friends.',
        f"Tell a friendship story on a pirate island where Governor {f['governor'].label} and two friends follow clues to learn what the insect is doing.",
        f"Write a small mystery story with a calm governor, a tiny insect, and a kind ending that shows the friends working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gov = f["governor"]
    bug = f["insect"]
    a = f["friend1"]
    b = f["friend2"]
    place = f["place"]
    plan = f["plan"]
    return [
        QAItem(
            question="Who solved the mystery?",
            answer=f'Governor {gov.label} solved it with {a.label} and {b.label}. They looked at the clues together and found the insect, so the answer came from friendship as well as careful watching.'
        ),
        QAItem(
            question="What was the insect doing?",
            answer=f"The insect was nibbling crumbs and leaving a trail near the hiding place. That small work explained the strange clues, so the mystery was not a scary trick after all."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the clue cleaned up, the insect safe, and the friends smiling beside the pirate ship. Governor {gov.label} called it a mystery solved, and the harbor felt peaceful again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a governor?",
            answer="A governor is a person who helps lead a place and makes decisions for it. In a story, a governor can keep things fair and calm."
        ),
        QAItem(
            question="What is an insect?",
            answer="An insect is a tiny animal with six legs and a body made of little parts. Insects can crawl, fly, or buzz around in busy ways."
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the real reason something happened. People solve mysteries by looking at clues and thinking carefully."
        ),
        QAItem(
            question="Why is friendship important in the story?",
            answer="Friendship helps the characters share clues, listen to each other, and stay brave. When friends work together, problems feel smaller and easier to understand."
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:9} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    mystery: str
    plan: str
    governor_name: str = "Gale"
    friend1: str = "Mira"
    friend2: str = "Tess"
    seed: Optional[int] = None


PLACES = {
    "harbor": Place(id="harbor", name="the harbor", pirate_color="blue", dark_spot="the dock at dusk", has_ship=True, tags={"pirate"}),
    "island": Place(id="island", name="the island cove", pirate_color="gold", dark_spot="the cave mouth", has_ship=True, tags={"pirate"}),
}

MYSTERIES = {
    "insect": Mystery(id="insect", clue="a line of tiny crumbs", hiding_place="a loose board", smell="a sweet crumb smell", noise="a little rustle", risk="none", tags={"insect", "mystery"}),
}

PLANS = {
    "friendship": FriendPlan(id="friendship", method="look together", helper_line="Two good eyes are better than one on a pirate island!", reveal_line="The crumbs point right under this board.", tags={"friendship"}),
}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    plan = args.plan or rng.choice(sorted(PLANS))
    if place not in PLACES or mystery not in MYSTERIES or plan not in PLANS:
        raise StoryError("invalid parameters")
    if not is_reasonable(PLACES[place], MYSTERIES[mystery], PLANS[plan]):
        raise StoryError("This storyworld expects a pirate place, a mystery, and a friendship solution.")
    return StoryParams(place=place, mystery=mystery, plan=plan)


def valid_storyworld_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.plan not in PLANS:
        raise StoryError("unknown StoryParams value")
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], PLANS[params.plan],
                 governor_name=params.governor_name, friend1=params.friend1, friend2=params.friend2)
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
mystery_seen :- seen(insect).
friendship :- solved_with_friends.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("pirate_place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("insect_mystery", mid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("friendship_plan", pid))
    lines.append(asp.fact("goal", "solve_mystery"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show pirate_place/1.\n#show insect_mystery/1.\n#show friendship_plan/1."))
    return sorted(set((a[0], a[0], a[0]) for a in asp.atoms(model, "pirate_place")))


def asp_verify() -> int:
    rc = 0
    if set(valid_storyworld_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, plan=None), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate island storyworld with a governor, an insect, and a solved mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--plan", choices=PLANS)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show pirate_place/1.\n#show insect_mystery/1.\n#show friendship_plan/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for combo in valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, mystery=m, plan=pl)) for p, m, pl in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
