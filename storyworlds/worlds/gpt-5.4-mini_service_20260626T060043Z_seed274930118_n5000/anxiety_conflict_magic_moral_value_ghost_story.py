#!/usr/bin/env python3
"""
A small storyworld about a worried child, a helpful ghost, and a moral choice.

Seed premise:
- A child feels anxiety at night.
- A ghost appears during a conflict.
- Magic can solve the problem, but only if the child chooses a kind moral value
  instead of selfish fear.

The simulated world keeps track of:
- physical meters: light, cold, damp, glow, distance, etc.
- emotional memes: anxiety, courage, trust, guilt, relief, kindness
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
# World entities and parameters
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    dim: bool = True
    has_window: bool = True
    has_hallway: bool = False
    has_lamp: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    guardian_type: str
    ghost_kind: str
    magic_item: str
    moral_value: str
    seed: Optional[int] = None


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    spooky_level: float = 0.0

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
        import copy as _copy
        return World(
            place=self.place,
            entities=_copy.deepcopy(self.entities),
            facts=_copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
            spooky_level=self.spooky_level,
        )


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic_room": Place(name="the attic room", dim=True, has_window=True, has_hallway=False, has_lamp=True),
    "old_house": Place(name="the old house", dim=True, has_window=True, has_hallway=True, has_lamp=False),
    "quiet_bedroom": Place(name="the quiet bedroom", dim=True, has_window=True, has_hallway=True, has_lamp=True),
}

GHOST_KINDS = {
    "pale_ghost": {"label": "a pale ghost", "voice": "a whispery voice", "wish": "to be remembered kindly"},
    "lantern_ghost": {"label": "a lantern ghost", "voice": "a soft humming voice", "wish": "to help a frightened child"},
    "shoe_ghost": {"label": "a shoe ghost", "voice": "a tiny tap-tap voice", "wish": "to guide lost people home"},
}

MAGIC_ITEMS = {
    "glow_jar": {"label": "a glow jar", "effect": "filled the room with warm gold light"},
    "paper_star": {"label": "a paper star charm", "effect": "shone like a tiny moon"},
    "bell_string": {"label": "a bell string", "effect": "rang a clear note that made the shadows shrink"},
}

MORAL_VALUES = {
    "kindness": {
        "label": "kindness",
        "lesson": "being kind can make a scary moment feel smaller",
        "action": "share the light",
    },
    "honesty": {
        "label": "honesty",
        "lesson": "telling the truth helps people trust one another",
        "action": "admit the mistake",
    },
    "courage": {
        "label": "courage",
        "lesson": "bravery means doing the right thing even when you feel shaky",
        "action": "step forward anyway",
    },
}

GIRL_NAMES = ["Mia", "Lina", "Ivy", "Nora", "Zoe", "Ada", "Ruby", "Lily"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Max", "Leo", "Owen", "Ben"]
TRAITS = ["quiet", "curious", "gentle", "thoughtful", "shy", "brave"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
class StoryWorld(World):
    pass


def _meter(entity: Entity, key: str, delta: float) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + delta


def _meme(entity: Entity, key: str, delta: float) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + delta


def _propagate(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    guardian = world.get("guardian")

    if child.memes.get("anxiety", 0) >= 1.0 and "conflict_started" not in world.fired:
        world.fired.add("conflict_started")
        _meme(child, "fear", 1.0)
        out.append(f"The room felt too still, and {child.id}'s chest tightened with anxiety.")

    if child.memes.get("kindness_choice", 0) >= 1.0 and "ghost_softens" not in world.fired:
        world.fired.add("ghost_softens")
        _meme(ghost, "trust", 1.0)
        _meme(child, "trust", 1.0)
        _meme(child, "anxiety", -1.0)
        _meme(child, "relief", 1.0)
        _meter(world.get("magic"), "glow", 1.0)
        out.append(f"The ghost's outline turned gentle as the magic began to glow.")

    if child.memes.get("honesty", 0) >= 1.0 and "truth_heals" not in world.fired:
        world.fired.add("truth_heals")
        _meme(guardian, "trust", 1.0)
        _meme(child, "guilt", -1.0)
        _meme(child, "relief", 1.0)
        out.append(f"The truth made the air feel lighter, and the grown-up listened instead of scolding.")

    if world.spooky_level > 0 and child.memes.get("courage", 0) >= 1.0 and "brave_end" not in world.fired:
        world.fired.add("brave_end")
        _meme(child, "courage", 1.0)
        _meme(child, "anxiety", -0.5)
        out.append(f"{child.id} could still feel a shiver, but {child.pronoun()} stood tall anyway.")

    return out


def _say_and_propagate(world: World, text: str) -> None:
    world.say(text)
    for s in _propagate(world):
        world.say(s)


def _intro(world: World, child: Entity, guardian: Entity, ghost: Entity, magic: Entity, moral: dict) -> None:
    place = world.place.name
    world.say(
        f"{child.id} was a {next(t for t in child.traits if t != 'little')} {child.type} who lived in {place}."
    )
    world.say(
        f"{child.id} liked the little lamp, but at night {place} could feel very quiet and very wide."
    )
    world.say(
        f"One evening, a {ghost.label} waited near the door, and its {ghost.traits[0]} wish was {ghost.metas['wish'] if 'wish' in ghost.metas else ''}".strip()
    )


def build_world(params: StoryParams) -> StoryWorld:
    place = PLACES[params.place]
    world = StoryWorld(place=place)

    child = world.add(Entity(
        id="child",
        kind="character",
        label=params.child_name,
        type=params.child_type,
        traits=["little", random.choice(TRAITS), "anxious"],
        meters={"distance_to_ghost": 3.0},
        memes={"anxiety": 1.0, "curiosity": 1.0},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        label="the grown-up",
        type=params.guardian_type,
        traits=["calm", "protective"],
        memes={"care": 1.0},
    ))
    ghost_cfg = GHOST_KINDS[params.ghost_kind]
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        label=ghost_cfg["label"],
        type="ghost",
        traits=[ghost_cfg["voice"], "lonely"],
        memes={"sadness": 1.0, "kindness": 0.5},
    ))
    magic_cfg = MAGIC_ITEMS[params.magic_item]
    magic = world.add(Entity(
        id="magic",
        kind="thing",
        label=magic_cfg["label"],
        type="magic",
        traits=[magic_cfg["effect"]],
        meters={"glow": 0.0},
    ))
    moral_cfg = MORAL_VALUES[params.moral_value]

    world.facts.update(
        child=child,
        guardian=guardian,
        ghost=ghost,
        magic=magic,
        moral_cfg=moral_cfg,
        ghost_cfg=ghost_cfg,
        magic_cfg=magic_cfg,
        place=place,
    )

    # Act 1
    world.say(
        f"{child.id} had anxiety about the dark hallway, because the hallway sometimes made small sounds."
    )
    world.say(
        f"{guardian.label} told {child.id} that the house was safe, but {child.id} still listened to every creak."
    )

    world.para()

    # Act 2: conflict and magic appear.
    _meme(child, "anxiety", 1.0)
    _meter(world.get("magic"), "glow", 0.2)
    world.spooky_level = 1.0
    world.say(
        f"Then {ghost.label} drifted out of the shadows. It did not boom or howl; it only whispered, "
        f'"I need help."'
    )
    world.say(
        f"{child.id} stepped back, because the room felt cold and the ghost looked strange."
    )
    world.say(
        f"{guardian.label} asked {child.id} to listen first, not run."
    )
    _meme(child, "conflict", 1.0)
    _say_and_propagate(
        world,
        f"{child.id} wanted to hide, but the ghost pointed at {magic.label} and the little lamp."
    )

    world.para()

    # Act 3: moral choice.
    if params.moral_value == "kindness":
        _meme(child, "kindness_choice", 1.0)
        world.say(
            f"{child.id} remembered that kindness means {moral_cfg['action']}."
        )
        world.say(
            f"Instead of shoving the ghost away, {child.id} held up {magic.label} and let the light reach the corner."
        )
        _propagate(world)
        world.say(
            f"The ghost softened at once, because the warm glow made the room less lonely."
        )
        world.say(
            f'“Thank you,” the ghost said. “I only wanted {ghost_cfg["wish"]}.”'
        )
        world.say(
            f"{guardian.label} smiled, and {child.id}'s anxiety turned into relief."
        )
        world.say(
            f"By the end, {child.id} was standing beside the ghost, sharing the light instead of fearing it."
        )
    elif params.moral_value == "honesty":
        _meme(child, "honesty", 1.0)
        world.say(
            f"{child.id} admitted the truth: the loud noise had scared {child.id}, and that was why {child.id} had hidden."
        )
        _propagate(world)
        world.say(
            f"The ghost listened kindly, and {guardian.label} thanked {child.id} for telling the truth."
        )
        world.say(
            f"Because the room had become honest and calm, the ghost could finally explain that it was lost, not mean."
        )
        world.say(
            f"{child.id} lit {magic.label}, and the bright little charm showed the way to the doorway."
        )
        world.say(
            f"At the end, honesty had turned the ghost from a scare into a visitor."
        )
    else:
        _meme(child, "courage", 1.0)
        world.say(
            f"{child.id} swallowed hard and chose courage."
        )
        world.say(
            f"Even though the ghost was eerie, {child.id} stepped forward and asked what was wrong."
        )
        _propagate(world)
        world.say(
            f"The ghost answered in a whisper, and the answer was gentle instead of mean."
        )
        world.say(
            f"{guardian.label} nodded proudly, because courage had helped {child.id} do the right thing."
        )
        world.say(
            f"Before long, the shadow in the hallway looked smaller, and {child.id} felt bigger."
        )

    world.facts["moral_value"] = moral_cfg["label"]
    return world


# ---------------------------------------------------------------------------
# Reasonable variation gates
# ---------------------------------------------------------------------------
def explain_invalid(reason: str) -> str:
    return f"(No story: {reason})"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    guardian_type = args.guardian_type or ("mother" if child_type == "girl" and rng.random() < 0.6 else "father")
    ghost_kind = args.ghost_kind or rng.choice(sorted(GHOST_KINDS))
    magic_item = args.magic_item or rng.choice(sorted(MAGIC_ITEMS))
    moral_value = args.moral_value or rng.choice(sorted(MORAL_VALUES))
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)

    if place not in PLACES:
        raise StoryError(explain_invalid("unknown place"))
    if child_type not in {"girl", "boy"}:
        raise StoryError(explain_invalid("child type must be girl or boy"))
    if guardian_type not in {"mother", "father"}:
        raise StoryError(explain_invalid("guardian type must be mother or father"))
    if ghost_kind not in GHOST_KINDS:
        raise StoryError(explain_invalid("unknown ghost kind"))
    if magic_item not in MAGIC_ITEMS:
        raise StoryError(explain_invalid("unknown magic item"))
    if moral_value not in MORAL_VALUES:
        raise StoryError(explain_invalid("unknown moral value"))

    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        guardian_type=guardian_type,
        ghost_kind=ghost_kind,
        magic_item=magic_item,
        moral_value=moral_value,
    )


# ---------------------------------------------------------------------------
# Generation and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        'Write a short child-friendly ghost story with anxiety, conflict, magic, and a moral choice.',
        f"Tell a gentle story about {f['child'].label} meeting {f['ghost_cfg']['label']} in {f['place'].name}, "
        f"where {f['magic_cfg']['label']} helps solve the trouble.",
        f"Write a spooky-but-kind story that ends with {f['moral_cfg']['label']} winning over fear.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ghost_cfg = f["ghost_cfg"]
    magic_cfg = f["magic_cfg"]
    moral_cfg = f["moral_cfg"]
    place = f["place"].name

    return [
        QAItem(
            question=f"Who felt anxiety in {place} when the ghost appeared?",
            answer=f"{child.label} felt anxiety first, because the room was dark and the ghost looked strange.",
        ),
        QAItem(
            question=f"What helped the story turn from conflict to calm?",
            answer=f"{magic_cfg['label']} helped by shining warmly, and the child also chose {moral_cfg['label']}.",
        ),
        QAItem(
            question=f"What did the ghost want in the end?",
            answer=f"The ghost wanted {ghost_cfg['wish']}, which turned out to be gentle and not scary at all.",
        ),
        QAItem(
            question=f"What moral value mattered most in the ending?",
            answer=f"{moral_cfg['label'].capitalize()} mattered most, because it helped the child make a good choice.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a ghost?",
            answer="A ghost is a spooky story character that is often shown as a floating figure in old tales.",
        ),
        QAItem(
            question="What does a glow jar do in a story?",
            answer="A glow jar gives off a warm light that can make a dark room feel safer.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating someone gently and helping instead of hurting or mocking them.",
        ),
    ]
    if f["moral_value"] == "honesty":
        out.append(QAItem(
            question="Why is honesty helpful?",
            answer="Honesty is helpful because telling the truth lets other people understand what really happened.",
        ))
    if f["moral_value"] == "courage":
        out.append(QAItem(
            question="What is courage?",
            answer="Courage means doing the right thing even when you feel nervous or scared.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for eid, e in world.entities.items():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {eid:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  spooky_level={world.spooky_level}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
ghost_kind(G) :- ghost(G).
magic_item(M) :- magic(M).
moral_value(V) :- moral(V).

compatible_story(P, G, M, V) :-
    place(P), ghost_kind(G), magic_item(M), moral_value(V).

#show compatible_story/4.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.has_window:
            lines.append(asp.fact("windowed", pid))
        if p.has_hallway:
            lines.append(asp.fact("hallway", pid))
        if p.has_lamp:
            lines.append(asp.fact("lamp", pid))
    for gid in GHOST_KINDS:
        lines.append(asp.fact("ghost", gid))
    for mid in MAGIC_ITEMS:
        lines.append(asp.fact("magic", mid))
    for vid in MORAL_VALUES:
        lines.append(asp.fact("moral", vid))
    return "\n".join(lines)


def asp_program(show: str = "#show compatible_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    python_set = {
        (p, g, m, v)
        for p in PLACES
        for g in GHOST_KINDS
        for m in MAGIC_ITEMS
        for v in MORAL_VALUES
    }
    clingo_set = set(asp_compatible())
    if clingo_set == python_set:
        print(f"OK: ASP parity matched ({len(clingo_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child, a ghost, magic, and a moral choice.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--guardian-type", choices=["mother", "father"])
    ap.add_argument("--ghost-kind", choices=GHOST_KINDS)
    ap.add_argument("--magic-item", choices=MAGIC_ITEMS)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)

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


CURATED = [
    StoryParams(place="quiet_bedroom", child_name="Mia", child_type="girl", guardian_type="mother", ghost_kind="lantern_ghost", magic_item="glow_jar", moral_value="kindness"),
    StoryParams(place="old_house", child_name="Eli", child_type="boy", guardian_type="father", ghost_kind="shoe_ghost", magic_item="paper_star", moral_value="honesty"),
    StoryParams(place="attic_room", child_name="Nora", child_type="girl", guardian_type="mother", ghost_kind="pale_ghost", magic_item="bell_string", moral_value="courage"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible()
        print(f"{len(combos)} compatible story combinations:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.ghost_kind} + {p.magic_item} + {p.moral_value}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
