#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/temperament_dare_lesson_learned_twist_myth.py
===============================================================================

A small myth-style storyworld about a hot temperament, a daring challenge, a
twist, and a lesson learned.

The domain is intentionally tiny and classical: a young seeker, a proud dare,
a guardian figure, and a mythic creature whose temperament determines whether
the challenge becomes a blessing or a blunder. The story engine simulates the
world state with physical meters and emotional memes, then renders prose from
that state.

The seed words are included in the core vocabulary: temperament, dare.
The narrative instruments are present as well: Lesson Learned, Twist.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "nymph"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class MythPlace:
    id: str
    name: str
    feature: str
    blessing: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Challenge:
    id: str
    dare_line: str
    action: str
    risk: str
    sign: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Creature:
    id: str
    name: str
    temperament: str
    task: str
    twist_line: str
    lesson: str
    meter: str
    meter_gain: float = 1.0

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_overfull(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["overfull"] < THRESHOLD:
            continue
        sig = ("overfull", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["unease"] += 1
        out.append("__twist__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["calm"] < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["peace"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("overfull", "social", _r_overfull), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s and not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def dare_is_reasonable(challenge: Challenge, creature: Creature) -> bool:
    return challenge.id in {"cross_bridge", "touch_flame", "sing_name"} and creature.task


def resolve_twist(world: World, creature: Entity, guardian: Entity, challenge: Challenge, place: MythPlace) -> None:
    creature.meters["dare"] += 1
    creature.memes["pride"] += 1
    world.say(
        f"{creature.id} lifted {creature.pronoun('possessive')} chin and took the dare. "
        f'"{challenge.dare_line}" {guardian.id} called across {place.name}.'
    )


def warn(world: World, guardian: Entity, creature: Entity, challenge: Challenge, place: MythPlace) -> None:
    guardian.memes["care"] += 1
    world.say(
        f"{guardian.id} knew the old temperament of the place. "
        f'"{creature.id}, that path can {challenge.risk}, and the {place.feature} is never still," '
        f"{guardian.pronoun()} warned."
    )


def act(world: World, creature: Entity, challenge: Challenge, place: MythPlace, target: Entity) -> None:
    creature.meters["approach"] += 1
    target.meters["spun"] += 1
    target.meters["overfull"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{creature.id} stepped toward the {place.feature}, and the air answered with a quiet hum. "
        f"{challenge.sign} shimmered above the stones."
    )


def twist(world: World, target: Entity, creature: Entity, place: MythPlace, challenge: Challenge, myth: Creature) -> None:
    target.meters["overfull"] = 0.0
    creature.memes["surprise"] += 1
    myth.meters[myth.meter] += myth.meter_gain
    world.say(
        f"Then came the twist: the {myth.name} was not fierce at all, only shy. "
        f"{myth.twist_line}"
    )
    world.say(
        f"The {place.feature} softened, and what looked like a threat became a guide."
    )


def lesson(world: World, creature: Entity, guardian: Entity, challenge: Challenge, myth: Creature) -> None:
    creature.memes["lesson"] += 1
    guardian.memes["relief"] += 1
    world.say("That was the lesson learned.")
    world.say(
        f"{creature.id} bowed low and said, \"A hot temperament makes a loud dare, but wisdom listens first.\" "
        f"{guardian.id} smiled, because now {creature.id} knew the difference between bravado and brave care."
    )
    world.say(myth.lesson)


def tell(place: MythPlace, challenge: Challenge, myth: Creature,
         seeker_name: str = "Mina", seeker_type: str = "girl",
         guardian_name: str = "Elder", guardian_type: str = "woman") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type, role="seeker"))
    guardian = world.add(Entity(id=guardian_name, kind="character", type=guardian_type, role="guardian"))
    target = world.add(Entity(id="threshold", type="thing", label=place.feature))
    spirit = world.add(Entity(id=myth.id, kind="character", type="nymph", label=myth.name, role="spirit"))

    seeker.memes["temperament"] = 2.0
    guardian.memes["temperament"] = 5.0
    spirit.memes["temperament"] = 1.0

    world.say(
        f"Long ago, {seeker.id} came to {place.name}, where {place.feature} kept the old myths alive. "
        f"{seeker.id} had a quick temperament and loved a dare."
    )
    world.say(
        f'One evening, {guardian.id} pointed to the stones and said, "{challenge.dare_line}" '
        f"{seeker.id} wanted to prove {seeker.pronoun('possessive')} courage."
    )
    world.para()
    warn(world, guardian, seeker, challenge, place)
    resolve_twist(world, seeker, guardian, challenge, place)
    world.para()
    act(world, seeker, place, challenge, target)
    twist(world, target, seeker, place, challenge, myth)
    world.para()
    lesson(world, seeker, guardian, challenge, myth)

    world.facts.update(
        seeker=seeker,
        guardian=guardian,
        target=target,
        place=place,
        challenge=challenge,
        myth=myth,
        outcome="twist",
    )
    return world


PLACES = {
    "ridge": MythPlace("ridge", "the moonlit ridge", "wind", "a silver blessing"),
    "spring": MythPlace("spring", "the hidden spring", "water", "a clear blessing"),
    "cave": MythPlace("cave", "the echoing cave", "echo", "a deep blessing"),
}

CHALLENGES = {
    "cross_bridge": Challenge("cross_bridge", "If you dare, cross the old bridge and ring the bell.", "cross the bridge", "fall", "a bell-note"),
    "touch_flame": Challenge("touch_flame", "If you dare, touch the blue flame and tell me its name.", "touch the blue flame", "burn", "a blue glimmer"),
    "sing_name": Challenge("sing_name", "If you dare, sing the river's secret name without trembling.", "sing the river's secret name", "forget", "a bright ripple"),
}

MYTHS = {
    "wind_spirit": Creature("wind_spirit", "Wind Spirit", "shy", "guide travelers", "A shy breeze brushed the path instead of hissing fire.", "The shyest heart may still guard the road.", "calm", 1.0),
    "river_sprite": Creature("river_sprite", "River Sprite", "gentle", "steady the crossing", "The water opened a small shining path underfoot.", "The river teaches that strength can look soft.", "flow", 1.0),
    "echo_knight": Creature("echo_knight", "Echo Knight", "playful", "answer questions", "The cave answered with laughter, not fear.", "Not every loud sound is a warning; some are invitations.", "ring", 1.0),
}



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CHALLENGES:
            for m in MYTHS:
                if dare_is_reasonable(CHALLENGES[c], MYTHS[m]):
                    combos.append((p, c, m))
    return combos


@dataclass
class StoryParams:
    place: str
    challenge: str
    myth: str
    seeker: str
    seeker_type: str
    guardian: str
    guardian_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("ridge", "cross_bridge", "wind_spirit", "Mina", "girl", "Elder", "woman"),
    ("spring", "touch_flame", "river_sprite", "Arlo", "boy", "Guide", "man"),
    ("cave", "sing_name", "echo_knight", "Nia", "girl", "Old Sage", "man"),
]



