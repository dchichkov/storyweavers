#!/usr/bin/env python3
"""
storyworlds/worlds/skittle_stationery_foreshadowing_cautionary_humor_tall_tale.py
=================================================================================

A standalone story world sketch for a tall-tale cautionary story about a
skittle, stationery, foreshadowing, and a funny little warning that pays off.

Seed tale:
---
At the old desk by the road, a child named Pippa found a shiny skittle in a jar
of stationery. The skittle rolled like a marble, winked like a star, and looked
too lively to be ordinary. Pippa wanted to toss it into a letterpress that could
stamp a whole mountain of invitations. But the desk drawer kept rattling, the
ink bottle kept tipping, and Grandpa kept saying, "When a skittle starts acting
like a storm in a sugar coat, best mind your paper and keep your shoes tied."

Pippa ignored him, and the skittle bounced into the paper tray. Every sheet in
the tray started fluttering, the envelopes flew open, and the rubber stamp
thumped like a drum. Then Grandpa laughed, fished the skittle out with a ruler,
and said the desk had been trying to warn them all along.

The child tucked the skittle back in its jar, the stationery stayed tidy, and
the old desk looked proud to have told the story first.

World contract:
- typed entities with meters and memes
- world state drives the prose
- foreshadowing, caution, humor
- tall-tale style, but child-facing and concrete
- explicit invalid choices raise StoryError
- include Python gate and inline ASP twin
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Desk:
    id: str
    label: str
    phrase: str
    near: str
    old_saying: str
    tells: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    opens: str
    closes: str
    holds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


class World:
    def __init__(self, desk: Desk) -> None:
        self.desk = desk
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.desk)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    kid = world.get("child")
    tray = world.get("tray")
    if kid.meters.get("bouncy", 0) < THRESHOLD:
        return out
    if tray.meters.get("tilted", 0) < THRESHOLD:
        return out
    sig = ("scatter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tray.meters["messy"] = tray.meters.get("messy", 0) + 1
    tray.meters["fluttering"] = tray.meters.get("fluttering", 0) + 1
    world.get("letters").meters["shuffled"] = world.get("letters").meters.get("shuffled", 0) + 1
    out.append("The stationery started fluttering like goslings in a windstorm.")
    return out


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    if world.get("desk").meters.get("foretold", 0) < THRESHOLD:
        return out
    if world.get("child").memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("warn",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["hesitation"] = world.get("child").memes.get("hesitation", 0) + 1
    out.append("Grandpa said the desk was giving a warning in its own creaky way.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes.get("humor", 0) < THRESHOLD:
        return out
    if world.get("jar").meters.get("closed", 0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("tray").meters["tidy"] = world.get("tray").meters.get("tidy", 0) + 1
    out.append("That made the desk look pleased, as if a tidy joke had been told back to it.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_warn, _r_scatter, _r_calm):
            got = rule(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str = "desk"
    prize: str = "skittle"
    container: str = "jar"
    name: str = "Pippa"
    adult: str = "Grandpa"
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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


DESKS = {
    "desk": Desk(
        id="desk",
        label="the old desk",
        phrase="the old desk by the road",
        near="near the window",
        old_saying="when a skittle starts acting like a storm in a sugar coat, keep your shoes tied",
        tells="It had a thousand tiny scratches that looked like warning lines.",
        tags={"desk", "foreshadowing"},
    ),
    "counter": Desk(
        id="counter",
        label="the bakery counter",
        phrase="the bakery counter under the bell",
        near="beside the flour bin",
        old_saying="when the sugar begins to roll, the paper ought to stay put",
        tells="Its brass bell trembled before anyone touched it.",
        tags={"counter", "foreshadowing"},
    ),
}

PRIZES = {
    "skittle": Prize("skittle", "a shiny skittle", "the shiny skittle", True, {"skittle", "humor"}),
}

CONTAINERS = {
    "jar": Container("jar", "jar", "a jar of stationery", "opened", "closed", {"skittle"}, {"stationery"}),
    "tin": Container("tin", "tin", "a tin of stationery", "opened", "closed", {"skittle"}, {"stationery"}),
}

NAMES = ["Pippa", "Milo", "Nora", "Lennie", "Ava", "Toby"]
ADULTS = ["Grandpa", "Aunt June", "Uncle Bert"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(d, p, c) for d in DESKS for p in PRIZES for c in CONTAINERS if PRIZES[p].risky]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world about skittle and stationery.")
    ap.add_argument("--place", choices=DESKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULTS)
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
              and (args.prize is None or c[1] == args.prize)
              and (args.container is None or c[2] == args.container)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, prize, container = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        prize=prize,
        container=container,
        name=args.name or rng.choice(NAMES),
        adult=args.adult or rng.choice(ADULTS),
    )


def tell(params: StoryParams) -> World:
    if params.place not in DESKS or params.prize not in PRIZES or params.container not in CONTAINERS:
        raise StoryError("invalid story parameters")
    desk = DESKS[params.place]
    prize = PRIZES[params.prize]
    container = CONTAINERS[params.container]
    world = World(desk)
    child = world.add(Entity("child", kind="character", type="girl", label=params.name))
    adult = world.add(Entity("adult", kind="character", type="man", label=params.adult))
    tray = world.add(Entity("tray", type="thing", label="paper tray", meters={"tilted": 0.0}, memes={"drama": 0.0}))
    jar = world.add(Entity("jar", type="thing", label=container.label, meters={"closed": 1.0}, memes={"ordinary": 1.0}))
    skittle = world.add(Entity("skittle", type="thing", label=prize.label, meters={"rolling": 0.0}, memes={"mischief": 0.0}))
    letters = world.add(Entity("letters", type="thing", label="stationery", meters={"shuffled": 0.0}, memes={"tidy": 1.0}, plural=True))
    world.facts.update(child=child, adult=adult, tray=tray, jar=jar, skittle=skittle, letters=letters, desk=desk, params=params)

    child.meters["bouncy"] = 1.0
    child.memes["wonder"] = 1.0
    child.memes["humor"] = 1.0
    child.memes["worry"] = 1.0
    adult.memes["caution"] = 1.0
    desk_old = desk.old_saying

    world.say(f"{params.name} came to {desk.phrase}, where {desk.tells}")
    world.say(f"Inside sat {container.phrase}, and in it was {prize.phrase}.")
    world.say(f"{params.name} smiled at the odd little treasure, because a skittle is a tiny round thing with a big idea in its head.")
    world.para()
    world.say(f"{params.adult} pointed at the desk and said, \"{desk_old}.\"")
    world.say(f"{params.name} laughed, but the desk drawer gave a small rattling cough as if it knew more than it said.")
    desk.meters["foretold"] = 1.0
    propagate(world)
    world.para()
    tray.meters["tilted"] = 1.0
    world.say(f"{params.name} wanted to toss the skittle into the paper tray, where the stationery waited like a flock of white geese.")
    child.meters["bouncy"] += 1.0
    world.say(f"But the jar wobbled, the tray leaned, and {params.adult} lifted a finger like a weather vane before a storm.")
    if world.get("jar").meters["closed"] >= THRESHOLD:
        world.say(f'\"Keep that jar closed,\" {params.adult} said, \"or the stationery will dance itself into a dither.\"')
    if prize.label == "a shiny skittle":
        skittle.meters["rolling"] = 1.0
    propagate(world)
    if child.meters["bouncy"] >= THRESHOLD:
        world.say(f"{params.name} ignored the warning, and the skittle zipped right into the tray.")
        tray.meters["messy"] = 1.0
        tray.meters["tilted"] = 1.0
        skittle.meters["rolling"] = 1.0
        propagate(world)
    world.para()
    if tray.meters.get("messy", 0) >= THRESHOLD:
        world.say(f"{params.adult} reached in with a ruler as long as a fishing pole and hooked the skittle out.")
        child.memes["humor"] += 1.0
        world.say(f"Then {params.adult} laughed so hard the windows fogged, because the skittle had been bossing the stationery like a mayor in a parade.")
        world.say("The child tucked the skittle back in its jar, and the papers settled down neat as Sunday clothes.")
        jar.meters["closed"] = 1.0
        tray.meters["tidy"] = 1.0
    else:
        world.say(f"{params.name} thought better of it and kept the skittle in the jar.")
        world.say("The stationery stayed stacked, the desk stopped rattling, and the whole room looked as calm as a quilt in summer.")
    world.facts.update(outcome="mess" if tray.meters.get("messy", 0) >= THRESHOLD else "calm")
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a tall-tale style story for a young child that includes the words "{p.prize}" and "stationery".',
        f"Tell a cautionary story where {p.name} meets a skittle near stationery and an adult gives a funny warning.",
        f"Write a foreshadowing-heavy, humorous story about {p.name}, {p.adult}, and a desk that seems to know what is coming.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]
    desk: Desk = world.facts["desk"]
    outcome = world.facts["outcome"]
    return [
        QAItem(
            question=f"What did {p.name} find at {desk.label}?",
            answer=f"{p.name} found a shiny skittle in a jar of stationery. It looked small, but it stirred up big trouble for the paper tray.",
        ),
        QAItem(
            question=f"Why did {p.adult} warn {p.name} about the skittle?",
            answer=f"{p.adult} warned {p.name} because the desk and the rattling drawer were already acting like a foreshadowing sign. The warning mattered because the skittle could make the stationery fly apart.",
        ),
        QAItem(
            question=f"What happened when the skittle reached the paper tray?",
            answer="The stationery started fluttering and the tray got messy. That was the tall-tale joke paying off, because the little skittle caused a grand commotion.",
        ),
        QAItem(
            question=f"How did the story end if the papers were still in order?",
            answer="The skittle went back into its jar, the stationery stayed tidy, and the desk looked proud of itself. The ending proved the warning had been worth hearing.",
        ) if outcome == "calm" else QAItem(
            question=f"How did the story end after the skittle caused a mess?",
            answer="The adult hooked the skittle out with a ruler, then laughed until the windows fogged. The stationery got straightened out again, so the child learned to mind the warning next time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is stationery?", "Stationery is paper stuff like letters, envelopes, and cards that people write on or send to someone."),
        QAItem("What is a skittle in this story?", "A skittle is a small round candy or game piece here, and the story uses it like a lively little troublemaker."),
        QAItem("Why are foreshadowing clues useful?", "Foreshadowing clues hint that something is about to happen. They help a reader feel the story coming before it arrives."),
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
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
stationery(paper).
stationery(envelope).
foreshadowing(desk_rattle).
cautionary(warning).
humor(laugh).
messy(E) :- bouncy(child), tilted(tray), stationery(E).
payoff(ended_tidy) :- closed(jar), not messy(paper).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("stationery", "paper"),
        asp.fact("stationery", "envelope"),
        asp.fact("foreshadowing", "desk_rattle"),
        asp.fact("cautionary", "warning"),
        asp.fact("humor", "laugh"),
        asp.fact("bouncy", "child"),
        asp.fact("tilted", "tray"),
        asp.fact("closed", "jar"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show stationery/1."))
    return sorted(set(asp.atoms(model, "stationery")))


def asp_verify() -> int:
    import tempfile
    ok = set(asp_valid_combos()) == {("envelope",), ("paper",)}
    sample_ok = False
    try:
        sample = generate(StoryParams(place="desk", prize="skittle", container="jar", name="Pippa", adult="Grandpa"))
        sample_ok = bool(sample.story)
    except Exception:
        sample_ok = False
    if ok and sample_ok:
        print("OK: ASP twin and Python generation smoke test passed.")
        return 0
    print("VERIFY FAILED")
    return 1


def valid_story(params: StoryParams) -> bool:
    return params.place in DESKS and params.prize in PRIZES and params.container in CONTAINERS


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError("invalid params")
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


CURATED = [
    StoryParams(place="desk", prize="skittle", container="jar", name="Pippa", adult="Grandpa"),
    StoryParams(place="counter", prize="skittle", container="tin", name="Milo", adult="Aunt June"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show stationery/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{k}" for k in sorted({x[0] for x in valid_combos()})))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
