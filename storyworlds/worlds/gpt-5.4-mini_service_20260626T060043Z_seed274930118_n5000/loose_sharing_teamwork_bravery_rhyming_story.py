#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/loose_sharing_teamwork_bravery_rhyming_story.py
========================================================================================================

A standalone story world for a small rhyming tale about something loose,
with sharing, teamwork, and bravery at the center.

Seed tale:
---
A little child notices a loose shoelace before a fun day of sharing treats.
The child wants to dash off anyway, but a parent warns that a tumble could
spoil the trip. A friend shares a bright ribbon, everyone works together to
tie a neat bow, and the child bravely goes on to share the goodies.

World model:
---
A loose, trailing lace can snag during a dash, making a fall likely.
Sharing a spare ribbon and tying it together prevents the fall.
Bravery shows up as asking for help and trying again.
Teamwork shows up as two helpers fixing the lace and one child choosing a slower, safer step.

Rhyming style:
---
The prose is kept child-facing and lightly rhymed, with concrete actions
driving the state changes rather than frozen description.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

RHYME_ENDINGS = {
    "night": "bright",
    "day": "play",
    "way": "stay",
    "light": "bright",
    "tale": "trail",
    "near": "cheer",
    "glow": "show",
}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "work": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "bravery": 0.0, "sharing": 0.0, "teamwork": 0.0}

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
    rush: str
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "playground": Setting(place="the playground", affords={"dash"}),
    "schoolyard": Setting(place="the schoolyard", affords={"dash"}),
    "market": Setting(place="the market square", affords={"dash"}),
}

ACTIVITIES = {
    "dash": Activity(
        id="dash",
        verb="dash to the snack stand",
        gerund="dashing to the snack stand",
        rush="run too fast toward the snacks",
        risk="a trip on the loose lace",
        weather="clear",
        keyword="loose",
        tags={"loose", "sharing", "teamwork", "bravery"},
    ),
}

