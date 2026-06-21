#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/possessive_git_bad_ending_suspense_tall_tale.py
================================================================================

A standalone storyworld for a tall-tale suspense yarn about a child's
possessive habit, a troublesome git, and a bad ending that still feels like a
complete little story.

Premise
-------
A child guards a prized bundle on a windy river day. A sneaky git keeps
dabbling in the gear, and the child must decide whether to trust, chase, or
call for help. Suspense rises from missing items, distant sounds, and the
feeling that something important is getting away.

Ending shape
------------
This world is intentionally built to allow a bad ending: the git gets loose,
the storm ruins the plan, and the child loses the prize. The story still ends
with an image that proves what changed.

Required words
--------------
The generated story always includes:
- "possessive"
- "git"

Style
-----
Tall tale: concrete, exaggerated, child-facing, and a little windy in its
language, but still driven by state changes rather than a frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/possessive_git_bad_ending_suspense_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/possessive_git_bad_ending_suspense_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/possessive_git_bad_ending_suspense_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/possessive_git_bad_ending_suspense_tall_tale.py --verify
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
SUSPENSE_TENSION = 2.0
BAD_ENDING_MARK = 1.0
BRAVERY_INIT = 5.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    weather: str
    sound: str
    danger_word: str


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    value: str
    carry: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Git:
    id: str
    label: str
    phrase: str
    sneaky: str
    steal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    damage: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["unease"] < THRESHOLD:
            continue
        if "camp" in world.entities:
            camp = world.get("camp")
            sig = ("suspense", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            camp.meters["danger"] += 1
            out.append("__suspense__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("loss", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("child").memes["heartache"] += 1
        out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("loss", "physical", _r_loss),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(prize: Prize, git: Git) -> bool:
    return True if prize.fragile else False


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def git_truth(setting: Setting, prize: Prize, git: Git) -> bool:
    return prize_at_risk(prize, git) and setting.weather in {"windy", "stormy", "foggy"}


def chance_of_loss(setting: Setting, risk: Risk) -> int:
    base = risk.severity
    if setting.weather == "stormy":
        base += 2
    elif setting.weather == "windy":
        base += 1
    return base


def is_lost(response: Response, setting: Setting, risk: Risk) -> bool:
    return response.power < chance_of_loss(setting, risk)


def _do_chaos(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["lost"] += 1
    propagate(world, narrate=narrate)


def predict_loss(world: World, prize_id: str, risk_id: str) -> dict:
    sim = world.copy()
    _do_chaos(sim, sim.get(prize_id), narrate=False)
    return {"lost": sim.get(prize_id).meters["lost"] >= THRESHOLD,
            "danger": sim.get("camp").meters["danger"]}


def opening(world: World, child: Entity, setting: Setting, prize: Prize) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a wind-bitten morning, {child.id} stood by {setting.place}, where the "
        f"water went by like a blue wagon road and the reeds bowed like polite old men."
    )
    world.say(
        f"{child.id} had {child.pronoun('possessive')} {prize.phrase}, and {prize.value} "
        f"made {child.pronoun('possessive')} heart stand up proud."
    )


def suspense_beat(world: World, child: Entity, git: Git, setting: Setting) -> None:
    child.memes["unease"] += 1
    world.say(
        f"Then something little and sly came rustling under the dock -- a git, "
        f"{git.sneaky}, with eyes bright as bottle glass."
    )
    world.say(
        f"It kept nudging closer, and every time it moved, the ropes made a creak "
        f"that sounded a whole mile long."
    )


def possessive_warning(world: World, child: Entity, git: Git, prize: Prize) -> None:
    child.memes["possessive"] += 1
    world.say(
        f'"That is {child.pronoun("possessive")} {prize.label}!" {child.id} said, '
        f"with a very possessive voice."
    )
    world.say(
        f"The git only blinked and looked at the {prize.label} like it had already "
        f"borrowed it in its mind."
    )


def warn(world: World, parent: Entity, child: Entity, risk: Risk, setting: Setting) -> None:
    pred = predict_loss(world, "prize", "risk")
    child.memes["unease"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{parent.id} squinted at the sky. "That {risk.label} is coming," '
        f"{parent.pronoun()} said. \"If that git keeps meddling, the whole "
        f"day may turn sideways.\""
    )
    if pred["danger"] >= 1:
        world.say(
            f"The camp already felt too small for the trouble, and the river wind "
            f"kept whispering that something was about to go wrong."
        )


def chase(world: World, child: Entity, git: Git, prize: Prize) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} darted after the git, saying the {prize.label} would not be "
        f"taken by a whisker-thin rascal."
    )


def chaos(world: World, risk: Risk, prize: Prize) -> None:
    prize_ent = world.get("prize")
    _do_chaos(world, prize_ent)
    prize_ent.meters["damage"] += 1
    world.say(
        f"Then the {risk.label} hit like a tumbling barn. The {prize.label} slipped "
        f"from {world.get('child').id}'s hands, skidded into the mud, and the git "
        f"vanished into the reeds."
    )


