#!/usr/bin/env python3
"""
storyworlds/worlds/religion_format_bad_ending_cautionary_slice_of.py
====================================================================

A small slice-of-life story world about a child, a religious gathering, and
the cautionary trouble that comes from ignoring the expected format.

Premise:
- A child helps prepare for a quiet worship service or community prayer.
- The setting has a simple order: welcome, quiet waiting, song, reading, and
  a closing thanks.
- The child wants to improvise or rush the format.
- Careful adults warn that the wrong order can upset people, interrupt the
  service, or make the child lose something important.

Story shape:
- Beginning: a warm household / hall / courtyard routine.
- Middle: a small social mistake tied to format and respect.
- Ending: a bad ending in the sense that the child does not get the desired
  outcome; the story closes on a cautionary image that proves what changed.

The world uses meters for physical state and memes for emotional state.
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

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "brother", "son"}
        female = {"girl", "mother", "mom", "woman", "sister", "daughter"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap_pronoun(self) -> str:
        return self.pronoun().capitalize()


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    vibe: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass
class RitualFormat:
    id: str
    label: str
    steps: list[str]
    required_items: set[str] = field(default_factory=set)
    respect_words: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    ritual: str
    item: str
    name: str
    gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, ritual: RitualFormat) -> None:
        self.place = place
        self.ritual = ritual
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.place, self.ritual)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


PLACES = {
    "home_room": Place(
        id="home_room",
        label="the front room",
        indoor=True,
        vibe="soft and quiet",
        affords={"prepare", "sort", "practice"},
    ),
    "hall": Place(
        id="hall",
        label="the community hall",
        indoor=True,
        vibe="bright and careful",
        affords={"prepare", "sort", "practice", "gather"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the courtyard",
        indoor=False,
        vibe="open and breezy",
        affords={"gather", "wait", "practice"},
    ),
}

RITUALS = {
    "song_reading_thanks": RitualFormat(
        id="song_reading_thanks",
        label="song, reading, thanks",
        steps=["welcome", "quiet_waiting", "song", "reading", "thanks"],
        required_items={"song_card", "reading_page"},
        respect_words=["quiet", "careful", "respect", "listen"],
    ),
    "prayer_offering_bow": RitualFormat(
        id="prayer_offering_bow",
        label="prayer, offering, bow",
        steps=["wash_hands", "prayer", "offering", "bow"],
        required_items={"offering_bowl", "clean_cloth"},
        respect_words=["gentle", "steady", "respect", "listen"],
    ),
}

ITEMS = {
    "song_card": Item("song_card", "song card", "a folded song card", "hands", fragile=True),
    "reading_page": Item("reading_page", "reading page", "a printed reading page", "hands", fragile=True),
    "offering_bowl": Item("offering_bowl", "offering bowl", "a small offering bowl", "hands", fragile=True),
    "clean_cloth": Item("clean_cloth", "clean cloth", "a clean cloth", "hands", fragile=False),
}

NAMES = {
    "girl": ["Mia", "Leah", "Nora", "Ava", "Zoe", "Rina"],
    "boy": ["Owen", "Noah", "Eli", "Finn", "Leo", "Theo"],
}
TRAITS = ["careful", "curious", "serious", "shy", "busy", "quiet"]

CURATED = [
    StoryParams(place="hall", ritual="song_reading_thanks", item="song_card", name="Mia", gender="girl", caretaker="mother", trait="curious"),
    StoryParams(place="home_room", ritual="prayer_offering_bow", item="offering_bowl", name="Owen", gender="boy", caretaker="father", trait="careful"),
    StoryParams(place="courtyard", ritual="song_reading_thanks", item="reading_page", name="Nora", gender="girl", caretaker="mother", trait="quiet"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for ritual in RITUALS.values():
            for item in ITEMS.values():
                if place.id in {"hall", "home_room", "courtyard"}:
                    if item.id in ritual.required_items:
                        combos.append((place.id, ritual.id, item.id))
    return combos


def reason_invalid(ritual: RitualFormat, item: Item) -> str:
    return (
        f"(No story: the chosen ritual format depends on {sorted(ritual.required_items)}, "
        f"but the item {item.label} does not fit that format.)"
    )


def reason_gender(item_id: str, gender: str) -> str:
    return f"(No story: the requested combination does not fit the chosen child gender {gender}.)"


def _step_needed(ritual: RitualFormat) -> str:
    return ritual.steps[0] if ritual.steps else "the first step"


def _last_step(ritual: RitualFormat) -> str:
    return ritual.steps[-1] if ritual.steps else "the last step"


def setup_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    ritual = RITUALS[params.ritual]
    world = World(place, ritual)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker, label=params.caretaker))
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        type=params.item,
        label=ITEMS[params.item].label,
        phrase=ITEMS[params.item].phrase,
        owner=child.id,
        caretaker=caretaker.id,
    ))
    world.facts.update(child=child, caretaker=caretaker, item=item, place=place, ritual=ritual)
    return world


def tell_story(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    ritual: RitualFormat = f["ritual"]  # type: ignore[assignment]

    child.memes["curiosity"] = 1
    child.memes["desire"] = 1
    world.say(
        f"{child.id} was a {world.facts.get('trait', 'quiet')} child who liked the calm little "
        f"rituals at {place.label}."
    )
    world.say(
        f"On days like this, the family used a simple format: {', '.join(ritual.steps[:-1])}, and then {ritual.steps[-1]}."
    )
    world.say(
        f"{child.id} carried {item.phrase} because it was {item.label} day, and {caretaker.pronoun('possessive')} "
        f"{caretaker.label} had asked for careful hands."
    )

    world.para()
    child.memes["restless"] = 1
    world.say(
        f"When they reached {place.label}, {child.id} saw people waiting in the wrong order for {child.pronoun('possessive')} taste."
    )
    world.say(
        f"{child.cap_pronoun()} thought the format looked slow, so {child.pronoun()} tried to skip ahead and do the loud part first."
    )
    child.meters["careless_move"] = 1
    child.memes["defiance"] = 1

    if item.id in {"song_card", "reading_page"}:
        item.meters["creased"] = 1
        item.meters["dropped"] = 1
        child.meters["mess"] = 1
        world.say(
            f"The {item.label} slipped from {child.pronoun('possessive')} fingers and bent at the corner."
        )
    else:
        item.meters["spilled"] = 1
        child.meters["mess"] = 1
        world.say(
            f"The little {item.label} tipped, and now there was a mess to clean before the next step."
        )

    world.say(
        f"{caretaker.cap_pronoun()} took a slow breath and said that a good format helps everyone stay calm and listen."
    )
    child.memes["shame"] = 1
    child.memes["worry"] = 1

    world.para()
    world.say(
        f"{child.id} wanted to fix it fast, but the line had already broken and the service could not be rewound."
    )
    world.say(
        f"In the end, {child.id} sat very still while the grown-ups finished without {child.pronoun('object')}."
    )
    child.memes["loss"] = 1
    world.say(
        f"The {item.label} stayed bent, the room stayed quiet, and {child.id} learned that rushing a sacred format can leave a lonely feeling behind."
    )

    world.facts["bad_ending"] = True
    world.facts["trait"] = world.facts.get("trait", "quiet")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    ritual: RitualFormat = f["ritual"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    return [
        f'Write a short slice-of-life story about religion and format at {place.label} that includes {item.label}.',
        f"Tell a gentle cautionary story where {child.id} ignores the order of {ritual.label} and learns too late.",
        f"Write a child-facing story about a small service, a fragile object, and a bad ending that still feels realistic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    item: Entity = f["item"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    ritual: RitualFormat = f["ritual"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {child.id} go with the {item.label}?",
            answer=f"{child.id} went to {place.label}, where the family followed a careful religious format.",
        ),
        QAItem(
            question=f"What was the format the family wanted to follow?",
            answer=f"They wanted to follow {ritual.label}: {', '.join(ritual.steps)}.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry when {child.id} rushed ahead?",
            answer=f"{caretaker.pronoun('subject').capitalize()} worried because the {item.label} was fragile and the order of the service mattered.",
        ),
        QAItem(
            question=f"What happened to the {item.label} at the end?",
            answer=f"It got bent or spoiled when {child.id} hurried, so the story ends with a cautionary bad feeling instead of a happy fix.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ritual: RitualFormat = f["ritual"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is a format?",
            answer="A format is the order that people plan to do things in, like step by step.",
        ),
        QAItem(
            question="Why do people keep a quiet tone in a religious gathering?",
            answer="People stay quiet so they can listen, show respect, and let the service feel calm.",
        ),
    ]
    if "song" in ritual.steps:
        out.append(
            QAItem(
                question="Why do families sometimes use song cards or reading pages?",
                answer="They use them to help people remember the words and follow the service in the right order.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {' '.join(bits) if bits else 'idle'}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Place,Ritual,Item) :- place(Place), ritual(Ritual), item(Item), requires(Ritual,Item), affords(Place,Ritual).
bad_combo(Place,Ritual,Item) :- place(Place), ritual(Ritual), item(Item), not valid_combo(Place,Ritual,Item).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for rid, r in RITUALS.items():
        lines.append(asp.fact("ritual", rid))
        for s in r.steps:
            lines.append(asp.fact("step", rid, s))
        for req in sorted(r.required_items):
            lines.append(asp.fact("requires", rid, req))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for rid, r in RITUALS.items():
            if not (p.affords & {"gather", "practice", "prepare"}):
                continue
            for iid in r.required_items:
                if iid in ITEMS:
                    out.append((pid, rid, iid))
    return sorted(out)


def asp_valid_story_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_story_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life religion format cautionary story world.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--ritual", choices=sorted(RITUALS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.ritual and args.item:
        if (args.place, args.ritual, args.item) not in valid_story_combos():
            raise StoryError(reason_invalid(RITUALS[args.ritual], ITEMS[args.item]))
    choices = valid_story_combos()
    choices = [c for c in choices if (not args.place or c[0] == args.place) and (not args.ritual or c[1] == args.ritual) and (not args.item or c[2] == args.item)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, ritual, item = rng.choice(choices)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, ritual=ritual, item=item, name=name, gender=gender, caretaker=caretaker, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world.facts["trait"] = params.trait
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
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_story_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
