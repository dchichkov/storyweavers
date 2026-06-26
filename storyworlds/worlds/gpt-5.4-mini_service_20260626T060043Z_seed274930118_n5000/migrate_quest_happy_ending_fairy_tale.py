#!/usr/bin/env python3
"""
A fairy-tale storyworld about a small quest that helps a traveler migrate to a
safe new home with a happy ending.

The source tale behind this world:
- A young hero must migrate after their old home becomes unsafe.
- They set out on a quest to cross a forest, a river, and a hill.
- Along the way, a helpful guide and a magical token make the journey possible.
- The ending is joyful: the hero reaches a new home, and the village welcomes them.

This script turns that premise into a small simulation with physical meters and
emotional memes, a reasonableness gate, and an inline ASP twin.
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
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "maiden", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "boy-child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    safe: bool
    welcomes: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    name: str
    action: str
    travel: str
    obstacle: str
    hardship: str
    success: str
    keyword: str = "migrate"
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    title: str
    helps_with: set[str]
    offer: str
    tail: str


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    gives: str
    region: str = "heart"


class World:
    def __init__(self, place: Place):
        self.place = place
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

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def migrate_risk(place: Place, quest: Quest) -> bool:
    return not place.safe and "migrate" in quest.tags


def choose_guide(quest: Quest, place: Place) -> Optional[Guide]:
    for g in GUIDES:
        if quest.id in g.helps_with and place.id in g.helps_with:
            return g
    return None


def choose_token(quest: Quest, place: Place) -> Optional[Token]:
    for t in TOKENS:
        if quest.obstacle in t.protects_from and place.id in t.protects_from:
            return t
    return None


def _r_blessing(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("hope", 0) < THRESHOLD:
        return out
    sig = ("blessing", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    out.append("A brave light seemed to follow the traveler.")
    return out


def _r_resolve(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    token = world.entities.get("token")
    if not token or hero.memes.get("homeward", 0) < THRESHOLD:
        return out
    sig = ("resolve", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    out.append("The path ahead grew gentle and bright.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_r_blessing, _r_resolve):
            sents = fn(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


SETTINGS = {
    "lost-valley": Place("lost-valley", "the Lost Valley", safe=False, hazards={"flood"}),
    "dark-woods": Place("dark-woods", "the Dark Woods", safe=False, hazards={"wolves"}),
    "stone-river": Place("stone-river", "the Stone River", safe=False, hazards={"water"}),
    "sunny-meadow": Place("sunny-meadow", "the Sunny Meadow", safe=True, welcomes={"travelers"}),
}

QUESTS = {
    "migrate": Quest(
        id="migrate",
        name="a migration quest",
        action="migrate to a safer home",
        travel="walk by lantern light",
        obstacle="flood",
        hardship="the road was wet and long",
        success="a new home waited beyond the hills",
        tags={"migrate", "quest", "journey"},
    ),
    "cross-river": Quest(
        id="cross-river",
        name="a river quest",
        action="cross the river",
        travel="follow the stepping stones",
        obstacle="water",
        hardship="the current was quick and cold",
        success="the far bank shone like gold",
        tags={"quest", "journey"},
    ),
    "find-home": Quest(
        id="find-home",
        name="a home-finding quest",
        action="find a new home",
        travel="follow the singing birds",
        obstacle="wolves",
        hardship="the woods were deep and whispery",
        success="a cottage glimmered under the moon",
        tags={"quest", "home"},
    ),
}

GUIDES = [
    Guide("owl", "an owl", "wise owl", {"migrate", "dark-woods", "lost-valley"}, "a lantern and a calm map", "flew ahead to mark the safe way"),
    Guide("deer", "a deer", "gentle deer", {"migrate", "sunny-meadow", "stone-river"}, "a soft path through reeds", "led them where the stones were sure"),
]

TOKENS = [
    Token("lantern", "a lantern", "a little lantern with a steady flame", {"flood", "lost-valley"}, "light"),
    Token("cloak", "a silver cloak", "a silver cloak that kept off rain", {"water", "stone-river"}, "warmth"),
]

HERO_NAMES = ["Mira", "Elin", "Nora", "Talin", "Luna", "Evan"]
HERO_TYPES = ["girl", "boy"]
HERO_TRAITS = ["small", "brave", "gentle", "hopeful", "patient"]
PARENT_TYPES = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    hero_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale quest about migration and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--trait", choices=HERO_TRAITS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [("lost-valley", "migrate"), ("dark-woods", "migrate"), ("stone-river", "migrate")]


def reason_invalid(place: Place, quest: Quest) -> str:
    return f"(No story: {place.label} is already safe, so a migration quest would not be needed.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest:
        if (args.place, args.quest) not in valid_combos():
            raise StoryError(reason_invalid(SETTINGS[args.place], QUESTS[args.quest]))
    combos = [c for c in valid_combos()
              if (not args.place or c[0] == args.place)
              and (not args.quest or c[1] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(HERO_TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(HERO_TRAITS)
    return StoryParams(place=place, quest=quest, hero_name=name, hero_type=gender, parent_type=parent, trait=trait)


def tell(place: Place, quest: Quest, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero_name,
                            memes={"hope": 1.0, "fear": 0.0}))
    parent = world.add(Entity("parent", kind="character", type=params.parent_type, label=f"the {params.parent_type}",
                              memes={"care": 1.0}))
    q = QUESTS[quest.id]
    guide = choose_guide(q, place)
    token = choose_token(q, place)
    if token:
        world.add(Entity("token", label=token.label, phrase=token.phrase, protective=True))
    world.say(f"Once upon a time, {hero.label} lived in {place.label}, where the old homes were no longer safe.")
    world.say(f"{hero.label} was {params.trait} and dreamed of {q.action}.")
    world.say(f"One evening, {hero.pronoun('possessive')} {params.parent_type} said the time had come to migrate.")
    world.para()
    world.say(f"So {hero.label} began a quest to {q.action}, and {q.travel}.")
    hero.memes["homeward"] = 1.0
    if guide:
        world.say(f"Then {guide.label} appeared with {guide.offer}, and {guide.tail}.")
    if token:
        world.say(f"{hero.label} took {token.phrase}, because {token.gives} can be a small kind of magic on a hard road.")
    world.say(f"At first, {q.hardship}.")
    if migrate_risk(place, q):
        hero.memes["fear"] = 1.0
        world.say(f"{hero.label} was frightened, but {hero.pronoun('subject').capitalize()} did not turn back.")
    propagate(world)
    world.para()
    if place.safe:
        world.say(f"The land was already safe, so there was no true quest to tell.")
    else:
        world.say(f"At last, {q.success}.")
        world.say(f"{hero.label} reached {SETTINGS['sunny-meadow'].label}, where friendly faces welcomed every traveler.")
        hero.meters["arrival"] = 1.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        hero.memes["fear"] = 0.0
        world.say(f"{hero.label} smiled, because migration had become a journey to hope, and hope had become home.")
    world.facts.update(hero=hero, parent=parent, quest=q, place=place, guide=guide, token=token)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    q = f["quest"]
    place = f["place"]
    return [
        f'Write a fairy tale about a child who must {q.action} from {place.label}.',
        f"Tell a gentle quest story where {hero.label} must migrate, meet a helper, and reach a happy ending.",
        f'Write a child-friendly story about "{q.keyword}" with a brave journey and a warm homecoming.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, q, place = f["hero"], f["parent"], f["quest"], f["place"]
    guide, token = f["guide"], f["token"]
    qa = [
        QAItem(
            question=f"Who is the fairy-tale story about?",
            answer=f"It is about {hero.label}, who lives in {place.label} and must {q.action}.",
        ),
        QAItem(
            question=f"Why did {hero.label} need to leave {place.label}?",
            answer=f"{place.label} was no longer safe, so {hero.label} and {hero.pronoun('possessive')} {parent.label} decided to migrate.",
        ),
        QAItem(
            question=f"What quest did {hero.label} go on?",
            answer=f"{hero.label} went on a quest to {q.action}, even though {q.hardship}.",
        ),
    ]
    if guide:
        qa.append(QAItem(
            question=f"Who helped {hero.label} on the way?",
            answer=f"{guide.label} helped by bringing {guide.offer} and guiding the way.",
        ))
    if token:
        qa.append(QAItem(
            question=f"What magical thing did {hero.label} carry?",
            answer=f"{hero.label} carried {token.phrase}, which gave {token.gives} for the journey.",
        ))
    qa.append(QAItem(
        question=f"How did the story end?",
        answer=f"{hero.label} reached a new home, and the story ended happily with welcome and relief.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a journey made to find something, solve a problem, or reach an important goal."),
        QAItem(question="What does migrate mean?", answer="To migrate means to move from one place to another, often to find safety or a better home."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the problem gets solved and the story ends with joy or peace."),
    ]


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
        if e.protective:
            parts.append("protective=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid_combo(P,Q) :- place(P), quest(Q), migratory(Q), unsafe(P).
invalid_combo(P,Q) :- place(P), quest(Q), safe(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.safe:
            lines.append(asp.fact("safe", pid))
        else:
            lines.append(asp.fact("unsafe", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if "migrate" in q.tags:
            lines.append(asp.fact("migratory", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams("lost-valley", "migrate", "Mira", "girl", "mother", "brave"),
    StoryParams("dark-woods", "migrate", "Evan", "boy", "grandmother", "gentle"),
    StoryParams("stone-river", "migrate", "Luna", "girl", "father", "hopeful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], params)
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
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/quest combos:")
        for combo in combos:
            print(" ", combo)
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
