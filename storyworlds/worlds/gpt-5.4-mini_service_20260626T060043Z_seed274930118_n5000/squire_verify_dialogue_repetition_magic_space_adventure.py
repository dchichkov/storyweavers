#!/usr/bin/env python3
"""
A standalone Storyweavers world for a small space-adventure tale.

Premise:
A young squire aboard a starship wants to help verify a magical navigation
beacon. The beacon keeps repeating the same warning, the crew worries it may be
glitched, and the squire must use careful dialogue, repetition checks, and a
little magic to prove what is really happening.

The world is built around:
- a squire character
- a verify task
- dialogue as the main social tool
- repetition as a causal feature
- magic as a real but constrained force
- a space-adventure setting

The story engine simulates state changes in meters and memes, then renders a
child-facing story with grounded Q&A.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SPACE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "squire-girl"}
        male = {"boy", "man", "father", "squire-boy", "squire"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    name: str
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    effect: str
    cost: str
    can_verify: bool = True


@dataclass
class StoryParams:
    setting: str
    magic: str
    name: str
    role: str = "squire"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.repeated_warning: str = ""
        self.magic_used = False
        self.verified = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.events = list(self.events)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.repeated_warning = self.repeated_warning
        clone.magic_used = self.magic_used
        clone.verified = self.verified
        return clone


SETTINGS = {
    "orbit": Setting(name="orbit", place="the ship in orbit", affordances={"verify", "dialogue", "magic"}),
    "dock": Setting(name="dock", place="the bright space dock", affordances={"verify", "dialogue", "magic"}),
    "moonbase": Setting(name="moonbase", place="the moon base", affordances={"verify", "dialogue", "magic"}),
}

MAGIC_TOOLS = {
    "starwand": MagicTool(
        id="starwand",
        label="a star wand",
        effect="glimmering scan light",
        cost="a tiny spark of blue light",
    ),
    "moonrune": MagicTool(
        id="moonrune",
        label="a moon rune stone",
        effect="soft silver truth",
        cost="a warm silver hum",
    ),
    "helmseal": MagicTool(
        id="helmseal",
        label="a seal of clear sight",
        effect="clear sight",
        cost="a calm pulse",
    ),
}

TRAITS = ["brave", "careful", "curious", "steady", "kind", "bold"]
NAMES = ["Lina", "Milo", "Tara", "Jory", "Pia", "Nico", "Arin", "Sora"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MAGIC_TOOLS:
            combos.append((s, m))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label="the squire",
        traits=[random.choice(TRAITS)],
        meters={"calm": 0.0, "joy": 0.0, "doubt": 0.0, "magic": 0.0, "verify": 0.0},
        memes={"curiosity": 1.0, "duty": 1.0, "worry": 0.0, "confidence": 0.0},
        tags={"squire"},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type="captain",
        label="the captain",
        meters={"calm": 0.0, "worry": 0.0, "trust": 0.0},
        memes={"authority": 1.0},
    ))
    mechanic = world.add(Entity(
        id="Mechanic",
        kind="character",
        type="mechanic",
        label="the mechanic",
        meters={"calm": 0.0, "worry": 0.0, "trust": 0.0},
        memes={"patience": 1.0},
    ))
    beacon = world.add(Entity(
        id="Beacon",
        kind="thing",
        type="beacon",
        label="the starlight beacon",
        phrase="a silver beacon with a glass ring",
        meters={"pulse": 0.0, "repeat": 0.0, "stability": 0.0},
        memes={"mystery": 1.0},
        tags={"verify", "magic", "repeat"},
    ))
    tool = MAGIC_TOOLS[params.magic]
    staff = world.add(Entity(
        id=tool.id,
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.label,
        meters={"glow": 0.0, "charge": 1.0},
        memes={"magic": 1.0},
        owner=hero.id,
        tags={"magic"},
    ))

    world.facts.update(hero=hero, captain=captain, mechanic=mechanic, beacon=beacon, staff=staff, tool=tool)
    return world


def pulse_beacon(world: World) -> None:
    beacon = world.get("Beacon")
    beacon.meters["repeat"] += 1
    beacon.meters["pulse"] += 1
    world.repeated_warning = "beep-beep verify beep-beep"
    world.say('The beacon blinked and said, "beep-beep verify beep-beep."')


def ask_verify(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    captain = world.get("Captain")
    hero.meters["verify"] += 1
    hero.memes["curiosity"] += 0.5
    world.say(
        f'{hero.id} listened carefully and asked, "Should we verify the beacon again?" '
        f'{captain.label.capitalize()} nodded at the repeating light.'
    )


def reply_dialogue(world: World) -> None:
    mechanic = world.get("Mechanic")
    hero = world.get(world.facts["hero"].id)
    world.say(
        f'{mechanic.label.capitalize()} said, "If the message repeats, we should check what stays the same and what changes." '
        f'{hero.id} whispered, "Then we can verify it with care."'
    )


def use_magic(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    beacon = world.get("Beacon")
    staff = world.get(world.facts["staff"].id)
    hero.meters["magic"] += 1
    staff.meters["glow"] += 1
    beacon.meters["stability"] += 1
    world.magic_used = True
    world.say(
        f"{hero.id} lifted {staff.label} and let out a small, safe spell. "
        f"The air shimmered, and the beacon's light became steady."
    )


def verify_result(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    captain = world.get("Captain")
    beacon = world.get("Beacon")
    if beacon.meters["repeat"] >= SPACE_THRESHOLD:
        world.verified = True
        hero.memes["confidence"] += 1
        captain.meters["trust"] += 1
        world.say(
            f'{hero.id} checked the pattern twice, then once more, and smiled. '
            f'"It was not broken," {hero.id} said. "It was repeating on purpose so we would notice the warning."'
        )
        world.say(
            f'{captain.label.capitalize()} laughed softly. "Good work, little squire. You verified the truth." '
            f"The beacon's glow stayed bright instead of flickering."
        )
    else:
        raise StoryError("The beacon never repeated enough to create a verify story.")


def tell_story(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    tool = world.facts["tool"]
    world.say(
        f"{hero.id} was a small squire aboard a ship that sailed through the stars."
    )
    world.say(
        f"{hero.id} liked quiet jobs, shiny panels, and any puzzle that needed careful eyes."
    )
    world.say(
        f"One day, the crew found {tool.label} resting near the navigation chair, ready for a little magic."
    )
    world.para()
    world.say(
        f"At {world.setting.place}, the starlight beacon kept repeating the same message."
    )
    pulse_beacon(world)
    ask_verify(world)
    reply_dialogue(world)
    world.say("The captain and the mechanic listened, because repetition can hide a clue.")
    use_magic(world)
    verify_result(world)
    world.para()
    world.say(
        f"In the end, the starship floated on with the beacon shining steady and calm."
    )
    world.say(
        f"{hero.id} tucked {tool.label} back in place, proud that careful dialogue and a little magic had helped the crew verify the truth."
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    tool = world.facts["tool"]
    beacon = world.facts["beacon"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a small squire who helped the crew verify a repeating beacon.",
        ),
        QAItem(
            question="What did the beacon keep doing?",
            answer=f"It kept repeating the same warning: \"beep-beep verify beep-beep.\"",
        ),
        QAItem(
            question=f"What did {hero.id} use to help?",
            answer=f"{hero.id} used {tool.label} to make a safe little spell that helped steady the beacon.",
        ),
        QAItem(
            question="How did the crew solve the problem?",
            answer="They talked about the pattern, listened carefully, used magic safely, and verified that the beacon was warning them on purpose.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the beacon was steady, the crew trusted the result, and the ship could keep flying through space.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to verify something?",
            answer="To verify something means to check it carefully and make sure it is true.",
        ),
        QAItem(
            question="Why can repetition be useful?",
            answer="Repetition can be useful because a message or action that happens the same way again and again can help you notice a pattern.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special force that can do surprising things, like make lights glow or help someone discover a clue.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    tool = world.facts["tool"]
    return [
        'Write a short space-adventure story for a child about a squire who must verify a repeating beacon.',
        f"Tell a gentle starship story where {hero.id} uses dialogue, repetition, and {tool.label} to solve a mystery.",
        'Write a simple space adventure that includes a squire, a verify task, and a magical clue.',
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, tool in MAGIC_TOOLS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("tool_label", mid, tool.label))
    return "\n".join(lines)


ASP_RULES = r"""
setting(S).
magic(M).

verifiable(S,M) :- setting(S), magic(M).

#show verifiable/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show verifiable/2."))
    return sorted(set(asp.atoms(model, "verifiable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a squire who verifies a magical beacon.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGIC_TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["squire"], default="squire")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.magic:
        combos = [c for c in combos if c[1] == args.magic]
    if not combos:
        raise StoryError("No valid space story matches the given options.")
    setting, magic = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, magic=magic, name=name, role="squire")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


CURATED = [
    StoryParams(setting="orbit", magic="starwand", name="Lina"),
    StoryParams(setting="dock", magic="moonrune", name="Milo"),
    StoryParams(setting="moonbase", magic="helmseal", name="Sora"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show verifiable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} with {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
