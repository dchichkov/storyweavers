#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/big_agitate_street_twist_flashback_inner_monologue.py
=====================================================================================

A small mythic storyworld about a giant lantern, an agitated street, a remembered
warning, an inner monologue, and a twist ending. The world is built to support
TinyStories-style variation around a simple legend:

A child or young hero wants to calm a noisy street by moving a sacred, glowing
stone. They remember a past lesson in a flashback, hear their own inner monologue,
and discover a twist: the "bad omen" is actually a festival signal, so the street
is agitated because it is waiting for music and light.

The simulation tracks physical meters and emotional memes. The story begins with a
problem, shifts through memory and self-talk, and resolves with an ending image
that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/big_agitate_street_twist_flashback_inner_monologue.py
    python storyworlds/worlds/gpt-5.4-mini/big_agitate_street_twist_flashback_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4-mini/big_agitate_street_twist_flashback_inner_monologue.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/big_agitate_street_twist_flashback_inner_monologue.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Street:
    id: str
    label: str
    crowded: bool = True
    agitate_word: str = "agitate"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SacredStone:
    id: str
    label: str
    big: bool = True
    glows: bool = True
    moved: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Festival:
    id: str
    label: str
    signal: str
    music: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    street: Street | None = None
    stone: SacredStone | None = None
    festival: Festival | None = None
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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.street = _copy.deepcopy(self.street)
        clone.stone = _copy.deepcopy(self.stone)
        clone.festival = _copy.deepcopy(self.festival)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    mentor: str
    mentor_gender: str
    street: str
    stone: str
    festival: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


HEROES = {
    "boy": ["Iason", "Milo", "Nikos", "Theo", "Ari", "Leo"],
    "girl": ["Sera", "Mira", "Lina", "Iris", "Nora", "Hera"],
}
MENTORS = {
    "boy": ["Old Ezra", "Orion", "Marek"],
    "girl": ["Old Ada", "Selene", "Maya"],
}

STREETS = {
    "marble": Street(id="marble", label="the marble street", crowded=True),
    "olive": Street(id="olive", label="the olive street", crowded=True),
    "harbor": Street(id="harbor", label="the harbor street", crowded=True),
}

STONES = {
    "sunstone": SacredStone(id="sunstone", label="a big sunstone"),
    "moonstone": SacredStone(id="moonstone", label="a big moonstone"),
    "drumstone": SacredStone(id="drumstone", label="a big drumstone"),
}