def bad_ending(world: World, child: Entity, parent: Entity, prize: Prize, risk: Risk) -> None:
    child.memes["heartache"] += 1
    world.say(
        f"When the storm finished shouting, there was only a soggy patch, a bent "
        f"string, and {child.id}'s empty hands."
    )
    world.say(
        f"{parent.id} pulled {child.id} under the lean-to, but the prize was gone "
        f"for good, carried off by the river and the bad luck with it."
    )
    world.say(
        f"{child.id} looked at the gray water and knew {prize.label} would never be "
        f"the same again."
    )


def lesson(world: World, child: Entity, parent: Entity, git: Git, setting: Setting) -> None:
    world.say(
        f"After that, {parent.id} said a tall tale truth: \"A git can be little, "
        f"but trouble can be mighty.\""
    )
    world.say(
        f"{child.id} nodded in the rain and tucked {child.pronoun('possessive')} "
        f"empty {setting.danger_word} of a pocket close, wishing the day had turned "
        f"out different."
    )


def tell(setting: Setting, prize: Prize, git: Git, risk: Risk, response: Response,
         child_name: str = "Pip", child_gender: str = "boy",
         parent_name: str = "Aunt June", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=["bold"], attrs={"setting": setting.id}))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender,
                              role="parent"))
    camp = world.add(Entity(id="camp", type="place", label="camp"))
    world.add(Entity(id="prize", type="thing", label=prize.label))
    world.add(Entity(id="risk", type="thing", label=risk.label))
    world.facts["setting"] = setting
    world.facts["prize_cfg"] = prize
    world.facts["git_cfg"] = git
    world.facts["risk_cfg"] = risk
    world.facts["response"] = response

    opening(world, child, setting, prize)
    world.para()
    suspense_beat(world, child, git, setting)
    possessive_warning(world, child, git, prize)
    warn(world, parent, child, risk, setting)
    world.para()
    chase(world, child, git, prize)
    if is_lost(response, setting, risk):
        chaos(world, risk, prize)
        bad_ending(world, child, parent, prize, risk)
    else:
        world.say(
            f"The trouble was caught in time, and the prize stayed safe beside the "
            f"fire barrel."
        )
    lesson(world, child, parent, git, setting)
    world.facts.update(child=child, parent=parent, camp=camp, outcome="lost" if is_lost(response, setting, risk) else "saved")
    return world


SETTINGS = {
    "river": Setting(id="river", place="the river landing", detail="a dock and a lean-to", weather="windy", sound="water slapping the posts", danger_word="pocket"),
    "marsh": Setting(id="marsh", place="the marsh edge", detail="a reed maze and a crooked boardwalk", weather="foggy", sound="frogs muttering low", danger_word="satchel"),
    "storm": Setting(id="storm", place="the old ferry camp", detail="a canvas lean-to and a mooring post", weather="stormy", sound="the tarps snapping hard", danger_word="bundle"),
}

PRIZES = {
    "map": Prize(id="map", label="map", phrase="a folded map of the river bends", value="the way home", carry="folded in a pocket", tags={"paper"}),
    "compass": Prize(id="compass", label="compass", phrase="a brass compass with a cracked face", value="the north star in a tin case", carry="hung on a cord", tags={"metal"}),
    "lantern": Prize(id="lantern", label="lantern", phrase="a little lantern with a glass belly", value="the camp light", carry="held with care", tags={"glass"}),
}

GITS = {
    "dock": Git(id="dock", label="git", phrase="a dockside git", sneaky="slippery as a minnow", steal="snatched at cords", tags={"git"}),
    "reeds": Git(id="reeds", label="git", phrase="a reed-rustling git", sneaky="thin as a whippoorwill shadow", steal="twisted through stems", tags={"git"}),
}

RISKS = {
    "gust": Risk(id="gust", label="gust of wind", damage="blown loose", severity=2, tags={"wind"}),
    "storm": Risk(id="storm", label="storm squall", damage="washed away", severity=3, tags={"storm"}),
}

RESPONSES = {
    "hide": Response(id="hide", sense=3, power=2, text="covered the prize with a tarp and held it down until the wind tired itself out", fail="covered the prize, but the wind tore it free anyway", tags={"sense"}),
    "tie": Response(id="tie", sense=4, power=3, text="tied the prize to the mooring post with a double knot and kept one hand on it", fail="tied it fast, but the squall snapped the cord", tags={"sense"}),
    "call": Response(id="call", sense=2, power=1, text="called for the grown-ups and got the camp ready as fast as a startled fox", fail="called too late, and the storm had already won", tags={"sense"}),
}

