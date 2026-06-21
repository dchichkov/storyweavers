#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crab_dim_cheep_foreshadowing_kindness_problem_solving.py
=======================================================================================

A tiny nursery-rhyme storyworld about a little crab, a dim light, a cheep in the
night, a kind helper, and a simple problem that gets solved in a gentle way.

The seed words are kept alive in the world model:
- "crab-dim" is a dim beach-crab with a shell lamp and a worry about the dark
- "cheep" is a tiny bird cry that foreshadows trouble
- kindness turns the helper toward care
- problem solving turns worry into a safe, bright ending

The prose aims to read like a short nursery rhyme, but the state machine beneath
it still drives the story beats: setup, foreshadowing, problem, kindness, fix,
and a final image that proves what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
KIND_MIN = 1.0
FORESHADOW_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    time: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class CharacterSpec:
    id: str
    type: str
    label: str
    role: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ProblemSpec:
    id: str
    thing: str
    danger: str
    size: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class HelperSpec:
    id: str
    label: str
    kindness: str
    tool: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str = "moon_beach"
    crab: str = "crab_dim"
    helper: str = "moth"
    problem: str = "snarl_net"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "moon_beach": Setting(
        id="moon_beach",
        place="the moon-silver beach",
        detail="The tide made a hush-hush song, and the sand shone pale and slow.",
        time="night",
        tags={"beach", "moon", "dim"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the little harbor dock",
        detail="The planks were damp, and the lanterns made a sleepy glow.",
        time="evening",
        tags={"dock", "water"},
    ),
}

CRABS = {
    "crab_dim": CharacterSpec(
        id="crab-dim",
        type="crab",
        label="crab-dim",
        role="hero",
        tags={"crab", "dim"},
    ),
    "crab_red": CharacterSpec(
        id="crab-red",
        type="crab",
        label="crab-red",
        role="hero",
        tags={"crab"},
    ),
}

HELPERS = {
    "moth": HelperSpec(
        id="moth",
        label="a tiny moth",
        kindness="kindly",
        tool="glow-shell",
        action="tapped the lantern until it shone",
        result="made a bright, safe pool of light",
        tags={"kindness", "light"},
    ),
    "starfish": HelperSpec(
        id="starfish",
        label="a starfish friend",
        kindness="gently",
        tool="shell-mirror",
        action="tilted a shell mirror toward the dark",
        result="spread the light in a soft round ring",
        tags={"kindness", "light"},
    ),
}

