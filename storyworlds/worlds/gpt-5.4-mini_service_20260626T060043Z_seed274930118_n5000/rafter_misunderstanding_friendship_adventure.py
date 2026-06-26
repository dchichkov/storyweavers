#!/usr/bin/env python3
"""
storyworlds/worlds/rafter_misunderstanding_friendship_adventure.py
==================================================================

A small adventure storyworld about a rafter, a misunderstanding, and a friendship
repair. A child explores an old loft, notices something strange hanging from a
rafter, and briefly thinks a friend has been careless or secretive. The truth
turns out gentler, and the two children work together to fix the problem.

The world is built as a tiny simulation:
- physical meters track height, balance, dust, damage, and safety
- emotional memes track worry, hurt, curiosity, trust, and friendship
- story events are driven by the simulated state, not a fixed template
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

# Story state thresholds.
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    anchored_to: Optional[str] = None
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def display(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the old barn loft"
    afford_height: bool = True
    afford_climb: bool = True
    afford_rope: bool = True


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    risk: str
    reveal: str
    help_item: str
    help_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    clue: str
    hero: str
    friend: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _inc(m: dict[str, float], key: str, amt: float = 1.0) -> None:
    m[key] = m.get(key, 0.0) + amt


def _has(m: dict[str, float], key: str) -> bool:
    return m.get(key, 0.0) >= THRESHOLD


def _story_name(e: Entity) -> str:
    return e.id


def tell(setting: Setting, clue: Clue, hero_name: str, friend_name: str) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label=friend_name))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="Mom"))
    rafter = world.add(Entity(
        id="rafter",
        kind="thing",
        type="rafter",
        label="rafter",
        phrase="an old wooden rafter",
        meters={"height": 3.0, "balance": 2.0},
        memes={"mystery": 1.0},
    ))
    hanging = world.add(Entity(
        id="hanging",
        kind="thing",
        type="bundle",
        label=clue.label,
        phrase=clue.phrase,
        caretaker=friend.id,
        anchored_to=rafter.id,
        meters={"height": 3.0, "dust": 1.0},
        memes={"mystery": 1.0},
    ))
    toolkit = world.add(Entity(
        id=clue.help_item,
        kind="thing",
        type="tool",
        label=clue.help_item,
        phrase=clue.help_phrase,
        owner=parent.id,
        wearable=False,
        meters={"helpfulness": 1.0},
    ))

    # Act 1: adventure setup.
    world.say(
        f"{hero.id} and {friend.id} climbed into the old loft where the beams crossed "
        f"like secret paths."
    )
    world.say(
        f"High above them, the {rafter.label} held a small {clue.label} that looked "
        f"odd and out of place."
    )
    world.say(
        f"{hero.id} loved adventures, and {friend.id} loved finding strange things "
        f"before anyone else did."
    )

    # Act 2: misunderstanding.
    world.para()
    _inc(hero.memes, "curiosity", 1.0)
    _inc(friend.memes, "trust", 1.0)
    _inc(hero.meters, "balance", 1.0)

    world.say(
        f"{hero.id} pointed up and frowned. The {clue.label} looked like proof that "
        f"{friend.id} had been hiding something."
    )
    world.say(
        f"{hero.id} thought, '{friend.id} must have left that there on purpose.'"
    )
    _inc(hero.memes, "worry", 1.0)
    _inc(friend.memes, "hurt", 1.0)
    _inc(friend.memes, "confusion", 1.0)

    # Parent notices the tension and invites a safer look.
    world.say(
        f"Mom came in with a lantern and said, 'Let's not guess too fast. Let's look '
        f'at the rafter together.'"
    )

    # Act 3: reveal and repair.
    world.para()
    _inc(parent.memes, "calm", 1.0)
    _inc(hero.memes, "worry", 0.0)
    world.say(
        f"When they looked closely, they saw the {clue.label} was not a secret at all."
    )
    world.say(
        f"It was {clue.reveal}, and the knot had slipped because a draft had tugged it "
        f"while nobody was watching."
    )
    world.say(
        f"{friend.id}'s face went soft. '{friend.id} thought you might be mad,' Mom said, "
        f"and {hero.id} suddenly understood the mistake."
    )
    _inc(hero.memes, "guilt", 1.0)
    _inc(friend.memes, "hurt", -1.0 if friend.memes.get("hurt", 0.0) else 0.0)
    _inc(hero.memes, "trust", 1.0)

    # Fix the situation with the toolkit.
    world.say(
        f"{hero.id} and {friend.id} used the {toolkit.label} to tie the bundle safely "
        f"back to the {rafter.label}."
    )
    _inc(hanging.meters, "safety", 1.0)
    _inc(hanging.meters, "damage", 0.0)
    _inc(hero.memes, "friendship", 1.0)
    _inc(friend.memes, "friendship", 1.0)
    _inc(hero.memes, "curiosity", 1.0)
    _inc(friend.memes, "trust", 1.0)

    world.say(
        f"Then {hero.id} apologized for jumping to conclusions, and {friend.id} smiled "
        f"because the misunderstanding had finally cleared."
    )
    world.say(
        f"By the time they climbed down, the loft felt less spooky and more like a place "
        f"where friends could solve a mystery together."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        rafter=rafter,
        hanging=hanging,
        toolkit=toolkit,
        clue=clue,
        setting=setting,
        resolved=True,
        misunderstood=True,
    )
    return world


SETTINGS = {
    "loft": Setting(place="the old barn loft", afford_height=True, afford_climb=True, afford_rope=True),
    "attic": Setting(place="the attic above the shed", afford_height=True, afford_climb=True, afford_rope=True),
    "gallery": Setting(place="the rope bridge gallery", afford_height=True, afford_climb=True, afford_rope=True),
}

CLUES = {
    "kite": Clue(
        id="kite",
        label="kite",
        phrase="a bright kite with a frayed string",
        risk="could tear if it snagged",
        reveal="a friend had flown it inside to dry it after rain",
        help_item="rope",
        help_phrase="a soft rope for tying knots",
        tags={"rafter", "friendship", "adventure"},
    ),
    "map": Clue(
        id="map",
        label="map",
        phrase="a folded map tied with twine",
        risk="could fall and get torn",
        reveal="a trail map that the friend was keeping safe for tomorrow's walk",
        help_item="clip",
        help_phrase="a small clip to hold paper in place",
        tags={"rafter", "friendship", "adventure"},
    ),
    "lantern": Clue(
        id="lantern",
        label="lantern",
        phrase="a little lantern hanging by a cord",
        risk="could swing and bump the beam",
        reveal="a lantern the friend had set up for a late reading game",
        help_item="hook",
        help_phrase="a wooden hook to steady the cord",
        tags={"rafter", "friendship", "adventure"},
    ),
}

NAMES_GIRL = ["Ava", "Mia", "Luna", "Nora", "Ivy", "Zoe"]
NAMES_BOY = ["Finn", "Eli", "Theo", "Noah", "Max", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for clue in CLUES:
            out.append((place, clue, "friendship"))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short adventure story for a young child about {f['hero'].id} and {f['friend'].id} in {f['setting'].place}.",
        f"Tell a gentle story with a rafter, a misunderstanding, and a friendship repair.",
        f"Make a simple story where children find something hanging from a rafter and learn it was not what they first thought.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    parent: Entity = f["parent"]
    clue: Clue = f["clue"]
    setting: Setting = f["setting"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Where did {hero.id} and {friend.id} go in the story?",
            answer=f"They went to {setting.place}, where the beams and the rafter made the place feel like a little adventure.",
        ),
        QAItem(
            question=f"What did {hero.id} think at first when the {clue.label} was seen?",
            answer=f"{hero.id} thought {friend.id} had left it there on purpose, which was the misunderstanding.",
        ),
        QAItem(
            question=f"Who helped the two children calm down and look again?",
            answer=f"{parent.id} helped them slow down, look at the rafter together, and talk about what they were seeing.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The misunderstanding was cleared up, the hanging item was tied back safely, and the friendship between {hero.id} and {friend.id} felt stronger.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a rafter?",
            answer="A rafter is a long beam that helps hold up a roof or ceiling.",
        ),
        QAItem(
            question="Why can a hanging thing be dangerous near a beam?",
            answer="If something hangs badly, it can fall, swing, or get tangled, so people often secure it carefully.",
        ),
        QAItem(
            question="What does a friendship mean?",
            answer="Friendship means people care about each other, help each other, and try to fix problems together.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing about a situation and needs more information to understand it correctly.",
        ),
    ]
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.anchored_to:
            bits.append(f"anchored_to={e.anchored_to}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="loft", clue="kite", hero="Ava", friend="Finn"),
    StoryParams(place="attic", clue="map", hero="Mia", friend="Leo"),
    StoryParams(place="gallery", clue="lantern", hero="Nora", friend="Eli"),
]

ASP_RULES = r"""
% A clue is relevant when it hangs from a rafter in an adventure setting.
relevant(C) :- clue(C), hangs_from_rafter(C).

