#!/usr/bin/env python3
"""
A small ghost-story world with loud, interspersed noises, inner monologue, and a
happy ending.

Seed premise:
A child hears loud sounds in a quiet place, thinks a ghost might be nearby,
and slowly learns the ghost is friendly. The scary noises are interspersed with
small clues, and the ending proves the ghost was helping all along.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    mood: str
    light: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class GhostBeat:
    id: str
    title: str
    sound: str
    whisper: str
    clue: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    where: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        chunks: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    chunks.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            chunks.append(" ".join(buf))
        return "\n\n".join(chunks)


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty", light="thin moonlight", affordances={"listen", "search"}),
    "hall": Setting(place="the long hall", mood="quiet", light="moonlight", affordances={"listen", "search"}),
    "garden": Setting(place="the moonlit garden", mood="soft", light="starlight", affordances={"listen", "search"}),
}

BEATS = {
    "loud_knock": GhostBeat(
        id="loud_knock",
        title="loud knock",
        sound="a loud knock",
        whisper="a tiny whisper",
        clue="a trail of little glowing dots",
        reveal="the ghost was trying to point the way",
        tags={"loud", "ghost"},
    ),
    "rattle_chain": GhostBeat(
        id="rattle_chain",
        title="rattling chain",
        sound="a loud rattle",
        whisper="a soft shiver of humming",
        clue="a silver charm on the floor",
        reveal="the ghost had dropped a charm while helping",
        tags={"loud", "ghost"},
    ),
    "windy_window": GhostBeat(
        id="windy_window",
        title="windy window",
        sound="a loud creak",
        whisper="a tiny breath of song",
        clue="a warm candle stub",
        reveal="the ghost was keeping the room bright and kind",
        tags={"loud", "ghost"},
    ),
}

PRIZES = {
    "lantern": Prize(id="lantern", label="lantern", phrase="a little brass lantern", type="lantern", where="desk", tags={"light"}),
    "blanket": Prize(id="blanket", label="blanket", phrase="a soft blue blanket", type="blanket", where="chair", tags={"warm"}),
    "teddy": Prize(id="teddy", label="teddy bear", phrase="a beloved teddy bear", type="teddy", where="bed", tags={"comfort"}),
}

NAMES = ["Mina", "Ivy", "Noah", "Piper", "Theo", "Luna", "Eli", "Nora"]
TRAITS = ["brave", "curious", "small", "sleepy", "gentle", "careful"]


@dataclass
class StoryParams:
    place: str
    beat: str
    prize: str
    name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for beat_id, beat in BEATS.items():
            if "ghost" not in beat.tags:
                continue
            for prize_id, prize in PRIZES.items():
                if "light" in prize.tags and place == "garden":
                    combos.append((place, beat_id, prize_id))
                elif prize_id in {"blanket", "teddy", "lantern"}:
                    combos.append((place, beat_id, prize_id))
    return sorted(set(combos))


def reasonableness_gate(setting: Setting, beat: GhostBeat, prize: Prize) -> bool:
    return (setting.place in {"the attic", "the long hall", "the moonlit garden"} and
            beat.id in BEATS and prize.id in PRIZES)


def explain_rejection(place: str, beat_id: str, prize_id: str) -> str:
    return f"(No story: {place}, {beat_id}, and {prize_id} do not make a gentle ghost story here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world with loud clues and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--beat", choices=BEATS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.beat is None or c[1] == args.beat)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, beat, prize = rng.choice(combos)
    if args.place and args.beat and args.prize:
        if not reasonableness_gate(SETTINGS[place], BEATS[beat], PRIZES[prize]):
            raise StoryError(explain_rejection(place, beat, prize))
    return StoryParams(
        place=place,
        beat=beat,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    beat = BEATS[params.beat]
    prize = PRIZES[params.prize]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type="child", label=params.name, meters={}, memes={"fear": 0.0, "curiosity": 0.0, "relief": 0.0, "courage": 0.0}))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", meters={"glow": 1.0}, memes={"kindness": 1.0}))
    prize_ent = world.add(Entity(id="prize", kind="thing", type=prize.type, label=prize.label, phrase=prize.phrase))

    world.facts.update(child=child, ghost=ghost, prize=prize_ent, beat=beat, setting=setting)

    world.say(f"{params.name} was a {params.trait} child in {setting.place}.")
    world.say(f"At night, {setting.light} made the room feel {setting.mood}, and {params.name} hugged {prize_ent.label} close.")

    world.para()
    world.say(f"Then came {beat.sound}.")
    child.memes["fear"] += 1.0
    child.memes["curiosity"] += 0.5
    world.say(f"{params.name}'s heart jumped. In a small inner monologue, {child.pronoun('subject')} thought, 'That sounds loud. What if a ghost is here?'")
    world.say(f"A moment later, {beat.whisper} drifted in, interspersed with the noise.")
    child.memes["curiosity"] += 1.0

    world.para()
    world.say(f"{params.name} tiptoed toward the sound and found {beat.clue}.")
    child.memes["courage"] += 1.0
    world.say(f"In another inner monologue, {child.pronoun('subject')} thought, 'Maybe the ghost is not mean. Maybe it needs help.'")
    world.say(f"That guess was right: {beat.reveal}.")

    world.para()
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1.5
    world.say(f"The ghost floated nearer and made one last gentle swirl of light around {prize_ent.label}.")
    world.say(f"{params.name} smiled, because the scary sound had been a helper all along.")
    world.say(f"By the end, the room felt safe, {prize_ent.label} stayed with {params.name}, and the ghost gave a tiny bow before fading like a moonbeam.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    beat: GhostBeat = f["beat"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        f'Write a short ghost story for a child named {child.id} set in {setting.place} with a loud clue and a happy ending.',
        f'Write a gentle story where {beat.sound} is interspersed with a whisper, and the child discovers {beat.reveal}.',
        f'Write a simple spooky-but-safe story that includes "{beat.title}" and ends with {prize.label} staying safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    beat: GhostBeat = f["beat"]  # type: ignore[assignment]
    prize: Entity = f["prize"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where was {child.id} when the loud sound started?",
            answer=f"{child.id} was in {setting.place}, where the room felt {setting.mood} under {setting.light}.",
        ),
        QAItem(
            question=f"What did {child.id} first think when {beat.sound} happened?",
            answer=f"{child.id} thought it might be a ghost, but then the child became curious instead of only scared.",
        ),
        QAItem(
            question=f"What helped show that the ghost was friendly?",
            answer=f"The loud sound was interspersed with {beat.whisper}, and that clue led {child.id} to {beat.reveal}.",
        ),
        QAItem(
            question=f"What was still safe at the end of the story?",
            answer=f"{prize.label} stayed safe with {child.id}, and the ending showed that everything turned out well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is usually a spooky-looking character, but in a gentle story it can be friendly and helpful.",
        ),
        QAItem(
            question="What does interspersed mean?",
            answer="Interspersed means mixed in between other things, like a whisper between loud noises.",
        ),
        QAItem(
            question="Why can a loud sound feel scary at night?",
            answer="A loud sound can feel scary at night because everything is quieter, so the noise stands out more.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem is solved and the characters finish the story feeling safe or glad.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("place_name", pid, s.place))
    for bid, b in BEATS.items():
        lines.append(asp.fact("beat", bid))
        lines.append(asp.fact("sound", bid, b.sound))
    for prid, p in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("safe_item", prid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,B,R) :- setting(P), beat(B), prize(R), safe_item(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="attic", beat="loud_knock", prize="teddy", name="Mina", trait="curious"),
    StoryParams(place="hall", beat="rattle_chain", prize="blanket", name="Theo", trait="careful"),
    StoryParams(place="garden", beat="windy_window", prize="lantern", name="Nora", trait="brave"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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
