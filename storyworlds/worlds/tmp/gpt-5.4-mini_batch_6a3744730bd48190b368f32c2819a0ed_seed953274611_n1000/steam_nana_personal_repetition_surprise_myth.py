#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/steam_nana_personal_repetition_surprise_myth.py
================================================================================

A standalone storyworld for a small mythic tale about steam, a nana, a personal
promise, repetition, and a surprise.

The world is built from a tiny simulated domain: a child and Nana prepare tea at
a hill shrine. Repeated actions build steam and memory. The steam reveals an
unexpected spirit, and the ending turns that surprise into a personal gift.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/steam_nana_personal_repetition_surprise_myth.py
    python storyworlds/worlds/gpt-5.4-mini/steam_nana_personal_repetition_surprise_myth.py --qa
    python storyworlds/worlds/gpt-5.4-mini/steam_nana_personal_repetition_surprise_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REPETITION_MIN = 3
SURPRISE_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "nana", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    details: str
    quiet: str
    surprise_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ritual:
    id: str
    gesture: str
    repeat_line: str
    offering: str
    steam_gain: float
    memory_gain: float
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    effect: str
    gift: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_steam(world: World) -> list[str]:
    out = []
    kettle = world.entities.get("kettle")
    if not kettle or kettle.meters["heated"] < THRESHOLD:
        return out
    sig = ("steam",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kettle.meters["steam"] += 1
    if "air" in world.entities:
        world.get("air").meters["steam"] += 1
    out.append("__steam__")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    if world.entities.get("air", Entity("x")).meters["steam"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["wonder"] += 1
    child.memes["surprise"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("steam", _r_steam), Rule("surprise", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def repeat_chant(world: World, child: Entity, ritual: Ritual) -> None:
    child.memes["anticipation"] += 1
    world.say(
        f"At the hill shrine, {child.id} and Nana began the old work: "
        f"{ritual.repeat_line} {ritual.repeat_line} {ritual.repeat_line}."
    )
    world.say(
        f"Again and again, they followed the same small steps, and the pot "
        f"grew warm with a faithful sigh."
    )


def tend_fire(world: World, nana: Entity, ritual: Ritual) -> None:
    nana.meters["care"] += 1
    kettle = world.get("kettle")
    kettle.meters["heated"] += ritual.memory_gain
    world.say(
        f"Nana set the kettle on the coals and whispered, "
        f'"{ritual.gesture}, little one."'
    )
    world.say(
        f"She did it once, then once more, then one more time, because old songs "
        f"work best when they are kept close."
    )
    propagate(world, narrate=True)


def watch_steam(world: World, child: Entity, place: Place) -> None:
    if world.get("air").meters["steam"] >= THRESHOLD:
        world.say(
            f"White steam rose over {place.label}, and the air turned soft as "
            f"breath."
        )
        world.say(
            f"{child.id} watched it curl around the stones. It felt personal, as "
            f"if the hill itself had leaned in to listen."
        )


def reveal_surprise(world: World, surprise: Surprise, child: Entity, nana: Entity) -> None:
    if child.memes["surprise"] < SURPRISE_MIN:
        return
    world.say(
        f"Then the steam split open, and {surprise.reveal}."
    )
    world.say(
        f"{surprise.effect} Nana laughed, not with fear but with the calm of "
        f"someone who had always known the mountain kept a secret."
    )
    child.memes["joy"] += 1
    child.meters["gifted"] += 1
    world.get("gift").label = surprise.gift
    world.say(
        f"She placed {surprise.gift} in {child.id}'s hands and said it was a "
        f"personal blessing for remembering the old way."
    )


def close_story(world: World, child: Entity, nana: Entity) -> None:
    world.say(
        f"By evening, the kettle was quiet, the steam was gone, and {child.id} "
        f"still felt the surprise shining inside {child.pronoun('possessive')} chest."
    )
    world.say(
        f"{nana.id} patted {child.pronoun('possessive')} hand. " 
        f'"Some gifts arrive as steam," she said, "and some arrive as memory."'
    )
    world.say(
        f"So the child went home with a warm cup, a new song, and a story that "
        f"belonged to {child.id} alone."
    )


def tell(place: Place, ritual: Ritual, surprise: Surprise, child_name: str = "Mina",
         child_gender: str = "girl", nana_name: str = "Nana") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    nana = world.add(Entity(id=nana_name, kind="character", type="nana", role="mentor", label="Nana"))
    hill = world.add(Entity(id="hill", kind="place", type="place", label=place.label))
    air = world.add(Entity(id="air", kind="thing", type="air", label="air"))
    kettle = world.add(Entity(id="kettle", kind="thing", type="kettle", label="kettle"))
    gift = world.add(Entity(id="gift", kind="thing", type="gift", label="gift"))

    world.facts.update(place=place, ritual=ritual, surprise=surprise, child=child, nana=nana, hill=hill)
    world.say(f"On the quiet hill, {place.details}")
    repeat_chant(world, child, ritual)
    world.para()
    tend_fire(world, nana, ritual)
    watch_steam(world, child, place)
    world.para()
    reveal_surprise(world, surprise, child, nana)
    world.para()
    close_story(world, child, nana)
    world.facts["steam"] = kettle.meters["steam"]
    world.facts["wonder"] = child.memes["wonder"]
    return world


PLACES = {
    "hill_shrine": Place(
        id="hill_shrine",
        label="the hill shrine",
        details="an old stone shrine stood on the hill, wrapped in moss and morning light.",
        quiet="quiet",
        surprise_word="secret",
        tags={"myth", "shrine"},
    ),
    "river_steps": Place(
        id="river_steps",
        label="the river steps",
        details="broad steps went down to the river, where reeds bowed in the wind.",
        quiet="listening",
        surprise_word="whisper",
        tags={"myth", "river"},
    ),
}

RITUALS = {
    "tea": Ritual(
        id="tea",
        gesture="Pour, pause, pour",
        repeat_line="pour, pause",
        offering="tea leaves",
        steam_gain=1.0,
        memory_gain=1.0,
        tags={"steam", "repetition"},
    ),
    "incense": Ritual(
        id="incense",
        gesture="light, bow, wait",
        repeat_line="bow, wait",
        offering="incense",
        steam_gain=1.0,
        memory_gain=1.0,
        tags={"steam", "repetition"},
    ),
}

SURPRISES = {
    "fox_spirit": Surprise(
        id="fox_spirit",
        reveal="a fox spirit wore the steam like a silver cloak",
        effect="Its tail brushed the cup, and the water tasted like moonlight.",
        gift="a tiny charm shaped like a crescent moon",
        tags={"surprise", "myth"},
    ),
    "bird_messenger": Surprise(
        id="bird_messenger",
        reveal="a bird made of mist unfolded from the steam",
        effect="It circled Nana's head three times, as if counting the family's names.",
        gift="a blue feather tied with red thread",
        tags={"surprise", "myth"},
    ),
}

CURATED = [
    StoryParams(place="hill_shrine", ritual="tea", surprise="fox_spirit", child_name="Mina", child_gender="girl", nana_name="Nana"),
    StoryParams(place="river_steps", ritual="incense", surprise="bird_messenger", child_name="Taro", child_gender="boy", nana_name="Nana"),
    StoryParams(place="hill_shrine", ritual="tea", surprise="bird_messenger", child_name="Aya", child_gender="girl", nana_name="Nana"),
]


@dataclass
class StoryParams:
    place: str
    ritual: str
    surprise: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    nana_name: str = "Nana"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, r, s) for p in PLACES for r in RITUALS for s in SURPRISES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic steam storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--nana", default="Nana")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ritual is None or c[1] == args.ritual)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ritual, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mina", "Taro", "Aya", "Sora", "Hana", "Ren"])
    nana = args.nana
    return StoryParams(place=place, ritual=ritual, surprise=surprise, child_name=name, child_gender=gender, nana_name=nana)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story that includes the words "steam", "{f["nana"].id}", and "personal".',
        f"Tell a calm, repeated ritual story where {f['child'].id} and {f['nana'].id} make tea, and a surprise appears in the steam.",
        f"Write a short myth for children where repetition leads to steam, then a personal gift arrives as a surprise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    nana = f["nana"]
    place = f["place"]
    surprise = f["surprise"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {nana.id} at {place.label}. They work together in a quiet, myth-like way."),
        ("Why did the steam matter?",
         f"The steam rose because the kettle grew hot after the repeated ritual. That steam mattered because it hid a surprise until the air opened up."),
        ("What was the surprise?",
         f"{surprise.reveal}. It changed the ending from a simple tea-making moment into a magical one."),
        ("What made the story feel personal?",
         f"The gift was meant for {child.id} alone, so the blessing felt personal. It belonged to {child.id} like a private song passed down by Nana."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is steam?",
         "Steam is warm water vapor. It rises when water gets hot enough."),
        ("What does Nana mean in this story?",
         "Nana is a grandmother. In a family story, Nana often guides the child with warmth and care."),
        ("What is repetition?",
         "Repetition means doing the same thing again and again. In stories, repetition can make a ritual feel important or magical."),
        ("What is a surprise?",
         "A surprise is something unexpected. It can make a story feel exciting because the reader does not know it is coming."),
    ]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
steam :- heated(kettle).
surprise :- steam, reveal_hidden.
valid(P,R,S) :- place(P), ritual(R), surprise_cfg(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in RITUALS:
        lines.append(asp.fact("ritual", r))
    for s in SURPRISES:
        lines.append(asp.fact("surprise_cfg", s))
    lines.append(asp.fact("heated", "kettle"))
    lines.append(asp.fact("reveal_hidden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    rc = 0 if a == b else 1
    if rc == 0:
        print(f"OK: ASP matches Python ({len(a)} combos).")
    else:
        print("MISMATCH:")
        print(" only in asp:", sorted(a - b))
        print(" only in py:", sorted(b - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.ritual not in RITUALS or params.surprise not in SURPRISES:
        raise StoryError("(Invalid parameters for this storyworld.)")
    world = tell(PLACES[params.place], RITUALS[params.ritual], SURPRISES[params.surprise],
                 child_name=params.child_name, child_gender=params.child_gender, nana_name=params.nana_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible stories:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