% A misunderstanding exists when one child suspects another child caused the clue.
misunderstanding(H, F, C) :- child(H), child(F), clue(C), relevant(C),
                             suspects(H, F, C).

% Friendship is strengthened when the children learn the truth and fix the clue.
friendship_fixed(H, F, C) :- misunderstanding(H, F, C), reveal(C), repair(H, F, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        if s.afford_height:
            lines.append(asp.fact("affords", sid, "height"))
        if s.afford_climb:
            lines.append(asp.fact("affords", sid, "climb"))
        if s.afford_rope:
            lines.append(asp.fact("affords", sid, "rope"))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("hangs_from_rafter", cid))
        lines.append(asp.fact("reveal", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show relevant/1."))
    clingo_set = set(asp.atoms(model, "relevant"))
    python_set = {(c,) for c in CLUES}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid story clues ({len(clingo_set)} clues).")
        return 0
    print("MISMATCH between clingo and python clues:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small adventure world about a rafter, a misunderstanding, and friendship."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, _ = rng.choice(sorted(combos))
    hero = args.name or rng.choice(NAMES_GIRL)
    friend = args.friend or rng.choice(NAMES_BOY)
    return StoryParams(place=place, clue=clue, hero=hero, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.hero, params.friend)
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
        print(asp_program("#show relevant/1.\n#show misunderstanding/3.\n#show friendship_fixed/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show relevant/1.\n#show misunderstanding/3.\n#show friendship_fixed/3."))
        print("relevant:", sorted(set(asp.atoms(model, "relevant"))))
        print("misunderstanding:", sorted(set(asp.atoms(model, "misunderstanding"))))
        print("friendship_fixed:", sorted(set(asp.atoms(model, "friendship_fixed"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
