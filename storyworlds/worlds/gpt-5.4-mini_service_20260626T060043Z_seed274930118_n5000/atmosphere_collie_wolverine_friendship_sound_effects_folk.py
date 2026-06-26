#!/usr/bin/env python3
"""
Storyworld: atmosphere, collie, wolverine, friendship, and sound effects in a
small folk-tale domain.

A collie and a wolverine meet on a windy hillside. The air itself carries
messages: a hush, a whistle, a growl, a bark, and the soft sound of helping
paws. The story turns when each animal misunderstands the other's sounds and
then learns to listen. The ending proves the change through a shared song in
the atmosphere.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"collie", "dog"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"wolverine"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
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


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    weather: str
    collie_name: str
    wolverine_name: str
    seed: Optional[int] = None


SETTINGS = {
    "hillside": {
        "place": "the windy hillside",
        "atmosphere": "clear and bright",
    },
    "pinewood": {
        "place": "the pinewood path",
        "atmosphere": "cool and whispering",
    },
    "riverside": {
        "place": "the riverside meadow",
        "atmosphere": "misty and soft",
    },
}

WEATHERS = {
    "breezy": {
        "sky": "breezy",
        "sound": "whoosh",
        "mood": "restless",
    },
    "misty": {
        "sky": "misty",
        "sound": "hush",
        "mood": "gentle",
    },
    "stormy": {
        "sky": "stormy",
        "sound": "rumble",
        "mood": "rough",
    },
}

COLLIE_NAMES = ["Mara", "Lila", "Nell", "Bess", "Tilly", "Runa"]
WOLVERINE_NAMES = ["Bran", "Orin", "Garr", "Borek", "Tor", "Soren"]


# ---------------------------------------------------------------------------
# Narrative state and rules
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    weather = WEATHERS[params.weather]
    world = World(setting=setting["place"], weather=weather["sky"])

    collie = world.add(Entity(
        id=params.collie_name,
        kind="character",
        type="collie",
        label="a bright-eyed collie",
        phrase=f"a bright-eyed collie named {params.collie_name}",
        meters={"distance": 0.0, "wind": 0.0},
        memes={"curiosity": 1.0, "hope": 0.0, "friendship": 0.0, "worry": 0.0},
    ))
    wolverine = world.add(Entity(
        id=params.wolverine_name,
        kind="character",
        type="wolverine",
        label="a shaggy wolverine",
        phrase=f"a shaggy wolverine named {params.wolverine_name}",
        meters={"distance": 0.0, "wind": 0.0},
        memes={"curiosity": 1.0, "hope": 0.0, "friendship": 0.0, "worry": 0.0, "pride": 1.0},
    ))

    world.facts.update(
        collie=collie,
        wolverine=wolverine,
        setting=params.setting,
        weather=params.weather,
        atmosphere=setting["atmosphere"],
        sky=weather["sky"],
        sound=weather["sound"],
        mood=weather["mood"],
    )
    return world


def sound_effect(text: str) -> str:
    return f"*{text}*"


def speak(world: World, speaker: Entity, line: str, sound: str) -> None:
    world.say(f'{speaker.id} said, "{line}" {sound}.')


def atmosphere_line(world: World) -> str:
    return f"The atmosphere above the {world.setting} felt {world.facts['atmosphere']}."


def first_meeting(world: World) -> None:
    c = world.facts["collie"]
    w = world.facts["wolverine"]
    world.say(f"Once, on {world.setting}, there lived {c.phrase} and {w.phrase}.")
    world.say(atmosphere_line(world))
    world.say(
        f"The wind went {sound_effect(world.facts['sound']).strip('*')}, and the grass replied with a soft rustle."
    )
    world.say(
        f"{c.id} was quick to listen to every little sound, and {w.id} was quick to sniff out any stranger."
    )


def misunderstanding(world: World) -> None:
    c = world.facts["collie"]
    w = world.facts["wolverine"]
    world.para()
    world.say(
        f"One morning, {c.id} barked, {sound_effect('yip-yip')}, because {c.pronoun()} had found a berry patch near a stone."
    )
    world.say(
        f"{w.id} answered with a low {sound_effect('grr')} because {w.pronoun()} thought the bark meant trouble."
    )
    c.memes["worry"] += 1
    w.memes["worry"] += 1
    c.meters["wind"] += 1
    w.meters["wind"] += 1
    world.say(
        f"The whole hillside seemed to hold its breath, and even the leaves made a little {sound_effect('shiver')} sound."
    )


def helper_turn(world: World) -> None:
    c = world.facts["collie"]
    w = world.facts["wolverine"]
    world.para()
    world.say(
        f"{c.id} trotted closer and wagged {c.pronoun('possessive')} tail slowly, saying, "
        f'"I am not here to chase you away."'
    )
    world.say(
        f"{w.id} blinked, sat down, and let out a thoughtful {sound_effect('hmm')}. "
        f"Then {w.pronoun()} nudged the berry patch back toward {c.id}."
    )
    c.memes["hope"] += 1
    w.memes["hope"] += 1
    c.memes["friendship"] += 1
    w.memes["friendship"] += 1


def resolution(world: World) -> None:
    c = world.facts["collie"]
    w = world.facts["wolverine"]
    world.para()
    world.say(
        f"After that, {c.id} and {w.id} listened before they leaped. "
        f"The wind still went {sound_effect(world.facts['sound']).strip('*')}, but it no longer sounded lonely."
    )
    world.say(
        f"{c.id} sang a bright {sound_effect('woof-woo')} and {w.id} answered with a warm {sound_effect('mrrp')}. "
        f"Together their voices made the atmosphere feel friendly."
    )
    world.say(
        f"By sunset, the two animals were sharing berries on the hillside, and the sky above them looked kind."
    )
    c.meters["distance"] += 1
    w.meters["distance"] += 1
    c.memes["friendship"] += 1
    w.memes["friendship"] += 1
    c.memes["worry"] = 0
    w.memes["worry"] = 0


def tell(params: StoryParams) -> World:
    world = make_world(params)
    first_meeting(world)
    misunderstanding(world)
    helper_turn(world)
    resolution(world)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: str, weather: str) -> bool:
    return setting in SETTINGS and weather in WEATHERS


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A setting and weather are compatible when both are present in the registry.
valid_story(S,W) :- setting(S), weather(W).

% The friendship turn is reasonable when the air is active and the two
% animals share the hillside story.
shared_story(S,W) :- valid_story(S,W), atmosphere(S,A), mood(W,M), A != "", M != "".
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s, data in SETTINGS.items():
        lines.append(asp.fact("setting", s))
        lines.append(asp.fact("atmosphere", s, data["atmosphere"]))
    for w, data in WEATHERS.items():
        lines.append(asp.fact("weather", w))
        lines.append(asp.fact("sound", w, data["sound"]))
        lines.append(asp.fact("mood", w, data["mood"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {(s, w) for s in SETTINGS for w in WEATHERS if valid_combo(s, w)}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about a collie and a wolverine on {world.setting} where sound effects matter.',
        f'Tell a gentle story where {f["collie"].id} and {f["wolverine"].id} first misunderstand each other, then become friends.',
        f'Write a child-friendly tale with the words atmosphere, collie, wolverine, and a clear happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["collie"]
    w = world.facts["wolverine"]
    return [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {c.phrase} and {w.phrase}. They begin as strangers and end as friends.",
        ),
        QAItem(
            question=f"Why did {w.id} growl when {c.id} barked near the berry patch?",
            answer=f"{w.id} thought the bark meant danger. After {c.id} explained with a kind tail wag, {w.id} understood that the bark was only a friendly call.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"At first the two animals worried and did not understand each other, but by the end they listened, shared berries, and felt friendship in the atmosphere above the {world.setting}.",
        ),
        QAItem(
            question=f"What sound did the wind make in the story?",
            answer=f"The wind went {world.facts['sound']}, which helped make the scene feel alive and a little mysterious.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the atmosphere?",
            answer="The atmosphere is the air around us. It is what we breathe and what carries the wind, smells, and sounds.",
        ),
        QAItem(
            question="What does a collie sound like?",
            answer="A collie often barks in a bright, alert way. In a story, that sound can show excitement or warning.",
        ),
        QAItem(
            question="What does a wolverine sound like?",
            answer="A wolverine can growl or make rough little noises. In a story, those sounds can make the scene feel wild.",
        ),
        QAItem(
            question="Why do folk tales often repeat sounds?",
            answer="Folk tales repeat sounds so the story feels musical and easy to remember, almost like a little song.",
        ),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:12} ({e.type:9}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  setting={world.setting}")
    lines.append(f"  weather={world.weather}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.weather and args.weather not in WEATHERS:
        raise StoryError("Unknown weather.")
    setting = args.setting or rng.choice(list(SETTINGS))
    weather = args.weather or rng.choice(list(WEATHERS))
    if not valid_combo(setting, weather):
        raise StoryError("No valid combination matches the given options.")
    collie_name = args.collie_name or rng.choice(COLLIE_NAMES)
    wolverine_name = args.wolverine_name or rng.choice(WOLVERINE_NAMES)
    if collie_name == wolverine_name:
        raise StoryError("The collie and wolverine need different names.")
    return StoryParams(
        setting=setting,
        weather=weather,
        collie_name=collie_name,
        wolverine_name=wolverine_name,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale story world about atmosphere, a collie, and a wolverine becoming friends."
    )
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--weather", choices=list(WEATHERS))
    ap.add_argument("--collie-name")
    ap.add_argument("--wolverine-name")
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


CURATED = [
    StoryParams(setting="hillside", weather="breezy", collie_name="Mara", wolverine_name="Bran"),
    StoryParams(setting="pinewood", weather="misty", collie_name="Tilly", wolverine_name="Orin"),
    StoryParams(setting="riverside", weather="stormy", collie_name="Bess", wolverine_name="Tor"),
]


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
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:\n")
        for s, w in stories:
            print(f"  {s} / {w}")
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
            header = f"### {p.collie_name} and {p.wolverine_name}: {p.setting} in {p.weather} weather"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
