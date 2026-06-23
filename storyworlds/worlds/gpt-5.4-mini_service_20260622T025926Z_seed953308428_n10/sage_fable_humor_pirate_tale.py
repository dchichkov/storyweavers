#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T025926Z_seed953308428_n10/sage_fable_humor_pirate_tale.py
==============================================================================================================

A small standalone storyworld about a pirate crew, a wise sage, and a funny
fable that turns a grumpy problem into a bright sea lesson.

The story model uses a tiny state machine:
- a pirate crew wants to brag about a treasure route,
- a sage offers a fable instead of a boast,
- the fable causes laughter that changes the crew's mood,
- the ending image proves the change with a new shared habit.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- exposes StoryParams, build_parser, resolve_params, generate, emit, main
- supports --trace, --qa, --json, --asp, --verify, --show-asp, --all, --seed, -n
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


@dataclass
class Harbor:
    id: str
    place: str
    detail: str
    sway: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TaleNeed:
    id: str
    object_word: str
    phrase: str
    risk_word: str
    covers: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Responder:
    id: str
    label: str
    power: int
    sense: int
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    harbor: str
    need: str
    responder: str
    crew_name: str
    crew_type: str
    sage_name: str
    sage_type: str
    captain_name: str
    captain_type: str
    mood: str = "grumpy"
    seed: Optional[int] = None


class World:
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.events = list(self.events)
        return clone


HARBOURS = {
    "dock": Harbor(id="dock", place="the dock", detail="gulls circled the posts", sway="the ropes clacked softly", tags={"sea", "dock"}),
    "cove": Harbor(id="cove", place="the cove", detail="the water glittered against the rocks", sway="the little waves slapped the hull", tags={"sea", "cove"}),
    "island": Harbor(id="island", place="the island shore", detail="palms bent over the sand", sway="the tide licked the beach", tags={"sea", "island"}),
}

NEEDS = {
    "map": TaleNeed(id="map", object_word="map", phrase="a creased map", risk_word="lost, muddy treasure route", covers={"paper"}, tags={"map", "paper"}),
    "flag": TaleNeed(id="flag", object_word="flag", phrase="a bright little flag", risk_word="soggy pride", covers={"cloth"}, tags={"flag", "cloth"}),
    "lamp": TaleNeed(id="lamp", object_word="lamp", phrase="a brass lamp", risk_word="smoky confusion", covers={"light"}, tags={"lamp", "light"}),
}

RESPONDERS = {
    "calm_bell": Responder(id="calm_bell", label="a ship bell", power=1, sense=3, phrase="rang a cheerful bell", tags={"humor", "sound"}),
    "sea_shanty": Responder(id="sea_shanty", label="a sea shanty", power=2, sense=4, phrase="sang a silly sea shanty", tags={"humor", "song"}),
    "sage_fable": Responder(id="sage_fable", label="the sage's fable", power=3, sense=5, phrase="told a funny fable", tags={"humor", "fable", "sage"}),
    "big_story": Responder(id="big_story", label="a long story", power=1, sense=2, phrase="drifted into a long story", tags={"humor", "fable"}),
}

