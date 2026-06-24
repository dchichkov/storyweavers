#!/usr/bin/env python3
"""
A small heartwarming storyworld about keeping a kitten, with foreshadowing
built into the simulated state.

Premise:
- A child wants to keep a kitten nearby.
- A small "tab" (a tug-tab on a toy blanket or soft bed) matters later.
- Early clues foreshadow that the tab will help the kitten feel safe and stay put.
- The ending resolves in a gentle, affectionate way.

The simulation tracks:
- physical meters: cozy, tired, hungry, safe, nosiness, pulled
- emotional memes: love, worry, relief, trust, delight

ASP twin:
- A Python reasonableness gate and inline ASP rules both validate the same
  compatible story choices.
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

# ---------------------------------------------------------------------------
# Entities / world model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    hint: str
    outcome: str
    foreshadow: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    ending: str
    helps_with: set[str] = field(default_factory=set)


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting("the nursery", {"keep", "snuggle", "hide", "settle"}),
    "porch": Setting("the sunny porch", {"keep", "snuggle", "hide"}),
    "bedroom": Setting("the bedroom", {"keep", "snuggle", "hide", "settle"}),
}

ACTIVITIES = {
    "keep": Activity(
        id="keep",
        verb="keep the kitten nearby",
        gerund="keeping the kitten nearby",
        hint="the kitten would not want to wander far",
        outcome="stayed close and cozy",
        foreshadow="A little tug-tab on the blanket kept flipping up when the kitten kneaded it.",
        mess="moved",
        tags={"kitten", "tab", "cozy"},
    ),
    "snuggle": Activity(
        id="snuggle",
        verb="snuggle with the kitten",
        gerund="snuggling with the kitten",
        hint="the kitten liked warm laps and soft fabric",
        outcome="fell asleep in a warm pile",
        foreshadow="The blanket's tab made a tiny corner the kitten could hold with one paw.",
        mess="moved",
        tags={"kitten", "tab", "cozy"},
    ),
    "hide": Activity(
        id="hide",
        verb="hide the kitten's tab toy",
        gerund="hiding the tab toy",
        hint="the kitten would follow the soft tab like a tiny fishing line",
        outcome="found the toy by its little tab and calmed down",
        foreshadow="When the tab peeked from under the cushion, the kitten's ears pointed straight at it.",
        mess="moved",
        tags={"kitten", "tab"},
    ),
    "settle": Activity(
        id="settle",
        verb="settle the kitten into bed",
        gerund="settling the kitten into bed",
        hint="a tucked-in place would help after play",
        outcome="snugged under the blanket and purred",
        foreshadow="The stitched tab on the bedspread kept showing where the kitten should climb.",
        mess="moved",
        tags={"kitten", "tab", "cozy"},
    ),
}

PRIZES = {
    "kitten": Prize(
        id="kitten",
        label="kitten",
        phrase="a tiny gray kitten",
        type="kitten",
        region="lap",
        genders={"girl", "boy"},
    ),
}

TOOLS = {
    "blanket": Tool(
        id="blanket",
        label="blanket with a tab",
        prep="tuck the kitten into the blanket and keep the tab where it could find it",
        ending="They tucked the blanket snugly around the kitten, and the little tab stayed easy to paw.",
        helps_with={"keep", "snuggle", "settle"},
    ),
    "tabtoy": Tool(
        id="tabtoy",
        label="a soft tab toy",
        prep="let the kitten chase the soft tab toy first",
        ending="The soft tab toy made one last soft swish, and the kitten curled up beside it.",
        helps_with={"hide", "keep"},
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Nora", "Eva", "Zoe", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Sam", "Finn", "Theo"]
TRAITS = ["gentle", "careful", "kind", "patient", "quiet", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    tool: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                # For this world, all listed activities are valid with the kitten,
                # but only if some tool can support the foreshadowed resolution.
                if any(act_id in tool.helps_with for tool in TOOLS.values()):
                    combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(place: str, activity: str, prize: str) -> str:
    return (
        f"(No story: {activity} at {place} does not leave room for a gentle "
        f"foreshadowing payoff with the {prize}. Pick an activity that has a "
        f"matching tab-themed tool.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: a {PRIZES[prize_id].label} is not gendered here; any child can keep one.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, kitten: Entity, tool: Tool) -> None:
    world.say(
        f"{child.id} was a {next(t for t in ['gentle','careful','kind','patient','quiet','bright'] if t == world.facts['trait'])} {child.type} who loved the tiny kitten."
    )
    world.say(
        f"The kitten liked soft places best, especially things with a little tab to tug."
    )
    world.say(
        f"That was why {child.id} kept noticing the {tool.label} before anything else."
    )


def foreshadow(world: World, kitten: Entity, activity: Activity, tool: Tool) -> None:
    world.say(activity.foreshadow)
    kitten.memes["curiosity"] = kitten.memes.get("curiosity", 0.0) + 1
    kitten.memes["trust"] = kitten.memes.get("trust", 0.0) + 0.5


def tension(world: World, child: Entity, kitten: Entity, activity: Activity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"At first, {child.id} worried the kitten might wander off while everyone was busy."
    )
    world.say(
        f"But {child.pronoun().capitalize()} also knew the kitten loved {activity.hint}."
    )


def resolve(world: World, child: Entity, kitten: Entity, activity: Activity, tool: Tool) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["love"] = child.memes.get("love", 0.0) + 1
    kitten.meters["safe"] = kitten.meters.get("safe", 0.0) + 1
    kitten.meters["cozy"] = kitten.meters.get("cozy", 0.0) + 1
    world.say(
        f"Then {child.id} used the {tool.label} just the way it was meant to be used."
    )
    world.say(
        f"{tool.ending} The kitten purred, and {child.id} smiled at the soft little tab."
    )
    world.say(
        f"In the end, the kitten stayed {activity.outcome}, and the room felt warm and peaceful."
    )


def scene(world: World, child: Entity, kitten: Entity, activity: Activity, tool: Tool) -> None:
    world.say(f"{child.id} and the kitten were in {world.setting.place}.")
    world.say(f"{child.id} wanted to {activity.verb}, and {child.pronoun('possessive')} heart felt full.")
    foreshadow(world, kitten, activity, tool)
    tension(world, child, kitten, activity)
    world.para()
    resolve(world, child, kitten, activity, tool)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
valid(Place, Act, Prize) :- affords(Place, Act), prize(Prize), tool(T), helps(T, Act), prize(Prize).
valid_story(Place, Act, Prize, Gender) :- valid(Place, Act, Prize), wears(Gender, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        for g in sorted(PRIZES[pid].genders):
            lines.append(asp.fact("wears", g, pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about "{f["name"]}" keeping a kitten safe, with an early clue about a tab.',
        f"Tell a gentle story where a child named {f['name']} and a kitten are helped by a small tab on a soft thing.",
        f"Write a short story for a young child that foreshadows how a tab will help a kitten feel safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    kitten: Entity = f["kitten"]
    activity: Activity = f["activity"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who is keeping the kitten in this story?",
            answer=f"{child.id} is keeping the kitten close, because {child.pronoun('subject')} cares about the little cat and wants {kitten.pronoun('object')} to feel safe.",
        ),
        QAItem(
            question=f"What small thing was hinted at before the ending?",
            answer=f"The story foreshadowed the tab on the {tool.label}. That little tab mattered later when {child.id} used it to help the kitten settle.",
        ),
        QAItem(
            question=f"What did the kitten do at the end?",
            answer=f"The kitten stayed {activity.outcome} and purred in a warm, quiet place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kitten?",
            answer="A kitten is a baby cat. Kittens are small, curious, and they like warm, safe places.",
        ),
        QAItem(
            question="What is a tab on a blanket or toy?",
            answer="A tab is a small piece of fabric that sticks out a little, so tiny hands or paws can tug or hold it.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a small clue early on about something that will matter later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Sampling / generation
# ---------------------------------------------------------------------------

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act = ACTIVITIES[args.activity]
        if args.activity not in next(iter(SETTINGS.values())).affords:
            raise StoryError(explain_rejection(args.place or "the nursery", args.activity, args.prize))
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(SETTINGS[place].affords))
    prize = args.prize or "kitten"
    if args.gender and args.gender not in PRIZES[prize].genders:
        raise StoryError(explain_gender(prize, args.gender))
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS) if hasattr(args, "trait") else rng.choice(TRAITS)
    tool = args.tool or rng.choice([t.id for t in TOOLS.values() if activity in t.helps_with])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait, tool=tool)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    tool = TOOLS[params.tool]

    if params.activity not in setting.affords:
        raise StoryError(explain_rejection(params.place, params.activity, params.prize))
    if params.gender not in prize.genders:
        raise StoryError(explain_gender(params.prize, params.gender))
    if params.activity not in tool.helps_with:
        raise StoryError("(No story: the selected tab tool does not support this gentle resolution.)")

    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    kitten = world.add(Entity(id="kitten", kind="character", type="kitten"))
    prize_ent = world.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=child.id, plural=prize.plural))
    tool_ent = world.add(Entity(id=tool.id, type="thing", label=tool.label))
    world.facts.update(name=params.name, trait=params.trait, child=child, kitten=kitten, prize=prize_ent, activity=activity, tool=tool_ent)

    world.say(f"{child.id} was a {params.trait} {params.gender} who loved a tiny kitten.")
    world.say(f"The kitten had a habit of noticing every soft tab it could see.")
    world.para()
    scene(world, child, kitten, activity, tool)
    world.facts["resolved"] = True

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


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
    ap = argparse.ArgumentParser(description="Heartwarming kitten storyworld with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


CURATED = [
    StoryParams(place="nursery", activity="keep", prize="kitten", name="Mia", gender="girl", trait="gentle", tool="blanket"),
    StoryParams(place="bedroom", activity="snuggle", prize="kitten", name="Noah", gender="boy", trait="kind", tool="blanket"),
    StoryParams(place="porch", activity="hide", prize="kitten", name="Lily", gender="girl", trait="careful", tool="tabtoy"),
    StoryParams(place="nursery", activity="settle", prize="kitten", name="Ben", gender="boy", trait="patient", tool="blanket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
                params.seed = seed
                sample = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
