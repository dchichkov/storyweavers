#!/usr/bin/env python3
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "sister"}
        male = {"boy", "father", "king", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    mood: str
    hazards: set[str] = field(default_factory=set)
    echoes: bool = False


@dataclass
class Challenge:
    id: str
    name: str
    verb: str
    danger: str
    rhyme_clue: str
    risk_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    challenge: str
    tool: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_scream(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes.get("alarm", 0) < THRESHOLD:
            continue
        sig = ("scream", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["fear"] = ent.memes.get("fear", 0) + 1
        out.append(f"{ent.id} let out a scream.")
    return out


def _r_defeat(world: World) -> list[str]:
    out: list[str] = []
    foe = world.entities.get("foe")
    hero = world.entities.get("hero")
    if not foe or not hero:
        return out
    if hero.memes.get("courage", 0) < THRESHOLD:
        return out
    if hero.memes.get("rhyme_ready", 0) < THRESHOLD:
        return out
    sig = ("defeat", foe.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    foe.meters["defeated"] = 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    out.append("The foe was defeated by a brave rhyme.")
    return out


CAUSAL_RULES = [
    _r_scream,
    _r_defeat,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(name: str, challenge: Challenge) -> str:
    return {
        "bridge": f"{name} said, 'No gloom, no doom, just room to zoom!'",
        "cave": f"{name} said, 'No fright, just light in sight!'",
        "tower": f"{name} said, 'No roar can stop me at the door!'",
    }.get(challenge.id, f"{name} said a neat rhyme and kept pace.")


def build_world(place: Place, challenge: Challenge, tool: Tool, name: str, role: str, helper: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=role, label=name, location=place.id))
    friend = world.add(Entity(id="friend", kind="character", type=helper, label=helper, location=place.id))
    foe = world.add(Entity(id="foe", kind="character", type="thing", label=challenge.name, location=place.id))
    item = world.add(Entity(id="tool", type="thing", label=tool.label, phrase=tool.phrase, owner=hero.id))

    world.say(f"{name} was a little {role} who loved an adventure.")
    world.say(f"{name} carried {item.phrase} and followed a trail into {place.label}.")
    world.say(f"The air felt {place.mood}, and {challenge.name} waited ahead.")

    world.para()
    world.say(f"Then {challenge.name} blocked the way and promised to {challenge.verb}.")
    world.say(f"{name} felt a small shake of fear, and {name} almost had to scream.")
    hero.memes["alarm"] = 1
    hero.meters["tension"] = 1
    propagate(world)
    world.say(f"{friend.label} pointed to the path and whispered a clue about a rhyme.")

    world.para()
    world.say(f"{name} took a breath and tried a rhyme instead of running away.")
    world.say(rhyme_line(name, challenge))
    hero.memes["rhyme_ready"] = 1
    hero.memes["courage"] = 1
    if challenge.risk_word in tool.helps:
        world.say(f"The {tool.label} helped by making the path steady and safe.")
    propagate(world)

    world.para()
    if foe.meters.get("defeated", 0) >= 1:
        world.say(f"{challenge.name} stepped back, surprised that the rhyme had won.")
        world.say(f"{name} smiled, and the adventure ended in bright, peaceful quiet.")
    else:
        world.say(f"{challenge.name} did not fall, but it stopped and listened.")
        world.say(f"That was enough for {name} to pass by and finish the adventure.")
    world.facts = {
        "hero": hero,
        "friend": friend,
        "foe": foe,
        "tool": item,
        "place": place,
        "challenge": challenge,
    }
    return world


PLACES = {
    "forest": Place(id="forest", label="the forest", mood="green and brave", hazards={"branches"}, echoes=False),
    "cave": Place(id="cave", label="the cave", mood="dark and echoey", hazards={"echo"}, echoes=True),
    "bridge": Place(id="bridge", label="the old bridge", mood="windy and wobbly", hazards={"drop"}, echoes=False),
}

CHALLENGES = {
    "troll": Challenge(
        id="bridge",
        name="a grumpy troll",
        verb="block the bridge",
        danger="the bridge",
        rhyme_clue="a rhyme that could make a grump grin",
        risk_word="drop",
        tags={"rhyme", "adventure"},
    ),
    "echo": Challenge(
        id="cave",
        name="a booming echo",
        verb="bounce the sound back",
        danger="the cave",
        rhyme_clue="a rhyme that could tame the echo",
        risk_word="echo",
        tags={"rhyme", "scream"},
    ),
    "wolf": Challenge(
        id="forest",
        name="a sharp-eyed wolf",
        verb="snarl at the trail",
        danger="the forest",
        rhyme_clue="a rhyme that could make the wolf blink",
        risk_word="branches",
        tags={"rhyme", "adventure"},
    ),
}

TOOLS = {
    "lantern": Tool(id="lantern", label="lantern", phrase="a small lantern", helps={"echo"}),
    "rope": Tool(id="rope", label="rope", phrase="a sturdy rope", helps={"drop"}),
    "flute": Tool(id="flute", label="flute", phrase="a tiny flute", helps={"branches"}),
}

NAMES = ["Mina", "Tobi", "Lena", "Pip", "Arlo", "Nia", "Joss", "Rina"]
ROLES = ["boy", "girl"]
HELPERS = ["mother", "father", "friend", "sister"]


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk", cid, c.risk_word))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,T) :- place(P), challenge(C), tool(T), risk(C,R), helps(T,R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c, chal in CHALLENGES.items():
            for t, tool in TOOLS.items():
                if chal.risk_word in tool.helps:
                    combos.append((p, c, t))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with a rhyme that can defeat trouble.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.challenge is None or c[1] == args.challenge)
                and (args.tool is None or c[2] == args.tool)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, tool = rng.choice(sorted(filtered))
    return StoryParams(
        place=place,
        challenge=challenge,
        tool=tool,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        helper=args.helper or rng.choice(HELPERS),
    )


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story about {f["hero"].label} who faces {f["foe"].label} and uses a rhyme to win.',
        f'Tell a child-friendly story where a scream almost happens, but a brave rhyme defeats the trouble.',
        f'Write a tiny adventure in {f["place"].label} with a helpful tool, a scary moment, and a rhyming finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    foe = f["foe"]
    place = f["place"]
    return [
        QAItem(
            question=f"Where did {hero.label} go for the adventure?",
            answer=f"{hero.label} went to {place.label} for the adventure.",
        ),
        QAItem(
            question=f"What almost made {hero.label} scream?",
            answer=f"{foe.label} made {hero.label} feel afraid enough that a scream almost happened.",
        ),
        QAItem(
            question=f"How was {foe.label} defeated?",
            answer=f"{foe.label} was defeated when {hero.label} used a brave rhyme instead of giving up.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line or word sound that matches another line or word sound near the end.",
        ),
        QAItem(
            question="What does it mean to defeat something?",
            answer="To defeat something means to beat it or make it stop winning.",
        ),
        QAItem(
            question="Why might someone scream?",
            answer="Someone might scream when they feel very scared, surprised, or overwhelmed.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = build_world(
        PLACES[params.place],
        CHALLENGES[params.challenge],
        TOOLS[params.tool],
        params.name,
        params.role,
        params.helper,
    )
    return StorySample(
        params=params,
        story=story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="bridge", challenge="troll", tool="rope", name="Mina", role="girl", helper="father"),
    StoryParams(place="cave", challenge="echo", tool="lantern", name="Tobi", role="boy", helper="mother"),
    StoryParams(place="forest", challenge="wolf", tool="flute", name="Nia", role="girl", helper="friend"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:\n")
        for p, c, t in vals:
            print(f"  {p:8} {c:8} {t:8}")
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
            header = f"### {p.name}: {p.challenge} in {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