FESTIVALS = {
    "lantern": Festival(id="lantern", label="the lantern festival", signal="lanterns", music="drums"),
    "harvest": Festival(id="harvest", label="the harvest festival", signal="bread", music="flutes"),
    "spring": Festival(id="spring", label="the spring festival", signal="flowers", music="pipes"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, st, f) for s in STREETS for st in STONES for f in FESTIVALS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with twist, flashback, and inner monologue.")
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-gender", choices=["boy", "girl"])
    ap.add_argument("--street", choices=STREETS)
    ap.add_argument("--stone", choices=STONES)
    ap.add_argument("--festival", choices=FESTIVALS)
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
              if (args.street is None or c[0] == args.street)
              and (args.stone is None or c[1] == args.stone)
              and (args.festival is None or c[2] == args.festival)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    street, stone, festival = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    mentor_gender = args.mentor_gender or rng.choice(["boy", "girl"])
    hero = args.hero or rng.choice(HEROES[hero_gender])
    mentor = args.mentor or rng.choice(MENTORS[mentor_gender])
    return StoryParams(
        hero=hero,
        hero_gender=hero_gender,
        mentor=mentor,
        mentor_gender=mentor_gender,
        street=street,
        stone=stone,
        festival=festival,
    )


def _setup_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    mentor = w.add(Entity(id=params.mentor, kind="character", type=params.mentor_gender, role="mentor"))
    street = STREETS[params.street]
    stone = STONES[params.stone]
    festival = FESTIVALS[params.festival]
    w.street = street
    w.stone = stone
    w.festival = festival
    w.facts.update(hero=hero, mentor=mentor, street=street, stone=stone, festival=festival)
    return w


def tell(world: World) -> None:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    street = world.street
    stone = world.stone
    festival = world.festival

    hero.memes["curiosity"] = 1
    street.meters["noise"] = 1
    street.memes["agitated"] = 1

    world.say(
        f"On {street.label}, the crowd had grown restless, and the whole road seemed to agitate like a sea before a storm."
    )
    world.say(
        f"At the center of the square stood {stone.label}, big as a cart wheel and bright as a star hidden in day."
    )
    world.say(
        f"{hero.id} looked at the stone and thought, 'If I move it, perhaps the street will quiet.'"
    )

    world.para()
    world.say(
        f"Then came a flashback: {mentor.id} had once said, 'A big thing can carry two meanings. "
        f"One meaning frightens. Another meaning invites.'"
    )
    hero.memes["memory"] = 1
    hero.memes["doubt"] = 1
    world.say(
        f"{hero.id} felt a small inner monologue stir inside {hero.pronoun('possessive')} chest: "
        f"'Be brave. Be careful. Listen before you lift.'"
    )

    world.para()
    twist = (
        f"Just then, {mentor.id} raised {mentor.pronoun('possessive')} arms and the street answered at once: "
        f"children poured from doors with {festival.signal}, and the drums began."
    )
    world.say(twist)
    street.meters["noise"] = 0
    street.memes["agitated"] = 0
    festival.meters["joy"] = 1
    hero.memes["relief"] = 1
    hero.meters["moved"] = 1
    stone.moved = True
    world.say(
        f"The great surprise was that the stone had not been a warning at all. It was the old festival mark, "
        f"waiting to be carried into the light as a sign that the night celebration could begin."
    )

    world.para()
    world.say(
        f"{hero.id} lifted {stone.label} with both hands and walked the center of {street.label} as if carrying a little sun."
    )
    world.say(
        f"The crowd stopped quarrelling, and by the last drumbeat the whole street shone bright, calm, and glad."
    )

    world.facts["twist"] = True
    world.facts["outcome"] = "festival"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a myth-style story that includes the words big, agitate, and street, and uses a twist, flashback, and inner monologue.",
        f"Tell a short legend where {f['hero'].id} thinks the {f['stone'].label} is causing trouble on the {f['street'].label}, but the truth turns out to be kinder.",
        f"Write a child-facing myth in which a restless street becomes calm after a remembered lesson and a surprising reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    mentor = world.facts["mentor"]
    street = world.facts["street"]
    stone = world.facts["stone"]
    festival = world.facts["festival"]
    return [
        QAItem(
            question=f"Why did {hero.id} first worry about the {stone.label}?",
            answer=(
                f"{hero.id} thought the big stone might be making the street agitate even more. "
                f"In the flashback, {mentor.id} had warned that a big thing can seem frightening before its true meaning is known."
            ),
        ),
        QAItem(
            question="What was the inner monologue doing in the story?",
            answer=(
                f"It let {hero.id} hear private thoughts like 'Be brave. Be careful. Listen before you lift.' "
                f"That quiet voice helped {hero.id} pause before acting."
            ),
        ),
        QAItem(
            question="What was the twist at the end?",
            answer=(
                f"The stone was not a danger at all. It was the old festival sign, and when it was carried into the light, "
                f"the street changed from restless to joyful."
            ),
        ),
        QAItem(
            question=f"How did {street.label} feel after the ending?",
            answer=(
                f"It became calm and bright, with no agitation left in it. "
                f"The drums, the crowd, and the shining stone made the whole road feel like a blessing."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening. It makes the ending feel new without breaking the story.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a quick return to something that happened before. It helps the reader understand the present moment better.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice of a character's thoughts. It can show worry, courage, or a new idea.",
        ),
        QAItem(
            question="What does agitate mean?",
            answer="To agitate means to stir up or make something restless. A crowd, water, or a heart can be agitated.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} type={e.type} role={e.role} meters={e.meters} memes={e.memes}")
    lines.append(f"street: {world.street}")
    lines.append(f"stone: {world.stone}")
    lines.append(f"festival: {world.festival}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(street, stone, festival).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in STREETS:
        lines.append(asp.fact("street", s))
    for s in STONES:
        lines.append(asp.fact("stone", s))
    for f in FESTIVALS:
        lines.append(asp.fact("festival", f))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    print("MISMATCH: ASP parity failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.street not in STREETS or params.stone not in STONES or params.festival not in FESTIVALS:
        raise StoryError("(Invalid story parameters.)")
    world = _setup_world(params)
    tell(world)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(1 << 30))
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(hero="Iason", hero_gender="boy", mentor="Old Ezra", mentor_gender="boy", street="marble", stone="sunstone", festival="lantern")),
            generate(StoryParams(hero="Sera", hero_gender="girl", mentor="Old Ada", mentor_gender="girl", street="olive", stone="moonstone", festival="harvest")),
            generate(StoryParams(hero="Hera", hero_gender="girl", mentor="Selene", mentor_gender="girl", street="harbor", stone="drumstone", festival="spring")),
        ]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random((args.seed or 0) + i))
            params.seed = (args.seed or 0) + i if args.seed is not None else None
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
