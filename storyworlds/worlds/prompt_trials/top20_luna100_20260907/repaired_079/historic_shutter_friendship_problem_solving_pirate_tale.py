#!/usr/bin/env python3
"""
A child-facing pirate tale about a historic shutter, a friendship, and a
problem solved by careful teamwork.
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
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "sailor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
    captain_name: str = "Luna"
    friend_name: str = "Finn"
    ship_name: str = "the Bright Gull"


NAMES = ["Luna", "Mara", "Pip", "Finn", "Tessa", "Rafi", "Nell", "Jo"]
SHIP_NAMES = ["the Bright Gull", "the Salt Star", "the Kind Kraken", "the Moonfish"]


SCENARIOS = [
    {
        "place": "an old harbor fort",
        "shutter": "a historic wooden shutter carved with a silver seahorse",
        "treasure": "the harbor's friendship bell",
        "problem": "the shutter had swollen in the sea air and would not open",
        "wrong": "pulled hard on the rusted latch",
        "setback": "the latch snapped, and the treasure room stayed dark",
        "clue": "three small shells rested in a row beneath the hinge",
        "method": "they placed warm cloths along the wood, loosened the hinge with oil, and lifted together",
        "resolution": "the historic shutter opened without another splinter",
        "ending": "the friendship bell shone in the sunset while sailors from both boats rang it together",
        "lesson": "Strong friends solve hard problems by listening before pulling",
    },
    {
        "place": "a lighthouse built by the first island sailors",
        "shutter": "a historic storm shutter painted with faded blue waves",
        "treasure": "a brass map of safe waters",
        "problem": "the shutter was jammed before a storm could reach the lighthouse keeper",
        "wrong": "tried to force the middle bolt with a boat hook",
        "setback": "the hook slipped, and the lighthouse window remained covered",
        "clue": "a tiny arrow was carved beside the lower hinge",
        "method": "they followed the arrow, cleaned sand from the lower hinge, and pushed gently from both sides",
        "resolution": "the historic shutter swung open just before the rain arrived",
        "ending": "the brass map guided two friendly crews into a calm cove",
        "lesson": "A quiet clue can be more useful than a loud effort",
    },
    {
        "place": "a museum ship resting above the tide",
        "shutter": "a historic red shutter from an admiral's cabin",
        "treasure": "a captain's old friendship letter",
        "problem": "the shutter covered the cabin where the letter was kept",
        "wrong": "tugged the rope without checking which knot held it",
        "setback": "the rope tangled around the railing, and the cabin stayed closed",
        "clue": "the knot had one loose loop shaped like a fish",
        "method": "they copied the fish-shaped loop, untied the rope slowly, and held the shutter steady",
        "resolution": "the historic shutter folded back like a careful wing",
        "ending": "the friends read the letter aloud and promised to share every future voyage",
        "lesson": "Patience lets friendship uncover what haste hides",
    },
    {
        "place": "a cliffside fort above a turquoise sea",
        "shutter": "a historic iron shutter covered in tiny star marks",
        "treasure": "a lantern needed by a lost fishing boat",
        "problem": "the shutter was stuck while dusk gathered over the water",
        "wrong": "searched only for a key and ignored the shutter's moving pins",
        "setback": "the sky grew dim before they could light the lantern",
        "clue": "the star marks showed the order of the four pins",
        "method": "they pressed the pins in the starry order while their friends watched the waves",
        "resolution": "the historic shutter clicked open",
        "ending": "the lantern beam found the fishing boat, which sailed home beside the pirate ship",
        "lesson": "Good problem solving means noticing how every piece belongs together",
    },
]


@dataclass
class Friendship:
    trust: float = 0.0
    shared_task: bool = False


@dataclass
class ProblemSolving:
    noticed_clue: bool = False
    first_try_failed: bool = False
    repaired_plan: bool = False


@dataclass
class HistoricShutter:
    material: str = "wood"
    opened: bool = False
    preserved: bool = True


def _setup(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(params.captain_name, "character", "girl", params.captain_name))
    friend = world.add(Entity(params.friend_name, "character", "boy", params.friend_name))
    ship = world.add(Entity("ship", "thing", "ship", params.ship_name))
    captain.meters["courage"] = 1.0
    friend.meters["patience"] = 1.0
    ship.meters["safety"] = 1.0
    captain.memes["trust"] = 0.5
    friend.memes["trust"] = 0.5
    world.facts.update(captain=captain, friend=friend, ship=ship)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        params.captain_name + params.friend_name + params.ship_name
    ))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    scenario = SCENARIOS[_token(params) % len(SCENARIOS)]
    captain = world.facts["captain"]
    friend = world.facts["friend"]
    ship = world.facts["ship"]

    shutter = HistoricShutter()
    friendship = Friendship()
    solving = ProblemSolving()

    world.add(Entity("shutter", "thing", "historic_shutter", scenario["shutter"]))
    world.add(Entity("treasure", "thing", "treasure", scenario["treasure"]))
    world.facts.update(
        scenario=scenario,
        shutter=shutter,
        friendship=friendship,
        solving=solving,
        params=params,
    )

    world.say(
        f"Captain {captain.label} and {friend.label} sailed {ship.label} toward {scenario['place']}."
    )
    world.say(
        f"Inside stood {scenario['shutter']}, protecting {scenario['treasure']}."
    )
    world.say(
        f"Everyone wanted to help, but {scenario['problem']}."
    )

    world.para()
    world.say(
        f"Captain {captain.label} {scenario['wrong']}. The attempt failed because the old shutter needed care, not force."
    )
    world.say(
        f'"We cannot treat history like a treasure chest," {friend.label} said. '
        f'"Let us look for what the shutter is telling us."'
    )
    world.say(
        f'"You are right," {captain.label} replied. "A friend who notices details is better than a strong arm."'
    )
    solving.first_try_failed = True
    friendship.trust = 0.8
    world.say(f"{scenario['setback']}.")

    world.para()
    world.say(
        f"Together they examined the shutter and found {scenario['clue']}."
    )
    solving.noticed_clue = True
    world.say(
        f'"That is our clue," said {friend.label}. "We should solve one small part at a time."'
    )
    world.say(
        f'"And we will do it together," said {captain.label}.'
    )
    world.say(f"They {scenario['method']}.")
    solving.repaired_plan = True
    friendship.shared_task = True
    friendship.trust = 1.0
    shutter.opened = True
    world.fired.update({("wrong_attempt",), ("clue_found",), ("friends_worked",), ("shutter_opened",)})

    world.para()
    world.say(f"{scenario['resolution']}.")
    world.say(
        f"The two friends carefully took out {scenario['treasure']} and carried it where every sailor could see."
    )
    world.say(f"{scenario['ending']}.")
    world.say(f"{scenario['lesson']}.")

    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        f"Write a child-friendly pirate tale in which {p.captain_name} and {p.friend_name} face {s['problem']}.",
        f"Tell how two friends solve a historic shutter problem by noticing a clue instead of using force.",
        f"Create a pirate adventure with friendship, a failed first attempt, a careful repair, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s = world.facts["scenario"]
    return [
        QAItem(
            f"Where did {p.captain_name} and {p.friend_name} sail?",
            f"They sailed {p.ship_name} toward {s['place']}.",
        ),
        QAItem(
            "What problem did they face?",
            f"They found that {s['problem']}.",
        ),
        QAItem(
            "Why did the first attempt fail?",
            f"The first attempt failed because they used force before understanding how the old shutter worked.",
        ),
        QAItem(
            "What clue helped the friends?",
            f"They noticed that {s['clue']}.",
        ),
        QAItem(
            "How did they solve the problem?",
            f"They {s['method']}.",
        ),
        QAItem(
            "How did friendship help?",
            f"They listened to each other, shared the task, and solved the shutter problem carefully instead of blaming one another.",
        ),
        QAItem(
            "What showed that the story ended happily?",
            f"{s['ending'].capitalize()}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a shutter?",
            "A shutter is a covering fitted over a window or opening to protect it or keep light out.",
        ),
        QAItem(
            "What does historic mean?",
            "Historic means important because it belongs to the past or helps people remember the past.",
        ),
        QAItem(
            "What is friendship?",
            "Friendship is a caring relationship in which people trust, help, and listen to one another.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- shutter_stuck(S), problem_present(S).
bad_ending(S) :- confused(S), first_attempt_failed(S).
happy_ending(S) :- clue_noticed(S), friends_worked(S), shutter_opened(S).
valid_story(S) :- bad_ending(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("shutter_stuck", "story1"),
        asp.fact("problem_present", "story1"),
        asp.fact("first_attempt_failed", "story1"),
        asp.fact("clue_noticed", "story1"),
        asp.fact("friends_worked", "story1"),
        asp.fact("shutter_opened", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale about a historic shutter, friendship, and problem solving."
    )
    ap.add_argument("--captain-name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--ship-name", choices=SHIP_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    choices = [n for n in NAMES if n != captain]
    friend = args.friend_name or rng.choice(choices)
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(
        captain_name=captain,
        friend_name=friend,
        ship_name=ship,
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
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) {' '.join(details)}"
        )
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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(captain_name="Luna", friend_name="Finn", ship_name="the Bright Gull"),
    StoryParams(captain_name="Mara", friend_name="Pip", ship_name="the Salt Star"),
    StoryParams(captain_name="Tessa", friend_name="Rafi", ship_name="the Moonfish"),
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
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