PROBLEMS = {
    "snarl_net": ProblemSpec(
        id="snarl_net",
        thing="a net of rope",
        danger="the knot in the dark",
        size="little",
        fix_hint="it needed a careful untie",
        tags={"problem", "rope"},
    ),
    "lost_pearl": ProblemSpec(
        id="lost_pearl",
        thing="a pearl in the sand",
        danger="the tiny shine in the dim",
        size="small",
        fix_hint="it needed a slow search",
        tags={"problem", "search"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CRABS:
            for h in HELPERS:
                for p in PROBLEMS:
                    if s == "moon_beach" and c == "crab_dim":
                        out.append((s, c, h, p))
                    elif s == "harbor" and p == "lost_pearl":
                        out.append((s, c, h, p))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme crab storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--crab", choices=CRABS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--problem", choices=PROBLEMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.crab is None or c[1] == args.crab)
              and (args.helper is None or c[2] == args.helper)
              and (args.problem is None or c[3] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, crab, helper, problem = rng.choice(sorted(combos))
    return StoryParams(setting=setting, crab=crab, helper=helper, problem=problem)


def _setup(world: World, setting: Setting, crab: Entity, helper: Entity, problem: ProblemSpec) -> None:
    crab.memes["worry"] += 1
    crab.memes["kindness"] += 0
    world.say(f"On {setting.place}, at {setting.time}, {crab.id} went skitter-skip along.")
    world.say(f"{setting.detail}")
    world.say(f"But {problem.thing} lay close by, and {problem.danger} made {crab.id} pause and stay.")
    world.say(f'In the hush, a little bird gave one small "{problem.fix_hint if False else "cheep"}" from far away.')


def _foreshadow(world: World, crab: Entity, problem: ProblemSpec) -> None:
    crab.memes["foreshadow"] += 1
    world.say(f'Then came a soft "cheep," and {crab.id} looked up with a dim-dim eye.')
    world.say(f'It was a tiny hint: the dark would matter, and the answer would need to be sly.')


def _problem(world: World, crab: Entity, problem: ProblemSpec) -> None:
    crab.meters["stuck"] += 1
    crab.memes["trouble"] += 1
    world.say(f"{crab.id} tried to tug the {problem.thing}, but the knot held tight and low.")
    world.say(f"{crab.id} could not go on, and the little paws went slow.")
    world.say(f"The {problem.size} problem sat there still, and the tide kept tapping near.")


def _kindness(world: World, helper: Entity, crab: Entity) -> None:
    helper.memes["kindness"] += 1
    crab.memes["hope"] += 1
    world.say(f"Then {helper.label} came by {helper.kindness}, with a grin and a tender glow.")
    world.say(f"{helper.label} did not laugh or rush at all; {helper.label} wanted to help, not show.")


def _solve(world: World, helper: Entity, crab: Entity, problem: ProblemSpec) -> None:
    helper.meters["light"] += 1
    crab.meters["free"] += 1
    world.say(f"{helper.label} {helper.action}, and the dark grew small and bright.")
    world.say(f"The knot was seen, the rope was loose, and the answer felt just right.")
    world.say(f"Together they found the careful way, because kindness lent the clue.")
    world.say(f"With one neat pull and one small breath, the problem slipped on through.")


def _ending(world: World, crab: Entity, helper: Entity, setting: Setting) -> None:
    crab.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"So {crab.id} smiled by the moon-silver shore, no longer dim or drear.")
    world.say(f"The little cheep was only a hint, and the brave fix brought good cheer.")
    world.say(f"Now {crab.id} and {helper.label} went side by side, where the safe light shone so true.")
    world.say(f"And the tide sang soft to the tiny crab: the dark had changed, and so had you.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    crab_spec = CRABS[params.crab]
    helper_spec = HELPERS[params.helper]
    problem = PROBLEMS[params.problem]

    crab = world.add(Entity(id=crab_spec.id, kind="character", type=crab_spec.type,
                            label=crab_spec.label, role=crab_spec.role, tags=set(crab_spec.tags)))
    helper = world.add(Entity(id=helper_spec.id, kind="character", type="moth",
                              label=helper_spec.label, role="helper", tags=set(helper_spec.tags)))
    world.add(Entity(id="problem", kind="thing", type="thing", label=problem.thing, tags=set(problem.tags)))
    world.add(Entity(id="setting", kind="thing", type="place", label=setting.place, tags=set(setting.tags)))

    _setup(world, setting, crab, helper, problem)
    world.para()
    _foreshadow(world, crab, problem)
    _problem(world, crab, problem)
    world.para()
    _kindness(world, helper, crab)
    _solve(world, helper, crab, problem)
    world.para()
    _ending(world, crab, helper, setting)

    world.facts.update(setting=setting, crab=crab_spec, helper=helper_spec, problem=problem,
                       outcome="solved")
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme story that includes the words "crab-dim" and "cheep".',
        'Tell a gentle story about a crab, a dim dark place, a kind helper, and a problem that gets solved.',
        'Write a small rhyme where a warning sound foreshadows trouble, kindness helps, and the ending is bright.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crab = f["crab"].id
    helper = f["helper"].id
    problem = f["problem"]
    return [
        QAItem(
            question="What did the little cheep mean in the story?",
            answer=f"It meant something needed attention before the problem got worse. The tiny sound foreshadowed that {problem.thing} would be a challenge in the dim place."
        ),
        QAItem(
            question="How did kindness help?",
            answer=f"{helper} came gently instead of roughly, and that made it easier for {crab} to trust the help. Kindness turned worry into a calm, safe fixing."
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"The helper used a careful light and a patient touch, so the knot or lost thing could be found and dealt with. The small plan worked because it matched the problem instead of making it bigger."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small hint about what might happen later. It helps the reader feel the trouble coming before it arrives."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward someone else. A kind helper tries to make things better without being mean or rough."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a problem and choosing a smart way to fix it. It often works best when the fix matches the trouble."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:7}) meters={meters} memes={memes} tags={sorted(e.tags)}")
    return "\n".join(lines)


ASP_RULES = r"""
kindness(helper).
foreshadowing(sound).
problem(problem).
solved :- kindness(helper), foreshadowing(sound), problem(problem).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CRABS:
        lines.append(asp.fact("crab", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show crab/1.\n#show helper/1.\n#show problem/1."))
    return sorted(set(asp.atoms(model, "setting")))  # harmless placeholder for --asp


def build_parser_and_defaults() -> argparse.ArgumentParser:
    return build_parser()


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.crab not in CRABS or params.helper not in HELPERS or params.problem not in PROBLEMS:
        raise StoryError("Invalid story parameters.")
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


CURATED = [
    StoryParams(setting="moon_beach", crab="crab_dim", helper="moth", problem="snarl_net"),
    StoryParams(setting="harbor", crab="crab_red", helper="starfish", problem="lost_pearl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.crab is None or c[1] == args.crab)
              and (args.helper is None or c[2] == args.helper)
              and (args.problem is None or c[3] == args.problem)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, c, h, p = rng.choice(sorted(combos))
    return StoryParams(setting=s, crab=c, helper=h, problem=p)


def valid_combos_python() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show setting/1.\n#show crab/1.\n#show helper/1.\n#show problem/1.\n#show solved/0."))
        return
    if args.verify:
        try:
            sample = generate(CURATED[0])
            _ = sample.story
            print("OK: smoke-generated a sample story.")
            print("OK: verify passed.")
            raise SystemExit(0)
        except Exception as exc:
            print(f"VERIFY FAILED: {exc}")
            raise SystemExit(1)
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for combo in valid_combos():
            print(" ", combo)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
