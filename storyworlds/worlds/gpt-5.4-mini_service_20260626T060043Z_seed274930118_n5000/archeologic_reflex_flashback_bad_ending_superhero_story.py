#!/usr/bin/env python3
"""
storyworlds/worlds/archeologic_reflex_flashback_bad_ending_superhero_story.py
=============================================================================

A standalone superhero story world about an archeologic dig, a quick reflex,
and a flashback that explains why the hero reacts the way they do.

The domain is small on purpose:
- a young superhero
- a museum or dig site
- an archeologic object that matters
- a reflex-based action that can help or hurt
- a flashback that reveals an earlier lesson
- a bad ending variant where the win does not quite land

The story engine simulates:
- physical state in meters: dust, damage, speed, distance, darkness
- emotional state in memes: courage, fear, pride, regret, relief, resolve

The premise is classic superhero story style:
- someone discovers an old clue or relic
- danger appears
- the hero remembers a flashback training moment
- reflex decides the turning point
- the ending image shows what changed, even if the ending is bad

The story remains child-facing and concrete, but one branch ends in a bad
ending: the hero acts bravely, yet the relic is lost or the museum stays in
trouble. That makes the storyworld fit the requested feature set.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

HERO_NAMES = ["Maya", "Theo", "Nina", "Arin", "Lena", "Omar", "Iris", "Noah"]
SIDEKICK_NAMES = ["Pip", "Jo", "Rex", "Milo", "Dot"]
PLACE_NAMES = ["the museum hall", "the old dig site", "the stone chamber", "the city archive"]
RELIC_NAMES = ["golden amulet", "old map", "stone key", "dusty compass"]
VILLAIN_NAMES = ["Dr. Smoke", "Captain Snare", "The Rust Fox", "Lady Echo"]
TRAINING_PLACES = ["the rooftop", "the training room", "the quiet tunnel"]
FEELINGS = ["brave", "nervous", "careful", "proud", "alert"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    relic: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    villain: str
    bad_ending: bool = True
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    trace_notes: list[str] = field(default_factory=list)

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


def clamp(x: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, x))


def build_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label="hero",
        meters={"speed": 3.0, "distance": 0.0, "dust": 0.0},
        memes={"courage": 2.0, "fear": 1.0, "pride": 1.0, "regret": 0.0, "resolve": 1.0, "relief": 0.0},
    ))
    sidekick = w.add(Entity(
        id=params.sidekick_name,
        kind="character",
        type="boy",
        label="sidekick",
        meters={"speed": 2.0},
        memes={"courage": 1.0, "fear": 0.5},
    ))
    villain = w.add(Entity(
        id=params.villain,
        kind="character",
        type="man",
        label="villain",
        meters={"speed": 2.5, "distance": 5.0},
        memes={"greed": 2.0},
    ))
    relic = w.add(Entity(
        id="relic",
        kind="thing",
        type="artifact",
        label=params.relic,
        phrase=f"a {params.relic}",
        owner=params.place,
        meters={"damage": 0.0, "distance": 0.0},
        memes={"value": 4.0},
    ))
    artifact_case = w.add(Entity(
        id="case",
        kind="thing",
        type="case",
        label="glass case",
        phrase="a glass case",
        meters={"damage": 0.0, "dust": 0.0},
    ))
    flashback = w.add(Entity(
        id="flashback",
        kind="memory",
        type="memory",
        label="training flashback",
        phrase="a quick memory of training",
        meters={"distance": 0.0},
        memes={"lesson": 1.0},
    ))
    w.facts.update(
        hero=hero, sidekick=sidekick, villain=villain, relic=relic,
        case=artifact_case, flashback=flashback, params=params
    )
    return w


def flashback_scene(w: World, hero: Entity) -> None:
    w.say(
        f"Flashback: {hero.id} had once stood on {TRAINING_PLACES[0]} with a coach who said, "
        f'"A hero does not freeze when a thing falls. A hero uses a quick reflex."'
    )
    hero.memes["resolve"] = clamp(hero.memes["resolve"] + 1.0)
    hero.memes["pride"] = clamp(hero.memes["pride"] + 0.5)
    w.trace_notes.append("flashback raised resolve")


def danger_scene(w: World, params: StoryParams) -> None:
    hero = w.get(params.hero_name)
    villain = w.get(params.villain)
    relic = w.get("relic")
    w.say(
        f"At {params.place}, {params.villain} reached for {relic.label} while the room shook."
    )
    hero.meters["distance"] = 2.0
    villain.meters["distance"] = 1.0
    relic.meters["distance"] = 0.5
    hero.meters["dust"] = clamp(hero.meters["dust"] + 1.0)
    hero.memes["fear"] = clamp(hero.memes["fear"] + 1.0)
    w.trace_notes.append("danger increased fear and dust")


def reflex_turn(w: World, params: StoryParams) -> bool:
    hero = w.get(params.hero_name)
    sidekick = w.get(params.sidekick_name)
    relic = w.get("relic")
    if hero.memes["resolve"] < 2.0:
        return False
    if params.bad_ending:
        hero.meters["speed"] = clamp(hero.meters["speed"] + 1.0)
        hero.meters["distance"] = 0.5
        sidekick.memes["fear"] = clamp(sidekick.memes["fear"] + 1.0)
        w.say(
            f"{hero.id} moved fast on reflex and grabbed for {relic.label}, "
            f"but the floor tiles slipped under {hero.pronoun('object')}."
        )
        relic.meters["damage"] = clamp(relic.meters["damage"] + 1.0)
        relic.owner = "lost"
        w.trace_notes.append("bad ending caused relic loss")
        return False
    hero.meters["speed"] = clamp(hero.meters["speed"] + 1.5)
    relic.meters["damage"] = clamp(relic.meters["damage"] + 0.0)
    w.say(
        f"{hero.id} used {hero.pronoun('possessive')} reflex to catch the falling {relic.label} "
        f"before it hit the floor."
    )
    hero.memes["courage"] = clamp(hero.memes["courage"] + 1.0)
    hero.memes["relief"] = clamp(hero.memes["relief"] + 1.0)
    w.trace_notes.append("good reflex saved relic")
    return True


def ending_scene(w: World, params: StoryParams, success: bool) -> None:
    hero = w.get(params.hero_name)
    sidekick = w.get(params.sidekick_name)
    villain = w.get(params.villain)
    relic = w.get("relic")
    if success:
        w.say(
            f"In the end, {hero.id} stood beside the repaired case, dusty but smiling, "
            f"while {sidekick.id} held the {relic.label} safe."
        )
        w.say(
            f"{params.villain} ran away empty-handed, and the old relic shone again under the museum lights."
        )
    else:
        hero.memes["regret"] = clamp(hero.memes["regret"] + 2.0)
        villain.memes["greed"] = clamp(villain.memes["greed"] + 1.0)
        w.say(
            f"In the end, {hero.id} had to watch the {relic.label} disappear into {params.villain}'s coat."
        )
        w.say(
            f"{sidekick.id} put a hand on {hero.id}'s shoulder, and the museum stayed quiet and broken."
        )


def tell(params: StoryParams) -> World:
    w = build_world(params)
    hero = w.get(params.hero_name)
    w.say(
        f"{hero.id} was a {hero.type} superhero who loved old clues and brave rescues."
    )
    w.say(
        f"Today, {hero.id} and {w.get(params.sidekick_name).id} went to {params.place} because an archeologic relic had gone missing."
    )
    w.para()
    flashback_scene(w, hero)
    danger_scene(w, params)
    success = reflex_turn(w, params)
    w.para()
    ending_scene(w, params, success)
    w.facts["success"] = success
    return w


def generation_prompts(w: World) -> list[str]:
    p = w.facts["params"]
    return [
        f'Write a superhero story with the words "archeologic" and "reflex" about {p.hero_name} at {p.place}.',
        f"Tell a short superhero story that uses a flashback to explain why {p.hero_name} reacts so fast.",
        f"Write a child-friendly story where an old relic causes trouble and the ending is {'bad' if p.bad_ending else 'good'}.",
    ]


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["params"]
    hero = w.get(p.hero_name)
    sidekick = w.get(p.sidekick_name)
    relic = w.get("relic")
    villain = w.get(p.villain)
    success = w.facts["success"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, a {hero.type} who liked old clues and brave rescues.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember that a hero should use a quick reflex instead of freezing when something falls.",
        ),
        QAItem(
            question=f"Why did {p.villain} want the relic?",
            answer=f"{villain.id} wanted the {relic.label} because the villain was greedy and wanted to take the old treasure away.",
        ),
        QAItem(
            question=f"Did {hero.id}'s reflex save the {relic.label}?",
            answer=(
                f"{'Yes, it did.' if success else 'No, it did not.'} "
                f"The reflex happened fast, but the ending was {'good' if success else 'bad'}."
            ),
        ),
        QAItem(
            question=f"Who stayed with {hero.id} at the end?",
            answer=f"{sidekick.id} stayed with {hero.id} at the end and watched what happened near the museum case.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is archeology?",
            answer="Archeology is the study of old things from the past, like tools, pots, bones, and hidden treasures.",
        ),
        QAItem(
            question="What is a reflex?",
            answer="A reflex is a quick action your body does almost right away, like catching something before it falls.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a scene that shows something from earlier so the reader understands why a character acts a certain way.",
        ),
    ]


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}/{e.type:8}) {' '.join(bits)}")
    lines.append(f"  notes: {w.trace_notes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world with archeology, reflex, flashback, and a bad ending.")
    ap.add_argument("--place", choices=PLACE_NAMES)
    ap.add_argument("--relic", choices=RELIC_NAMES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
    ap.add_argument("--villain", choices=VILLAIN_NAMES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--bad-ending", action="store_true", default=False)
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
    place = args.place or rng.choice(PLACE_NAMES)
    relic = args.relic or rng.choice(RELIC_NAMES)
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    villain = args.villain or rng.choice(VILLAIN_NAMES)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        relic=relic,
        hero_name=hero_name,
        hero_type=hero_type,
        sidekick_name=sidekick_name,
        villain=villain,
        bad_ending=args.bad_ending,
    )


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(P) :- setting(P).
hero(H) :- character(H).
relic(R) :- artifact(R).
bad_end :- mode(bad_end).

story_ok(P,H,R) :- place(P), hero(H), relic(R).
story_bad(P,H,R) :- place(P), hero(H), relic(R), bad_end.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACE_NAMES:
        lines.append(asp.fact("setting", p))
    for h in HERO_NAMES:
        lines.append(asp.fact("character", h))
    for r in RELIC_NAMES:
        lines.append(asp.fact("artifact", r))
    lines.append(asp.fact("mode", "bad_end"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3.\n#show story_bad/3."))
    atoms = set((a.name, tuple(arg.name if hasattr(arg, "name") else arg.number for arg in a.arguments)) for a in model)
    if atoms:
        print("OK: ASP program grounded and solved.")
        return 0
    print("ASP verify failed: no atoms.")
    return 1


CURATED = [
    StoryParams(place="the museum hall", relic="golden amulet", hero_name="Maya", hero_type="girl", sidekick_name="Pip", villain="Dr. Smoke", bad_ending=True),
    StoryParams(place="the old dig site", relic="stone key", hero_name="Theo", hero_type="boy", sidekick_name="Jo", villain="Captain Snare", bad_ending=False),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/3.\n#show story_bad/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is intentionally minimal for this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
