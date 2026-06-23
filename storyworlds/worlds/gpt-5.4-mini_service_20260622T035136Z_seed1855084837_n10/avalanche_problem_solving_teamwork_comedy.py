#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035136Z_seed1855084837_n10/avalanche_problem_solving_teamwork_comedy.py
==============================================================================================================

A small storyworld about a comic avalanche rescue with problem solving and teamwork.

A short seed tale behind the world:
---
A group of friends goes sledding near a mountain village. One friend knocks over a sign
and accidentally loosens a snowy slope. An avalanche starts, blocking the path back to town.
The friends and a nearby guide work together: they use ropes, shovels, and a sled to dig
a safe path and rescue a stuck kitten from a crate. They laugh in relief when the path is open.
---

The world model tracks a few physical meters and emotional memes:
- snow depth, blockage, trapped, free, rescue progress
- worry, confidence, laughter, teamwork, relief

The story is deliberately small and state-driven. A reasonableness gate only allows
situations where a real problem exists and the chosen team actually has a plausible way
to solve it.
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

def _add_repo_root_to_path() -> None:
    here = os.path.abspath(__file__)
    current = os.path.dirname(here)
    while True:
        candidate = os.path.join(current, "results.py")
        if os.path.exists(candidate):
            if current not in sys.path:
                sys.path.insert(0, current)
            return
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

_add_repo_root_to_path()
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
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    place: str
    slope: str
    village: str
    rescue_spot: str
    afford_avalanche: bool = True


@dataclass
class ToolKit:
    id: str
    label: str
    phrase: str
    use: str
    helps_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    danger: str
    blocker: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    problem: str
    toolkit: str
    hero: str
    sidekick: str
    guide: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


SCENES = {
    "mountain": Scene(place="the mountain path", slope="a snowy slope", village="the village", rescue_spot="the trail below"),
    "ridge": Scene(place="the high ridge", slope="a steep drift", village="the town", rescue_spot="the narrow path"),
    "valley": Scene(place="the valley hill", slope="a packed snowbank", village="the cabins", rescue_spot="the lower road"),
}

PROBLEMS = {
    "sled_track": Problem(id="sled_track", label="the sled track", phrase="a sled track blocked by snow", danger="avalanche", blocker="snow"),
    "cabin_door": Problem(id="cabin_door", label="the cabin door", phrase="a cabin door buried in snow", danger="avalanche", blocker="snow"),
    "bridge_path": Problem(id="bridge_path", label="the bridge path", phrase="a bridge path buried under a white heap", danger="avalanche", blocker="snow"),
}

TOOLS = {
    "shovel": ToolKit(id="shovel", label="shovels", phrase="two bright shovels", use="dig",
                      helps_with={"snow"}, tags={"shovel", "snow"}, plural=True),
    "rope": ToolKit(id="rope", label="rope", phrase="a long rope", use="pull",
                    helps_with={"snow", "trapped"}, tags={"rope", "teamwork"}),
    "sled": ToolKit(id="sled", label="sled", phrase="a wooden sled", use="carry",
                    helps_with={"trapped"}, tags={"sled", "teamwork"}),
    "bucket": ToolKit(id="bucket", label="bucket", phrase="a bucket", use="scoop",
                      helps_with={"snow"}, tags={"bucket"}),
}