PRIZES = {
    "shoelace": Prize(
        label="shoelace",
        phrase="a loose red shoelace",
        type="shoelace",
        region="feet",
    ),
    "ribbon": Prize(
        label="ribbon",
        phrase="a loose blue ribbon",
        type="ribbon",
        region="feet",
    ),
    "sash": Prize(
        label="sash",
        phrase="a loose yellow sash",
        type="sash",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="bow",
        label="a neat bow",
        covers={"feet"},
        guards={"trip"},
        prep="share the ribbon and tie a neat bow",
        tail="shared the ribbon and tied it into a neat bow",
    ),
    Gear(
        id="knot",
        label="a snug knot",
        covers={"feet"},
        guards={"trip"},
        prep="work together to make a snug knot",
        tail="worked together and made a snug knot",
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Rosa"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Sam"]
TRAITS = ["brave", "kind", "cheery", "gentle", "spry"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"feet", "torso"} and activity.id == "dash"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if not prize_at_risk(activity, prize):
        return None
    return GEAR[0] if prize.region == "feet" else None


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def _r_trip(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        if actor.memes["bravery"] >= THRESHOLD and actor.memes["teamwork"] >= THRESHOLD:
            continue
        sig = ("trip", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append(f"The loose lace could snag and send {actor.id} in a spin.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.type not in {"ribbon"}:
            continue
        if item.meters.get("shared", 0.0) < THRESHOLD:
            continue
        sig = ("share", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The ribbon was shared, and the room felt warm and bright.")
    return out


CAUSAL_RULES = [Rule("trip", _r_trip), Rule("share", _r_share)]


def predict(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["risk"] += 1
    propagate(sim, narrate=False)
    return {"trip": True, "fear": sim.get(actor.id).memes["fear"]}


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------
def choose_rhyme(word: str) -> str:
    return RHYME_ENDINGS.get(word, "glow")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"joy": 0.0, "fear": 0.0, "bravery": 0.0, "sharing": 0.0, "teamwork": 0.0}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=parent_type))
    friend = world.add(Entity(id="friend", kind="character", type="boy", label="friend"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    ribbon = world.add(Entity(
        id="ribbon", type="ribbon", label="ribbon", phrase="a bright spare ribbon",
        owner=friend.id, caretaker=friend.id
    ))
    hero.worn_by = None

    world.say(f"{hero.id} was a {trait} child with a grin, so bright,")
    world.say(f"With {prize.phrase} on {hero.pronoun('possessive')} feet, like a little dawn light.")
    world.say(f"{hero.id} loved {activity.gerund}, and loved it with glee,")
    world.say(f"for sharing sweet treats was the plan of the day, you see.")

    world.para()
    world.say(f"At {setting.place}, the path was a-sparkle, the air felt alive,")
    world.say(f"but {hero.id} wanted to {activity.verb}, ready to dive.")
    hero.meters["risk"] += 1
    hero.memes["joy"] += 1
    world.say(f"{parent_type.capitalize()} said, “Careful, dear child, that lace is loose and might slide;")
    world.say(f"one tumble could spoil the fun of your ride.”")

    world.para()
    world.say(f"{hero.id} paused, then smiled with some bravery near,")
    hero.memes["bravery"] += 1
    world.say(f"“I can ask for help,” {hero.id} said, bold and clear.")
    friend.memes["sharing"] += 1
    friend.memes["teamwork"] += 1
    ribbon.meters["shared"] = 1.0
    world.say(f"{friend.id} shared a ribbon so shiny and neat,")
    world.say(f"and {parent_type} helped tie it snug at {hero.id}'s feet.")
    gear = select_gear(activity, prize)
    if gear:
        world.say(f"They {gear.tail}, and the knot held tight,")
    world.say(f"so {hero.id} could go on in a slow, careful light.")
    hero.memes["teamwork"] += 1
    hero.memes["sharing"] += 1
    hero.memes["joy"] += 1

    world.para()
    world.say(f"Then off went {hero.id}, with a hop and a cheer,")
    world.say(f"to share the sweet snacks with the friends gathered near.")
    world.say(f"The loose lace stayed snug, and the day stayed bright;")
    world.say(f"bravery, sharing, and teamwork made everything right.")

    world.facts.update(
        hero=hero, parent=parent, friend=friend, prize=prize, ribbon=ribbon,
        activity=activity, setting=setting, trait=trait, gear=gear, resolved=True
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "loose": [
        ("What does loose mean?",
         "Loose means not tied or fastened tightly, so it can slip, wiggle, or fall free.")
    ],
    "sharing": [
        ("What is sharing?",
         "Sharing is when people let someone else use, have, or enjoy something together.")
    ],
    "teamwork": [
        ("What is teamwork?",
         "Teamwork means people help each other and work together to do a job.")
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery is being willing to face a scary or tricky moment and try anyway.")
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for little kids about "{f["activity"].keyword}" and a loose thing that needs help.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} but must slow down, share, and work together.",
        f'Write a child-friendly rhyme with sharing, teamwork, and bravery that ends with a loose lace being tied tight.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, friend, prize, activity = f["hero"], f["parent"], f["friend"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What was loose in the story?",
            answer=f"It was {prize.phrase}, which could snag if {hero.id} dashed too fast."
        ),
        QAItem(
            question=f"Why did {parent.type} warn {hero.id} before the dash?",
            answer=f"{parent.type.capitalize()} warned {hero.id} because the loose lace could trip {hero.pronoun('object')} and spoil the happy day."
        ),
        QAItem(
            question=f"How did {hero.id}, {friend.id}, and the parent solve the problem together?",
            answer=f"They shared a ribbon, worked together, and tied a snug bow so {hero.id} could go on safely."
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do?",
            answer=f"{hero.id} bravely slowed down and asked for help instead of rushing ahead alone."
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} went on to {activity.verb} and share the treats, with the lace held tight and safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["loose", "sharing", "teamwork", "bravery"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,P) :- dash(A), worn_on(P, feet).
compatible(A,P,G) :- at_risk(A,P), gear(G), covers(G, feet), guards(G, trip).
valid_story(S,A,P,G) :- setting(S), affords(S,A), at_risk(A,P), compatible(A,P,G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("dash", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    # Normalize python combos to the same tuple shape expected by valid_story
    py4 = set()
    for s, a, p in python_set:
        for g in ["girl", "boy"]:
            py4.add((s, a, p, g))
    if clingo_set == py4:
        print(f"OK: clingo gate matches Python set ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo-only:", sorted(clingo_set - py4))
    print("  python-only:", sorted(py4 - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for a in setting.affords:
            act = ACTIVITIES[a]
            for p, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((s, a, p))
    return combos


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about loose, sharing, teamwork, and bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not reasonably risk {prize.phrase}, so the warning would feel fake.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    prize_obj = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(prize_obj.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("playground", "dash", "shoelace", "Mia", "girl", "mother", "brave"),
            StoryParams("schoolyard", "dash", "ribbon", "Leo", "boy", "father", "kind"),
            StoryParams("market", "dash", "shoelace", "Ava", "girl", "mother", "cheery"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
