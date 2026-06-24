#!/usr/bin/env python3
"""
storyworlds/worlds/brang_hideous_suspense_inner_monologue_fairy_tale.py
=======================================================================

A small fairy-tale storyworld about suspense, an anxious inner monologue, and
a gentle compromise around the brang of a bell.

Seed tale sketch:
---
A little child in a moonlit village hears a brang from the old bell tower.
Below the tower lives a hideous goblin who hates loud sounds and has locked the
ladder gate. The child wants to ring the bell so the lost fairy can find her way
home, but the child worries the noise may wake the sleeping giant in the hill.

The child thinks and thinks, then chooses a softer plan: they wrap the bell
clapper with ribbon, ring it carefully, and guide the fairy home without waking
the giant.

World model:
---
    loud action -> sound meter rises, suspense rises
    suspense + worry -> inner monologue becomes visible
    soft compromise -> sound stays low, fear falls, hope rises
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["sound", "suspense", "fear", "hope", "worry", "joy"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "queen", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "king", "goblin", "giant"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    sound: str
    suspense: str
    weather: str
    keyword: str = ""
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
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["sound"] < THRESHOLD:
            continue
        if e.memes["fear"] < THRESHOLD:
            continue
        sig = ("suspense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["suspense"] += 1
        out.append("The hush grew tight with suspense.")
    return out


def _r_inner_monologue(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("hero")
    if not child or child.memes["worry"] < THRESHOLD or child.memes["suspense"] < THRESHOLD:
        return out
    sig = ("monologue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__monologue__")
    return out


CAUSAL_RULES = [_r_suspense, _r_inner_monologue]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule(world)
            if res:
                changed = True
                produced.extend(x for x in res if x != "__monologue__")
    if narrate:
        for s in produced:
            world.say(s)


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"too_loud": prize.meters["sound"] >= THRESHOLD, "fear": prize.memes["fear"]}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot host {activity.id}.)")
    actor.meters["sound"] += 1
    actor.memes["hope"] += 1
    actor.memes["suspense"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "tower": Setting(place="the old bell tower", affords={"ring_bell"}),
    "bridge": Setting(place="the moon bridge", affords={"cross_bridge"}),
    "garden": Setting(place="the fairy garden", affords={"find_fairy"}),
}

ACTIVITIES = {
    "ring_bell": Activity(
        id="ring_bell",
        verb="ring the bell",
        gerund="ringing the bell",
        rush="run to the bell rope",
        sound="brang",
        suspense="trembling suspense",
        weather="night",
        keyword="brang",
        tags={"brang", "bell"},
    ),
    "cross_bridge": Activity(
        id="cross_bridge",
        verb="cross the moon bridge",
        gerund="crossing the moon bridge",
        rush="dash onto the bridge",
        sound="creak",
        suspense="soft suspense",
        weather="night",
        keyword="moon",
        tags={"moon", "bridge"},
    ),
    "find_fairy": Activity(
        id="find_fairy",
        verb="look for the fairy",
        gerund="looking for the fairy",
        rush="hurry through the flowers",
        sound="rustle",
        suspense="gentle suspense",
        weather="night",
        keyword="fairy",
        tags={"fairy", "flowers"},
    ),
}

PRIZES = {
    "bell": Prize(label="bell", phrase="an old brass bell", type="bell", region="hands"),
    "lantern": Prize(label="lantern", phrase="a tiny lantern", type="lantern", region="hands"),
    "ribbon": Prize(label="ribbon", phrase="a silk ribbon", type="ribbon", region="hands"),
}

GEAR = [
    Gear(
        id="soft_ribbon",
        label="a soft ribbon",
        guards={"brang"},
        prep="tie a soft ribbon around the clapper",
        tail="tied the ribbon and rang the bell gently",
    ),
    Gear(
        id="quiet_slippers",
        label="quiet slippers",
        guards={"creak"},
        prep="put on quiet slippers",
        tail="stepped across without a loud creak",
    ),
]

GIRL_NAMES = ["Mina", "Lina", "Nora", "Elsa", "Ivy", "Pippa"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Milo", "Eli", "Jasper"]
TRAITS = ["brave", "gentle", "curious", "tiny", "careful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if act_id == "ring_bell" and prize_id == "bell":
                    combos.append((place, act_id, prize_id))
                if act_id == "cross_bridge" and prize_id == "lantern":
                    combos.append((place, act_id, prize_id))
                if act_id == "find_fairy" and prize_id == "ribbon":
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world of brang, suspense, and a soft inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    hero.memes["worry"] += 1
    hero.memes["suspense"] += 1
    helper = world.add(Entity(id="helper", kind="character", type="fairy", label="the fairy"))
    guardian = world.add(Entity(id="guardian", kind="character", type="goblin", label="the hideous goblin"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase))
    gear = None

    act = ACTIVITIES[params.activity]

    world.say(f"Once upon a time, little {params.name} went to {world.setting.place}.")
    world.say(f"The night was still, but {params.name} heard a {act.sound} — brang! — from far away.")
    world.say(f"Inside {params.name}'s own head, a small voice whispered, 'What if the sound wakes the hideous goblin?'")
    world.para()

    world.say(f"{params.name} wanted to {act.verb}, because the lost fairy could then find the way home.")
    world.say(f"But {params.name} also feared the giant sleeping in the hill, and the worry made {params.name}'s heart thump.")
    world.say(f"The hideous goblin stood by the gate and frowned at every loud noise.")
    hero.meters["sound"] += 1
    hero.memes["fear"] += 1
    propagate(world, narrate=True)
    world.para()

    if params.activity == "ring_bell":
        gear = world.add(Entity(id="ribbon", type="ribbon", label="a soft ribbon", protective=True))
        gear.worn_by = hero.id
        world.say(f"Then {params.name} saw a soft ribbon on the table.")
        world.say(f"{params.name} thought, 'If I tie that around the bell, maybe I can make a brang that is kind, not loud.'")
        world.say(f"So {params.name} decided to {GEAR[0].prep}.")
        hero.memes["hope"] += 1
        hero.meters["sound"] = 0.5
        world.say(f"The bell gave only a tiny brang, and the fairy listened closely.")
        world.say(f"The hideous goblin did not wake, and the giant kept sleeping in the hill.")
        world.say(f"The fairy smiled, and {params.name} felt the worry melt into joy.")
        hero.memes["joy"] += 1
    elif params.activity == "cross_bridge":
        gear = world.add(Entity(id="slippers", type="slippers", label="quiet slippers", protective=True))
        gear.worn_by = hero.id
        world.say(f"Then {params.name} put on quiet slippers and thought, 'If I step softly, the bridge will not complain.'")
        world.say(f"So {params.name} crossed the moon bridge without a creak, and the lantern shone like a small star.")
        hero.memes["hope"] += 1
        hero.memes["joy"] += 1
    else:
        gear = world.add(Entity(id="ribbon", type="ribbon", label="a silk ribbon", protective=True))
        gear.worn_by = hero.id
        world.say(f"Then {params.name} held the silk ribbon up and thought, 'A gentle thing can guide a gentle fairy.'")
        world.say(f"{params.name} followed the ribbon through the flowers until the fairy came out smiling.")
        hero.memes["hope"] += 1
        hero.memes["joy"] += 1

    world.facts = {
        "hero": hero,
        "helper": helper,
        "guardian": guardian,
        "prize": prize,
        "gear": gear,
        "activity": act,
        "params": params,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    act = world.facts["activity"]
    return [
        f'Write a fairy-tale story for a young child that includes the word "{act.keyword}".',
        f"Tell a suspenseful but gentle story about {p.name} who wants to {act.verb} and has an inner monologue of worry.",
        f"Write a short fairy tale where a child hears a {act.sound} and finds a safer way to finish the job.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    act = world.facts["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about little {p.name}, a {p.trait} {p.gender} who visits {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} want to do?",
            answer=f"{p.name} wanted to {act.verb}, because the lost fairy needed help finding the way home.",
        ),
        QAItem(
            question=f"Why was the moment suspenseful?",
            answer=f"It felt suspenseful because {p.name} worried the loud {act.sound} would wake the hideous goblin and the sleeping giant.",
        ),
        QAItem(
            question=f"What did {p.name} think inside their head?",
            answer=f"{p.name} thought, 'What if the sound wakes the hideous goblin?' and then looked for a gentler plan.",
        ),
    ]
    if world.facts.get("gear"):
        qa.append(
            QAItem(
                question="How did the child solve the problem?",
                answer="The child used a soft, careful trick — a gentle piece of gear — so the important thing could happen without making too much noise.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does brang mean in a fairy tale?", answer="Brang is a bright, ringing bell sound, like a bell being struck in a castle or tower."),
        QAItem(question="What does hideous mean?", answer="Hideous means very ugly or scary-looking."),
        QAItem(question="Why do people whisper in suspenseful stories?", answer="People whisper when they are worried or trying not to wake someone or make a scene."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
soundful(A) :- activity(A), says_sound(A).
suspenseful(X) :- character(X), fear(X), worries(X).
soft_fix(A,P) :- activity(A), prize(P), safe_combo(A,P).
valid_story(Place,A,P) :- affords(Place,A), safe_combo(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("says_sound", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    lines.append(asp.fact("safe_combo", "ring_bell", "bell"))
    lines.append(asp.fact("safe_combo", "cross_bridge", "lantern"))
    lines.append(asp.fact("safe_combo", "find_fairy", "ribbon"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_stories())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid stories ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams(place="tower", activity="ring_bell", prize="bell", name="Mina", gender="girl", trait="careful"),
    StoryParams(place="bridge", activity="cross_bridge", prize="lantern", name="Finn", gender="boy", trait="brave"),
    StoryParams(place="garden", activity="find_fairy", prize="ribbon", name="Ivy", gender="girl", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