NAMES = ["Mia", "Leo", "Ava", "Noah", "Zoe", "Ben", "Lily", "Finn"]
GUIDES = ["Rita", "Omar", "Tess", "Ivy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        if not scene.afford_avalanche:
            continue
        for problem_id, problem in PROBLEMS.items():
            for toolkit_id, toolkit in TOOLS.items():
                if "snow" in toolkit.helps_with and problem.danger == "avalanche":
                    combos.append((scene_id, problem_id, toolkit_id))
                if "trapped" in toolkit.helps_with and problem.danger == "avalanche":
                    combos.append((scene_id, problem_id, toolkit_id))
    # Deduplicate while preserving deterministic sort.
    combos = sorted(set(combos))
    return combos


def reasonableness(scene: Scene, problem: Problem, toolkit: ToolKit) -> bool:
    if problem.danger != "avalanche":
        return False
    if not scene.afford_avalanche:
        return False
    return bool(problem.blocker == "snow" and (("snow" in toolkit.helps_with) or ("trapped" in toolkit.helps_with)))


def explain_rejection(problem: Problem, toolkit: ToolKit) -> str:
    return f"(No story: {toolkit.label} would not plausibly solve {problem.phrase} after an avalanche.)"


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("avalanche_started") and ("settle", "avalanche") not in world.fired:
        world.fired.add(("settle", "avalanche"))
        world.get("blockage").meters["snow"] += 2
        for e in world.characters():
            e.memes["worry"] += 1
        out.append("The avalanche left the path packed tight.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork_called") and ("teamwork",) not in world.fired:
        world.fired.add(("teamwork",))
        for e in world.characters():
            e.memes["teamwork"] += 1
            e.memes["confidence"] += 1
        world.get("progress").meters["clear"] += 1
        out.append("Everyone started helping in the same direction.")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("kitten").meters["trapped"] >= THRESHOLD and world.get("progress").meters["clear"] >= THRESHOLD:
        if ("rescue",) not in world.fired:
            world.fired.add(("rescue",))
            world.get("kitten").meters["trapped"] = 0
            world.get("kitten").meters["free"] = 1
            world.get("kitten").memes["relief"] += 1
            out.append("The kitten popped free with a tiny sneeze.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_settle, _r_teamwork, _r_rescue):
            lines = fn(world)
            if lines:
                changed = True
                all_lines.extend(lines)
    if narrate:
        for line in all_lines:
            world.say(line)
    return all_lines


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    sim.facts["avalanche_started"] = True
    propagate(sim, narrate=False)
    return {
        "blocked": sim.get("blockage").meters["snow"] >= THRESHOLD,
        "kitten_free": sim.get("kitten").meters["free"] >= THRESHOLD,
    }


def setup(world: World, hero: Entity, sidekick: Entity, guide: Entity, problem: Problem, toolkit: ToolKit) -> None:
    world.say(f"{hero.id} and {sidekick.id} were having a very serious day of fun at {world.scene.place}.")
    world.say(f"They had {toolkit.phrase} and a plan to fix {problem.phrase}, because the word avalanche had already done its dramatic little entrance.")
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    guide.memes["calm"] += 1


def avalanche_beats(world: World, problem: Problem) -> None:
    world.facts["avalanche_started"] = True
    world.say(f"Then came the avalanche, which rolled down like a giant sleepy pillow with terrible manners.")
    world.say(f"It stuffed {problem.label} with snow and made the mountain path vanish.")


def problem_solving(world: World, hero: Entity, sidekick: Entity, guide: Entity, toolkit: ToolKit) -> None:
    world.facts["teamwork_called"] = True
    world.say(f"{guide.id} pointed at the snow and said, 'One of us shovels, one of us pulls, and one of us keeps the plan from slipping away.'")
    world.say(f"{hero.id} grabbed {toolkit.phrase}, {sidekick.id} moved the sled, and {guide.id} tied the rope where it could do the most good.")


def comic_turn(world: World, kitten: Entity) -> None:
    world.say(f"Under a drift, a kitten sneezed so hard that it looked offended by the entire weather system.")
    kitten.memes["annoyance"] += 1


def resolution(world: World, hero: Entity, sidekick: Entity, guide: Entity, problem: Problem, toolkit: ToolKit) -> None:
    world.say(f"They kept going anyway, laughing at their own serious faces as the shovels went scrape-scrape and the rope said whoosh.")
    propagate(world, narrate=True)
    world.say(f"At last, {problem.label} was clear, the kitten was free, and the whole team was covered in snow in the most ridiculous way possible.")
    world.say(f"{guide.id} smiled and said the rescue was a masterpiece of teamwork, with bonus comedy from everyone's eyebrows.")


def tell(scene: Scene, problem: Problem, toolkit: ToolKit, hero_name: str, sidekick_name: str, guide_name: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="girl", label=sidekick_name))
    guide = world.add(Entity(id=guide_name, kind="character", type="woman", label=guide_name))
    blockage = world.add(Entity(id="blockage", type="thing", label=problem.label))
    progress = world.add(Entity(id="progress", type="thing", label="progress"))
    kitten = world.add(Entity(id="kitten", type="thing", label="kitten"))
    kitten.meters["trapped"] = 1
    world.facts["problem"] = problem
    world.facts["toolkit"] = toolkit

    setup(world, hero, sidekick, guide, problem, toolkit)
    world.para()
    avalanche_beats(world, problem)
    world.para()
    problem_solving(world, hero, sidekick, guide, toolkit)
    comic_turn(world, kitten)
    resolution(world, hero, sidekick, guide, problem, toolkit)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem: Problem = f["problem"]
    toolkit: ToolKit = f["toolkit"]
    return [
        f'Write a funny story for a young child that includes the word "avalanche" and shows friends solving {problem.phrase} together.',
        f"Tell a comedic rescue story where a team uses {toolkit.phrase} to handle an avalanche problem with teamwork.",
        f"Write a short funny mountain story with an avalanche, a tricky problem, and a team that works together to fix it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    problem: Problem = f["problem"]
    toolkit: ToolKit = f["toolkit"]
    kitten = world.get("kitten")
    hero, sidekick = [e for e in world.characters() if e.id in {world.characters()[0].id, world.characters()[1].id}]
    guide = [e for e in world.characters() if e.id not in {hero.id, sidekick.id}][0]
    qa = [
        QAItem(
            question=f"What problem did the avalanche cause for {problem.label}?",
            answer=f"The avalanche buried {problem.label} under a lot of snow. It made the path hard to use until the team cleared it.",
        ),
        QAItem(
            question=f"How did {hero.id}, {sidekick.id}, and {guide.id} work together?",
            answer=f"They split the job into pieces: one used {toolkit.phrase}, one helped pull, and one kept the plan steady. That teamwork moved the snow and made progress possible.",
        ),
        QAItem(
            question="Why was the rescue funny as well as serious?",
            answer="The rescue was serious because the snow blocked the path. It was funny because the kitten sneezed dramatically and everyone ended up covered in snow like messy snowmen.",
        ),
    ]
    if kitten.meters["free"] >= THRESHOLD:
        qa.append(QAItem(
            question="What changed for the kitten by the end?",
            answer="The kitten was trapped at first, but the team cleared enough snow to free it. By the end it was safe and no longer stuck.",
        ))
    qa.append(QAItem(
        question=f"Why did the team need {toolkit.phrase}?",
        answer=f"They needed {toolkit.phrase} because the avalanche left snow in the way. The tool helped them solve the problem instead of just staring at it.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer="An avalanche is a fast rush of snow sliding down a mountain. It can bury paths, rocks, and anything in its way.",
        ),
        QAItem(
            question="Why is teamwork helpful during a rescue?",
            answer="Teamwork helps because different helpers can do different jobs at once. That makes hard problems easier and faster to solve.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means figuring out what is wrong and choosing a way to fix it. It often works best when people stay calm and keep trying together.",
        ),
    ]


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
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
avalanche_started -> blocked.
teamwork_called -> teamwork.
kitten_trapped, teamwork -> kitten_free.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("danger", pid, p.danger))
        lines.append(asp.fact("blocker", pid, p.blocker))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    # Simple parity on validity only; also smoke-test generation.
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        print("MISMATCH between ASP and Python combo gates.")
        if cl - py:
            print("only in ASP:", sorted(cl - py))
        if py - cl:
            print("only in Python:", sorted(py - cl))
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as err:
        print(f"Generation smoke test failed: {err}")
        rc = 1
    if rc == 0:
        print(f"OK: ASP parity and generation smoke test passed ({len(py)} combos).")
    return rc


def valid_combo_to_params(combo: tuple[str, str, str], rng: random.Random) -> StoryParams:
    scene, problem, toolkit = combo
    hero = rng.choice(NAMES)
    sidekick = rng.choice([n for n in NAMES if n != hero])
    guide = rng.choice(GUIDES)
    return StoryParams(scene=scene, problem=problem, toolkit=toolkit, hero=hero, sidekick=sidekick, guide=guide)


CURATED = [
    StoryParams(scene="mountain", problem="sled_track", toolkit="shovel", hero="Mia", sidekick="Leo", guide="Rita"),
    StoryParams(scene="ridge", problem="cabin_door", toolkit="rope", hero="Ava", sidekick="Ben", guide="Omar"),
    StoryParams(scene="valley", problem="bridge_path", toolkit="sled", hero="Zoe", sidekick="Finn", guide="Tess"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy avalanche teamwork storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--toolkit", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--guide")
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (args.scene is None or c[0] == args.scene) and (args.problem is None or c[1] == args.problem) and (args.toolkit is None or c[2] == args.toolkit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    combo = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != hero])
    guide = args.guide or rng.choice(GUIDES)
    return StoryParams(scene=combo[0], problem=combo[1], toolkit=combo[2], hero=hero, sidekick=sidekick, guide=guide)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.problem not in PROBLEMS or params.toolkit not in TOOLS:
        raise StoryError("Invalid parameters.")
    scene = SCENES[params.scene]
    problem = PROBLEMS[params.problem]
    toolkit = TOOLS[params.toolkit]
    if not reasonableness(scene, problem, toolkit):
        raise StoryError(explain_rejection(problem, toolkit))
    world = tell(scene, problem, toolkit, params.hero, params.sidekick, params.guide)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos:")
        for c in asp_valid_combos():
            print(" ", c)
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
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
