#!/usr/bin/env python3
"""
compose_ugly_cautionary_tall_tale.py
====================================

A small cautionary tall-tale storyworld about a child who tries to compose an
ugly boastful tune, learns why that choice is a problem, and ends by making a
better sound.

The tale shape:
- beginning: the child is proud and wants to compose something loud and ugly
- middle: the ugly tune startles people and makes a mess of the room's mood
- turn: a wise helper warns that loud ugly show-offs can scare good work away
- ending: the child changes the tune into something kinder and cleaner

The world tracks both meters and memes:
- meters: volume, clutter, sparkle, silence, neatness
- memes: pride, worry, courage, relief, patience

This script follows the Storyweavers world contract and includes a Python
reasonableness gate plus an inline ASP twin for registry parity.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("volume", "clutter", "sparkle", "silence", "neatness"):
            self.meters.setdefault(k, 0.0)
        for k in ("pride", "worry", "courage", "relief", "patience", "humor"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
    quiet: bool = True


@dataclass
class Idea:
    id: str
    kind: str
    verb: str
    adjective: str
    effect: str
    caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    guards: set[str]
    use_line: str
    finish_line: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _nice_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    maker = world.get("child")
    if maker.meters["volume"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.place.quiet:
        world.facts["startled"] = True
        world.get("room").meters["silence"] = max(0.0, world.get("room").meters["silence"] - 1)
        out.append("The room shook with the sound, and even the teacup forgot how to sit still.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["clutter"] < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room = world.get("room")
    room.meters["neatness"] = max(0.0, room.meters["neatness"] - 1)
    out.append("The ugly pile of odds and ends made the whole place look like it had lost its comb.")
    return out


CAUSAL_RULES = [_r_noise, _r_mess]


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


@dataclass
class StoryParams:
    place: str
    idea: str
    child: str
    age: int
    helper: str
    seed: Optional[int] = None


PLACES = {
    "porch": Place("the long front porch", affords={"compose"}, quiet=True),
    "barn": Place("the red barn", affords={"compose"}, quiet=False),
    "kitchen": Place("the big kitchen", affords={"compose"}, quiet=True),
}

IDEAS = {
    "brag_song": Idea(
        id="brag_song",
        kind="song",
        verb="compose a bragging song",
        adjective="ugly",
        effect="loud and ugly",
        caution="loud and ugly songs can scare the calm right out of a room",
        tags={"compose", "ugly", "cautionary", "tall_tale"},
    ),
    "crooked_poem": Idea(
        id="crooked_poem",
        kind="poem",
        verb="compose a crooked poem",
        adjective="ugly",
        effect="sharp and ugly",
        caution="sharp and ugly words can poke more than they praise",
        tags={"compose", "ugly", "cautionary", "tall_tale"},
    ),
    "rattle_tune": Idea(
        id="rattle_tune",
        kind="tune",
        verb="compose a rattly tune",
        adjective="ugly",
        effect="rattly and ugly",
        caution="rattly and ugly tunes can rattle a careful heart",
        tags={"compose", "ugly", "cautionary", "tall_tale"},
    ),
}

TOOLS = {
    "metronome": Tool(
        id="metronome",
        label="a little metronome",
        helps={"compose"},
        guards={"clutter"},
        use_line="They set the little metronome ticking, so the idea could find its feet.",
        finish_line="The ticking kept the tune honest while the child polished every crooked note.",
    ),
    "blanket": Tool(
        id="blanket",
        label="a thick blanket",
        helps={"quiet"},
        guards={"volume"},
        use_line="They draped a thick blanket over the chair and let the sound soften.",
        finish_line="The blanket drank up the bluster until the ugly tune turned gentle enough to hug.",
    ),
    "pencil": Tool(
        id="pencil",
        label="a blue pencil",
        helps={"revise"},
        guards={"pride"},
        use_line="The blue pencil scratched out the boastful parts and left room for kinder words.",
        finish_line="One careful line at a time, the child rewrote the whole thing into a friendlier song.",
    ),
}

CHILDREN = ["Mabel", "Toby", "Nina", "Otis", "June", "Lena", "Wes", "Pippa"]
HELPERS = ["grandpa", "aunt", "neighbor", "teacher", "sibling"]


def reasonableness_gate(place: Place, idea: Idea) -> bool:
    return "compose" in place.affords and "ugly" in idea.tags


def select_tool(idea: Idea) -> Tool:
    if idea.id == "brag_song":
        return TOOLS["blanket"]
    if idea.id == "crooked_poem":
        return TOOLS["pencil"]
    return TOOLS["metronome"]


def tell(place: Place, idea: Idea, child_name: str, helper_kind: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type="child", label=child_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_kind))
    room = world.add(Entity(id="room", kind="place", type="room", label=place.name))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="tool"))

    child.memes["pride"] += 1
    child.say = world.say  # not used, but keeps intent obvious
    world.say(f"{child_name} was a small, quick-handed child with a head full of tunes and tall tales.")
    world.say(
        f"One day, {child_name} wanted to {idea.verb}, because {child_name} thought "
        f"something {idea.adjective} would sound bigger than anything sweet."
    )
    world.say(
        f"{child_name} chose {place.name} for the tryout, and the place was so still "
        f"that even the floorboards seemed to listen."
    )
    world.para()

    child.meters["volume"] += 1
    child.meters["clutter"] += 1
    room.meters["silence"] += 1
    world.say(
        f"{child_name} stomped out the first line: it was {idea.effect}, all elbows and thunder."
    )
    propagate(world, narrate=True)

    world.para()
    helper_ent = world.get("helper")
    helper_ent.memes["patience"] += 1
    child.memes["worry"] += 1 if world.facts.get("startled") else 0

    world.say(
        f"{helper_kind.capitalize()} came in with a calm eye and said, "
        f"'{idea.caution.capitalize()}.'"
    )
    world.say(
        f"'{child_name}, a good song can be loud, but it should not bruise the ears of the room.'"
    )

    chosen = select_tool(idea)
    tool.label = chosen.label
    tool.id = chosen.id
    world.say(chosen.use_line)
    if "volume" in chosen.guards:
        room.meters["silence"] += 1
    if "pride" in chosen.guards:
        child.memes["pride"] = max(0.0, child.memes["pride"] - 1)
        child.memes["courage"] += 1
    if "clutter" in chosen.guards:
        room.meters["neatness"] += 1

    world.say(
        f"{child_name} listened, took a breath, and started again, this time with fewer thumps and more thought."
    )
    child.meters["volume"] = max(0.0, child.meters["volume"] - 1)
    child.meters["clutter"] = max(0.0, child.meters["clutter"] - 1)
    child.meters["sparkle"] += 1
    child.memes["relief"] += 1
    child.memes["patience"] += 1
    room.meters["neatness"] += 1
    world.say(chosen.finish_line)
    world.say(
        f"By the last note, the ugly brag had turned into a brave little tune, and the room felt tidy enough to smile."
    )

    world.facts.update(
        child=child,
        helper=helper_ent,
        room=room,
        tool=chosen,
        idea=idea,
        place=place,
        startled=bool(world.facts.get("startled")),
    )
    return world


KNOWLEDGE = {
    "compose": [
        QAItem(
            question="What does it mean to compose something?",
            answer="To compose something means to make or put together a piece of music, a poem, or another creative work.",
        )
    ],
    "ugly": [
        QAItem(
            question="What does ugly mean in a story?",
            answer="Ugly usually means unpleasant to look at or hear, or rough in a way that feels harsh instead of lovely.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What is a cautionary story?",
            answer="A cautionary story is a story that warns about a bad choice and shows why a wiser choice matters.",
        )
    ],
    "tall_tale": [
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a funny, exaggerated story that makes ordinary things sound huge and impossible, but still easy to imagine.",
        )
    ],
}


@dataclass
class StoryConfig:
    place: str
    idea: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"].label
    idea = world.facts["idea"]
    return [
        f'Write a short cautionary tall tale about {child} trying to compose something ugly.',
        f"Tell a child-facing story where {child} wants to {idea.verb} and a helper shows a kinder way.",
        f'Write a funny warning story that uses the words "compose" and "ugly" and ends with a better tune.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"].label
    helper = world.facts["helper"].label
    idea = world.facts["idea"]
    place = world.facts["place"].name
    tool = world.facts["tool"].label
    qa = [
        QAItem(
            question=f"What did {child} want to do at {place}?",
            answer=f"{child} wanted to {idea.verb} at {place}, because {child} thought the result would sound bold and funny.",
        ),
        QAItem(
            question=f"Who helped {child} when the sound got too wild?",
            answer=f"{helper.capitalize()} helped {child} slow down and make the piece kinder.",
        ),
        QAItem(
            question=f"What did the helper use to improve the ugly piece?",
            answer=f"They used {tool} to tame the rough parts and shape the tune into something better.",
        ),
    ]
    if world.facts.get("startled"):
        qa.append(
            QAItem(
                question=f"Why did the room react to {child}'s first try?",
                answer="The first try was loud and ugly, so it startled the still room and made everything feel less calm.",
            )
        )
    qa.append(
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child} stopped showing off and made a cleaner, gentler piece that fit the room much better.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("compose", "ugly", "cautionary", "tall_tale"):
        out.extend(KNOWLEDGE[tag])
    return out


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
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, in world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "porch": Place("the long front porch", affords={"compose"}, quiet=True),
    "barn": Place("the red barn", affords={"compose"}, quiet=False),
    "kitchen": Place("the big kitchen", affords={"compose"}, quiet=True),
}

IDEA_REGISTRY = IDEAS

CURATED = [
    StoryConfig(place="porch", idea="brag_song"),
    StoryConfig(place="kitchen", idea="crooked_poem"),
    StoryConfig(place="barn", idea="rattle_tune"),
]


def explain_rejection(place: Place, idea: Idea) -> str:
    if "compose" not in place.affords:
        return f"(No story: {place.name} does not support composing.)"
    if "ugly" not in idea.tags:
        return f"(No story: that idea is not ugly enough for this cautionary tale.)"
    return "(No story: the requested options do not make a reasonable story.)"


@dataclass
class StoryParams:
    place: str
    idea: str
    name: str
    helper: str
    seed: Optional[int] = None


ASP_RULES = r"""
place(porch). place(barn). place(kitchen).
affords(porch,compose). affords(barn,compose). affords(kitchen,compose).
quiet(porch). quiet(kitchen).

