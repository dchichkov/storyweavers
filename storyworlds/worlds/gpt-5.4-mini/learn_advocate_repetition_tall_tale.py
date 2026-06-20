#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/learn_advocate_repetition_tall_tale.py
======================================================================

A standalone storyworld for a tiny Tall Tale domain: a child learns a pattern,
then advocates for a repeated solution when the situation grows strange.

Premise
-------
A small, stubborn problem keeps coming back: a crop needs watering, a fence keeps
tilting, a bell keeps getting stuck, or a lantern keeps flickering. A child
notices the pattern, learns from it, and advocates for a repeated, practical
ritual. The tall-tale flavor comes from exaggerated scale, repeated beats, and a
friendly, mythic ending image.

This file follows the Storyweavers contract:
- self-contained stdlib script
- typed entities with meters and memes
- simulated world drives prose
- Python reasonableness gate and inline ASP twin
- generation prompts, story QA, world-knowledge QA
- support for --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
PATTERN_MIN = 2
MIN_HELP = 1


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

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    sky: str
    feat: str
    height_phrase: str
    ends_phrase: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    noun: str
    phrase: str
    trouble: str
    repeats: str
    handle: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class AdvocateTool:
    id: str
    name: str
    phrase: str
    ritual: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_pattern(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["tries"] < PATTERN_MIN:
            continue
        sig = ("pattern", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["knows_pattern"] += 1
        out.append("__pattern__")
    return out


def _r_hope(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["hope"] < THRESHOLD:
            continue
        sig = ("hope", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["steady"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("pattern", "mind", _r_pattern), Rule("hope", "mind", _r_hope)]


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


def repeatable(problem: Problem, tool: AdvocateTool) -> bool:
    return problem.id in {"dry_stream", "tilting_gate", "stuck_bell", "flickering_lantern"} and tool.id in {"bucket_line", "brace_posts", "pull_rope", "lamp_song"}


def sensible_tools() -> list[AdvocateTool]:
    return [t for t in TOOLS.values() if t.id in {"bucket_line", "brace_posts", "pull_rope", "lamp_song"}]


def best_tool() -> AdvocateTool:
    return max(TOOLS.values(), key=lambda t: t.meters.get("sense", 0))


def _do_problem(world: World, problem: Entity, narrate: bool = True) -> None:
    problem.meters["tries"] += 1
    problem.meters["worse"] += 1
    propagate(world, narrate=narrate)


def predict_repeat(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _do_problem(sim, sim.get(problem_id), narrate=False)
    p = sim.get(problem_id)
    return {"still_trouble": p.meters["worse"] >= 1, "tries": p.meters["tries"]}


def intro(world: World, kid: Entity, setting: Setting) -> None:
    kid.memes["curiosity"] += 1
    world.say(
        f"Under a sky big enough to hold a hundred kites, {kid.id} lived by {setting.place}. "
        f"{setting.feat} rose like a long song, and {setting.height_phrase} from the ground."
    )


def problem_start(world: World, kid: Entity, problem: Entity, setting: Setting) -> None:
    world.say(
        f"Each day the {problem.label} came back again and again. {problem.phrase.capitalize()} "
        f"kept {problem.trouble}, and the whole place felt like a tiny giant had poked it."
    )
    world.say(
        f"{kid.id} watched the pattern once, then watched it twice, then watched it a third time."
    )


def learn(world: World, kid: Entity, problem: Entity) -> None:
    kid.meters["tries"] += 1
    kid.meters["learn"] += 1
    world.say(
        f"{kid.id} learned the pattern: when the {problem.noun} acted up, it did not mean to be rude; "
        f"it meant the same trouble was returning."
    )


def advocate(world: World, kid: Entity, helper: Entity, problem: Entity, tool: AdvocateTool) -> None:
    kid.memes["advocate"] += 1
    helper.memes["listening"] += 1
    world.say(
        f'{kid.id} stood up straight and said, "We should {tool.ritual}, and then {tool.fix}." '
        f'{kid.id} said it once, then said it again, so nobody missed the idea.'
    )
    world.say(
        f'{kid.id} told {helper.id}, "This works because the trouble keeps repeating, and a repeated answer beats a repeated trouble."'
    )


def repeat_fix(world: World, helper: Entity, tool: AdvocateTool, problem: Entity) -> None:
    helper.meters["help"] += 1
    problem.meters["quiet"] += 1
    world.say(
        f"{helper.label_word.capitalize()} nodded. Together they {tool.ritual}, then {tool.ritual} again, "
        f"and the answer felt as sturdy as an old barn in a storm."
    )


def finish(world: World, kid: Entity, helper: Entity, problem: Entity, tool: AdvocateTool, setting: Setting) -> None:
    kid.memes["pride"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After that, the {problem.noun} stayed calm, the {tool.name} did its work, and {setting.ends_phrase}."
    )
    world.say(
        f"{kid.id} smiled because {kid.id} had learned something true: when a trouble comes back and back again, "
        f"advocate for the same brave fix until the world listens."
    )


def tell(setting: Setting, problem_cfg: Problem, tool: AdvocateTool, child_name: str, child_gender: str, helper_type: str) -> World:
    world = World(setting)
    kid = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper", role="helper"))
    problem = world.add(Entity(id="problem", type="thing", label=problem_cfg.noun))
    kid.meters["tries"] = 0
    intro(world, kid, setting)
    problem_start(world, kid, problem, setting)
    world.para()
    learn(world, kid, problem)
    advocate(world, kid, helper, problem, tool)
    world.para()
    repeat_fix(world, helper, tool, problem)
    _do_problem(world, problem, narrate=False)
    finish(world, kid, helper, problem, tool, setting)
    world.facts.update(kid=kid, helper=helper, problem_cfg=problem_cfg, problem=problem, tool=tool, setting=setting)
    return world


SETTINGS = {
    "riverbank": Setting("riverbank", "the riverbank", "The wind ran over the water", "A willow tree leaned like a listener", "the reeds stood tall", "the river kept flowing"),
    "hill": Setting("hill", "the hill", "The clouds rolled like wool", "A lookout stone rose like a chimney", "the grass waved high", "the meadow glittered below"),
    "harbor": Setting("harbor", "the harbor", "The gulls called as if they knew secrets", "The mast of a docked ship pointed to the moon", "the ropes hung tall", "the boats bobbed like thoughts"),
}

PROBLEMS = {
    "dry_stream": Problem("dry_stream", "stream", "The little stream", "running thin and dry", "drying up by noon", "carry water back and forth", tags={"water", "repetition"}),
    "tilting_gate": Problem("tilting_gate", "gate", "The gate", "tilting and squeaking", "falling to one side", "push the brace into place", tags={"wood", "repetition"}),
    "stuck_bell": Problem("stuck_bell", "bell", "The bell", "sticking and staying silent", "hiding its song", "pull the rope just right", tags={"metal", "repetition"}),
    "flickering_lantern": Problem("flickering_lantern", "lantern", "The lantern", "flickering and coughing out light", "going dim again and again", "sing the steadying tune", tags={"light", "repetition"}),
}

TOOLS = {
    "bucket_line": AdvocateTool("bucket_line", "bucket line", "a line of buckets", "carry bucket after bucket", "keep the stream fed", tags={"water", "repetition"}),
    "brace_posts": AdvocateTool("brace_posts", "brace posts", "two stout brace posts", "set the posts and set them again", "keep the gate from tilting", tags={"wood", "repetition"}),
    "pull_rope": AdvocateTool("pull_rope", "pulling rope", "a long pulling rope", "pull once, then pull again", "loosen the bell’s snag", tags={"metal", "repetition"}),
    "lamp_song": AdvocateTool("lamp_song", "lamp song", "a soft lamp song", "hum the same tune twice", "steady the lantern flame", tags={"light", "repetition"}),
}

NAMES_GIRL = ["Mira", "Nell", "Ada", "June", "Ivy", "Bea", "Luna"]
NAMES_BOY = ["Rufus", "Hank", "Otto", "Jasper", "Levi", "Milo", "Beck"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]



@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    child: str
    child_gender: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("riverbank", "dry_stream", "bucket_line", "Mira", "girl", "mother"),
    ("hill", "tilting_gate", "brace_posts", "Rufus", "boy", "father"),
    ("harbor", "stuck_bell", "pull_rope", "Ada", "girl", "grandmother"),
    ("riverbank", "flickering_lantern", "lamp_song", "Levi", "boy", "grandfather"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for t in TOOLS:
                if repeatable(PROBLEMS[p], TOOLS[t]):
                    combos.append((s, p, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale world about learning, advocating, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def explain_rejection(problem: Problem, tool: AdvocateTool) -> str:
    return f"(No story: {tool.name} does not honestly solve the repeating trouble of the {problem.noun}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool and not repeatable(PROBLEMS[args.problem], TOOLS[args.tool]):
        raise StoryError(explain_rejection(PROBLEMS[args.problem], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, tool = rng.choice(sorted(combos))
    prob = PROBLEMS[problem]
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting, problem, tool, child, gender, helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a 3-to-5-year-old that uses the words "learn" and "advocate" and leans on repetition.',
        f'Tell a story where {f["kid"].id} learns the repeating pattern of the {f["problem_cfg"].noun} and advocates for {f["tool"].phrase}.',
        f'Write a repeated, folksy story in which a child says "learn" and "advocate" and a helper repeats the same fix until it works.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, helper, prob, tool, setting = f["kid"], f["helper"], f["problem_cfg"], f["tool"], f["setting"]
    return [
        QAItem(
            question="What did the child learn?",
            answer=(
                f"{kid.id} learned that the trouble was not random; it kept returning in the same pattern. "
                f"That is why {kid.id} could predict what help would be needed next."
            ),
        ),
        QAItem(
            question="What did the child advocate for?",
            answer=(
                f"{kid.id} advocated for {tool.phrase}. The child said the same plan more than once because the trouble itself kept repeating."
            ),
        ),
        QAItem(
            question="How did the helper respond?",
            answer=(
                f"{helper.id} listened and repeated the fix with {kid.id}. Together they used the same careful ritual until the {prob.noun} settled down."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("What does it mean to learn something?", "To learn means to understand it better after noticing, practicing, or being taught. Then you can use that knowledge later."),
        QAItem("What does advocate mean?", "To advocate means to speak up for an idea or a choice because you believe it is the right one. It is a brave way of helping."),
        QAItem("Why can repetition help?", "Repetition can help because doing the same useful thing again and again can make a pattern steady. A steady pattern is easier to trust."),
        QAItem(f"Why was the {f['problem_cfg'].noun} easy to notice?", f"It kept acting the same way over and over, so the child could spot the pattern. Repeated trouble is easier to learn from than a one-time surprise."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], TOOLS[params.tool], params.child, params.child_gender, params.helper)
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
problem_repeats(P) :- problem(P).
learns(C) :- child(C), tries(C, N), N >= 2.
advocates(C) :- child(C), learns(C).
resolved(P) :- problem(P), tool(T), fits(P, T).
story_ok(S, P, T) :- setting(S), problem(P), tool(T), problem_repeats(P), resolved(P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    rc = 0
    import asp
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset != pset:
        rc = 1
        print("MISMATCH between ASP and Python gate")
        print("only in asp:", sorted(cset - pset))
        print("only in python:", sorted(pset - cset))
    else:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, tool=None, gender=None, helper=None, name=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
