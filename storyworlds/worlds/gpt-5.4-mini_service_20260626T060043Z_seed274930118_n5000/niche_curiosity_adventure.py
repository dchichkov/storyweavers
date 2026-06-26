#!/usr/bin/env python3
"""
storyworlds/worlds/niche_curiosity_adventure.py
================================================

A standalone story world about a curious child, a niche discovery, and a
small adventure that turns safe and bright with the right help.

The seed image:
- a child notices a tiny niche hidden in an old place
- curiosity pulls them toward it
- there is a small risk: dust, darkness, or a narrow passage
- a helper offers a sensible adventure tool
- the child explores, learns something surprising, and comes back happier

This world keeps the prose close to adventure while staying child-facing and
constraint-checked. The simulated state tracks both physical meters and emotional
memes, and the story grows from those changes rather than from a fixed paragraph
template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("dusty", "dark", "scuffed", "safe", "found"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "fear", "joy", "wonder", "pride", "care"):
            self.memes.setdefault(k, 0.0)

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
    outdoor: bool
    affords: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    turn: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "museum": Setting(
        place="the old museum",
        outdoor=False,
        affords={"peek", "explore", "discover"},
        detail="The halls were quiet, and a sleepy lantern glowed beside a stone wall.",
    ),
    "library": Setting(
        place="the little library",
        outdoor=False,
        affords={"peek", "explore", "discover"},
        detail="Tall shelves leaned overhead, and a dusty reading nook hid in the corner.",
    ),
    "garden": Setting(
        place="the moon garden",
        outdoor=True,
        affords={"peek", "explore", "discover"},
        detail="The path wound past ferns, and a curved stone wall made a tiny shadowy niche.",
    ),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek into the niche",
        gerund="peeking into the niche",
        rush="run to the wall",
        risk="the niche could be dark and dusty",
        turn="the niche opened into a surprising little hiding place",
        keyword="niche",
        tags={"niche", "curiosity", "dust"},
    ),
    "explore": Activity(
        id="explore",
        verb="explore the niche",
        gerund="exploring the niche",
        rush="tiptoe into the corner",
        risk="the narrow space could feel strange and scary",
        turn="the niche held a tiny treasure and a neat old clue",
        keyword="niche",
        tags={"niche", "curiosity", "dark"},
    ),
    "discover": Activity(
        id="discover",
        verb="discover what the niche hid",
        gerund="discovering what the niche hid",
        rush="climb closer to the wall",
        risk="the hidden space might be too dusty to enter safely",
        turn="the niche revealed a small map tucked behind a stone",
        keyword="niche",
        tags={"niche", "curiosity", "map"},
    ),
}

TOOLS = [
    Tool(
        id="lantern",
        label="a small lantern",
        phrase="a small lantern with a warm yellow glow",
        prep="bring a small lantern first",
        tail="walked back with the lantern shining softly",
        guards={"dark"},
        covers={"eyes"},
    ),
    Tool(
        id="mask",
        label="a soft dust mask",
        phrase="a soft dust mask with a stretchy band",
        prep="put on a soft dust mask first",
        tail="came back with the dust mask in place",
        guards={"dust"},
        covers={"nose"},
    ),
    Tool(
        id="gloves",
        label="a pair of little gloves",
        phrase="a pair of little gloves with bright fingertips",
        prep="slip on a pair of little gloves first",
        tail="returned with the gloves ready for climbing",
        guards={"dust", "scratch"},
        covers={"hands"},
        plural=True,
    ),
]

HERO_NAMES = ["Mina", "Leo", "Tia", "Nico", "Zara", "Ben", "Ivy", "Owen"]
TRAITS = ["curious", "brave", "quiet", "bright", "careful", "spirited"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, act) for place, s in SETTINGS.items() for act in s.affords]


def reasonable(activity: Activity) -> bool:
    return "curiosity" in activity.tags


def select_tool(activity: Activity) -> Optional[Tool]:
    if activity.id == "peek":
        return next((t for t in TOOLS if "dark" in t.guards), None)
    if activity.id == "explore":
        return next((t for t in TOOLS if "dust" in t.guards and "dark" in t.guards), None)
    if activity.id == "discover":
        return next((t for t in TOOLS if "dust" in t.guards), None)
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A curious adventure around a hidden niche.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
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
    if args.activity:
        act = ACTIVITIES[args.activity]
        if not reasonable(act):
            raise StoryError("That activity is not curious enough for this world.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def _pronoun_gender(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def story_name_to_type(gender: str) -> str:
    return _pronoun_gender(gender)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    act = ACTIVITIES[params.activity]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=story_name_to_type(params.gender), traits=[params.trait, "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    niche = world.add(Entity(id="niche", type="place", label="the niche", phrase="a tiny niche in the wall"))
    tool = select_tool(act)

    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} was a {params.trait} little {hero.type} who loved noticing secret places."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a special eye for a niche, a tiny hiding spot that seemed to whisper, "
        f"“Come look closer.”"
    )
    world.say(
        f"At {setting.place}, {setting.detail.lower()}"
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, and {hero.pronoun('possessive')} feet had already started {act.gerund}."
    )

    world.para()
    if act.id == "peek":
        hero.meters["dark"] += 1
    elif act.id == "explore":
        hero.meters["dark"] += 1
        hero.meters["dusty"] += 1
    else:
        hero.meters["dusty"] += 1

    parent.say = None  # no-op guard for editors; not used

    world.say(
        f"But {hero.pronoun('possessive')} {params.parent} saw the spot and worried. "
        f"{act.risk.capitalize()}."
    )

    if tool is None:
        raise StoryError("No sensible tool exists for this adventure.")
    world.say(
        f'"Then let us {tool.prep}," {hero.pronoun("possessive")} {params.parent} said.'
    )

    hero.memes["fear"] += 0.5
    hero.meters["safe"] += 1
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        protective=True,
        plural=tool.plural,
    ))
    tool_ent.worn_by = hero.id

    world.para()
    hero.memes["joy"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["pride"] += 1
    niche.meters["found"] += 1

    if act.id == "peek":
        world.say(
            f"{hero.id} went back with the lantern shining softly. {hero.pronoun().capitalize()} peered in, and "
            f"{act.turn}."
        )
    elif act.id == "explore":
        world.say(
            f"{hero.id} came back with the lantern glowing and the dust mask on. {hero.pronoun().capitalize()} slipped inside, "
            f"and {act.turn}."
        )
    else:
        world.say(
            f"{hero.id} returned with the dust mask ready. {hero.pronoun().capitalize()} found the hidden place, and "
            f"{act.turn}."
        )

    world.say(
        f"{hero.id} grinned at {hero.pronoun('possessive')} {params.parent}. {hero.pronoun().capitalize()} had found something small and special, "
        f"and the niche did not feel scary anymore."
    )

    world.facts.update(hero=hero, parent=parent, activity=act, setting=setting, tool=tool, niche=niche)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    return [
        f'Write a short adventure story for a small child that uses the word "niche" and shows curiosity.',
        f"Tell a gentle adventure about {hero.id}, who wants to {act.verb} while {hero.pronoun('possessive')} {parent.type} helps with a safe tool.",
        f"Write a story where a curious child finds a niche, pauses to listen, and comes back with something surprising.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, tool, niche = f["hero"], f["parent"], f["activity"], f["tool"], f["niche"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}. {hero.pronoun().capitalize()} was curious about the niche in the wall.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.type} worry?",
            answer=f"{hero.pronoun('possessive').capitalize()} {parent.type} worried because {act.risk}. The niche was interesting, but it needed a careful plan.",
        ),
        QAItem(
            question=f"What helped {hero.id} explore safely?",
            answer=f"{tool.phrase.capitalize()} helped {hero.id} go back to the niche safely. It made the adventure feel brave instead of risky.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"{hero.id} came back smiling because the niche had a surprise inside, and {hero.pronoun('possessive')} {parent.type} was happy too.",
        ),
    ]


KNOWLEDGE = {
    "niche": [
        ("What is a niche?", "A niche is a small hollow space or corner in a wall, shelf, or rock where something can fit snugly."),
    ],
    "curiosity": [
        ("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn about something new."),
    ],
    "dark": [
        ("Why do people use a lantern in the dark?", "A lantern makes a little light so you can see where you are going and avoid bumping into things."),
    ],
    "dust": [
        ("Why can dust make you sneeze?", "Dust has tiny bits floating in the air, and those bits can tickle your nose and make you sneeze."),
    ],
    "map": [
        ("What is a map for?", "A map is a picture that shows places and paths, so you can find your way."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ("niche", "curiosity", "dark", "dust", "map"):
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
niche_story(P,A) :- setting(P), activity(A), affords(P,A).
curious(A) :- activity(A), tags(A,curiosity).
reasonable(P,A) :- niche_story(P,A), curious(A).
#show niche_story/2.
#show reasonable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", aid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {(p, a) for p, a in valid_combos() if reasonable(ACTIVITIES[a])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
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
    StoryParams(place="museum", activity="peek", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="library", activity="explore", name="Leo", gender="boy", parent="father", trait="brave"),
    StoryParams(place="garden", activity="discover", name="Ivy", gender="girl", parent="mother", trait="careful"),
]


def build_sample_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        combos = sorted(set(asp.atoms(model, "reasonable")))
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(f"  {combo[0]} {combo[1]}")
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
            try:
                params = build_sample_from_args(args, random.Random(seed))
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
