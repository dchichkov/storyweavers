#!/usr/bin/env python3
"""
Storyworld: synthesize / chic / hint
A tiny Tall Tale-style living-room domain about Curiosity and Moral Value.

Premise:
A child in a living room tries to synthesize a chic idea from scraps of wonder,
but a helpful hint shows that style without kindness is not really elegant at all.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the living room"
    affords: set[str] = field(default_factory=lambda: {"synthesize", "hint"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    trait: str
    requires_curiosity: bool = True


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_spill(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    obj = world.get("prize")
    if kid.meters.get("messy", 0) < THRESHOLD:
        return out
    if obj.meters.get("stained", 0) >= THRESHOLD:
        return out
    sig = ("spill", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obj.meters["stained"] = 1
    out.append(f"{obj.label.capitalize()} got a little smudged by all that bustling wonder.")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    mom = world.get("parent")
    if kid.memes.get("defiance", 0) < THRESHOLD or kid.memes.get("heard_hint", 0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["curiosity"] = 0
    kid.memes["moral_value"] = 1
    kid.memes["joy"] = 1
    mom.memes["joy"] = 1
    out.append("__calm__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spill, _r_calm):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "__calm__":
                world.say(s)
    return produced


SETTING = Setting()

ACTIVITIES = {
    "synthesize": Activity(
        id="synthesize",
        verb="synthesize a chic plan",
        gerund="synthesizing chic plans",
        rush="dash about the cushions and postcards",
        risk="a flashy idea with no kind heart",
        keyword="synthesize",
        tags={"curiosity", "chic"},
    ),
    "hint": Activity(
        id="hint",
        verb="listen for a hint",
        gerund="listening for hints",
        rush="lean close to hear the whisper",
        risk="a wise little nudge toward kindness",
        keyword="hint",
        tags={"curiosity", "moral"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a chic little hat with a shiny band",
        type="hat",
        trait="chic",
    ),
    "puzzle": Prize(
        label="puzzle",
        phrase="a tidy puzzle with bright corners",
        type="puzzle",
        trait="curious",
    ),
    "crown": Prize(
        label="crown",
        phrase="a paper crown trimmed with gold stars",
        type="crown",
        trait="chic",
    ),
}

FIXES = {
    "kindness": Fix(
        id="kindness",
        label="a kindness note",
        prep="write a kindness note first",
        tail="wrote the kindness note and tucked it under the lamp",
    ),
    "tidy_table": Fix(
        id="tidy_table",
        label="the tidy table",
        prep="clear the little table and lay everything out",
        tail="cleared the table and lined up the bright scraps",
    ),
}

NAMES = {
    "girl": ["Maya", "June", "Lola", "Ivy", "Nora"],
    "boy": ["Theo", "Ben", "Milo", "Finn", "Ari"],
}


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def can_story(activity: Activity, prize: Prize) -> bool:
    if activity.id == "synthesize" and prize.trait != "chic":
        return False
    if activity.id == "hint" and prize.trait != "curious":
        return False
    return True


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    if activity.id == "synthesize":
        return FIXES["kindness"]
    if activity.id == "hint":
        return FIXES["tidy_table"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for act in ACTIVITIES:
        for prize in PRIZES:
            if can_story(ACTIVITIES[act], PRIZES[prize]) and select_fix(ACTIVITIES[act], PRIZES[prize]):
                out.append((act, prize))
    return out


def tell(params: StoryParams) -> World:
    act = ACTIVITIES[params.activity]
    prize_cfg = PRIZES[params.prize]
    fix = select_fix(act, prize_cfg)
    if fix is None:
        raise StoryError("No reasonable fix exists for this story.")

    world = World(SETTING)
    kid = world.add(Entity(
        id="kid",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"messy": 0},
        memes={"curiosity": 1, "moral_value": 0, "joy": 0, "defiance": 0, "heard_hint": 0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        memes={"joy": 0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=kid.id,
    ))

    world.say(f"In the living room, {kid.label} was a little whirlwind with a big Curious eye.")
    world.say(f"{kid.pronoun().capitalize()} loved to {act.verb} from scraps of ribbon, lamp-light, and sofa-shadow.")
    world.say(f"The {params.parent} had just brought home {prize_cfg.phrase}, and {kid.label} admired it like a moonbeam in a hatbox.")

    world.para()
    world.say(f"One afternoon, {kid.label} tried to {act.verb} beside the rug and the cookie tin.")
    kid.meters["messy"] += 1
    kid.memes["curiosity"] += 1
    world.say(f"{kid.pronoun().capitalize()} rushed around so fast that the room began to feel like a little thundercloud of ideas.")
    world.say(f"But the clever little plan had a flaw: it risked {act.risk}.")

    world.para()
    world.say(f"The {params.parent} gave a gentle hint: \"A chic thing is not truly chic if it forgets a kind heart.\"")
    kid.memes["heard_hint"] += 1
    kid.memes["defiance"] += 1
    world.say(f"{kid.label} paused, because that hint was truer than a whistle on a winter fence.")
    propagate(world, narrate=True)

    world.para()
    if fix.id == "kindness":
        world.say(f"So {kid.label} chose a better shine.")
        world.say(f"{kid.label} decided to {fix.prep}, then synthesize the chic plan again with a kinder shape.")
    else:
        world.say(f"Then {kid.label} listened to the hint and {fix.prep}.")
    world.say(f"That small change turned the whole afternoon around.")
    world.say(f"{params.name} {fix.tail}, and the living room grew neat as a postcard porch.")
    world.say(f"In the end, {kid.label} was still curious, but now {kid.pronoun('possessive')} curiosity had manners, and {prize.label} stayed bright.")

    world.facts.update(
        kid=kid,
        parent=parent,
        prize=prize,
        activity=act,
        fix=fix,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a Tall Tale-style story about a child who wants to {act.verb} in the living room.',
        f'Write a short story that uses the words "synthesize", "chic", and "hint" and ends with {kid.label} learning a moral value.',
        f'Tell a gentle living-room tale where {kid.label} admires {prize.phrase} and a hint changes the plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["kid"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What did {kid.label} want to do in the living room?",
            answer=f"{kid.label} wanted to {act.verb}, because curiosity kept bobbing in {kid.pronoun('possessive')} chest like a lantern in the wind.",
        ),
        QAItem(
            question=f"Why did the {parent.type} give a hint?",
            answer=f"The {parent.type} gave a hint because the plan risked turning {prize.label} into a messy sight, and the story wanted a kinder, wiser choice.",
        ),
        QAItem(
            question=f"What changed after the hint?",
            answer=f"After the hint, {kid.label} chose {fix.label}, and that helped {kid.label} keep curiosity while also showing moral value.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {kid.label} still curious, but calmer and kinder, while {prize.label} stayed bright in the living room.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a living room?",
            answer="A living room is a room in a house where people sit, talk, and spend time together.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn, look, ask, and find out how things work.",
        ),
        QAItem(
            question="What is moral value?",
            answer="A moral value is a good rule for living, like being kind, honest, or fair.",
        ),
        QAItem(
            question="What is a hint?",
            answer="A hint is a small clue or gentle suggestion that helps someone understand what to do next.",
        ),
        QAItem(
            question="What does chic mean?",
            answer="Chic means neat, stylish, and pleasantly fashionable.",
        ),
        QAItem(
            question="What does synthesize mean?",
            answer="To synthesize means to put small pieces together to make one new thing.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} and {prize.label} do not make a reasonable pair for this living-room tale.)"


CURATED = [
    StoryParams(activity="synthesize", prize="hat", name="Maya", gender="girl", parent="mother"),
    StoryParams(activity="hint", prize="puzzle", name="Theo", gender="boy", parent="father"),
]


KNOWLEDGE_ORDER = ["synthesize", "chic", "hint", "curiosity", "moral"]


ASP_RULES = r"""
activity(synthesize;hint).
prize(hat;puzzle;crown).
trait(hat,chic).
trait(puzzle,curious).
trait(crown,chic).

valid(A,P) :- activity(A), prize(P), trait(P,chic), A = synthesize.
valid(A,P) :- activity(A), prize(P), trait(P,curious), A = hint.
#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("trait", p, PRIZES[p].trait))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - asp_set))
    print("asp only:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale-style living-room storyworld about Curiosity and Moral Value.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        prize = PRIZES[args.prize]
        if not can_story(act, prize):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.activity is None or c[0] == args.activity)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(activity=activity, prize=prize, name=name, gender=gender, parent=parent)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for a, p in combos:
            print(f"  {a:12} {p}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
