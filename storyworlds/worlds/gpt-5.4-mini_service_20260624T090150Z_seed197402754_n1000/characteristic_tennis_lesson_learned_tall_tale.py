#!/usr/bin/env python3
"""
A tiny Tall Tale storyworld about a characteristic tennis lesson learned.

Seed premise:
A kid thinks tennis is only about big swings and loud victories, but a coach
shows that the real lesson is smaller and wiser: watch the ball, keep your feet,
and use the right stroke at the right time.

The world model tracks:
- a player with confidence, balance, focus, and pride
- a tennis drill with physical meters and emotional memes
- a dramatic overreach that causes a miss
- a correction that leads to a lesson learned

The style aims for tall tale flavor: larger-than-life descriptions, but still a
classical setup -> trouble -> turn -> resolution story.
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
# Registries
# ---------------------------------------------------------------------------

PLAYER_NAMES = [
    "Milo", "Ruby", "June", "Theo", "Nina", "Owen", "Pia", "Finn"
]

COACH_NAMES = [
    "Coach Bell", "Coach Sera", "Coach Pike", "Coach Lark"
]

CHARACTERISTICS = [
    "tall",
    "quick",
    "steady",
    "courageous",
    "clever",
    "bright-eyed",
]

COURTS = {
    "sunny_court": {
        "label": "the sunny court",
        "detail": "The court gleamed so hard it looked polished by a friendly sunbeam.",
        "indoors": False,
    },
    "school_gym": {
        "label": "the school gym",
        "detail": "The gym hummed with shoe squeaks and the smell of clean floor wax.",
        "indoors": True,
    },
    "windy_park": {
        "label": "the park court",
        "detail": "The park court stood in a gusty patch where even the tape on the net seemed to sway.",
        "indoors": False,
    },
}

DRILLS = {
    "forehand": {
        "verb": "hit a forehand",
        "gerund": "hitting forehands",
        "mistake": "swung like a hammer at a nail",
        "correction": "turned the shoulders and met the ball out in front",
        "effect": "the ball flew straight and true",
        "focus_gain": 1,
        "balance_gain": 1,
        "power_gain": 1,
        "lesson": "a good forehand starts with watching the ball and planting the feet",
    },
    "serve": {
        "verb": "serve the ball",
        "gerund": "serving",
        "mistake": "tossed the ball too high and chased it with wild hope",
        "correction": "tossed it gently and reached up like a ladder to the sky",
        "effect": "the serve dropped in like a postcard from the clouds",
        "focus_gain": 2,
        "balance_gain": 0,
        "power_gain": 1,
        "lesson": "a serve works best when the toss is calm and the body stays smooth",
    },
    "backhand": {
        "verb": "hit a backhand",
        "gerund": "hitting backhands",
        "mistake": "twisted around like a windy weather vane",
        "correction": "turned sideways and let the racket whisper across the ball",
        "effect": "the ball zipped away like a sparrow shot from a sling",
        "focus_gain": 1,
        "balance_gain": 2,
        "power_gain": 0,
        "lesson": "a backhand needs balance more than bravado",
    },
}

GEAR = {
    "racket": {
        "label": "a wooden racket",
        "kind": "racket",
        "weight": 1,
        "power": 1,
    },
    "shoes": {
        "label": "grippy tennis shoes",
        "kind": "shoes",
        "weight": 1,
        "balance": 2,
    },
    "cap": {
        "label": "a sun cap",
        "kind": "cap",
        "weight": 0,
        "focus": 1,
    },
}

# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carries: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    court: dict
    entities: dict[str, Entity] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        clone = World(self.court)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "worn_by": v.worn_by,
            "carries": set(v.carries), "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    court: str
    drill: str
    gear: str
    name: str
    coach: str
    characteristic: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def reasonableness_gate(params: StoryParams) -> None:
    drill = DRILLS[params.drill]
    if params.gear == "cap" and params.drill == "forehand":
        return
    if params.gear == "cap" and params.drill == "serve":
        return
    if params.gear == "shoes":
        return
    if params.gear == "racket":
        return
    raise StoryError("That gear and drill do not make a believable tennis lesson.")


def predict_miss(world: World, player: Entity, drill: dict) -> bool:
    sim = world.copy()
    p = sim.get(player.id)
    p.memes["confidence"] = p.memes.get("confidence", 0) + 1
    p.meters["wildness"] = p.meters.get("wildness", 0) + 1
    return p.meters.get("focus", 0) < THRESHOLD


def intro(world: World, player: Entity, coach: Entity) -> None:
    world.say(
        f"{player.id} was a {player.label} child with a {player.meters['height_word']} way of standing, "
        f"and people in town said {player.pronoun('subject')} could make a tennis court look small."
    )
    world.say(
        f"{coach.label} had seen more tennis balls than a bakery has buns, and {coach.pronoun('subject')} knew "
        f"that big swagger does not always mean good play."
    )


def setup(world: World, player: Entity, coach: Entity, drill: dict) -> None:
    world.say(world.court["detail"])
    world.say(
        f"{player.id} loved {drill['gerund']}, because every clean hit sounded like a little thunderclap."
    )
    world.say(
        f"{coach.label} promised to teach {player.id} the {drill['verb']} way, and said the day would end with a lesson learned."
    )


def hand_out_gear(world: World, player: Entity, gear: dict) -> None:
    item = world.add(Entity(id=gear["kind"], label=gear["label"], owner=player.id))
    item.worn_by = player.id
    if gear["kind"] == "shoes":
        player.meters["balance"] = player.meters.get("balance", 0) + 2
    elif gear["kind"] == "cap":
        player.memes["focus"] = player.memes.get("focus", 0) + 1
    elif gear["kind"] == "racket":
        player.meters["power"] = player.meters.get("power", 0) + 1
    world.say(f"{coach.label} handed over {gear['label']} so {player.id} could practice the right way.")


def attempt(world: World, player: Entity, coach: Entity, drill: dict) -> None:
    player.meters["wildness"] = player.meters.get("wildness", 0) + 1
    player.memes["pride"] = player.memes.get("pride", 0) + 1
    world.say(
        f"At first {player.id} tried to {drill['mistake']}, and the ball popped away like it had grown wings."
    )
    if predict_miss(world, player, drill):
        world.say(
            f"{coach.label} called out, \"Easy now! In tennis, the ball listens best when you watch it.\""
        )


def correction(world: World, player: Entity, coach: Entity, drill: dict) -> None:
    player.meters["focus"] = player.meters.get("focus", 0) + drill["focus_gain"]
    player.meters["balance"] = player.meters.get("balance", 0) + drill["balance_gain"]
    player.meters["power"] = player.meters.get("power", 0) + drill["power_gain"]
    player.memes["pride"] = max(0.0, player.memes.get("pride", 0) - 1)
    player.memes["confidence"] = player.memes.get("confidence", 0) + 1
    world.say(
        f"{coach.label} showed {player.id} how to {drill['correction']}, and suddenly the swing felt as steady as a church bell."
    )
    world.say(
        f"{player.id} tried again, and {drill['effect']}."
    )
    world.say(
        f"{player.id} smiled and realized the biggest part of tennis was not showing off; it was learning."
    )


def ending(world: World, player: Entity, coach: Entity, drill: dict) -> None:
    world.say(
        f"By sunset, {player.id} could {drill['verb']} without wobbling, and {coach.label} said the finest trophy was a lesson learned."
    )
    world.say(
        f"{player.id} tucked {player.pronoun('possessive')} racket under {player.pronoun('possessive')} arm and walked home feeling taller than a flagpole."
    )


def tell_story(params: StoryParams) -> World:
    reasonableness_gate(params)
    court = COURTS[params.court]
    drill = DRILLS[params.drill]
    gear = GEAR[params.gear]
    world = World(court)

    player = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Ruby", "June", "Pia", "Nina"} else "boy",
        label=f"{params.characteristic} tennis player",
        meters={"height_word": 1, "focus": 1, "balance": 0, "power": 0, "wildness": 0},
        memes={"confidence": 1, "pride": 0},
    ))
    coach = world.add(Entity(
        id=params.coach,
        kind="character",
        type="adult",
        label=params.coach,
        meters={"patience": 2},
        memes={"calm": 2},
    ))

    world.facts.update(player=player, coach=coach, drill=drill, gear=gear, court=court)

    intro(world, player, coach)
    world.say("")
    setup(world, player, coach, drill)
    hand_out_gear(world, player, gear)
    world.say("")
    attempt(world, player, coach, drill)
    correction(world, player, coach, drill)
    world.say("")
    ending(world, player, coach, drill)

    world.facts["lesson"] = drill["lesson"]
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    player = f["player"]
    drill = f["drill"]
    court = f["court"]
    return [
        f'Write a tall tale about a {player.label} child learning tennis on {court["label"]}.',
        f"Tell a child-friendly story where {player.id} first makes a wild tennis mistake, then learns the smarter way to {drill['verb']}.",
        f'Write a story with the word "tennis" and a clear lesson learned at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    player = f["player"]
    coach = f["coach"]
    drill = f["drill"]
    gear = f["gear"]
    court = f["court"]
    return [
        QAItem(
            question=f"What was {player.id} learning to do at {court['label']}?",
            answer=f"{player.id} was learning to {drill['verb']} with {coach.label} on {court['label']}.",
        ),
        QAItem(
            question=f"What mistake did {player.id} make before learning the better way?",
            answer=f"At first {player.id} {drill['mistake']}, and the ball shot off like it had a mind of its own.",
        ),
        QAItem(
            question=f"What helped {player.id} improve in the tennis lesson?",
            answer=f"{coach.label} showed the correction, and {gear['label']} helped make the practice steadier.",
        ),
        QAItem(
            question=f"What did {player.id} learn by the end?",
            answer=f"{player.id} learned that tennis is not only about big swings; it is also about watching the ball, keeping balance, and learning carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where players use rackets to hit a ball back and forth over a net.",
        ),
        QAItem(
            question="Why are tennis shoes helpful?",
            answer="Tennis shoes are helpful because they give better grip, so a player can stop and turn without slipping.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is something someone understands better after trying, making a mistake, and then doing it the wiser way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
player(X) :- player_name(X).
coach(X) :- coach_name(X).
drill(D) :- drill_name(D).
gear(G) :- gear_name(G).

lesson_learned(P,D) :- player(P), drill(D), mistake_first(P,D), correction_done(P,D).

compatible(G,D) :- gear_kind(G,racket), drill_name(D,forehand).
compatible(G,D) :- gear_kind(G,shoes), drill_name(D,backhand).
compatible(G,D) :- gear_kind(G,cap), drill_name(D,serve).

valid_story(Court,D,G) :- court(Court), drill(D), gear(G), compatible(G,D).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid in COURTS:
        lines.append(asp.fact("court", cid))
    for did in DRILLS:
        lines.append(asp.fact("drill_name", did))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear_name", gid))
        lines.append(asp.fact("gear_kind", gid, g["kind"]))
    for name in PLAYER_NAMES:
        lines.append(asp.fact("player_name", name))
    for name in COACH_NAMES:
        lines.append(asp.fact("coach_name", name))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    # Basic parity check: ensure the inline rules compile and yield at least one model.
    import asp
    model = asp.one_model(asp_program())
    if model is None:
        print("ASP produced no model.")
        return 1
    print("OK: ASP program compiled and produced a model.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale tennis storyworld with a lesson learned.")
    ap.add_argument("--court", choices=COURTS)
    ap.add_argument("--drill", choices=DRILLS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name", choices=PLAYER_NAMES)
    ap.add_argument("--coach", choices=COACH_NAMES)
    ap.add_argument("--characteristic", choices=CHARACTERISTICS)
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
    court = args.court or rng.choice(list(COURTS))
    drill = args.drill or rng.choice(list(DRILLS))
    gear = args.gear or rng.choice(list(GEAR))
    name = args.name or rng.choice(PLAYER_NAMES)
    coach = args.coach or rng.choice(COACH_NAMES)
    characteristic = args.characteristic or rng.choice(CHARACTERISTICS)
    if gear == "cap" and drill == "backhand":
        raise StoryError("A cap does not meaningfully help a backhand lesson here.")
    return StoryParams(court=court, drill=drill, gear=gear, name=name, coach=coach, characteristic=characteristic)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print("\n--- trace ---")
        print(json.dumps({
            "facts": {
                "lesson": sample.world.facts.get("lesson"),
                "court": sample.world.facts["court"]["label"],
            }
        }, indent=2))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(court="sunny_court", drill="forehand", gear="shoes", name="Milo", coach="Coach Bell", characteristic="tall"),
    StoryParams(court="school_gym", drill="serve", gear="cap", name="Ruby", coach="Coach Sera", characteristic="bright-eyed"),
    StoryParams(court="windy_park", drill="backhand", gear="shoes", name="Theo", coach="Coach Pike", characteristic="quick"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program())
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
            except StoryError as e:
                print(e)
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
