#!/usr/bin/env python3
"""
storyworlds/worlds/prompt_trials/top20_mini100_20260907/repaired_007/historic_shutter_friendship_problem_solving_pirate_tale.py
==============================================================================================================================

A tiny child-facing pirate-tale storyworld about friendship and problem solving.
The seed words are historic and shutter. The domain stays small and classical:
a crew reaches an old harbor inn, a stubborn shutter causes trouble, friends
talk it through, and their shared plan changes the world state.

The story model uses typed entities with physical meters and emotional memes,
a Python causal simulation, and a matching inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            self.entities[eid] = Entity(id=eid, label=eid.replace("_", " "))
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
        import copy
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: callable


def _r_breeze_knocks(world: World) -> list[str]:
    lines: list[str] = []
    shutter = world.entities.get("historic_shutter")
    if shutter and shutter.meters["stuck"] >= THRESHOLD and ("breeze_knocks", "historic_shutter") not in world.fired:
        world.fired.add(("breeze_knocks", "historic_shutter"))
        world.get("captain_mara").memes["worry"] += 1
        world.get("bosun_elliot").memes["worry"] += 1
        lines.append("The old shutter rattled in the sea breeze.")
    return lines


def _r_friend_plan(world: World) -> list[str]:
    lines: list[str] = []
    shutter = world.entities.get("historic_shutter")
    if not shutter or shutter.meters["stuck"] < THRESHOLD:
        return lines
    if ("friend_plan", "historic_shutter") in world.fired:
        return lines
    captain = world.get("captain_mara")
    bosun = world.get("bosun_elliot")
    if captain.memes["talked"] >= THRESHOLD and bosun.memes["talked"] >= THRESHOLD:
        world.fired.add(("friend_plan", "historic_shutter"))
        shutter.meters["stuck"] = 0.0
        shutter.meters["open"] = 1.0
        shutter.meters["repaired"] = 1.0
        captain.memes["relief"] += 1
        bosun.memes["relief"] += 1
        captain.meters["helped"] += 1
        bosun.meters["helped"] += 1
        lines.append("Together they freed the shutter and made the old room bright again.")
    return lines


def _r_treasure_glow(world: World) -> list[str]:
    lines: list[str] = []
    room = world.entities.get("historic_inn")
    if room and room.meters["bright"] >= THRESHOLD and ("treasure_glow", "historic_inn") not in world.fired:
        world.fired.add(("treasure_glow", "historic_inn"))
        lines.append("The lantern light spilled over the maps like gold on the table.")
    return lines


CAUSAL_RULES = [Rule("breeze_knocks", _r_breeze_knocks), Rule("friend_plan", _r_friend_plan), Rule("treasure_glow", _r_treasure_glow)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    for _ in range(len(CAUSAL_RULES) + 3):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                lines.extend(out)
        if not changed:
            break
    if narrate:
        for line in lines:
            world.say(line)
    return lines


@dataclass(frozen=True)
class StoryArc:
    key: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    teamwork: tuple[str, str]
    ending: tuple[str, str]
    problem: str
    action: str
    result: str


STORY_ARC = StoryArc(
    key="historic_shutter",
    opening=(
        "At the historic harbor inn, Captain Mara and Bosun Elliot found an old map room above the dock.",
        "The room smelled of salt, lamp oil, and stories from long ago.",
    ),
    trouble=(
        "A stubborn shutter jammed shut with a sharp clack. The wind pushed, but it would not budge.",
        '"That shutter is stuck," said Mara. "A problem can be puzzled out, mate."',
    ),
    teamwork=(
        '"Let us try together," said Elliot. "You push from inside, and I will steady the frame."',
        '"Aye," said Mara. "We will think first, then pull with care."',
    ),
    ending=(
        "With one careful tug and one steady push, the shutter swung open wide.",
        "Moonlight washed over the maps, and the two friends smiled at their bright old prize.",
    ),
    problem="the historic shutter was jammed shut in the old map room",
    action="Captain Mara pushed from inside while Bosun Elliot steadied the frame and pulled the latch free",
    result="the shutter opened and the map room filled with moonlight",
)


@dataclass
class StoryParams:
    place: str
    captain_name: str = "Mara"
    bosun_name: str = "Elliot"
    seed: Optional[int] = None


PLACES = {
    "harbor_inn": Place(id="harbor_inn", label="the historic harbor inn", tags={"historic", "dock"}),
    "old_lighthouse": Place(id="old_lighthouse", label="the old lighthouse room", tags={"historic", "tower"}),
}

CURATED = [
    StoryParams(place="harbor_inn", captain_name="Mara", bosun_name="Elliot"),
    StoryParams(place="old_lighthouse", captain_name="Nina", bosun_name="Jonas"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale world about friendship and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--captain")
    ap.add_argument("--bosun")
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
    place = args.place or rng.choice(list(PLACES))
    captain = args.captain or rng.choice(["Mara", "Nina", "Ada", "June"])
    bosun = args.bosun or rng.choice([n for n in ["Elliot", "Jonas", "Theo", "Lina"] if n != captain])
    return StoryParams(place=place, captain_name=captain, bosun_name=bosun)


def make_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    world = World(place=PLACES[params.place])
    captain = world.add(Entity(id="captain_mara", kind="character", type="person", label=params.captain_name, role="captain"))
    bosun = world.add(Entity(id="bosun_elliot", kind="character", type="person", label=params.bosun_name, role="bosun"))
    shutter = world.add(Entity(id="historic_shutter", kind="thing", type="shutter", label="historic shutter"))
    room = world.add(Entity(id="historic_inn", kind="place", type="room", label=world.place.label))
    shutter.meters["stuck"] = 1.0
    room.meters["bright"] = 0.0
    captain.memes["curious"] += 1
    bosun.memes["curious"] += 1
    return world


def simulate(world: World) -> None:
    c = world.get("captain_mara")
    b = world.get("bosun_elliot")
    s = world.get("historic_shutter")
    r = world.get("historic_inn")

    world.say(STORY_ARC.opening[0])
    world.say(STORY_ARC.opening[1])
    world.para()
    world.say(STORY_ARC.trouble[0])
    world.say(STORY_ARC.trouble[1])
    c.memes["worry"] += 1
    b.memes["worry"] += 1
    propagate(world)
    world.para()
    c.memes["talked"] += 1
    b.memes["talked"] += 1
    world.say(STORY_ARC.teamwork[0])
    world.say(STORY_ARC.teamwork[1])
    s.meters["stuck"] = 0.0
    s.meters["open"] = 1.0
    s.meters["repaired"] = 1.0
    r.meters["bright"] = 1.0
    c.memes["joy"] += 1
    b.memes["joy"] += 1
    c.meters["helped"] += 1
    b.meters["helped"] += 1
    propagate(world)
    world.para()
    world.say(STORY_ARC.ending[0])
    world.say(STORY_ARC.ending[1])

    world.facts.update(
        captain=c,
        bosun=b,
        shutter=s,
        room=r,
        place=world.place,
        problem=STORY_ARC.problem,
        action=STORY_ARC.action,
        result=STORY_ARC.result,
        ending=STORY_ARC.ending[1],
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    simulate(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a child that includes the word "historic" and the word "shutter".',
        f"Tell a friendly pirate story where {f['captain'].label} and {f['bosun'].label} solve {f['problem']}.",
        f"Make the ending prove that {f['result']} at {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What was the problem in the story?",
            answer=f"The problem was that {f['problem']}. That kept the map room closed until the friends worked it out."
        ),
        QAItem(
            question="How did the friends solve it?",
            answer=f"They solved it with friendship and problem solving: {f['action']}. That careful plan fixed the trouble."
        ),
        QAItem(
            question="What showed the problem was solved at the end?",
            answer=f"The ending image showed it clearly: {f['ending']}. That bright moonlight proved the shutter was open."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other and help each other. Friends can stay calm and work side by side."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving is finding a good plan for a tricky situation. It often means looking closely, trying a careful step, and working together."
        ),
    ]


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
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:18} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(shutter) :- shutter(shutter), stuck_meter(shutter,S), S >= 1.
talked(C) :- captain(C), talked_meter(C,1).
talked(B) :- bosun(B), talked_meter(B,1).
open(shutter) :- stuck(shutter), talked(C), talked(B), captain(C), bosun(B), C != B.
bright(room) :- open(shutter), room(room).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("shutter", "historic_shutter"),
        asp.fact("stuck_meter", "historic_shutter", 1),
        asp.fact("talked_meter", "captain_mara", 1),
        asp.fact("talked_meter", "bosun_elliot", 1),
        asp.fact("captain", "captain_mara"),
        asp.fact("bosun", "bosun_elliot"),
        asp.fact("room", "historic_inn"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show open/1.\n#show bright/1."))
    if not model:
        print("ASP produced no model.")
        return 1
    try:
        sample = generate(CURATED[0])
        if "shutter" not in sample.story or "friends" not in sample.story:
            print("Story smoke test failed.")
            return 1
    except Exception as exc:
        print(f"Story smoke test failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show open/1.\n#show bright/1."))
    return sorted(set(asp.atoms(model, "open")) | set(asp.atoms(model, "bright")))


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
        print(asp_program("#show open/1.\n#show bright/1."))
        return
    if args.verify:
        sys.exit(asp_story_check())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