idea(brag_song). idea(crooked_poem). idea(rattle_tune).
ugly(brag_song). ugly(crooked_poem). ugly(rattle_tune).
cautionary(brag_song). cautionary(crooked_poem). cautionary(rattle_tune).
tall_tale(brag_song). tall_tale(crooked_poem). tall_tale(rattle_tune).

valid(P,I) :- place(P), idea(I), affords(P,compose), ugly(I), cautionary(I), tall_tale(I).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, idea in IDEA_REGISTRY.items():
        lines.append(asp.fact("idea", iid))
        lines.append(asp.fact("ugly", iid))
        lines.append(asp.fact("cautionary", iid))
        lines.append(asp.fact("tall_tale", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, i) for p in SETTINGS for i in IDEA_REGISTRY if reasonableness_gate(SETTINGS[p], IDEA_REGISTRY[i])}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary tall-tale storyworld about composing an ugly tune.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--idea", choices=sorted(IDEA_REGISTRY))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(set(HELPERS)))
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
    place = args.place or rng.choice(list(SETTINGS))
    idea = args.idea or rng.choice(list(IDEA_REGISTRY))
    if not reasonableness_gate(SETTINGS[place], IDEA_REGISTRY[idea]):
        raise StoryError(explain_rejection(SETTINGS[place], IDEA_REGISTRY[idea]))
    name = args.name or rng.choice(CHILDREN)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, idea=idea, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], IDEA_REGISTRY[params.idea], params.name, params.helper)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combos:")
        for p, i in vals:
            print(f"  {p} {i}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=c.place, idea=c.idea, name="Mabel", helper="grandpa")) for c in CURATED]
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
            header = f"### {p.name}: {p.idea} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
