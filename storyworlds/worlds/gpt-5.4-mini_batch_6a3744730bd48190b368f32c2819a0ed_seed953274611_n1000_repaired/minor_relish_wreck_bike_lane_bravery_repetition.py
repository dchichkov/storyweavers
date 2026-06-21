#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/minor_relish_wreck_bike_lane_bravery_repetition.py
===================================================================================

A standalone story world for a small mythic bike-lane tale.

Premise:
- A minor child rides a bike lane path.
- The child relishes repeating a brave chant or action.
- A small wreck blocks the lane.
- Bravery and Repetition turn fear into a useful, myth-like solution.

The world is intentionally tiny and state-driven: a block in the bike lane
accumulates risk, the child's courage rises through repeated attempts, and the
ending proves what changed by leaving the lane clear and the child steadier.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/minor_relish_wreck_bike_lane_bravery_repetition.py
    python storyworlds/worlds/gpt-5.4-mini/minor_relish_wreck_bike_lane_bravery_repetition.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/minor_relish_wreck_bike_lane_bravery_repetition.py --verify
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
BRAVERY_MIN = 2
REPETITION_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    image: str
    sound: str
    mood: str
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
    blocker: str
    thing: str
    risk: str
    severity: int
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
class Ritual:
    id: str
    name: str
    repeated_action: str
    call: str
    gain: str
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
class Aid:
    id: str
    name: str
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
    setting: str
    problem: str
    ritual: str
    aid: str
    child_name: str
    child_type: str
    guide_name: str
    guide_type: str
    minor_age: int = 9
    repetitions: int = 3
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["bravery"] < THRESHOLD:
        return out
    sig = ("brave", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["steady"] += 1
    out.append("__brave__")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["tries"] < REPETITION_MIN:
        return out
    sig = ("repeat", child.id, int(child.meters["tries"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["resolve"] += 1
    out.append("__repeat__")
    return out


CAUSAL_RULES = [Rule("bravery", _r_bravery), Rule("repetition", _r_repetition)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            xs = rule.apply(world)
            if xs:
                changed = True
                produced.extend(x for x in xs if not x.startswith("__"))
    if narrate:
        for x in produced:
            world.say(x)
    return produced


def setting_at_risk(problem: Problem) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for r in RITUALS:
                if setting_at_risk(PROBLEMS[p]):
                    combos.append((s, p, r))
    return combos


def skillful(aid: Aid, problem: Problem) -> bool:
    return aid.id in {"clear_branch", "carry_off", "signal_help"}


def tell(setting: Setting, problem: Problem, ritual: Ritual, aid: Aid,
         child_name: str, child_type: str, guide_name: str, guide_type: str,
         minor_age: int, repetitions: int) -> World:
    w = World()
    child = w.add(Entity(id="child", kind="character", type=child_type, label=child_name,
                         traits=["minor", "curious"], attrs={"age": str(minor_age)}))
    guide = w.add(Entity(id="guide", kind="character", type=guide_type, label=guide_name,
                         traits=["guide", "steady"]))
    lane = w.add(Entity(id="lane", type="place", label="bike lane"))
    block = w.add(Entity(id="block", type="thing", label=problem.thing))
    child.memes["bravery"] = 1
    child.memes["relish"] = 1
    child.meters["tries"] = 0
    child.meters["wobble"] = 0
    w.facts["setting"] = setting
    w.facts["problem"] = problem
    w.facts["ritual"] = ritual
    w.facts["aid"] = aid
    w.facts["guide"] = guide
    w.facts["child"] = child
    w.facts["lane"] = lane
    w.facts["block"] = block
    w.say(f"In the old myth-touched bike lane, {child_name} rode beneath {setting.image}.")
    w.say(f"The lane carried {setting.sound}, and the day felt {setting.mood}.")
    w.say(f"{child_name}, a minor child, went there with {guide_name}, {guide.pronoun()} as calm as a river stone.")
    w.say(f"Yet ahead lay {problem.blocker}: {problem.thing}. It threatened to {problem.risk}.")
    w.para()
    world_repeat = []
    for i in range(repetitions):
        child.meters["tries"] += 1
        child.memes["relish"] += 1
        world_repeat.append(f"{child_name} repeated {ritual.call}")
    propagate(w, narrate=False)
    w.say(f"{child_name} {ritual.repeated_action}.")
    w.say(f"Again {child_name} said {ritual.call}. Again the wheels found courage.")
    if child.memes["resolve"] >= THRESHOLD:
        w.say(f"The repetition made bravery grow like a torch fed by windless oil.")
    if skillful(aid, problem):
        w.para()
        child.meters["cleared"] += 1
        block.meters["moved"] += 1
        child.meters["lane_open"] += 1
        w.say(f"{guide_name} used {aid.action}, and {aid.result}.")
        w.say(f"The {problem.thing} no longer blocked the lane, and the path opened like a gate in a bright wall.")
        w.say(f"{child_name} rode on, still a minor child, but steadier now, and the repeated vow stayed warm in {child.pronoun('possessive')} chest.")
    else:
        w.para()
        child.meters["wobble"] += 1
        w.say(f"{guide_name} tried {aid.action}, but {aid.result}.")
        w.say(f"The {problem.thing} still crouched in the bike lane, and {child_name} learned to stop and call for help.")
    w.facts["outcome"] = "cleared" if skillful(aid, problem) else "blocked"
    return w


def _qa_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    problem: Problem = f["problem"]  # type: ignore[assignment]
    ritual: Ritual = f["ritual"]  # type: ignore[assignment]
    return [
        f'Write a myth-like story for a child in a bike lane that includes the words "minor", "{problem.id}", and "{ritual.id}".',
        f"Tell a short bravery story where {child.label_word} faces {problem.thing}, repeats a brave line, and the lane opens again.",
        f"Write a gentle myth about repetition turning fear into courage beside a bike lane.",
    ]


def _qa_story(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    guide: Entity = f["guide"]  # type: ignore[assignment]
    problem: Problem = f["problem"]  # type: ignore[assignment]
    ritual: Ritual = f["ritual"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    outcome = f["outcome"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label_word}, a minor child, and {guide.label_word}, who stayed beside the bike lane like a patient guardian."
        ),
        QAItem(
            question="What was the problem in the bike lane?",
            answer=f"{problem.thing} lay in the bike lane and could {problem.risk}. It was small, but it made the lane feel blocked and strange."
        ),
        QAItem(
            question="Why did the child keep repeating the brave line?",
            answer=f"{child.label_word} relished repetition because each repeat made the fear smaller and the courage larger. The repeated words helped {child.pronoun()} keep moving instead of turning away."
        ),
    ]
    if outcome == "cleared":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"{guide.label_word} used {aid.action}, and the {problem.thing} moved away. The bike lane opened, and {child.label_word} rode on with steadier shoulders and a brave heart."
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"The {problem.thing} stayed in the lane, so the two of them had to stop and ask for more help. Even then, the child kept the brave repetition close like a promise."
        ))
    return items


def _qa_world(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery do in this world?",
            answer="Bravery helps a small rider keep going when the lane looks frightening. It is the first ember that makes a useful choice possible."
        ),
        QAItem(
            question="What does repetition do in this world?",
            answer="Repetition makes a brave phrase or action stronger each time it happens. The world treats repeated courage like a path that becomes easier to follow."
        ),
        QAItem(
            question="Why can a wreck matter in a bike lane?",
            answer="A wreck matters because it can block the way and force riders to slow down or stop. In a bike lane, even a small obstacle can change the whole journey."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {params.problem}")
    if params.ritual not in RITUALS:
        raise StoryError(f"Unknown ritual: {params.ritual}")
    if params.aid not in AIDS:
        raise StoryError(f"Unknown aid: {params.aid}")
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], RITUALS[params.ritual],
                 AIDS[params.aid], params.child_name, params.child_type,
                 params.guide_name, params.guide_type, params.minor_age, params.repetitions)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_qa_prompts(world),
        story_qa=_qa_story(world),
        world_qa=_qa_world(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("== story qa ==")
        for q in sample.story_qa:
            print("Q:", q.question)
            print("A:", q.answer)
        print("== world qa ==")
        for q in sample.world_qa:
            print("Q:", q.question)
            print("A:", q.answer)


SETTINGS = {
    "bike_lane": Setting(id="bike_lane", place="bike lane", image="the hush of dawn", sound="small bells", mood="mythic and bright", tags={"bike", "lane"}),
    "lane": Setting(id="lane", place="bike lane", image="a silver morning", sound="wheel-song", mood="old as a tale", tags={"bike", "lane"}),
}

PROBLEMS = {
    "minor_wreck": Problem(id="minor_wreck", blocker="A minor wreck", thing="a minor wreck of broken branches", risk="snag the wheel", severity=1, tags={"minor", "wreck"}),
    "wreck_cart": Problem(id="wreck_cart", blocker="A wrecked cart", thing="a wrecked cart with one bent wheel", risk="block the lane", severity=2, tags={"wreck"}),
}

RITUALS = {
    "relish_repeat": Ritual(id="relish_repeat", name="relish repetition", repeated_action="pedaled in a steady circle of courage", call="I ride, I ride, I ride", gain="the next stroke felt easier", tags={"repetition", "relish"}),
    "brave_chant": Ritual(id="brave_chant", name="brave chant", repeated_action="spoke the same brave word three times", call="I can pass, I can pass, I can pass", gain="the fear loosened its grip", tags={"bravery", "repetition"}),
}

AIDS = {
    "clear_branch": Aid(id="clear_branch", name="clear branch", action="lifting the branches aside", result="the lane cleared at once", tags={"help"}),
    "carry_off": Aid(id="carry_off", name="carry the wreck away", action="carrying the wreck away together", result="the obstruction rolled safely to the curb", tags={"help"}),
    "signal_help": Aid(id="signal_help", name="signal help", action="calling to a grown helper", result="a helper came and opened the lane", tags={"help"}),
}

CURATED = [
    StoryParams(setting="bike_lane", problem="minor_wreck", ritual="relish_repeat", aid="clear_branch",
                child_name="Mira", child_type="girl", guide_name="Aster", guide_type="woman",
                minor_age=8, repetitions=3),
    StoryParams(setting="lane", problem="wreck_cart", ritual="brave_chant", aid="carry_off",
                child_name="Theo", child_type="boy", guide_name="Orion", guide_type="man",
                minor_age=9, repetitions=4),
    StoryParams(setting="bike_lane", problem="minor_wreck", ritual="brave_chant", aid="signal_help",
                child_name="Nia", child_type="girl", guide_name="Helios", guide_type="man",
                minor_age=7, repetitions=2),
]


def valid_combo(setting: str, problem: str, ritual: str, aid: str) -> bool:
    return setting in SETTINGS and problem in PROBLEMS and ritual in RITUALS and aid in AIDS


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid in RITUALS:
        lines.append(asp.fact("ritual", rid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid))
    lines.append(asp.fact("bike_lane", "bike_lane"))
    lines.append(asp.fact("minor_word", "minor"))
    lines.append(asp.fact("relish_word", "relish"))
    lines.append(asp.fact("wreck_word", "wreck"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,R,A) :- setting(S), problem(P), ritual(R), aid(A).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = {(s, p, r, a) for s in SETTINGS for p in PROBLEMS for r in RITUALS for a in AIDS if valid_combo(s, p, r, a)}
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in ASP parity")
    else:
        print(f"OK: ASP parity across {len(py)} combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print("SMOKE TEST FAILED:", e)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic bike-lane story world with bravery and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--guide")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    ritual = args.ritual or rng.choice(list(RITUALS))
    aid = args.aid or rng.choice(list(AIDS))
    if not valid_combo(setting, problem, ritual, aid):
        raise StoryError("Invalid parameter combination.")
    child_name = args.name or rng.choice(["Mira", "Theo", "Nia", "Ezra", "Luna"])
    guide_name = args.guide or rng.choice(["Aster", "Orion", "Helios", "Iris"])
    child_type = "girl" if child_name in {"Mira", "Nia", "Luna"} else "boy"
    guide_type = "woman" if guide_name in {"Aster", "Iris"} else "man"
    return StoryParams(setting=setting, problem=problem, ritual=ritual, aid=aid,
                       child_name=child_name, child_type=child_type,
                       guide_name=guide_name, guide_type=guide_type,
                       minor_age=rng.randint(6, 10), repetitions=rng.randint(2, 4))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
