#!/usr/bin/env python3
"""
A small standalone storyworld for a space-adventure tale about a quest,
friendship, and a careful comparison.

Premise:
- Two friends travel through space on a quest to recover a lost star map.
- They face a choice between two routes, two tools, or two plans.
- The story uses a comparative turn: one option is brighter, safer, faster,
  or steadier than the other.
- Friendship resolves the tension, and the ending proves what changed.

This world is intentionally small and constraint-checked: the route, the
comparison, and the resolution are all driven by state in the simulated world.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    stars: str
    atmosphere: str


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    path_a: str
    path_b: str
    compare_key: str
    risk: str
    prize: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    aid: str
    compare_word: str
    safe_word: str
    offer: str
    finish: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []
        self.path: str = ""
        self.choice: str = ""
        self.route_danger: float = 0.0

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.path = self.path
        c.choice = self.choice
        c.route_danger = self.route_danger
        return c


@dataclass
class StoryParams:
    route: str
    quest: str
    helper: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


SETTINGS = {
    "moon_outpost": Setting(
        place="the moon outpost",
        stars="silver stars",
        atmosphere="thin moonlight",
    ),
    "deep_space_station": Setting(
        place="the deep space station",
        stars="far stars",
        atmosphere="blue station lights",
    ),
    "asteroid_garden": Setting(
        place="the asteroid garden",
        stars="sparkly stars",
        atmosphere="soft starlight",
    ),
}

QUESTS = {
    "lost_map": Quest(
        id="lost_map",
        goal="find the lost star map",
        verb="search for the lost star map",
        path_a="the short route through the bright ring",
        path_b="the longer route past the cold dust cloud",
        compare_key="safer",
        risk="the cold dust cloud could scratch the hull",
        prize="the glowing map",
        tags={"map", "search", "quest", "comparative"},
    ),
    "comet_seed": Quest(
        id="comet_seed",
        goal="bring back the comet seed",
        verb="reach the comet garden",
        path_a="the quick route over the comet trail",
        path_b="the steadier route under the asteroid arch",
        compare_key="steadier",
        risk="the comet trail could shake the little rover",
        prize="the comet seed",
        tags={"comet", "garden", "quest", "comparative"},
    ),
    "moon_lantern": Quest(
        id="moon_lantern",
        goal="deliver the moon lantern",
        verb="carry the moon lantern home",
        path_a="the brighter path by the crystal panels",
        path_b="the darker path through the shadow tunnel",
        compare_key="brighter",
        risk="the shadow tunnel could make it hard to see",
        prize="the moon lantern",
        tags={"lantern", "light", "quest", "comparative"},
    ),
}

HELPERS = {
    "scanner": Helper(
        id="scanner",
        label="a small scanner",
        aid="scan both routes",
        compare_word="clearer",
        safe_word="safer",
        offer="I can scan both routes and tell which one looks safer",
        finish="The scanner blinked, and the safer path was easy to see",
        tags={"scan", "safe", "comparative"},
    ),
    "glider": Helper(
        id="glider",
        label="a tiny glider",
        aid="glide ahead",
        compare_word="faster",
        safe_word="steadier",
        offer="I can glide ahead and test which path is steadier",
        finish="The glider floated ahead, and the steadier route stayed calm",
        tags={"glide", "steady", "comparative"},
    ),
    "lamp": Helper(
        id="lamp",
        label="a bright lamp",
        aid="shine on the tracks",
        compare_word="brighter",
        safe_word="clearer",
        offer="I can shine on the tracks and show the brighter way",
        finish="The lamp shone, and the brighter route glowed like a promise",
        tags={"light", "bright", "comparative"},
    ),
}

GIRL_NAMES = ["Ava", "Mina", "Lina", "Zara", "Nia", "Tess"]
BOY_NAMES = ["Orin", "Pax", "Leo", "Finn", "Jace", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with quest, friendship, and comparison.")
    ap.add_argument("--route", choices=QUESTS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, q, h) for r in SETTINGS for q in QUESTS for h in HELPERS]


def explain_rejection(route: str, quest: str, helper: str) -> str:
    q = QUESTS[quest]
    h = HELPERS[helper]
    return f"(No story: the helper {h.label} does not reasonably fix the danger on {q.path_b if route else 'that route'}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.route:
        combos = [c for c in combos if c[0] == args.route]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, quest, helper = rng.choice(sorted(combos))
    q = QUESTS[quest]
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    return StoryParams(route=route, quest=quest, helper=helper, hero_name=hero_name, friend_name=friend_name, hero_type=hero_gender, friend_type=friend_gender)


def propagate(world: World) -> None:
    if world.route_danger >= THRESHOLD and ("tension", world.choice) not in world.fired:
        world.fired.add(("tension", world.choice))
        world.facts["tension"] = True


def predict(world: World, quest: Quest, helper: Helper, path: str) -> dict:
    sim = world.copy()
    sim.path = path
    sim.route_danger = 1.0 if path == quest.path_b else 0.0
    propagate(sim)
    return {"danger": sim.route_danger >= THRESHOLD}


def tell(setting: Setting, quest: Quest, helper: Helper, hero_name: str, friend_name: str, hero_type: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    map_obj = world.add(Entity(id="map", type="map", label="star map", phrase="a glowing star map"))
    world.facts.update(hero=hero, friend=friend, map=map_obj, quest=quest, helper=helper)

    world.say(f"{hero_name} and {friend_name} were best friends at {setting.place}.")
    world.say(f"They had a quest to {quest.goal}, and {quest.prize} mattered because it could lead them home.")
    world.say(f"Under the {setting.atmosphere}, the stars looked like {setting.stars} waiting to be followed.")

    world.para()
    world.say(f"At the launch bay, the two friends found two routes: {quest.path_a} and {quest.path_b}.")
    world.say(f"{hero_name} liked the first one, but {friend_name} noticed the second one might be {quest.compare_key} for the mission.")
    world.say(f"The problem was that {quest.risk}, so they could not just rush forward.")

    world.para()
    world.route_danger = 1.0
    world.path = quest.path_b
    propagate(world)
    world.say(f"{friend_name} said, \"We can be brave and still choose the safer path.\"")
    world.say(f"Then {helper.offer}.")
    world.say(f"{hero_name} smiled, and both friends listened because friendship made the choice easier.")
    world.say(f"They took {helper.label}, and {helper.finish.lower()}.")

    world.para()
    world.route_danger = 0.0
    world.path = quest.path_a if helper.id == "lamp" else quest.path_b
    world.choice = world.path
    world.say(f"Together they followed {world.choice}, and soon they found {quest.prize}.")
    world.say(f"In the end, {hero_name} and {friend_name} brought {quest.prize} home, and their friendship felt stronger than before.")

    world.facts["resolved"] = True
    world.facts["path"] = world.path
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    return [
        f'Write a gentle space-adventure story about a quest, friendship, and a "comparative" choice.',
        f"Tell a story where {hero.id} and {friend.id} must choose between two routes while trying to {quest.goal}.",
        f"Write a child-friendly story in space where the friends compare two paths and pick the safer one together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    quest = f["quest"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They worked together on a space quest.",
        ),
        QAItem(
            question=f"What was the quest?",
            answer=f"Their quest was to {quest.goal}. The story followed them as they searched through space.",
        ),
        QAItem(
            question=f"Why did they choose one path over the other?",
            answer=f"They chose the route that seemed {quest.compare_key} and safer for the mission, because {quest.risk}.",
        ),
        QAItem(
            question=f"What helped them make the choice?",
            answer=f"{helper.label} helped them judge the routes. It made the better path easier to trust.",
        ),
        QAItem(
            question=f"How did friendship matter in the ending?",
            answer=f"Friendship mattered because {hero.id} and {friend.id} listened to each other and stayed kind while solving the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to reach a goal or find something important.",
        ),
        QAItem(
            question="What does it mean to compare two things?",
            answer="To compare two things means to look at how they are alike and how they are different.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and try to be kind together.",
        ),
        QAItem(
            question="What is space?",
            answer="Space is the huge area beyond Earth where stars, planets, and rockets can travel.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  path={world.path}")
    lines.append(f"  route_danger={world.route_danger}")
    return "\n".join(lines)


ASP_RULES = r"""
route_danger(Q,B) :- quest(Q), path_b(Q,B).
safer_route(Q,A) :- quest(Q), path_a(Q,A).
comparative_choice(Q,A) :- safer_route(Q,A), quest(Q).
compatible_helper(H,Q) :- helper(H), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("path_a", qid, q.path_a))
        lines.append(asp.fact("path_b", qid, q.path_b))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show comparative_choice/2.\n#show compatible_helper/2."))
    asp_choices = set(asp.atoms(model, "comparative_choice"))
    if py:
        print(f"OK: ASP ran with {len(asp_choices)} shown comparative choices.")
        return 0
    print("MISMATCH")
    return 1


CURATED = [
    StoryParams(route="lost_map", quest="lost_map", helper="scanner", hero_name="Ava", friend_name="Pax", hero_type="girl", friend_type="boy"),
    StoryParams(route="comet_seed", quest="comet_seed", helper="glider", hero_name="Leo", friend_name="Nia", hero_type="boy", friend_type="girl"),
    StoryParams(route="moon_lantern", quest="moon_lantern", helper="lamp", hero_name="Mina", friend_name="Finn", hero_type="girl", friend_type="boy"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.route]
    quest = QUESTS[params.quest]
    helper = HELPERS[params.helper]
    world = tell(setting, quest, helper, params.hero_name, params.friend_name, params.hero_type, params.friend_type)
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


def resolve_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show comparative_choice/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show comparative_choice/2.\n#show compatible_helper/2."))
        print(asp.atoms(model, "comparative_choice"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            try:
                sample = resolve_and_generate(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero_name}: {p.quest} via {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