def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth storyworld: temperament, dare, twist, lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--myth", choices=MYTHS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-type", choices=["girl", "boy"])
    ap.add_argument("--guardian")
    ap.add_argument("--guardian-type", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.myth is None or c[2] == args.myth)]
    if not combos:
        raise StoryError("(No valid myth combination matches the given options.)")
    place, challenge, myth = rng.choice(sorted(combos))
    seeker_type = args.seeker_type or rng.choice(["girl", "boy"])
    guardian_type = args.guardian_type or ("woman" if seeker_type == "girl" else "man")
    seeker = args.seeker or rng.choice(["Mina", "Arlo", "Nia", "Theo", "Lina", "Oren"])
    guardian = args.guardian or "Elder"
    return StoryParams(place, challenge, myth, seeker, seeker_type, guardian, guardian_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story that includes the words "temperament" and "dare".',
        f"Tell a short myth where {f['seeker'].id} meets the {f['myth'].name} at {f['place'].name} and learns a lesson.",
        f"Write a child-friendly legend with a twist, a warning, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker, guardian, myth = f["seeker"], f["guardian"], f["myth"]
    return [
        QAItem(
            question="Why did the seeker feel excited?",
            answer=f"{seeker.id} felt excited because a dare was waiting, and {seeker.id} wanted to prove courage. The quick temperament made the challenge feel bigger than it was."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the {myth.name} was shy and helpful, not dangerous. What looked like a warning turned into a guide, and that changed the meaning of the dare."
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer=f"{seeker.id} learned that a hot temperament can push someone into a rash dare. The wiser choice is to listen first, because bravery and care can live together."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does temperament mean in a story like this?",
            answer="Temperament is the way someone tends to act and feel. A hot temperament can make a character quick to boast or rush into a dare."
        ),
        QAItem(
            question="What is a dare?",
            answer="A dare is a challenge that asks someone to prove courage by doing something bold. In myths, dares often reveal character and cause a twist."
        ),
        QAItem(
            question="Why do myths often include a twist?",
            answer="Myths often include a twist because the truth is not what it first seemed to be. The surprise helps the listener remember the lesson."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
has_dare(C) :- challenge(C).
valid(P, C, M) :- place(P), challenge(C), myth(M), dare_reasonable(C, M).
twist_happens(M) :- myth(M).
lesson_learned(M) :- myth(M), twist_happens(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for m in MYTHS:
        lines.append(asp.fact("myth", m))
        lines.append(asp.fact("dare_reasonable", m, "true"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp  # noqa: F401
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python combo gates.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP gate matches Python, and generation smoke test passed.")
    return rc


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    challenge = CHALLENGES[params.challenge]
    myth = MYTHS[params.myth]
    seeker = world.add(Entity(id=params.seeker, kind="character", type=params.seeker_type, role="seeker"))
    guardian = world.add(Entity(id=params.guardian, kind="character", type=params.guardian_type, role="guardian"))
    spirit = world.add(Entity(id=myth.id, kind="character", type="nymph", role="spirit", label=myth.name))
    world.add(Entity(id="place", type="thing", label=place.name))
    world.say(
        f"Long ago, {seeker.id} walked to {place.name}, where the old stories still breathed in the {place.feature}. "
        f"{seeker.id} had a sharp temperament and loved a dare."
    )
    world.say(
        f"{guardian.id} said, \"{challenge.dare_line}\" {seeker.id} wanted to show courage, so {seeker.id} listened."
    )
    world.para()
    warn(world, guardian, seeker, challenge, place)
    resolve_twist(world, seeker, guardian, challenge, place)
    world.para()
    act(world, seeker, place, challenge, spirit)
    twist(world, spirit, seeker, place, challenge, myth)
    world.para()
    lesson(world, seeker, guardian, challenge, myth)
    world.facts.update(seeker=seeker, guardian=guardian, myth=myth, place=place, challenge=challenge, spirit=spirit)
    return world


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    curated = [StoryParams(*c) for c in CURATED]
    if args.all:
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
