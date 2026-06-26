#!/usr/bin/env python3
"""
spite_curiosity_mystery_to_solve_fable.py
=========================================

A small fable-like story world about curiosity, a mystery to solve, and the
trouble that spite can cause before wisdom turns it around.

Premise:
- A curious little character notices a mystery in a peaceful place.
- A spiteful impulse tempts someone to hide the truth.
- Curiosity and kindness solve the mystery without cruelty.
- The ending proves the change in the world state.

This script is self-contained and follows the Storyweavers storyworld contract.
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "queen"}
        male = {"boy", "father", "man", "brother", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str
    detail: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    cause: str
    solution: str
    hidden_kind: str
    risk: str
    requires: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    trickster_name: str
    trickster_type: str
    seed: Optional[int] = None


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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS: dict[str, Setting] = {
    "oak_tree": Setting(
        place="the old oak tree",
        detail="Its roots curved like sleepy foxes under the grass.",
        mood="peaceful",
        affords={"search", "gather", "listen"},
    ),
    "riverbank": Setting(
        place="the riverbank",
        detail="The water sang softly around flat silver stones.",
        mood="restless",
        affords={"search", "listen", "follow"},
    ),
    "village_green": Setting(
        place="the village green",
        detail="Little paths crossed the grass between a well and a fence.",
        mood="gentle",
        affords={"search", "listen", "ask"},
    ),
    "orchard": Setting(
        place="the orchard",
        detail="The apple branches leaned low, as if they loved secrets.",
        mood="bright",
        affords={"search", "pick", "listen"},
    ),
}

MYSTERIES: dict[str, Mystery] = {
    "missing_bell": Mystery(
        id="missing_bell",
        label="the missing bell",
        clue="a faint ring heard in the grass",
        cause="a bell fell from the cart and rolled into the reeds",
        solution="finding the bell under a leaf and returning it to the owner",
        hidden_kind="object",
        risk="the baker would think it was stolen",
        requires={"search", "listen"},
    ),
    "stolen_honey": Mystery(
        id="stolen_honey",
        label="the stolen honey",
        clue="sticky footprints near the hive",
        cause="the wind tipped a pot and the honey dripped by the stone wall",
        solution="following the sticky trail to the pot and telling the truth",
        hidden_kind="trail",
        risk="the bees would be blamed for a mess they did not make",
        requires={"search", "follow"},
    ),
    "lost_key": Mystery(
        id="lost_key",
        label="the lost key",
        clue="a tiny glint in the mud",
        cause="the key slipped from a pocket while the shepherd rested",
        solution="lifting the key from the mud and opening the gate",
        hidden_kind="object",
        risk="the gate would stay shut and the flock would wait outside",
        requires={"search"},
    ),
    "broken_mooncake": Mystery(
        id="broken_mooncake",
        label="the broken mooncake",
        clue="crumbs shaped like a crescent path",
        cause="a child leaned on the table and split the cake",
        solution="sharing the pieces and admitting what happened",
        hidden_kind="crumbs",
        risk="a friendly feast would turn into blame",
        requires={"search", "ask"},
    ),
}

# Simple fable cast templates.
HEROES = [
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Pip", "rabbit"),
    ("Tara", "girl"),
    ("Jory", "boy"),
]
COMPANIONS = [
    ("Moss", "tortoise"),
    ("Lina", "girl"),
    ("Beck", "boy"),
    ("Wren", "bird"),
]
TRICKSTERS = [
    ("Sable", "fox"),
    ("Mira", "girl"),
    ("Crisp", "crow"),
    ("Bran", "boy"),
]

TRAITS = ["curious", "gentle", "small", "bright-eyed", "patient", "quick"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable if the setting affords the needed actions.
solvable(S, M) :- setting(S), mystery(M), requires(M, A), affords(S, A).

% Spite tempts a trickster to hide the clue, but a curious hero can still solve it.
can_resolve(S, M) :- solvable(S, M), hero_curious(S), trickster_spiteful(S).

% A valid story requires a solvable mystery and a curious hero.
valid_story(S, M) :- solvable(S, M), hero_curious(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for r in sorted(m.requires):
            lines.append(asp.fact("requires", mid, r))
    # generic facts for the parity gate
    lines.append(asp.fact("hero_curious", "any"))
    lines.append(asp.fact("trickster_spiteful", "any"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((s, m) for s in SETTINGS for m in MYSTERIES if reasonableness_gate(SETTINGS[s], MYSTERIES[m]))
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    return bool(setting.affords & mystery.requires)

def pick_name(rng: random.Random, pool: list[tuple[str, str]], desired_type: Optional[str] = None) -> tuple[str, str]:
    choices = [p for p in pool if desired_type is None or p[1] == desired_type]
    if not choices:
        choices = pool
    return rng.choice(choices)

def mood_sentence(setting: Setting) -> str:
    return {
        "peaceful": "The place felt peaceful, as if even the wind was listening.",
        "restless": "The place felt restless, because the water kept changing its mind.",
        "gentle": "The place felt gentle, and every path seemed to invite a walk.",
        "bright": "The place felt bright, and the fruit shone like little lanterns.",
    }.get(setting.mood, "The place was quiet and waiting.")

def introduce(world: World, hero: Entity, companion: Entity, trickster: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a {', '.join([t for t in hero.traits if t])} {hero.type} who loved to ask questions."
    )
    world.say(
        f"{companion.id} was {companion.pronoun('subject')} friend, and {trickster.id} often lurked nearby with a sharp little smile."
    )
    world.say(
        f"One day, the two friends noticed {mystery.clue} near {world.setting.place}."
    )

def curiosity_stirs(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} leaned closer, because a curious heart could not leave a mystery alone."
    )

def spite_interferes(world: World, trickster: Entity, mystery: Mystery) -> None:
    trickster.memes["spite"] = trickster.memes.get("spite", 0) + 1
    world.say(
        f"{trickster.id} saw the clue too, and spite made {trickster.pronoun('object')} decide to hide what had been found."
    )
    world.say(
        f"That meant the wrong story might grow around {mystery.label} unless someone spoke wisely."
    )

def investigate(world: World, hero: Entity, companion: Entity, mystery: Mystery) -> None:
    hero.meters["searching"] = hero.meters.get("searching", 0) + 1
    companion.meters["helping"] = companion.meters.get("helping", 0) + 1
    world.say(
        f"{hero.id} and {companion.id} searched carefully, one looking low and one listening high."
    )
    if "listen" in mystery.requires:
        world.say(
            f"They paused to listen, and the clue answered back with a tiny sound."
        )
    if "follow" in mystery.requires:
        world.say(
            f"They followed the trail without rushing, because slow feet notice the truth."
        )

def reveal(world: World, hero: Entity, trickster: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At last, {hero.id} found that {mystery.cause}."
    )
    world.say(
        f"When {hero.id} told the others, the false worry fell away like a leaf from a branch."
    )

def resolve(world: World, hero: Entity, companion: Entity, trickster: Entity, mystery: Mystery) -> None:
    trickster.memes["spite"] = 0.0
    trickster.memes["regret"] = trickster.memes.get("regret", 0) + 1
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0) + 1
    world.say(
        f"{trickster.id} looked ashamed and admitted the hiding trick."
    )
    world.say(
        f"{hero.id} did not answer with spite in return. Instead, {hero.pronoun('subject')} used kind words and showed the truth."
    )
    world.say(
        f"Then they solved {mystery.label} by {mystery.solution}."
    )

def moral_close(world: World, hero: Entity, companion: Entity, trickster: Entity, mystery: Mystery) -> None:
    world.say(
        f"In the end, the place was calm again: the clue was explained, the fear was gone, and everyone could see that curiosity, not spite, had won the day."
    )
    world.say(
        f"The little fable ended with a quiet lesson: a question asked kindly can open a door that anger keeps shut."
    )

def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero_name, hero_type = params.hero_name, params.hero_type
    companion_name, companion_type = params.companion_name, params.companion_type
    trickster_name, trickster_type = params.trickster_name, params.trickster_type

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["curious", rng.choice(TRAITS), "kind"],
        meters={"searching": 0.0},
        memes={"curiosity": 0.0, "joy": 0.0, "wisdom": 0.0},
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_type,
        traits=["steady", rng.choice(TRAITS)],
        meters={"helping": 0.0},
        memes={"trust": 0.0},
    ))
    trickster = world.add(Entity(
        id=trickster_name,
        kind="character",
        type=trickster_type,
        traits=["sharp", "secretive"],
        meters={"hiding": 0.0},
        memes={"spite": 0.0},
    ))

    world.facts = {
        "hero": hero,
        "companion": companion,
        "trickster": trickster,
        "mystery": mystery,
        "setting": setting,
    }

    introduce(world, hero, companion, trickster, mystery)
    world.para()
    world.say(mood_sentence(setting))
    curiosity_stirs(world, hero, mystery)
    spite_interferes(world, trickster, mystery)
    investigate(world, hero, companion, mystery)
    world.para()
    reveal(world, hero, trickster, mystery)
    resolve(world, hero, companion, trickster, mystery)
    world.para()
    moral_close(world, hero, companion, trickster, mystery)
    return world


# ---------------------------------------------------------------------------
# Story QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    hero: Entity = f["hero"]
    return [
        f'Write a short fable for children about curiosity and spite at {setting.place}, and include the mystery of {mystery.label}.',
        f"Tell a gentle story where {hero.id} asks questions, a spiteful character hides a clue, and the truth is found at {setting.place}.",
        f'Write a simple moral tale that uses the words "curiosity" and "spite" and ends with a solved mystery.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    trickster: Entity = f["trickster"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, who was curious about {mystery.label} at {setting.place}.",
        ),
        QAItem(
            question=f"What made the mystery harder to solve?",
            answer=f"{trickster.id}'s spite made the problem harder, because {trickster.pronoun('subject')} tried to hide the clue.",
        ),
        QAItem(
            question=f"How was {mystery.label} solved?",
            answer=f"It was solved by {mystery.solution}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} search?",
            answer=f"{companion.id} helped by searching carefully and staying calm beside {hero.id}.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The truth came out, the spiteful hiding stopped, and the place grew calm again.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    out = [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to know more, asking questions, and looking carefully at the world.",
        ),
        QAItem(
            question="What is spite?",
            answer="Spite is a mean feeling that makes someone want to cause trouble or hide the truth just to be unkind.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not explained yet, so people have to look for clues and think carefully.",
        ),
    ]
    if "search" in mystery.requires:
        out.append(QAItem(
            question="Why do people search for clues?",
            answer="People search for clues so they can find out what happened and understand the truth.",
        ))
    return out


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            if reasonableness_gate(s, m):
                out.append((sid, mid))
    return out


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.label} needs actions like {', '.join(sorted(mystery.requires))}, "
        f"but {setting.place} only affords {', '.join(sorted(setting.affords))}. "
        f"Try a setting that can support the needed clues.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable-like story world about curiosity, spite, and a mystery to solve."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type")
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type")
    ap.add_argument("--trickster-name")
    ap.add_argument("--trickster-type")
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
    if args.setting and args.mystery:
        s = SETTINGS[args.setting]
        m = MYSTERIES[args.mystery]
        if not reasonableness_gate(s, m):
            raise StoryError(explain_rejection(s, m))

    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id = rng.choice(sorted(combos))
    hero_name, hero_type = pick_name(rng, HEROES, args.hero_type)
    companion_name, companion_type = pick_name(rng, COMPANIONS, args.companion_type)
    trickster_name, trickster_type = pick_name(rng, TRICKSTERS, args.trickster_type)

    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        hero_name=args.hero_name or hero_name,
        hero_type=args.hero_type or hero_type,
        companion_name=args.companion_name or companion_name,
        companion_type=args.companion_type or companion_type,
        trickster_name=args.trickster_name or trickster_name,
        trickster_type=args.trickster_type or trickster_type,
    )


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
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams("oak_tree", "missing_bell", "Milo", "boy", "Moss", "tortoise", "Sable", "fox"),
    StoryParams("riverbank", "stolen_honey", "Nia", "girl", "Wren", "bird", "Crisp", "crow"),
    StoryParams("village_green", "lost_key", "Pip", "rabbit", "Lina", "girl", "Bran", "boy"),
    StoryParams("orchard", "broken_mooncake", "Tara", "girl", "Beck", "boy", "Mira", "girl"),
]


def asp_facts_for_story() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for r in sorted(m.requires):
            lines.append(asp.fact("requires", mid, r))
    lines.append(asp.fact("hero_curious", "any"))
    lines.append(asp.fact("trickster_spiteful", "any"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts_for_story()}\n{ASP_RULES}\n{show}\n"


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible (setting, mystery) combos:")
        for sid, mid in combos:
            print(f"  {sid:15} {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
