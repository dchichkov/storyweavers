#!/usr/bin/env python3
"""
A small Storyweavers world: a Friday exhibition with spaghetti, a tall tale, and
a misunderstanding that gets cleared up.

Premise:
- A child or small performer brings a dramatic "tall tale" to a Friday exhibition.
- Someone thinks the spaghetti is part of the exhibit instead of the lunch or prop.
- The misunderstanding raises tension.
- A clear explanation, a simple demonstration, and a helpful choice resolve it.

The prose is driven by world state, not a frozen template.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the hall"


@dataclass
class Exhibit:
    name: str
    feature: str
    crowd_words: list[str] = field(default_factory=list)


@dataclass
class Prop:
    label: str
    phrase: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hall": Setting(place="the exhibition hall"),
    "gym": Setting(place="the school gym"),
    "museum": Setting(place="the little museum"),
}

EXHIBITS = {
    "tall_tale": Exhibit(
        name="tall tale",
        feature="tall tale",
        crowd_words=["gigantic", "swooping", "marvelous"],
    ),
    "lanterns": Exhibit(
        name="lantern display",
        feature="lanterns",
        crowd_words=["glowing", "golden", "gentle"],
    ),
    "posters": Exhibit(
        name="poster wall",
        feature="posters",
        crowd_words=["bright", "busy", "colorful"],
    ),
}

PROPS = {
    "spaghetti": Prop(
        label="spaghetti",
        phrase="a big bowl of spaghetti",
    ),
    "fork": Prop(
        label="fork",
        phrase="a shiny fork",
    ),
    "cloth": Prop(
        label="cloth",
        phrase="a clean white cloth",
    ),
}

NAMES = ["Milo", "Nina", "June", "Tessa", "Arlo", "Luca", "Pia", "Owen"]
TRAITS = ["curious", "brave", "chatty", "careful", "sparkly", "small"]


@dataclass
class StoryParams:
    setting: str
    exhibit: str
    prop: str
    name: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for e in EXHIBITS:
            for p in PROPS:
                if e == "tall_tale" and p == "spaghetti":
                    combos.append((s, e, p))
    return combos


def explain_rejection(exhibit: str, prop: str) -> str:
    if not (exhibit == "tall_tale" and prop == "spaghetti"):
        return (
            f"(No story: this world needs the tall tale to get mixed up with "
            f"spaghetti, so try the tall_tale exhibit with spaghetti.)"
        )
    return "(No story: that combination is not supported.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def _setup_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.role))
    host = world.add(Entity(id="Host", kind="character", type="adult", label="the host"))
    prop = world.add(Entity(
        id=params.prop,
        type="thing",
        label=PROPS[params.prop].label,
        phrase=PROPS[params.prop].phrase,
        owner=hero.id,
    ))
    exhibit = world.add(Entity(
        id=params.exhibit,
        type="thing",
        label=EXHIBITS[params.exhibit].name,
        phrase=EXHIBITS[params.exhibit].feature,
    ))
    world.facts.update(hero=hero, host=host, prop=prop, exhibit=exhibit)
    return world


def tell_story(world: World) -> None:
    hero: Entity = world.facts["hero"]
    host: Entity = world.facts["host"]
    prop: Entity = world.facts["prop"]
    exhibit: Entity = world.facts["exhibit"]

    hero.memes["pride"] = 1
    hero.memes["wonder"] = 1

    world.say(
        f"On Friday, {hero.id} walked into {world.setting.place} with a grin and "
        f"a story so big it seemed to wear boots."
    )
    world.say(
        f"At the middle of the room stood the {exhibit.label}, all {random.choice(EXHIBITS[exhibit.id].crowd_words)} and proud."
    )
    world.say(
        f"{hero.id} had brought {prop.phrase}, because {hero.pronoun('possessive')} "
        f"plan for the day was to tell a tall tale and share it like treasure."
    )

    world.para()
    hero.memes["excited"] = 1
    hero.memes["misunderstood"] = 1
    world.say(
        f"Then someone looked at {prop.label} and blinked. "
        f'"Is that part of the exhibit?" the host asked, as if a bowl could be a giant statue.'
    )
    world.say(
        f"{hero.id} shook {hero.pronoun('possessive')} head. "
        f"{hero.pronoun().capitalize()} meant it for lunch, not for the display."
    )
    host.memes["confused"] = 1
    world.say(
        f"But the mix-up had already landed like a kite in a tree: now the room felt small and puzzled."
    )

    world.para()
    hero.memes["calm"] = 1
    world.say(
        f"{hero.id} took a breath and pointed at the bowl. "
        f'"The spaghetti is for eating," {hero.pronoun()} said. '
        f'"The tall tale is the one I am telling."'
    )
    world.say(
        f"To prove it, {hero.id} told the silliest part first, with {prop.label} held safely aside."
    )
    host.memes["relief"] = 1
    host.memes["confused"] = 0
    hero.memes["pride"] += 1
    world.say(
        f"The host laughed, because the mistake was only a mistake. "
        f"The Friday exhibition became brighter, and the spaghetti stayed a supper, not a sculpture."
    )

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short child-friendly tall tale about a Friday exhibition and spaghetti.',
        f"Tell a story where {f['hero'].id} brings spaghetti to {world.setting.place} and someone thinks it belongs in the exhibit.",
        "Write a simple story in which a misunderstanding at an exhibition gets cleared up kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prop: Entity = f["prop"]
    exhibit: Entity = f["exhibit"]
    host: Entity = f["host"]

    return [
        QAItem(
            question=f"What did {hero.id} bring to the Friday exhibition?",
            answer=f"{hero.id} brought {prop.phrase} to the exhibition.",
        ),
        QAItem(
            question=f"What did the host first think about the spaghetti?",
            answer=f"The host first thought the spaghetti might be part of the exhibit, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the misunderstanding?",
            answer=(
                f"{hero.id} explained that the spaghetti was for eating and the {exhibit.label} was the thing on display. "
                f"That made the host understand."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, the room felt cheerful again, the misunderstanding was cleared up, and the spaghetti stayed a meal instead of a display."
            ),
        ),
        QAItem(
            question=f"Who laughed after the misunderstanding was explained?",
            answer=f"The host laughed after hearing the explanation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an exhibition?",
            answer="An exhibition is a show where people display things so others can look at them.",
        ),
        QAItem(
            question="What is spaghetti?",
            answer="Spaghetti is long, thin pasta that people usually eat with sauce.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but it is not.",
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
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"  {e.id:10} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid_combo(S, E, P) :- setting(S), exhibit(E), prop(P), friday_story(S, E, P).
friday_story(S, tall_tale, spaghetti) :- setting(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid in EXHIBITS:
        lines.append(asp.fact("exhibit", eid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("feature", "tall_tale"))
    lines.append(asp.fact("word", "friday"))
    lines.append(asp.fact("word", "exhibition"))
    lines.append(asp.fact("word", "spaghetti"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid_combo/3.\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in ASP:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(setting="hall", exhibit="tall_tale", prop="spaghetti", name="Milo", role="boy"),
    StoryParams(setting="museum", exhibit="tall_tale", prop="spaghetti", name="Nina", role="girl"),
    StoryParams(setting="gym", exhibit="tall_tale", prop="spaghetti", name="Arlo", role="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Friday exhibition story world with spaghetti and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["boy", "girl"])
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
    if args.exhibit and args.prop and not (args.exhibit == "tall_tale" and args.prop == "spaghetti"):
        raise StoryError(explain_rejection(args.exhibit, args.prop))

    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.exhibit is None or c[1] == args.exhibit)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, exhibit, prop = rng.choice(combos)
    role = args.role or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, exhibit=exhibit, prop=prop, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
