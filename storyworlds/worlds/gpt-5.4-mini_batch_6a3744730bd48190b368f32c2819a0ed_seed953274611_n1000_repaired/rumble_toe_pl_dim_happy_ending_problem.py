#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rumble_toe_pl_dim_happy_ending_problem.py
===========================================================================

A standalone tiny storyworld for a tall-tale style story about a rumbling road,
a dimming lantern, a problem that gets solved, and a shared happy ending.

The world is intentionally small: a wagon, a lantern, a bridge, two kids, and a
helpful grown-up. The prose is driven by simulated state, not by swapping nouns
in a frozen paragraph.

Seed words: rumble, toe-pl-dim
Features: Happy Ending, Problem Solving, Sharing
Style: Tall Tale
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
LIGHT_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    feature: str
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
class Problem:
    id: str
    source: str
    effect: str
    risk: str
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
class Fix:
    id: str
    method: str
    power: int
    share_text: str
    success_text: str
    fail_text: str
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
    setting: str
    problem: str
    fix: str
    protagonist: str
    protagonist_gender: str
    helper: str
    helper_gender: str
    adult: str
    seed: Optional[int] = None
    headstart: int = 0
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    light = world.entities.get("lantern")
    if not light:
        return out
    if light.meters["glow"] < LIGHT_MIN:
        return out
    if world.get("bridge").meters["rumble"] < THRESHOLD:
        return out
    sig = ("dim",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    light.meters["glow"] = max(0.0, light.meters["glow"] - 1.0)
    for kid in [e for e in world.entities.values() if e.role in {"protagonist", "helper"}]:
        kid.memes["worry"] += 1
    out.append("__dim__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    if world.get("lantern").meters["glow"] >= LIGHT_MIN:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("protagonist").memes["sharing"] += 1
    world.get("helper").memes["sharing"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [Rule("dim", _r_dim), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def problem_bites(problem: Problem, setting: Setting) -> bool:
    return "bridge" in setting.tags and "rumble" in problem.tags


def fix_works(fix: Fix, headstart: int) -> bool:
    return fix.power >= 1 + headstart


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for fid, fix in FIXES.items():
                if problem_bites(problem, setting):
                    combos.append((sid, pid, fid))
    return combos


def explain_rejection(setting: Setting, problem: Problem) -> str:
    return (
        f"(No story: the setting '{setting.place}' never gives the '{problem.source}' "
        f"problem a real rumble. Pick the bridge story.)"
    )


def explain_fix(fix: Fix) -> str:
    return f"(Refusing fix '{fix.id}': it is too weak to solve the problem.)"


def tell(setting: Setting, problem: Problem, fix: Fix, params: StoryParams) -> World:
    world = World()
    pro = world.add(Entity(id=params.protagonist, kind="character", type=params.protagonist_gender,
                           role="protagonist", label=params.protagonist))
    hel = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender,
                           role="helper", label=params.helper))
    adult = world.add(Entity(id=params.adult, kind="character", type="mother",
                             role="adult", label="the grown-up"))
    bridge = world.add(Entity(id="bridge", label="the bridge"))
    lantern = world.add(Entity(id="lantern", label="the lantern"))
    lantern.meters["glow"] = 1.0

    pro.memes["curious"] += 1
    hel.memes["curious"] += 1
    world.say(
        f"On the longest day the little wagon rolled toward {setting.place}, where "
        f"{setting.feature} shone like a storybook sky. {pro.id} and {hel.id} were "
        f"full of tall-tale cheer."
    )
    world.say(
        f"They rode with a lantern bright as a firefly jar, and {pro.id} whispered, "
        f'"toe-pl-dim," just for luck.'
    )

    world.para()
    world.say(
        f"But then came {problem.source}: the road gave a mighty rumble and the "
        f"lantern started to dim, slow as a sleepy candle."
    )
    bridge.meters["rumble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hel.id} gasped that the dark was swallowing the path, and {pro.id} saw "
        f"the light getting smaller by the blink."
    )

    world.para()
    world.say(
        f"{hel.id} did not waste a second. {hel.id} suggested sharing the lantern, "
        f"because one bright idea is better when two heads hold it."
    )
    world.say(
        f"{fix.share_text}."
    )

    if fix_works(fix, params.headstart):
        lantern.meters["glow"] = 2.0
        pro.memes["joy"] += 1
        hel.memes["joy"] += 1
        world.say(
            f"{pro.id} and {hel.id} used {fix.method}, and the lantern answered with "
            f"a warm gold glow."
        )
        world.say(
            f"{adult.label_word.capitalize()} laughed, said the problem had been solved "
            f"the sensible way, and tipped {pro.id} and {hel.id} a wink big enough to "
            f"outshine the moon."
        )
        world.para()
        world.say(
            f"So the wagon crossed the bridge together, the lantern shared between two "
            f"grinning hands, and the whole road sang with light."
        )
        outcome = "happy"
    else:
        lantern.meters["glow"] = 0.0
        world.say(
            f"But {fix.fail_text}. The lantern stayed too dim, and the road still "
            f"looked like a black ribbon."
        )
        world.say(
            f"The grown-up came forward with a spare lamp from the wagon and shared "
            f"that light, so the little travelers could finish the crossing safely."
        )
        world.para()
        world.say(
            f"Even then, the night ended kindly: the bridge calmed, the lamp held, and "
            f"the travelers shared their last crust of bread under a friendly star."
        )
        outcome = "recovered"

    world.facts.update(
        setting=setting,
        problem=problem,
        fix=fix,
        protagonist=pro,
        helper=hel,
        adult=adult,
        outcome=outcome,
        headstart=params.headstart,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story that includes the words "rumble" and '
        f'"toe-pl-dim" and ends happily after the children share a lantern.',
        f"Tell a problem-solving story where {f['protagonist'].id} and {f['helper'].id} "
        f"face a rumbling road, then fix it by sharing light.",
        f"Write a child-facing adventure about a dim lantern, a wise helper, and a "
        f"happy ending built on sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    pro = f["protagonist"]
    hel = f["helper"]
    adult = f["adult"]
    qa = [
        QAItem(
            question="What happened on the road?",
            answer=(
                f"The road gave a mighty rumble and the lantern started to dim. "
                f"That made the trip feel scary for a moment, because they needed "
                f"light to cross the bridge."
            ),
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=(
                f"{hel.id} suggested sharing the lantern, and they used {f['fix'].method} "
                f"to keep the light going. That was the sensible answer, and it let "
                f"them keep moving together."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended happily, with the bridge crossed and the lantern shared "
                f"between the children. The grown-up was pleased because they solved "
                f"the problem without giving up."
            ),
        ),
    ]
    if f["outcome"] == "happy":
        qa.append(QAItem(
            question=f"Why did {pro.id} whisper 'toe-pl-dim'?",
            answer=(
                f"{pro.id} said it like a lucky little saying while riding toward the "
                f"bridge. In the end, the words matched the story: the dimming problem "
                f"was fixed and the light came back."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer=(
                "Sharing means letting other people use or enjoy something with you. "
                "It helps everyone feel included and can make a hard problem easier."
            ),
        ),
        QAItem(
            question="Why is a lantern useful in the dark?",
            answer=(
                "A lantern gives light when there is not enough sunlight. That helps "
                "people see the path and stay safe."
            ),
        ),
        QAItem(
            question="What should you do when a problem gets hard?",
            answer=(
                "Stay calm, think of a sensible plan, and ask for help if you need it. "
                "Working together can turn a big problem into a small one."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "bridge": Setting(id="bridge", place="the old bridge", feature="the river wind", tags={"bridge"}),
}
PROBLEMS = {
    "rumble": Problem(id="rumble", source="the rumble", effect="dim", risk="dark", tags={"rumble"}),
}
FIXES = {
    "share_lantern": Fix(
        id="share_lantern",
        method="sharing the lantern",
        power=2,
        share_text="They passed the lantern back and forth, each child holding it for a spell",
        success_text="kept the lantern bright",
        fail_text="the lantern would not hold enough glow for the whole crossing",
        tags={"sharing"},
    ),
    "double_hands": Fix(
        id="double_hands",
        method="using two hands together",
        power=1,
        share_text="They cupped the lantern together so the wind could not pinch it out",
        success_text="kept the lantern bright",
        fail_text="the little flame still coughed and winked",
        tags={"problem_solving"},
    ),
}
CURATED = [
    StoryParams(
        setting="bridge",
        problem="rumble",
        fix="share_lantern",
        protagonist="Milo",
        protagonist_gender="boy",
        helper="June",
        helper_gender="girl",
        adult="Aunt Nell",
        headstart=0,
    ),
    StoryParams(
        setting="bridge",
        problem="rumble",
        fix="double_hands",
        protagonist="Bea",
        protagonist_gender="girl",
        helper="Ollie",
        helper_gender="boy",
        adult="Grandma June",
        headstart=1,
    ),
]


def explain_response(fix: Fix) -> str:
    return f"(Refusing fix '{fix.id}': it does not solve the problem well enough.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with a rumble and a dimming lantern.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--protagonist")
    ap.add_argument("--protagonist-gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--adult")
    ap.add_argument("--headstart", type=int, choices=[0, 1, 2])
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
    if args.fix and args.fix not in FIXES:
        raise StoryError(explain_response(Fixes[args.fix]))  # type: ignore[name-defined]
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    protagonist_gender = args.protagonist_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if protagonist_gender == "boy" else "boy")
    protagonist = args.protagonist or rng.choice(["Milo", "Bea", "Nell", "Jasper", "June"])
    helper = args.helper or rng.choice([n for n in ["Milo", "Bea", "Nell", "Jasper", "June"] if n != protagonist])
    adult = args.adult or rng.choice(["Aunt Nell", "Grandma June", "Papa Reed"])
    headstart = args.headstart if args.headstart is not None else rng.randint(0, 2)
    return StoryParams(setting=setting, problem=problem, fix=fix,
                       protagonist=protagonist, protagonist_gender=protagonist_gender,
                       helper=helper, helper_gender=helper_gender, adult=adult,
                       headstart=headstart)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix], params)
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
dimmed :- bridge(B), rumble_problem(B), lantern(L), glow(L, G), G >= 1.
shared :- dimmed, fix(shared_lantern).
happy :- shared.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("bridge", "bridge"), asp.fact("rumble_problem", "bridge"), asp.fact("lantern", "lantern"), asp.fact("glow", "lantern", 1)]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    # smoke test the normal generator
    try:
        _ = generate(CURATED[0])
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)


if __name__ == "__main__":
    main()
