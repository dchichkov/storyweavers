#!/usr/bin/env python3
"""
storyworlds/worlds/scrunch_boycott_appear_dialogue_bad_ending_animal.py
=======================================================================

A small animal-story world about a shared place, a boycott, a scrunched note,
and a bad ending.

Premise:
- Friendly animals gather at a field-side snack stall.
- They hear a warning that the stall is unfair.
- One animal scrunches the flyer.
- The animals decide to boycott the stall.

Turn:
- The stall owner appears and argues back.
- Dialogue escalates instead of fixing the problem.

Bad ending:
- The stall closes for the day.
- The animals go home hungry and grumpy.
- The scrunched flyer stays on the ground, and nothing feels repaired.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports shared result containers eagerly
- lazy ASP helper import inside ASP helpers
- build_parser / resolve_params / generate / emit / main
- includes inline ASP rules and a Python reasonableness gate
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    bearer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"rabbit", "hare", "doe", "cat", "mouse"}
        male = {"fox", "buck", "dog", "boar", "bear"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Stance:
    id: str
    label: str
    reason: str
    sign_text: str
    dialogue: str


@dataclass
class Stall:
    id: str
    label: str
    sells: str
    unfair: bool = True


@dataclass
class StoryParams:
    setting: str
    activity: str
    stance: str
    hero_name: str
    hero_type: str
    owner_name: str
    owner_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.setting)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "field": Setting(place="the windy field"),
    "barnyard": Setting(place="the barnyard"),
    "riverbank": Setting(place="the riverbank"),
}

ACTIVITIES = {
    "scrunch": Activity(
        id="scrunch",
        verb="scrunch the unfair flyer",
        gerund="scrunching the flyer",
        rush="scrunch the flyer tighter",
        mess="scrunched",
        soil="creased and muddy",
        keyword="scrunch",
        tags={"paper", "mess"},
    ),
    "boycott": Activity(
        id="boycott",
        verb="boycott the snack stall",
        gerund="boycotting the stall",
        rush="call everyone away from the stall",
        mess="silent",
        soil="left waiting",
        keyword="boycott",
        tags={"refusal", "stall"},
    ),
    "appear": Activity(
        id="appear",
        verb="watch the owner appear",
        gerund="watching the owner appear",
        rush="turn around when the owner appeared",
        mess="startled",
        soil="shaken",
        keyword="appear",
        tags={"dialogue", "owner"},
    ),
}

STANCES = {
    "fairness": Stance(
        id="fairness",
        label="fairness",
        reason="the stall gave small berries to some animals and tiny berries to others",
        sign_text="Fair treats for every critter!",
        dialogue="We won't buy snacks until it's fair.",
    ),
    "noise": Stance(
        id="noise",
        label="quiet",
        reason="the bell over the stall rang too loudly all morning",
        sign_text="Too loud for sleepy ears!",
        dialogue="We won't stand near the stall until it gets quiet.",
    ),
    "mud": Stance(
        id="mud",
        label="clean paws",
        reason="the path to the stall was slick with mud and the owner would not sweep it",
        sign_text="Please sweep the mud!",
        dialogue="We won't line up until the path is swept.",
    ),
}

STALLS = {
    "berries": Stall(id="berries", label="the berry stall", sells="sweet berries", unfair=True),
    "corncakes": Stall(id="corncakes", label="the corncake cart", sells="warm corncakes", unfair=True),
    "nuts": Stall(id="nuts", label="the nut basket", sells="salted nuts", unfair=True),
}

ANIMAL_TYPES = {
    "rabbit": {"boy", "girl"},
    "fox": {"boy", "girl"},
    "mouse": {"boy", "girl"},
    "hare": {"boy", "girl"},
    "cat": {"boy", "girl"},
    "badger": {"boy", "girl"},
}

NAMES = {
    "rabbit": ["Pip", "Mina", "Lulu", "Tansy"],
    "fox": ["Finn", "Ruby", "Sly", "Moss"],
    "mouse": ["Nip", "Wren", "Pico", "Dot"],
    "hare": ["Harey", "Bram", "Twitch", "Nora"],
    "cat": ["Tibi", "Momo", "Sasha", "Purl"],
    "badger": ["Bruno", "Mabel", "Toto", "June"],
}

TAGS_ORDER = ["paper", "mess", "refusal", "stall", "dialogue", "owner"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An activity is relevant if it touches the stall or the sign.
relevant(A) :- activity(A), keyword(A, K), (K = scrunch; K = boycott; K = appear).

% A boycott is reasonable if there is an unfair stall and a voiced reason.
good_reason(S) :- stance(S).
can_boycott(A, S, T) :- activity(A), stance(S), stall(T), unfair(T), good_reason(S).

% Scrunching and appearing are part of the same story when the owner arrives
% after the sign has been used.
storyline(scrunch, boycott, appear).

#show can_boycott/3.
#show storyline/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
    for sid, st in STANCES.items():
        lines.append(asp.fact("stance", sid))
        lines.append(asp.fact("reason", sid, st.reason))
    for tid, st in STALLS.items():
        lines.append(asp.fact("stall", tid))
        if st.unfair:
            lines.append(asp.fact("unfair", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_boycott/3.\n#show storyline/3."))
    atoms = set(asp.atoms(model, "can_boycott"))
    py = set(valid_combos())
    if atoms == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(atoms - py))
    print("  python:", sorted(py - atoms))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for act in ACTIVITIES:
            for stance in STANCES:
                if setting in {"field", "barnyard", "riverbank"} and act in {"scrunch", "boycott", "appear"}:
                    combos.append((setting, act, stance))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested options do not form a reasonable animal boycott story.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def pick_name(rng: random.Random, animal: str) -> str:
    return rng.choice(NAMES[animal])


def build_hero(world: World, animal_type: str, name: str) -> Entity:
    return world.add(Entity(
        id=name,
        kind="character",
        type=animal_type,
        label=name,
        meters={"hunger": 0.0, "tired": 0.0},
        memes={"worry": 0.0, "anger": 0.0, "hope": 0.0},
        tags={animal_type},
    ))


def build_owner(world: World, animal_type: str, name: str) -> Entity:
    return world.add(Entity(
        id=name,
        kind="character",
        type=animal_type,
        label=name,
        meters={"hunger": 0.0},
        memes={"pride": 1.0, "annoyed": 0.0},
        tags={animal_type},
    ))


def apply_bad_ending(world: World, hero: Entity, owner: Entity, stall: Stall, stance: Stance) -> None:
    hero.meters["hunger"] += 1
    hero.memes["worry"] += 1
    owner.memes["annoyed"] += 1
    world.facts["bad_end"] = True
    world.say(
        f"In the end, the boycott did not fix anything. "
        f"The {stall.label} stayed shut, {hero.label} went home hungry, "
        f"and {owner.label} only frowned more."
    )
    world.say(
        f"The scrunched flyer stayed in the grass, and nobody came back to sweep it up."
    )


def generate_story(world: World, hero: Entity, owner: Entity, stall: Stall, activity: Activity, stance: Stance) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.label} was a little {hero.type} who loved the morning market at {world.setting.place}."
    )
    world.say(
        f"{hero.label} liked {stall.sells}, but {stance.reason} made the little crowd grumble."
    )
    world.say(
        f'"{stance.dialogue}" {hero.label} said.'
    )
    hero.memes["anger"] += 1
    world.say(
        f"Then {hero.label} {activity.gerund} and rubbed the sign between two paws until it was wrinkled and small."
    )
    world.say(
        f'"I mean it," {hero.label} said. "No fair treats, no buying today."'
    )
    world.para()
    world.say(
        f"After that, {owner.label} appeared at the stall with a tight face and a long sigh."
    )
    world.say(
        f'"Who scrunched my flyer?" {owner.label} asked.'
    )
    world.say(
        f'"We did," said {hero.label}. "We are boycotting until it is fair."'
    )
    world.say(
        f'"Then no one gets snacks," {owner.label} snapped, and the basket was pulled inside.'
    )
    world.para()
    apply_bad_ending(world, hero, owner, stall, stance)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story with the words "{f["activity"].keyword}", "boycott", and "appear".',
        f"Tell a short dialogue-heavy story about {f['hero'].label} the {f['hero'].type} "
        f"who wants fair treats at {f['setting'].place}.",
        "Write a simple story in which an animal scrunches a sign, the owner appears, "
        "and the ending is sad.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    owner: Entity = f["owner"]
    stall: Stall = f["stall"]
    stance: Stance = f["stance"]
    activity: Activity = f["activity"]
    return [
        QAItem(
            question=f"Who was boycotting the stall in the story?",
            answer=f"{hero.label} the {hero.type} was boycotting {stall.label} because {stance.reason}.",
        ),
        QAItem(
            question=f"What did {hero.label} do to the sign?",
            answer=f"{hero.label} scrunched the flyer until it was wrinkled and small.",
        ),
        QAItem(
            question=f"What happened when the owner appeared?",
            answer=f"{owner.label} appeared, asked who scrunched the flyer, and got angry instead of fixing the problem.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended badly: {stall.label} stayed shut, {hero.label} went home hungry, "
                f"and the scrunched flyer stayed in the grass."
            ),
        ),
        QAItem(
            question=f"Why did the animals boycott the stall?",
            answer=f"They boycotted because {stance.reason}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    tags = set(f["activity"].tags) | {"dialogue", "stall"}
    if f.get("owner"):
        tags.add("owner")
    for tag in TAGS_ORDER:
        if tag in tags:
            if tag == "paper":
                out.append(QAItem(
                    question="What is a flyer?",
                    answer="A flyer is a small paper notice that tells people about something.",
                ))
            elif tag == "mess":
                out.append(QAItem(
                    question="Why can wrinkled paper look messy?",
                    answer="Wrinkled paper looks messy because it has folds and creases that are hard to smooth out.",
                ))
            elif tag == "refusal":
                out.append(QAItem(
                    question="What is a boycott?",
                    answer="A boycott is when people decide not to buy, use, or join something because they want a change.",
                ))
            elif tag == "stall":
                out.append(QAItem(
                    question="What is a stall?",
                    answer="A stall is a small place where someone sells food or other goods.",
                ))
            elif tag == "dialogue":
                out.append(QAItem(
                    question="What is dialogue in a story?",
                    answer="Dialogue is when characters speak to each other using quoted words.",
                ))
            elif tag == "owner":
                out.append(QAItem(
                    question="What does an owner do?",
                    answer="An owner is the person or animal who runs or takes care of something that belongs to them.",
                ))
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
# Validation and parameter resolution
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal boycott storyworld with dialogue and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--stance", choices=STANCES)
    ap.add_argument("--hero-type", dest="hero_type", choices=sorted(ANIMAL_TYPES))
    ap.add_argument("--owner-type", dest="owner_type", choices=sorted(ANIMAL_TYPES))
    ap.add_argument("--hero-name")
    ap.add_argument("--owner-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    stance = args.stance or rng.choice(list(STANCES))
    hero_type = args.hero_type or rng.choice(list(ANIMAL_TYPES))
    owner_type = args.owner_type or rng.choice(list(ANIMAL_TYPES))
    hero_name = args.hero_name or pick_name(rng, hero_type)
    owner_name = args.owner_name or pick_name(rng, owner_type)

    if (setting, activity, stance) not in valid_combos():
        raise StoryError(explain_rejection())

    return StoryParams(
        setting=setting,
        activity=activity,
        stance=stance,
        hero_name=hero_name,
        hero_type=hero_type,
        owner_name=owner_name,
        owner_type=owner_type,
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = build_hero(world, params.hero_type, params.hero_name)
    owner = build_owner(world, params.owner_type, params.owner_name)
    stall = STALLS["berries"]
    activity = ACTIVITIES[params.activity]
    stance = STANCES[params.stance]

    world.add(Entity(id=stall.id, kind="thing", type="stall", label=stall.label, phrase=stall.sells, tags={"stall"}))
    world.add(Entity(id="flyer", kind="thing", type="paper", label="flyer", phrase=stance.sign_text, tags={"paper"}))

    world.facts.update(
        hero=hero,
        owner=owner,
        stall=stall,
        stance=stance,
        activity=activity,
        setting=world.setting,
    )

    generate_story(world, hero, owner, stall, activity, stance)

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
        print()
        print("--- world model state ---")
        for ent in sample.world.entities.values():
            bits = []
            if ent.meters:
                bits.append(f"meters={ent.meters}")
            if ent.memes:
                bits.append(f"memes={ent.memes}")
            if ent.tags:
                bits.append(f"tags={sorted(ent.tags)}")
            print(f"  {ent.id}: {ent.type} {', '.join(bits)}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="field", activity="scrunch", stance="fairness", hero_name="Pip", hero_type="rabbit", owner_name="Moss", owner_type="fox"),
    StoryParams(setting="barnyard", activity="boycott", stance="noise", hero_name="Nip", hero_type="mouse", owner_name="Ruby", owner_type="cat"),
    StoryParams(setting="riverbank", activity="appear", stance="mud", hero_name="Tansy", hero_type="hare", owner_name="Bruno", owner_type="badger"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_boycott/3.\n#show storyline/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_boycott/3.\n#show storyline/3."))
        combos = sorted(set(asp.atoms(model, "can_boycott")))
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
