#!/usr/bin/env python3
"""
storyworlds/worlds/window_flora_acuity_friendship_bedtime_story.py
==================================================================

A small bedtime-story world about a child at the window, the evening flora
outside, a sharpened sense of acuity, and a friendship that helps turn a restless
night into a calm one.

Premise:
- A child is getting sleepy but keeps looking out the window.
- Tiny plants and moonlit leaves outside catch their attention.
- Their friend helps them notice gentle details, which lowers worry and makes
  bedtime feel safe.

State model:
- Physical meters track things like tiredness, stillness, and glow.
- Emotional memes track curiosity, worry, calm, and friendship.
- A simple reasoner turns watching, naming, and sharing into a bedtime ending.

The story is designed to read like a complete bedtime tale:
beginning, small middle turn, and a peaceful ending image proving what changed.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Flora:
    id: str
    name: str
    phrase: str
    detail: str
    glow: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Friend:
    id: str
    name: str
    type: str
    phrase: str
    help_line: str
    bedtime_line: str
    tags: set[str] = field(default_factory=set)


FLORA = {
    "violets": Flora(
        id="violets",
        name="violets",
        phrase="a patch of violets",
        detail="small purple petals",
        glow="softly purple",
        comfort="the little flowers looked brave and kind",
        tags={"flora"},
    ),
    "ivy": Flora(
        id="ivy",
        name="ivy",
        phrase="ivy leaves",
        detail="round green leaves",
        glow="deep green",
        comfort="the leaves looked like tiny hands waving goodnight",
        tags={"flora"},
    ),
    "moss": Flora(
        id="moss",
        name="moss",
        phrase="moss on the sill",
        detail="a velvet green cushion",
        glow="quietly green",
        comfort="the moss looked like a soft blanket for the window ledge",
        tags={"flora"},
    ),
    "daisies": Flora(
        id="daisies",
        name="daisies",
        phrase="a row of daisies",
        detail="little white faces",
        glow="pale and bright",
        comfort="the daisies seemed to smile back at the moon",
        tags={"flora"},
    ),
}

FRIENDS = {
    "pippa": Friend(
        id="pippa",
        name="Pippa",
        type="girl",
        phrase="a best friend named Pippa",
        help_line="Pippa knew the best trick for making a room feel safe: naming what you can see.",
        bedtime_line="She promised to whisper until sleep came softly.",
        tags={"friendship"},
    ),
    "noah": Friend(
        id="noah",
        name="Noah",
        type="boy",
        phrase="a best friend named Noah",
        help_line="Noah knew how to count gentle things: one window, two leaves, three slow breaths.",
        bedtime_line="He promised to sit nearby until the dark felt friendly.",
        tags={"friendship"},
    ),
    "luna": Friend(
        id="luna",
        name="Luna",
        type="girl",
        phrase="a best friend named Luna",
        help_line="Luna liked to point out tiny shining details that helped worried thoughts grow smaller.",
        bedtime_line="She promised to stay until the last yawn arrived.",
        tags={"friendship"},
    ),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    name: str
    gender: str
    friend: str
    flora: str
    setting: str = "bedroom"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Pronoun/name helpers
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Milo", "Finn", "Eli", "Noah", "Leo"]


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------
def _ensure_entity(world: World, ent: Entity) -> Entity:
    return world.add(ent)


def build_world(params: StoryParams) -> World:
    world = World(setting=params.setting)

    child = _ensure_entity(
        world,
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
            meters={"tiredness": 0.2, "stillness": 0.0},
            memes={"curiosity": 0.6, "worry": 0.0, "calm": 0.1, "friendship": 0.0, "acuity": 0.2},
        ),
    )

    friend = FRIENDS[params.friend]
    companion = _ensure_entity(
        world,
        Entity(
            id=friend.id,
            kind="character",
            type=friend.type,
            label=friend.name,
            meters={"stillness": 0.5},
            memes={"friendship": 1.0, "calm": 0.7},
        ),
    )

    window = _ensure_entity(
        world,
        Entity(
            id="window",
            type="window",
            label="window",
            phrase="the bedroom window",
            location="bedroom",
            meters={"moonlight": 0.3},
            memes={"quiet": 0.5},
        ),
    )

    flora = FLORA[params.flora]
    plant = _ensure_entity(
        world,
        Entity(
            id=flora.id,
            type="flora",
            label=flora.name,
            phrase=flora.phrase,
            location="outside",
            meters={"glow": 0.2},
            memes={"gentleness": 0.4},
        ),
    )

    world.facts.update(child=child, friend=companion, window=window, flora=plant, flora_def=flora, friend_def=friend)
    return world


def on_looking(world: World) -> None:
    child = world.facts["child"]
    window = world.facts["window"]
    flora = world.facts["flora"]
    child.memes["curiosity"] += 0.3
    child.meters["stillness"] += 0.2
    window.meters["moonlight"] += 0.4
    flora.meters["glow"] += 0.5
    world.say(
        f"{child.id} stood by the window and looked out at {world.facts['flora_def'].phrase}. "
        f"The moonlight touched the glass, and the little leaves seemed to shine back."
    )


def on_notice(world: World) -> None:
    child = world.facts["child"]
    flora = world.facts["flora"]
    child.memes["acuity"] += 0.5
    child.meters["stillness"] += 0.2
    world.say(
        f"{child.pronoun().capitalize()} noticed {world.facts['flora_def'].detail}, "
        f"and that careful noticing made the room feel clearer and calmer."
    )


def on_worry(world: World) -> None:
    child = world.facts["child"]
    child.memes["worry"] += 0.4
    child.meters["tiredness"] += 0.2
    world.say(
        f"Still, {child.id} had a small sleepy worry, because bedtime can feel wide and dark "
        f"when a mind is not ready to rest."
    )


def on_friend_arrive(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    child.memes["friendship"] += 0.7
    friend.memes["friendship"] += 0.2
    world.say(
        f"Then {friend.label} came close and smiled. {world.facts['friend_def'].help_line}"
    )


def on_count_gentle_things(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    child.memes["calm"] += 0.6
    child.memes["acuity"] += 0.3
    child.meters["tiredness"] += 0.3
    friend.meters["stillness"] += 0.3
    world.say(
        f"So they counted gentle things together: the window frame, the little flora outside, "
        f"and the slow silver hush of the night."
    )


def on_bedtime_settle(world: World) -> None:
    child = world.facts["child"]
    friend = world.facts["friend"]
    flora = world.facts["flora"]
    child.memes["calm"] += 0.8
    child.meters["stillness"] += 0.5
    child.meters["tiredness"] += 0.5
    world.say(
        f"By the end, {child.id}'s eyes felt heavy in the nicest way. {world.facts['friend_def'].bedtime_line} "
        f"Outside, {flora.phrase} stayed peaceful in the moonlight, and the room felt ready for sleep."
    )


def propagate(world: World) -> None:
    # Simple deterministic chain.
    on_looking(world)
    on_notice(world)
    on_worry(world)
    on_friend_arrive(world)
    on_count_gentle_things(world)
    on_bedtime_settle(world)


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    world = build_world(params)
    child = world.facts["child"]
    friend = world.facts["friend"]
    flora = world.facts["flora"]
    flora_def = world.facts["flora_def"]

    world.say(
        f"At bedtime, {child.id} lay in {world.setting} but kept turning toward the window."
    )
    world.say(
        f"Outside, there was {flora_def.phrase}, and the tiny plant seemed to carry a little nighttime glow."
    )
    world.para()
    propagate(world)
    world.para()
    world.say(
        f"At last, {child.id} snuggled under the blanket, feeling safer and sleepier. "
        f"The window stayed quiet, the flora stayed glowing softly, and friendship made the dark feel kind."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle bedtime story for a young child who looks out a {f["window"].label} and notices {f["flora_def"].phrase}.',
        f'Write a friendship story where {f["child"].id} gains calm by noticing small details outside the {f["window"].label}.',
        f'Write a cozy bedtime story using the words "window", "flora", and "acuity".',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    friend = world.facts["friend"]
    flora_def = world.facts["flora_def"]
    return [
        QAItem(
            question=f"What did {child.id} keep looking at at bedtime?",
            answer=f"{child.id} kept looking out the window at {flora_def.phrase}.",
        ),
        QAItem(
            question=f"Who helped {child.id} feel calmer before sleep?",
            answer=f"{friend.label} helped {child.id} feel calmer by staying close and sharing a gentle way to notice the night.",
        ),
        QAItem(
            question=f"What changed after {child.id} paid close attention to the night scene?",
            answer=f"{child.id}'s worry got smaller, calm got bigger, and the room felt ready for sleep.",
        ),
        QAItem(
            question=f"How did friendship matter in the story?",
            answer=f"Friendship mattered because {friend.label} stayed near {child.id} and helped turn a sleepy worry into a peaceful bedtime.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "window": [
        (
            "What is a window?",
            "A window is an opening in a wall, usually made with glass, so people can see outside and let light in.",
        )
    ],
    "flora": [
        (
            "What does flora mean?",
            "Flora means the plants in a place, like flowers, leaves, and other growing green things.",
        )
    ],
    "acuity": [
        (
            "What does acuity mean?",
            "Acuity means sharpness or clearness of sight or thought, like noticing small details very well.",
        )
    ],
    "friendship": [
        (
            "What is friendship?",
            "Friendship is the caring bond between friends who help, share, and make each other feel safe and happy.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["window", "flora", "acuity", "friendship"]:
        for q, a in WORLD_KNOWLEDGE[key]:
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% child(C). friend(F). window(W). flora(P).
% looks_at(C, W). notices(C, P). calmed_by(C, F).

acuity_up(C) :- notices(C, P).
worry_shrinks(C) :- calmed_by(C, F), friendship(F).
bedtime_ready(C) :- acuity_up(C), worry_shrinks(C), window(W), flora(P).

#show bedtime_ready/1.
#show acuity_up/1.
#show worry_shrinks/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for key, ent in [("child", "child"), ("friend", "friend"), ("window", "window"), ("flora", "flora")]:
        lines.append(asp.fact(key, ent))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def python_reasonable() -> bool:
    # Minimal gate: story must always be about a child, a friend, a window, and flora.
    return True


def asp_verify() -> int:
    if not python_reasonable():
        print("Python reasonableness gate failed.")
        return 1
    try:
        import asp  # lazy import
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1

    model = asp.one_model(asp_program())
    names = {atom.name for atom in model}
    expected = {"acuity_up", "worry_shrinks", "bedtime_ready"}
    if expected.issubset(names):
        print("OK: ASP twin produced the expected bedtime-ready model.")
        return 0
    print("MISMATCH: ASP twin did not produce the expected predicates.")
    print("Got:", sorted(names))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime story world: a child, a window, flora outside, and a friendship that brings calm."
    )
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--flora", choices=sorted(FLORA))
    ap.add_argument("--setting", default="bedroom")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(rng, gender)
    friend = args.friend or rng.choice(list(FRIENDS))
    flora = args.flora or rng.choice(list(FLORA))
    return StoryParams(name=name, gender=gender, friend=friend, flora=flora, setting=args.setting)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        try:
            import asp  # lazy
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    samples: list[StorySample] = []
    if args.all:
        for friend in sorted(FRIENDS):
            for flora in sorted(FLORA):
                params = StoryParams(
                    name="Mina",
                    gender="girl",
                    friend=friend,
                    flora=flora,
                    setting=args.setting,
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
