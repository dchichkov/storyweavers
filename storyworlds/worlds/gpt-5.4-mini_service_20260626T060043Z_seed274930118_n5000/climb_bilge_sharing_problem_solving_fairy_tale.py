#!/usr/bin/env python3
"""
A small fairy-tale storyworld about climbing into a ship's bilge, sharing a
single useful thing, and solving a problem together.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "page"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Chamber:
    place: str = "the harbor"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(it.region == region for it in self.worn_items(actor) if it.kind == "gear")

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

        w = World(self.chamber)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("wet", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.kind != "prize":
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{item.label.capitalize()} got wet and dirty.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("worry", 0.0) < THRESHOLD or actor.memes.get("alone", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trouble"] = actor.memes.get("trouble", 0.0) + 1
        return ["__conflict__"]
    return []


RULES = [
    _r_soak,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_tool(problem: Problem, tool: Tool) -> bool:
    return problem.mess in tool.guards and "torso" in tool.covers


def problem_at_risk(problem: Problem, prize: Entity) -> bool:
    return prize.region in problem.zone


def predict(world: World, hero: Entity, problem: Problem, prize_id: str) -> dict:
    sim = world.copy()
    do_problem(sim, sim.get(hero.id), problem, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    if problem.id not in world.chamber.affords:
        return
    world.zone = set(problem.zone)
    actor.meters["wet"] = actor.meters.get("wet", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved old songs, bright lanterns, and tall climbs.")


def loves_problem(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved to {problem.verb}, for every riddle felt like a door waiting to open.")


def present_prize(world: World, owner: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One evening, {owner.label} gave {hero.id} {hero.pronoun('object')} {prize.phrase} to keep safe.")


def cling_to_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} cherished {hero.pronoun('possessive')} {prize.label} and held {prize.it()} close.")


def arrive(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"One dusk, {hero.id} and {friend.id} went to {world.chamber.place}, where a little boat rocked softly.")
    world.say("Below the deck, the bilge hid in the dark like a secret mouth under the floorboards.")


def want_to_climb(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {problem.verb}, but the way down was narrow and the bilge smelled damp and cold.")


def warn(world: World, friend: Entity, hero: Entity, problem: Problem, prize: Entity) -> bool:
    pred = predict(world, hero, problem, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = problem.soil
    world.say(f'"If you {problem.verb}, your {prize.label} will get {problem.soil}," {friend.id} said. "We should think together."')
    return True


def worry(world: World, hero: Entity) -> None:
    hero.memes["alone"] = hero.memes.get("alone", 0.0) + 1
    world.say(f"{hero.id} frowned and tried to go on alone, but the bilge was too dark and slippery for that.")


def share_light(world: World, friend: Entity, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"Then {friend.id} shared a single lantern with {hero.id}, and its warm glow made the bilge look less grim.")
    world.say(f'"Let us solve this together," {friend.id} said. "We can share the work and keep your {hero.pronoun("possessive")} prize safe."')


def compromise(world: World, friend: Entity, hero: Entity, problem: Problem, prize: Entity) -> Optional[Tool]:
    for proto in TOOLS:
        if select_tool(problem, proto):
            tool = world.add(Entity(
                id=proto.id,
                kind="gear",
                type="gear",
                label=proto.label,
                phrase=proto.phrase,
                owner=hero.id,
                caretaker=friend.id,
                region="torso",
                plural=proto.plural,
            ))
            tool.worn_by = hero.id
            if predict(world, hero, problem, prize.id)["soiled"]:
                tool.worn_by = None
                del world.entities[tool.id]
                return None
            world.say(f"{friend.id} smiled and said, \"How about we {proto.prep} and {problem.verb} together?\"")
            return tool
    return None


def accept(world: World, hero: Entity, friend: Entity, problem: Problem, prize: Entity, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["alone"] = 0.0
    hero.memes["worry"] = 0.0
    world.say(f"{hero.id} nodded, and the two of them went down with the lantern and the {tool.label}.")
    world.say(
        f"With the light shared and the {tool.label} in place, {hero.id} could {problem.gerund}, "
        f"{prize.label} stayed clean, and the bilge felt less like a trap and more like a place where kindness worked."
    )


def tell(chamber: Chamber, problem: Problem, prize_cfg: dict, hero_name: str = "Nora", hero_type: str = "girl") -> World:
    world = World(chamber)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id="Milo", kind="character", type="boy", label="Milo"))
    owner = world.add(Entity(id="Lady", kind="character", type="queen", label="the lady of the harbor"))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg["type"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg["region"],
        plural=prize_cfg.get("plural", False),
    ))
    intro(world, hero)
    loves_problem(world, hero, problem)
    present_prize(world, owner, hero, prize)
    cling_to_prize(world, hero, prize)
    world.para()
    arrive(world, hero, friend)
    want_to_climb(world, hero, problem)
    warn(world, friend, hero, problem, prize)
    worry(world, hero)
    share_light(world, friend, hero)
    world.para()
    tool = compromise(world, friend, hero, problem, prize)
    if tool is not None:
        accept(world, hero, friend, problem, prize, tool)
    world.facts.update(hero=hero, friend=friend, owner=owner, prize=prize, problem=problem, tool=tool, chamber=chamber)
    return world


SETTINGS = {
    "harbor": Chamber(place="the harbor", affords={"climb", "bilge"}),
    "old_dock": Chamber(place="the old dock", affords={"climb", "bilge"}),
    "moon_wharf": Chamber(place="the moonlit wharf", affords={"climb", "bilge"}),
}

PROBLEMS = {
    "climb": Problem(
        id="climb",
        verb="climb down into the bilge",
        gerund="climbing down into the bilge",
        rush="scramble down the ladder",
        mess="wet",
        soil="wet and muddy",
        zone={"feet", "legs", "torso"},
        keyword="climb",
        tags={"climb"},
    ),
    "bilge": Problem(
        id="bilge",
        verb="clean out the bilge",
        gerund="cleaning out the bilge",
        rush="run for a broom and bucket",
        mess="dirty",
        soil="muddy and smelly",
        zone={"feet", "legs", "torso"},
        keyword="bilge",
        tags={"bilge"},
    ),
}

TOOLS = [
    Tool(
        id="cloak",
        label="a shared cloak",
        phrase="a warm shared cloak",
        guards={"wet", "dirty"},
        covers={"torso"},
        prep="put on the shared cloak before going down",
        tail="went down wrapped in the shared cloak",
    ),
    Tool(
        id="apron",
        label="an old apron",
        phrase="an old apron with big pockets",
        guards={"dirty"},
        covers={"torso"},
        prep="tie on the old apron first",
        tail="went down with the old apron tied on",
    ),
    Tool(
        id="boots",
        label="rubber boots",
        phrase="rubber boots that kept water off",
        guards={"wet"},
        covers={"feet"},
        prep="wear the rubber boots first",
        tail="went down in the rubber boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Nora", "Elsa", "Mira", "Rose", "Ava", "Luna"]
BOY_NAMES = ["Milo", "Owen", "Toby", "Finn", "Ivo", "Jasper"]
TRAITS = ["brave", "curious", "gentle", "cheerful", "stubborn"]


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, chamber in SETTINGS.items():
        for pid in chamber.affords:
            for prize_id in PRIZES:
                p = PRIZES[prize_id]
                if problem_at_risk(PROBLEMS[pid], p) and any(select_tool(PROBLEMS[pid], t) for t in TOOLS):
                    combos.append((place, pid, prize_id))
    return combos


PRIZES = {
    "crown": {"label": "crown", "phrase": "a little golden crown", "type": "crown", "region": "torso"},
    "shawl": {"label": "shawl", "phrase": "a blue velvet shawl", "type": "shawl", "region": "torso"},
    "slippers": {"label": "slippers", "phrase": "soft slippers", "type": "slippers", "region": "feet", "plural": True},
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, problem, prize = f["hero"], f["problem"], f["prize"]
    return [
        f'Write a fairy tale about a child named {hero.id} who must {problem.verb} near a bilge and learns to share.',
        f"Tell a gentle story where {hero.id} wants to {problem.verb} while keeping {prize.label} safe.",
        f'Write a child-friendly fairy tale that uses the words "climb" and "bilge" and ends with a problem solved together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, problem = f["hero"], f["friend"], f["prize"], f["problem"]
    qa = [
        QAItem(
            question=f"Who wanted to {problem.verb} in the story?",
            answer=f"{hero.id} wanted to {problem.verb}, because the mystery of the bilge felt exciting to {hero.pronoun('subject')}."
        ),
        QAItem(
            question=f"What did {friend.id} share to help {hero.id}?",
            answer=f"{friend.id} shared a lantern and a plan, so they could work together in the dark bilge."
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer=f"The {prize.label} stayed clean because {hero.id} and {friend.id} solved the problem together before going all the way down."
        ),
    ]
    if f.get("tool"):
        qa.append(QAItem(
            question=f"How did the shared tool help {hero.id}?",
            answer=f"They used {f['tool'].label} so {hero.id} could {problem.verb} without ruining the {prize.label}."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a bilge?",
            answer="A bilge is the lowest part inside a boat, where water can collect and make the floor damp."
        ),
        QAItem(
            question="Why do people use a lantern in dark places?",
            answer="A lantern gives light so people can see where they are going and avoid bumps or slips."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy something too, so two people can help each other."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble and choosing a smart way to fix it."
        ),
    ]
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", problem="climb", prize="crown", name="Nora", gender="girl", trait="curious"),
    StoryParams(place="old_dock", problem="bilge", prize="shawl", name="Milo", gender="boy", trait="brave"),
]


ASP_RULES = r"""
prize_at_risk(P, R) :- prize(P), worn_on(P, R), zone(Z), in_zone(R, Z).
has_fix(Prob, P) :- problem(Prob), prize(P), prize_at_risk(P, R),
                    tool(T), guards(T, M), problem_mess(Prob, M), covers(T, R).
valid_story(Place, Prob, P) :- affords(Place, Prob), prize(P), has_fix(Prob, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, chamber in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for prob in sorted(chamber.affords):
            lines.append(asp.fact("affords", place, prob))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_mess", pid, prob.mess))
        for z in sorted(prob.zone):
            lines.append(asp.fact("zone", pid, z))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr["region"]))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place, prob, prize in valid_combos():
        if args.place and place != args.place:
            continue
        if args.problem and prob != args.problem:
            continue
        if args.prize and prize != args.prize:
            continue
        combos.append((place, prob, prize))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prob, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, problem=prob, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], PROBLEMS[params.problem], PRIZES[params.prize], params.name, params.gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: climb, bilge, sharing, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    if args.verify:
        import asp
        py = set(valid_combos())
        model = asp.one_model(asp_program("#show valid_story/3."))
        asp_set = set(asp.atoms(model, "valid_story"))
        print("OK" if py == asp_set else "MISMATCH")
        sys.exit(0 if py == asp_set else 1)

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
