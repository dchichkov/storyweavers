#!/usr/bin/env python3
"""
A heartwarming parade storyworld about a sailor, an infantry drummer, and a
small twist that turns a missed celebration into a shared one.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    sailor_name: str = "Luna"
    infantry_name: str = "Mara"
    parade_name: str = "Harbor Day Parade"
    harbor: str = "Brightwater Harbor"


SAILOR_NAMES = ["Luna", "Nell", "Pia", "Rosa", "Tess", "Milo"]
INFANTRY_NAMES = ["Mara", "Ivy", "June", "Theo", "Ari", "Sam"]
PARADE_NAMES = ["Harbor Day Parade", "Lantern Parade", "Welcome Home Parade", "Spring Drum Parade"]
HARBORS = ["Brightwater Harbor", "Seaglass Harbor", "Bellwater Harbor", "Sunrise Harbor"]


INCIDENTS = [
    {
        "object": "a little brass compass",
        "problem": "the parade banner boat could not find its way through the fog",
        "mistake": "Luna steered toward the loudest harbor bell instead of the quiet signal from shore",
        "setback": "the boat reached the wrong pier after the marching bands had passed",
        "clue": "Mara noticed that the children on shore were waving their lanterns in a slow, steady pattern",
        "action": "Luna lowered the sail and followed the lantern pattern while Mara answered with three gentle drumbeats",
        "turn": "the parade was not waiting for the boat at all; the children had begun a new parade along the pier to welcome it",
        "ending": "the brass compass rested above the drum as the boat joined the glowing line of lanterns",
        "lesson": "A celebration can change its route without losing its welcome",
    },
    {
        "object": "a red ribbon for the harbor flag",
        "problem": "a sudden wind tore the ribbon from the parade boat's mast",
        "mistake": "Luna chased it into a quiet inlet while Mara hurried ahead with the infantry band",
        "setback": "the boat missed the official starting bell and the empty mast looked very lonely",
        "clue": "Mara heard the band keeping a soft beat instead of marching away",
        "action": "Luna returned to the pier, and Mara invited every waiting family to tie small ribbons together",
        "turn": "the missing red ribbon became the first piece of a much larger streamer carried by the whole crowd",
        "ending": "the joined ribbons streamed from the mast like a warm, waving river",
        "lesson": "A small loss can become a shared gift when nobody gives up",
    },
    {
        "object": "a tin whistle wrapped in blue cloth",
        "problem": "the sailor's music signal vanished beneath the infantry drums",
        "mistake": "Luna sounded the whistle again and again until the boats scattered in different directions",
        "setback": "the parade slowed, and Luna feared she had spoiled the welcome",
        "clue": "Mara asked everyone to stop and listen for the one sound that came after the drums",
        "action": "the infantry played one quiet roll, Luna blew one clear note, and each boat followed the next reply",
        "turn": "the mistake had made a new call-and-answer song for the entire harbor",
        "ending": "sailors and infantry marched side by side while the whistle danced above the final drumbeat",
        "lesson": "Listening together can turn confusion into a song",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    sailor = world.add(Entity(params.sailor_name, "character", "sailor", params.sailor_name))
    infantry = world.add(Entity(params.infantry_name, "character", "infantry", params.infantry_name))
    parade = world.add(Entity("parade", "event", "parade", params.parade_name))
    boat = world.add(Entity("boat", "thing", "sailboat", "the little sailboat"))
    drum = world.add(Entity("drum", "thing", "drum", "the infantry drum"))

    sailor.meters.update(courage=1.0, sailing=1.0)
    sailor.memes["worry"] = 0.0
    infantry.meters.update(marching=1.0, listening=1.0)
    infantry.memes["kindness"] = 1.0
    parade.meters["welcome"] = 1.0
    boat.meters.update(sail=1.0, direction=1.0)
    drum.meters["voice"] = 1.0

    world.facts.update(sailor=sailor, infantry=infantry, parade=parade, boat=boat, drum=drum)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join([params.sailor_name, params.infantry_name, params.parade_name, params.harbor])
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    incident = INCIDENTS[_token(params) % len(INCIDENTS)]
    sailor = world.facts["sailor"]
    infantry = world.facts["infantry"]
    boat = world.facts["boat"]
    parade = world.facts["parade"]

    world.say(
        f"At {params.harbor}, {sailor.label} polished {incident['object']} while "
        f"{infantry.label} checked the drum for the {parade.label}."
    )
    world.say(
        f"The sailor had to guide the little sailboat, and the infantry had to lead the "
        f"marchers safely along the water. Everyone hoped the parade would begin with a bright welcome."
    )

    world.para()
    world.say(f"Then {incident['problem']}.")
    world.say(f"In the hurry, {sailor.label} {incident['mistake']}.")
    world.say(f'"I was trying to help," {sailor.label} said. "I know," {infantry.label} replied, "so let us look again."')
    world.say(f"The setback was real: {incident['setback']}.")
    sailor.memes["worry"] = 1.0
    boat.meters["direction"] = 0.0

    world.para()
    world.say(f"{infantry.label} did not scold. Instead, {incident['clue']}.")
    world.say(
        f'"The parade can hear us if we make one careful plan," {infantry.label} said. '
        f'"And I can follow your signal," {sailor.label} answered.'
    )
    world.say(f"Together they {incident['action']}.")
    world.fired.add(("observe", "lanterns"))
    world.fired.add(("share", "signal"))

    world.para()
    world.say(f"That careful choice revealed the twist: {incident['turn']}.")
    world.say(f"The sailors trimmed the sail, the infantry kept a gentle beat, and the crowd made room.")
    world.say(f"{incident['lesson']}.")
    world.say(f"The heartwarming ending arrived when {incident['ending']}.")
    sailor.memes["worry"] = 0.0
    boat.meters["direction"] = 1.0
    world.facts.update(
        params=params,
        incident=incident,
        incident_index=_token(params) % len(INCIDENTS),
        resolved=True,
        twist=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a heartwarming story about sailor {p.sailor_name}, infantry member {p.infantry_name}, and the {p.parade_name}.",
        f"Show how {incident['problem']} leads to a setback, a kind conversation, and a hopeful twist.",
        "Tell a child-friendly parade story in which listening and teamwork change the ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    i = world.facts["incident"]
    return [
        QAItem(
            f"Who worked together during the {p.parade_name}?",
            f"{p.sailor_name}, a sailor, and {p.infantry_name}, an infantry member, worked together to guide the parade.",
        ),
        QAItem("What problem began the story?", f"{i['problem'].capitalize()}."),
        QAItem("What mistake did the sailor make?", f"{p.sailor_name} {i['mistake']}."),
        QAItem("How did the infantry member help?", f"{p.infantry_name} noticed that {i['clue'].lower()} Then they made a careful plan together."),
        QAItem("What was the twist?", f"{i['turn'].capitalize()}."),
        QAItem("How did the story end?", f"{i['ending'].capitalize()}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a parade?", "A parade is a moving celebration in which people walk, play music, carry decorations, or ride together."),
        QAItem("What does a sailor do?", "A sailor works on or near boats and helps travel safely across water."),
        QAItem("What is infantry?", "Infantry are soldiers who travel and work on foot, often moving together in organized groups."),
        QAItem("Why is listening useful in a team?", "Listening helps people notice important clues and make a plan that uses everyone's strengths."),
    ]


ASP_RULES = r"""
confused(S) :- parade(S), sailor(S), infantry(S), problem(S).
setback(S) :- confused(S), wrong_choice(S).
twist(S) :- setback(S), listens(S), shared_plan(S).
heartwarming(S) :- twist(S), welcome_restored(S).
valid_story(S) :- heartwarming(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("parade", "story1"),
        asp.fact("sailor", "story1"),
        asp.fact("infantry", "story1"),
        asp.fact("problem", "story1"),
        asp.fact("wrong_choice", "story1"),
        asp.fact("listens", "story1"),
        asp.fact("shared_plan", "story1"),
        asp.fact("welcome_restored", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade storyworld with a sailor, infantry, and a twist.")
    ap.add_argument("--sailor-name", choices=SAILOR_NAMES)
    ap.add_argument("--infantry-name", choices=INFANTRY_NAMES)
    ap.add_argument("--parade-name", choices=PARADE_NAMES)
    ap.add_argument("--harbor", choices=HARBORS)
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
    sailor = args.sailor_name or rng.choice(SAILOR_NAMES)
    infantry = args.infantry_name or rng.choice([n for n in INFANTRY_NAMES if n != sailor])
    return StoryParams(
        seed=None,
        sailor_name=sailor,
        infantry_name=infantry,
        parade_name=args.parade_name or rng.choice(PARADE_NAMES),
        harbor=args.harbor or rng.choice(HARBORS),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {entity.id:10} ({entity.kind:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
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


CURATED = [
    StoryParams(sailor_name="Luna", infantry_name="Mara", parade_name="Harbor Day Parade", harbor="Brightwater Harbor"),
    StoryParams(sailor_name="Nell", infantry_name="Ivy", parade_name="Lantern Parade", harbor="Seaglass Harbor"),
    StoryParams(sailor_name="Pia", infantry_name="June", parade_name="Welcome Home Parade", harbor="Sunrise Harbor"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