SENSE_MIN = 2
CURATED = [
    {"setting": "river", "prize": "map", "git": "dock", "risk": "gust", "response": "tie", "child_name": "Pip", "child_gender": "boy", "parent_name": "Aunt June", "parent_gender": "woman"},
    {"setting": "marsh", "prize": "compass", "git": "reeds", "risk": "gust", "response": "hide", "child_name": "Mina", "child_gender": "girl", "parent_name": "Uncle Bo", "parent_gender": "man"},
    {"setting": "storm", "prize": "lantern", "git": "dock", "risk": "storm", "response": "call", "child_name": "Jory", "child_gender": "boy", "parent_name": "Mother Nell", "parent_gender": "woman"},
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for g in GITS:
            for r in RISKS:
                if git_truth(SETTINGS[s], PRIZES["map"], GITS[g]) or True:
                    combos.append((s, g, r))
    return combos


@dataclass
class StoryParams:
    setting: str
    prize: str
    git: str
    risk: str
    response: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "git": [("What is a git?", "A git is a rude or sneaky little troublemaker. In a tall tale, a git may be small, but it can still stir up a big mess.")],
    "map": [("What is a map?", "A map shows where places are and helps people find their way.")],
    "compass": [("What does a compass do?", "A compass points the way north and helps people stay on course.")],
    "lantern": [("What is a lantern?", "A lantern is a light you carry so you can see in the dark.")],
    "wind": [("Why can wind be dangerous?", "Strong wind can pull things loose, blow them away, or knock them over.")],
    "storm": [("Why is a storm risky?", "A storm can bring strong wind and heavy rain that make it hard to keep things safe.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that includes the words "possessive" and "git".',
        f"Tell a suspenseful story where {f['child'].id} guards {f['prize_cfg'].phrase} from a git, and the ending goes badly.",
        f"Write a child-friendly bad-ending story with a windy river setting, a sneaky git, and a prize that gets lost.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent = f["child"], f["parent"]
    prize, setting, git, risk = f["prize_cfg"], f["setting"], f["git_cfg"], f["risk_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who tried to keep {child.pronoun('possessive')} {prize.label} safe, and {parent.id}, who warned about the weather."),
        ("What made the story suspenseful?",
         f"The suspense came from the git sneaking around and the weather growing meaner and meaner. The reader keeps waiting to see whether the prize will stay safe."),
        ("What word did the child use to describe the feeling?",
         f"The story uses the word possessive when {child.id} guards {child.pronoun('possessive')} {prize.label}. That shows how tightly {child.id} wanted to keep it."),
    ]
    if f["outcome"] == "lost":
        qa.append((
            "How did the story end?",
            f"It ended badly: the {prize.label} was lost in the mud and wind, and the git got away. The last image is of empty hands and a ruined plan."
        ))
        qa.append((
            f"Why couldn't the response save the {prize.label}?",
            f"{parent.id} tried {world.facts['response'].text}, but the storm was stronger than that. The bad ending happened because the wind and rain outmatched the plan."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended safely, with the {prize.label} tied down and the git kept away. The camp looked calmer by the end."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["git_cfg"].tags) | set(world.facts["prize_cfg"].tags) | set(world.facts["risk_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in ["git", "map", "compass", "lantern", "wind", "storm"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P).
suspense :- risk(R), severity(R, S), S >= 2.
outcome(lost) :- suspense.
outcome(saved) :- not suspense.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for gid in GITS:
        lines.append(asp.fact("git", gid))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("", "#show outcome/1."))
        _ = asp.atoms(model, "outcome")
        sample = generate(resolve_params(argparse.Namespace(setting=None, prize=None, git=None, risk=None, response=None, child_name=None, child_gender=None, parent_name=None, parent_gender=None), random.Random(7)))
        print("OK: ASP executed and a sample story generated.")
        print(sample.story[:120].replace("\n", " "))
        return 0
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale suspense world with a bad ending about a possessive child and a git.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--git", choices=GITS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["boy", "girl"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["man", "woman"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    prize = args.prize or rng.choice(list(PRIZES))
    git = args.git or rng.choice(list(GITS))
    risk = args.risk or rng.choice(list(RISKS))
    response = args.response or rng.choice(list(RESPONSES))
    child_gender = args.child_gender or rng.choice(["boy", "girl"])
    child_name = args.child_name or rng.choice(["Pip", "Mara", "June", "Eli", "Nell"])
    parent_gender = args.parent_gender or rng.choice(["man", "woman"])
    parent_name = args.parent_name or rng.choice(["Aunt June", "Uncle Bo", "Mother Pike", "Father Reed"])
    if response not in RESPONSES:
        raise StoryError("Unknown response.")
    return StoryParams(setting=setting, prize=prize, git=git, risk=risk, response=response,
                       child_name=child_name, child_gender=child_gender,
                       parent_name=parent_name, parent_gender=parent_gender)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.prize not in PRIZES or params.git not in GITS or params.risk not in RISKS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], PRIZES[params.prize], GITS[params.git], RISKS[params.risk], RESPONSES[params.response], params.child_name, params.child_gender, params.parent_name, params.parent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.prize in PRIZES and params.git in GITS and params.risk in RISKS and params.response in RESPONSES


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="river", prize="map", git="dock", risk="gust", response="tie", child_name="Pip", child_gender="boy", parent_name="Aunt June", parent_gender="woman"),
            StoryParams(setting="marsh", prize="compass", git="reeds", risk="gust", response="hide", child_name="Mara", child_gender="girl", parent_name="Uncle Bo", parent_gender="man"),
            StoryParams(setting="storm", prize="lantern", git="dock", risk="storm", response="call", child_name="Nell", child_gender="girl", parent_name="Mother Pike", parent_gender="woman"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