GIVEN_NAMES = ["Mina", "Rory", "Nell", "Pip", "Sage", "Lulu", "Bram", "Tess", "Milo", "June"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, harb in HARBOURS.items():
        for nid, need in NEEDS.items():
            for rid, responder in RESPONDERS.items():
                if responder.sense >= 3 and need.object_word in {"map", "flag", "lamp"}:
                    combos.append((hid, nid, rid))
    return combos


def explain_invalid_response(rid: str) -> str:
    return f"(No story: response '{rid}' is too weak or too plain for this pirate tale.)"


def explain_invalid_combo(hid: str, nid: str) -> str:
    return f"(No story: {HARBOURS[hid].place} does not fit the need '{NEEDS[nid].object_word}' in a way this tale can turn into a funny lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with a sage, a fable, and humor.")
    ap.add_argument("--harbor", choices=HARBOURS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--responder", choices=RESPONDERS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.responder and RESPONDERS[args.responder].sense < 3:
        raise StoryError(explain_invalid_response(args.responder))
    if args.harbor and args.need:
        if (args.harbor, args.need, args.responder or "sage_fable") and False:
            pass
    combos = [c for c in valid_combos()
              if (args.harbor is None or c[0] == args.harbor)
              and (args.need is None or c[1] == args.need)
              and (args.responder is None or c[2] == args.responder)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    harbor, need, responder = rng.choice(sorted(combos))
    crew_name = rng.choice(GIVEN_NAMES)
    sage_name = "Sage"
    captain_name = rng.choice([n for n in GIVEN_NAMES if n != crew_name])
    crew_type = rng.choice(["boy", "girl"])
    captain_type = "boy" if rng.random() < 0.5 else "girl"
    sage_type = "woman" if rng.random() < 0.5 else "man"
    mood = rng.choice(["grumpy", "sulky", "stubborn", "proud"])
    return StoryParams(
        harbor=harbor,
        need=need,
        responder=responder,
        crew_name=crew_name,
        crew_type=crew_type,
        sage_name=sage_name,
        sage_type=sage_type,
        captain_name=captain_name,
        captain_type=captain_type,
        mood=mood,
    )


def _crew_article(name: str) -> str:
    return name


def tell(harbor: Harbor, need: TaleNeed, responder: Responder, crew_name: str, crew_type: str, sage_name: str, sage_type: str, captain_name: str, captain_type: str, mood: str) -> World:
    world = World(harbor)
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_type, label=crew_name, role="crew", tags={"pirate", "crew"}))
    sage = world.add(Entity(id=sage_name, kind="character", type=sage_type, label="the sage", role="sage", tags={"sage"}))
    captain = world.add(Entity(id=captain_name, kind="character", type=captain_type, label="the captain", role="captain", tags={"captain", "pirate"}))
    object_ent = world.add(Entity(id=need.id, kind="thing", type=need.object_word, label=need.object_word, phrase=need.phrase, tags=set(need.tags)))
    object_ent.meters["risk"] = 0.0
    crew.memes["mood"] = 1.0 if mood in {"grumpy", "sulky"} else 0.5
    captain.memes["pride"] = 1.0
    world.facts.update(crew=crew, sage=sage, captain=captain, object=object_ent, need=need, responder=responder, harbor=harbor, mood=mood)

    world.say(f"{crew_name} the pirate was {mood} at {harbor.place}, where {harbor.detail}.")
    world.say(f"{captain_name} wanted a grand brag, but {sage_name} smiled and promised a fable instead.")
    world.para()
    world.say(f"{harbor.sway.capitalize()}, and the crew listened while the sage told {responder.phrase}.")
    captain.memes["pride"] += 0.5
    crew.memes["joy"] += 1.0
    if responder.id == "sage_fable":
        crew.memes["laugh"] += 1.5
        captain.memes["pride"] -= 0.5
    elif responder.id == "sea_shanty":
        crew.memes["laugh"] += 1.0
    else:
        crew.memes["laugh"] += 0.5
    object_ent.meters["risk"] += 1.0
    world.para()
    if object_ent.meters["risk"] >= THRESHOLD:
        world.say(f"The joke worked: the crew stopped quarreling, and even {captain_name} laughed until the map shook.")
        crew.memes["mood"] = 0.0
        captain.memes["pride"] = 0.0
        world.say(f"By sunset, they tied the {need.object_word} beside the mast and sailed with a wiser grin.")
    else:
        world.say(f"The tale was short, but it still turned their sour mood into a quiet chuckle.")
        world.say(f"They kept the {need.object_word} safe and pointed the bow toward the open sea.")
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny pirate story that includes the words "sage" and "fable" and takes place at {f["harbor"].place}.',
        f"Tell a pirate tale where {f['captain'].id} wants bragging, but the sage answers with a fable and the crew laughs.",
        f"Write a short humorous story about a pirate crew, a sage, and a {f['need'].object_word} on the shore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew: Entity = f["crew"]  # type: ignore[assignment]
    sage: Entity = f["sage"]  # type: ignore[assignment]
    captain: Entity = f["captain"]  # type: ignore[assignment]
    need: TaleNeed = f["need"]  # type: ignore[assignment]
    harb: Harbor = f["harbor"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Where did {crew.id} and the captain listen to the sage's fable?",
            answer=f"They listened at {harb.place}. The sea around them set the stage for the joke, and the wise fable fit the salty mood.",
        ),
        QAItem(
            question=f"Why did the pirate crew smile when the sage told a fable?",
            answer=f"The fable was funny, so the crew laughed instead of arguing. That laughter softened the captain's pride and changed the mood of the whole deck.",
        ),
        QAItem(
            question=f"What important thing did the crew keep safe during the story?",
            answer=f"They kept the {need.object_word} safe beside the mast. The joke helped them stop fussing, so the object stayed out of trouble.",
        ),
    ]
    if f["responder"].id == "sage_fable":
        qa.append(QAItem(
            question=f"How did the sage help {captain.id} and {crew.id} solve the problem?",
            answer=f"The sage told a funny fable, and it gave the crew a new way to think. The story made them laugh, and once they laughed, they could sail on together.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["need"].tags) | set(f["responder"].tags) | {"sage"}
    out = []
    if "sage" in tags:
        out.append(QAItem("What is a sage?", "A sage is a very wise person who gives careful advice and notices what really matters."))
    if "fable" in tags:
        out.append(QAItem("What is a fable?", "A fable is a short story that often teaches a lesson, sometimes with a funny or clever twist."))
    if "humor" in tags:
        out.append(QAItem("Why do funny stories make people feel better?", "Funny stories can make people laugh, and laughter can help worries feel smaller for a while."))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(harbor="dock", need="map", responder="sage_fable", crew_name="Mina", crew_type="girl", sage_name="Sage", sage_type="woman", captain_name="Rory", captain_type="boy", mood="grumpy"),
    StoryParams(harbor="cove", need="flag", responder="sea_shanty", crew_name="Pip", crew_type="boy", sage_name="Sage", sage_type="man", captain_name="Nell", captain_type="girl", mood="sulky"),
    StoryParams(harbor="island", need="lamp", responder="calm_bell", crew_name="Tess", crew_type="girl", sage_name="Sage", sage_type="woman", captain_name="Bram", captain_type="boy", mood="stubborn"),
]


ASP_RULES = r"""
valid(H,N,R) :- harbor(H), need(N), responder(R), sense(R,S), S >= 3.
humor(R) :- responder(R).
sage_mode(R) :- responder(R), tags(R, sage).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for hid in HARBOURS:
        lines.append(asp.fact("harbor", hid))
    for nid, need in NEEDS.items():
        lines.append(asp.fact("need", nid))
        for t in sorted(need.tags):
            lines.append(asp.fact("tags", nid, t))
    for rid, resp in RESPONDERS.items():
        lines.append(asp.fact("responder", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        for t in sorted(resp.tags):
            lines.append(asp.fact("tags", rid, t))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("MISMATCH: empty story.")
            return 1
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {exc}")
        return 1
    parser = build_parser()
    for seed in (1, 7, 777):
        params = resolve_params(parser.parse_args(["--seed", str(seed)]), random.Random(seed))
        _ = generate(params)
    with redirect_stdout(io.StringIO()):
        qsample = generate(resolve_params(parser.parse_args(["--seed", "777"]), random.Random(777)))
        emit(qsample, qa=True)
    samples = []
    for i in range(3):
        params = resolve_params(parser.parse_args(["--seed", str(100 + i)]), random.Random(100 + i))
        samples.append(generate(params))
    seen = set()
    for s in samples:
        for qa in s.story_qa:
            key = (qa.question, qa.answer)
            if key in seen:
                print("MISMATCH: duplicate QA across samples.")
                return 1
            seen.add(key)
    return 0


def valid_combo_story(params: StoryParams) -> bool:
    return (params.harbor in HARBOURS and params.need in NEEDS and params.responder in RESPONDERS
            and RESPONDERS[params.responder].sense >= 3)


def generate(params: StoryParams) -> StorySample:
    if not valid_combo_story(params):
        raise StoryError("Invalid story parameters.")
    world = tell(
        HARBOURS[params.harbor],
        NEEDS[params.need],
        RESPONDERS[params.responder],
        params.crew_name,
        params.crew_type,
        params.sage_name,
        params.sage_type,
        params.captain_name,
        params.captain_type,
        params.mood,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.crew_name}: {p.harbor} / {p.need} / {p.responder}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
