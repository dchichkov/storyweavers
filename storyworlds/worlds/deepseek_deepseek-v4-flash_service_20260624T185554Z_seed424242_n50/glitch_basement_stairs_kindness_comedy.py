#!/usr/bin/env python3
"""
storyworlds/worlds/glitch_basement_stairs_kindness_comedy.py
=============================================================

A light‑hearted TinyStories‑style world: a child discovers a glitchy step on the
basement stairs, and a parent’s kind silliness “fixes” it.

Domain: glitch · kindness · comedy
Setting: basement stairs

Sound: “Bloop!” “Boing!” “Giggle.”
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_glitch_bounce(world: World) -> list[str]:
    """When glitch level is high, the step makes a funny sound and reverses direction."""
    out: list[str] = []
    for e in world.entities.values():
        if e.type == "stairs" and e.meters["glitch"] >= THRESHOLD:
            sig = ("bounce", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["glitch"] -= 0.5   # partially used
            out.append("The step went BOING and the child bounced right back up!")
    return out


def _r_giggle_fix(world: World) -> list[str]:
    """Kindness (giggle) reduces glitch."""
    out: list[str] = []
    for e in world.entities.values():
        if e.type == "stairs" and e.memes["giggle"] >= THRESHOLD and e.meters["glitch"] > 0:
            sig = ("fix", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.meters["glitch"] -= 1.0
            out.append("The stairs tickled with laughter and the glitch faded a little!")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bounce", tag="comedy", apply=_r_glitch_bounce),
    Rule(name="fix", tag="kindness", apply=_r_giggle_fix),
]


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


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "basement_stairs": Setting(place="the basement stairs", indoor=True,
                               affords={"glitch"}),
}

ACTIVITIES = {
    "glitch": Activity(
        id="glitch",
        verb="go down to the basement",
        gerund="going down the stairs",
        rush="run down the stairs",
        mess="glitchy",
        soil="tangled in a glitch",
        zone={"feet"},
        weather="",
        keyword="glitch",
        tags={"glitch", "stairs"},
    ),
}

PRIZES = {
    "socks": Prize(
        label="socks",
        phrase="a pair of rainbow socks",
        type="socks",
        region="feet",
        plural=True,
    ),
}

GEAR = []   # No gear needed; kindness alone resolves.

GIRL_NAMES = ["Luna", "Maya", "Nora", "Zara"]
BOY_NAMES = ["Finn", "Leo", "Max", "Ollie"]
TRAITS = ["silly", "curious", "patient", "kind"]


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str]

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str
    tags: set[str]

@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    return None   # no gear, kindness fixes

GEAR = []   # placeholder

# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Luna", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting.place)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "silly"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    stairs = world.add(Entity(
        id="stairs", type="stairs", label="the basement stairs",
        meters={"glitch": 1.5},      # starts glitchy
        memes={"giggle": 0.0},
    ))

    # Act 1
    world.say(f"{hero_name} was a little {hero_type} who loved exploring.")
    world.say(f"One day, {hero_name} wanted to {activity.verb} to fetch {prize.label}.")
    world.say(f"{hero_name} wore {prize.phrase} and felt very brave.")

    world.para()
    world.say(f"{hero_name} stood at the top of {setting.place}.")
    world.say(f"The first step looked normal. The second step had a weird sparkle.")
    world.say(f"{hero_name} put one foot on the glitchy step.")

    # Act 2 - glitch activates
    world.say(f"BLIP! The step boinged and {hero_name} bounced up again!")
    world.say(f"'{hero_name} chuckled. \"That was funny!\"")
    stairs.meters["glitch"] += 1.0   # triggered
    propagate(world)

    # Act 3 - kindness
    world.para()
    world.say(f"Parent came to see what the noise was.")
    world.say(f"Parent saw the glitchy step and said, \"It needs a kindness code!\"")
    world.say(f"Parent started singing a silly song: \"Step, step, you silly step, let my child go down and get the treat!\"")
    world.say(f"{hero_name} laughed and joined the song.")
    stairs.memes["giggle"] += 2.0
    propagate(world)

    # Resolution
    world.para()
    world.say(f"The stairs let out a happy sigh and the sparkle disappeared.")
    world.say(f"{hero_name} walked down carefully, picked up {prize.label}, and waved from the bottom.")
    world.say(f"Parent smiled. \"Kindness and a funny tune fix any glitch!\"")
    world.say(f"{hero_name} wore the rainbow socks all day, and the stairs never glitched again.")

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting, gear=None,
        conflict=True, resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Params
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
    ap = argparse.ArgumentParser(
        description="Glitch Basement Stairs – a kindness comedy.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    # Only one combo exists
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place="basement_stairs",
        activity="glitch",
        prize="socks",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name, params.gender,
        [params.trait, "silly"],
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a funny short story for a child about a glitchy step on basement stairs.',
        f'Tell a story where {hero.name} learns that kindness and a silly song can fix a glitch.',
        f'Include the word "glitch" and a happy ending with a parent and child laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pos = hero.pronoun("possessive")
    return [
        QAItem(
            question=f"What happened when {hero.name} stepped on the glitchy stair?",
            answer=f"The step went BOING and {hero.name} bounced back up. It made a funny blip sound and {hero.name} laughed.",
        ),
        QAItem(
            question=f"How did the parent fix the glitch?",
            answer=f"The parent sang a silly kindness song with {hero.name}. The stairs giggled and the glitch disappeared.",
        ),
        QAItem(
            question=f"What did {hero.name} wear that day?",
            answer=f"{hero.name} wore {prize.phrase} and felt very brave exploring the basement stairs.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a glitch?", "A glitch is a little mistake or a funny hiccup in something that should work smoothly, like a step that bounces when it shouldn't."),
        QAItem("Why does kindness help?", "Kindness and laughter can make scary or tricky things feel safe and fun. A silly song can turn a problem into a game."),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin (minimal, for contract)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Glitch step is at risk when activity splashes feet.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Kindness (giggle) fixes glitch.
fixes(G, A, P) :- gear(G), prize_at_risk(A, P),
                  mess_of(A, M), guards(G, M),
                  covers(G, R), worn_on(P, R).
has_fix(A, P) :- fixes(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in s.affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    # No gear in this world, so no guards/covers.
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    combos = set(asp.atoms(model, "valid"))
    # Python only one combo
    python_combos = {("basement_stairs", "glitch", "socks")}
    if combos == python_combos:
        print("OK: ASP matches Python")
        return 0
    print("MISMATCH")
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            if e.meters:
                print(f"  {e.id}: meters {dict(e.meters)}, memes {dict(e.memes)}")
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
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = asp.atoms(model, "valid")
        print(f"{len(combos)} compatible combo(s):")
        for c in combos:
            print(f"  {c[0]:20} {c[1]:10} {c[2]}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(resolve_params(args, random.Random(base_seed)))]
    else:
        seen = set()
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
        header = f"### Story {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
