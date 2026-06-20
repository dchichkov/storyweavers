#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/set_gerund_violet_magic_dialogue_twist_myth.py
===============================================================================

A standalone storyworld for a tiny mythic domain: a child apprentice, a violet
spell, a spoken warning, and a twist that turns a risky magic choice into a
better ending.

The seed words are intentionally strange: "set-gerund" and "violet". Here, the
world treats "set-gerund" as an old spell-name from myth: a setting charm that
keeps something moving in the right form, like a vow, a chant, or a river-song.

The core premise is myth-like:
- someone reaches for a powerful violet magic
- another character warns them in dialogue
- a twist changes what the magic was really for
- the ending proves something has changed in the world state
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
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Relic:
    id: str
    label: str
    glow: str
    powers: set[str] = field(default_factory=set)
    violet: bool = False
    kind: str = "relic"

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Spell:
    id: str
    label: str
    chant: str
    effect: str
    risk: int
    twist: str
    kind: str = "spell"
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_violet(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["violet_glow"] < THRESHOLD:
            continue
        sig = ("violet", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for char in list(world.entities.values()):
            if char.kind == "character":
                char.memes["wonder"] += 1
        out.append("__violet__")
    return out


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twisted"):
        return out
    if world.facts.get("lesson_seen") and world.facts.get("spell_used"):
        world.facts["twisted"] = True
        out.append("__twist__")
    return out


RULES = [Rule("violet", _r_violet), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
@dataclass
class StoryParams:
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    magic: str
    relic: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


HEROES = ["Ari", "Luna", "Mira", "Niko", "Sera", "Theo"]
ELDERS = ["Iris", "Bram", "Mara", "Orin", "Selene", "Dorian"]

MAGICS = {
    "set_gerund": Spell(
        "set_gerund",
        "set-gerund",
        "set-gerund",
        "set a vow into motion and keep it true",
        risk=2,
        twist="It was never a spell for making trouble; it was a spell for keeping a promise moving.",
        tags={"magic", "dialogue", "twist", "set-gerund"},
    ),
    "violet_flame": Spell(
        "violet_flame",
        "violet flame",
        "violet flame",
        "call a bright violet light that can scorch a path",
        risk=3,
        twist="The violet light was not a fire at all; it was a lantern for the lost.",
        tags={"magic", "dialogue", "violet"},
    ),
}

RELICS = {
    "stone": Relic("stone", "violet stone", "a quiet violet glow", {"light"}, violet=True),
    "reed": Relic("reed", "reed flute", "a soft silver hum", {"song"}, violet=False),
    "crown": Relic("crown", "moon crown", "a pale star-sheen", {"truth"}, violet=True),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic world of violet magic and a spoken twist.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--relic", choices=RELICS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in HEROES:
        for e in ELDERS:
            if h == e:
                continue
            for m in MAGICS:
                for r in RELICS:
                    combos.append((h, e, m, r))
    return combos


def explain_rejection() -> str:
    return "(No story: the chosen myth does not have enough contrast for a dialogue twist.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.hero is None or c[0] == args.hero)
              and (args.elder is None or c[1] == args.elder)
              and (args.magic is None or c[2] == args.magic)
              and (args.relic is None or c[3] == args.relic)]
    if not combos:
        raise StoryError(explain_rejection())
    hero, elder, magic, relic = rng.choice(combos)
    return StoryParams(hero, rng.choice(["girl", "boy"]), elder, rng.choice(["woman", "man", "priestess", "priest"]), magic, relic)


def tell(params: StoryParams) -> World:
    world = World()
    h = world.add(Entity(params.hero, kind="character", type=params.hero_gender, role="apprentice",
                         traits=["hopeful", "bold"]))
    e = world.add(Entity(params.elder, kind="character", type=params.elder_gender, role="elder",
                         traits=["wise", "careful"]))
    spell = MAGICS[params.magic]
    relic = RELICS[params.relic]
    world.add(Entity("shrine", kind="place", type="shrine", label="the violet shrine"))
    world.add(Entity(spell.id, kind="spell", type="spell", label=spell.label))
    world.add(Entity(relic.id, kind="relic", type="relic", label=relic.label))

    h.memes["longing"] += 1
    e.memes["care"] += 1

    world.say(
        f"At the edge of the old hill stood {params.hero}, a young seeker who had heard the shrine still sang."
    )
    world.say(
        f"Before the violet shrine rested {relic.label}, and its glow was like dusk caught in glass."
    )
    world.para()
    world.say(
        f"{params.hero} raised a hand. 'I can awaken it with {spell.label},' {h.pronoun()} said."
    )
    world.say(
        f"{params.elder} answered, 'Not every shining thing should be woken. Tell me what you want it for.'"
    )
    world.say(
        f"'{spell.chant},' {params.hero} whispered, and the old air trembled with the first taste of magic."
    )
    world.facts["spell_used"] = True
    relic_ent = world.get(params.relic)
    relic_ent.meters["violet_glow"] += 1
    h.memes["resolve"] += 1
    propagate(world, narrate=False)
    if relic.violet:
        world.say(
            f"The relic brightened in violet light, but {params.elder} smiled and said, 'Look again. The shrine is not asking for power.'"
        )
    else:
        world.say(
            f"The relic shivered, and {params.elder} said, 'That song is not for breaking.'"
        )
    world.facts["lesson_seen"] = True
    world.para()
    world.say(
        f"{params.hero} blinked. 'Then what is it for?' {h.pronoun()} asked."
    )
    world.say(
        f"{params.elder} touched the stone and replied, 'For naming the promise you already meant to keep.'"
    )
    world.facts["twisted"] = False
    propagate(world, narrate=False)
    world.say(
        f"So {params.hero} spoke the set-gerund again, this time as a vow: to keep watch, to keep the path clear, and to keep the shrine lit for travelers."
    )
    relic_ent.meters["violet_glow"] += 1
    h.memes["pride"] += 1
    e.memes["relief"] += 1
    world.facts["twisted"] = True
    world.say(
        f"At once the violet shine changed. It no longer flickered like a trick; it settled into a steady guiding lamp, and the hill path showed its safe little stones."
    )
    world.say(
        f"{params.hero} and {params.elder} walked home together under the new glow, speaking softly all the way."
    )
    world.facts.update(hero=h, elder=e, relic=relic_ent, spell=spell)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a myth-style story that includes the words "set-gerund" and "violet", with magic, dialogue, and a twist.',
        f"Tell a short myth where {f['hero'].id} thinks {f['spell'].label} is for power, but {f['elder'].id} reveals a kinder meaning.",
        "Write a child-facing legend with a spoken warning, a magical mistake, and a twist that turns the ending gentle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, e = f["hero"], f["elder"]
    spell, relic = f["spell"], f["relic"]
    return [
        QAItem(
            f"Who is the story about?",
            f"It is about {h.id}, a young seeker, and {e.id}, the wise elder who knows the old shrine. Their conversation changes how the magic is understood."
        ),
        QAItem(
            f"What did {h.id} think {spell.label} was for at first?",
            f"{h.id} thought it was for power and waking the shrine in a bold way. {e.id} warned that shining magic is not always meant to be used for force."
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that the set-gerund was not a spell for causing trouble at all. It was a vow-spell, and when {h.id} used it as a promise, the violet light became a safe guiding lamp."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a vow?",
            "A vow is a serious promise. In myths, vows often matter because they show what someone is choosing to do again and again."
        ),
        QAItem(
            "What does violet mean?",
            "Violet is a purple color. In stories, violet often feels magical, soft, and a little mysterious."
        ),
        QAItem(
            "Why do elders speak in myths?",
            "Elders often speak in myths because they know the old meanings behind things. Their words can change how a hero understands a problem."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for e in ELDERS:
        lines.append(asp.fact("elder", e))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
    lines.append(asp.fact("has_violet", "violet"))
    lines.append(asp.fact("has_set_gerund", "set-gerund"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(H, E, M, R) :- hero(H), elder(E), magic(M), relic(R), H != E.
twist(M) :- magic(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    rc = 0 if ok else 1
    if ok:
        print(f"OK: ASP and Python valid_combos agree ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos.")
    try:
        p = StoryParams("Ari", "girl", "Iris", "woman", "set_gerund", "stone")
        sample = generate(p)
        assert sample.story.strip()
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("Luna", "girl", "Iris", "woman", "set_gerund", "stone"),
    StoryParams("Mira", "girl", "Selene", "priestess", "violet_flame", "crown"),
    StoryParams("Niko", "boy", "Bram", "man", "set_gerund", "reed"),
]


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
        print(format_qa(sample))


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible mythic combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} with {p.magic} and {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
