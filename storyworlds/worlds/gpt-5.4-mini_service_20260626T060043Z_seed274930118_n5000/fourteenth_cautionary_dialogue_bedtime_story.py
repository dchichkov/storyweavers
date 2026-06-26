#!/usr/bin/env python3
"""
storyworlds/worlds/fourteenth_cautionary_dialogue_bedtime_story.py
==================================================================

A small bedtime story world with a cautionary turn and plenty of dialogue.

Seed sketch:
- A child wants one more tiny adventure after bedtime.
- A parent warns that the night can make a room feel bigger, darker, and lonelier.
- The child argues for "just one more" of the fourteenth bedtime thing.
- A soft compromise turns the last step into a safe, sleepy ending.

The domain is intentionally small and classical:
- one child
- one parent
- one bedtime object the child wants to keep using
- one nighttime place that becomes less cozy if the child disobeys
- one cautionary warning, followed by a dialogue-based resolution

The story quality goal is a gentle bedtime tale that still has a real turn:
the parent notices a risk, the child resists, and the ending proves what changed.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "cozy": 0.0, "risk": 0.0, "mess": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "defiance": 0.0, "calm": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class BedtimeItem:
    id: str
    label: str
    phrase: str
    cozy_bonus: float = 0.0
    risk_kind: str = ""
    risk_amount: float = 0.0
    allowed_risk: float = 0.0
    prompt: str = ""
    caution: str = ""


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    parent_type: str
    item: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "bedroom": "the bedroom",
    "nursery": "the nursery",
    "attic-room": "the attic room",
}

BEDTIME_ITEMS = {
    "lamp": BedtimeItem(
        id="lamp",
        label="little lamp",
        phrase="a little lamp with a warm yellow shade",
        cozy_bonus=2.0,
        risk_kind="bright",
        risk_amount=1.0,
        allowed_risk=0.0,
        prompt="keep the little lamp on for one more minute",
        caution="the room would stay awake too long",
    ),
    "book": BedtimeItem(
        id="book",
        label="picture book",
        phrase="a picture book with soft pages",
        cozy_bonus=1.5,
        risk_kind="tired",
        risk_amount=0.5,
        allowed_risk=0.0,
        prompt="read the fourteenth page again",
        caution="the child would get more and more sleepy",
    ),
    "bear": BedtimeItem(
        id="bear",
        label="bear",
        phrase="a stuffed bear with a red ribbon",
        cozy_bonus=1.0,
        risk_kind="lost",
        risk_amount=1.0,
        allowed_risk=0.0,
        prompt="take the bear on one more walk across the rug",
        caution="the bear could end up under the bed",
    ),
    "blanket": BedtimeItem(
        id="blanket",
        label="blanket",
        phrase="a striped blanket",
        cozy_bonus=2.5,
        risk_kind="cold",
        risk_amount=1.0,
        allowed_risk=0.0,
        prompt="peek out from under the blanket to listen to the night",
        caution="the child would feel chilly",
    ),
}

NAMES = {
    "girl": ["Mina", "Luna", "Ivy", "Nora", "Elsie", "Ada"],
    "boy": ["Milo", "Theo", "Finn", "Eli", "Noah", "Jasper"],
}

TRAITS = ["sleepy", "curious", "gentle", "stubborn", "quiet", "tender"]


def bedtime_dialogue(world: World, speaker: Entity, line: str) -> None:
    world.say(f'"{line}" {speaker.id} said.')


def parent_warning(world: World, parent: Entity, child: Entity, item: BedtimeItem) -> None:
    world.facts["warning"] = item.caution
    bedtime_dialogue(
        world,
        parent,
        f"Let's stop now. If we keep going, {item.caution}.",
    )
    child.memes["worry"] += 0.5
    world.say(f"{child.id} looked at {item.label} and listened, but {child.pronoun('possessive')} wish for one more tiny thing was still glowing.")


def child_pushes_back(world: World, child: Entity, item: BedtimeItem) -> None:
    child.memes["defiance"] += 1.0
    child.memes["curiosity"] += 1.0
    world.say(
        f'"But it is only the fourteenth {item.label}," {child.id} whispered. '
        f'"Can I please have one more?"'
    )


def state_shift(world: World, child: Entity, item: BedtimeItem) -> None:
    child.meters["tired"] += 1.0
    child.meters["risk"] += item.risk_amount
    if item.id == "lamp":
        child.meters["cozy"] += 0.5
    elif item.id == "blanket":
        child.meters["cozy"] += 1.0
    elif item.id == "bear":
        child.meters["cozy"] += 0.5
    elif item.id == "book":
        child.meters["tired"] += 0.5


def compromise(world: World, parent: Entity, child: Entity, item: BedtimeItem) -> bool:
    child.memes["defiance"] += 0.0
    if item.id == "book":
        world.say(f"{parent.id} smiled softly. \"One more page, and then the lamp goes out,\" {parent.id} said.")
    elif item.id == "bear":
        world.say(f"{parent.id} nodded. \"You may tuck the bear in first,\" {parent.id} said, \"then bear can stay right there all night.\"")
    elif item.id == "blanket":
        world.say(f"{parent.id} tucked the blanket higher. \"We can listen to the rain for one tiny minute,\" {parent.id} said.")
    else:
        world.say(f"{parent.id} softened. \"One last little glow, then sleep,\" {parent.id} said.")
    child.memes["calm"] += 1.0
    child.memes["love"] += 1.0
    child.memes["defiance"] = 0.0
    return True


def resolution(world: World, child: Entity, parent: Entity, item: BedtimeItem) -> None:
    child.meters["cozy"] += item.cozy_bonus
    child.meters["tired"] += 0.5
    world.say(
        f"{child.id} smiled and snuggled closer. "
        f"At last, {child.pronoun('subject')} let the {item.label} rest, and the room felt warm and small again."
    )
    world.say(
        f"{parent.id} kissed {child.pronoun('possessive')} forehead and whispered good night. "
        f"The fourteenth little thing was enough."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        meters={"tired": 1.5, "cozy": 1.0, "risk": 0.0, "mess": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "defiance": 0.0, "calm": 0.0, "love": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label="parent",
        meters={"tired": 0.5, "cozy": 1.0, "risk": 0.0, "mess": 0.0},
        memes={"curiosity": 0.0, "worry": 0.5, "defiance": 0.0, "calm": 1.0, "love": 1.0},
    ))
    item = BEDTIME_ITEMS[params.item]
    bedtime = world.add(Entity(
        id=item.id,
        type="thing",
        label=item.label,
        phrase=item.phrase,
        owner=child.id,
        caretaker=parent.id,
    ))
    bedtime.worn_by = child.id
    world.facts.update(child=child, parent=parent, item=item, bedtime=bedtime)

    world.say(
        f"{child.id} was a {next(t for t in ['sleepy', 'curious', 'gentle', 'stubborn'] if True)} little {child.type} in {world.setting}."
    )
    world.say(
        f"{child.id} loved {item.phrase}, especially when the room was hushed and the night was soft."
    )
    world.say(
        f"Before sleep, there had already been thirteen small bedtime things: thirteen kisses, thirteen tuck-ins, thirteen whispers. "
        f"This was the fourteenth."
    )

    world.para()
    world.say(f"At bedtime, {child.id} reached for {item.label} and wanted to {item.prompt}.")
    child_pushes_back(world, child, item)
    parent_warning(world, parent, child, item)
    state_shift(world, child, item)

    world.para()
    if item.id == "book":
        bedtime_dialogue(world, child, "Just one more page?")
    elif item.id == "bear":
        bedtime_dialogue(world, child, "Can Bear visit the pillow one last time?")
    elif item.id == "blanket":
        bedtime_dialogue(world, child, "Can I keep the blanket up for one more minute?")
    else:
        bedtime_dialogue(world, child, "Can the lamp stay on just a tiny bit longer?")

    compromise(world, parent, child, item)
    resolution(world, child, parent, item)

    world.facts["resolved"] = True
    return world


def story_for(params: StoryParams) -> str:
    return tell(params).render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    return [
        f'Write a short bedtime story for a young child named {child.id} about the fourteenth {item.label}.',
        f"Tell a gentle cautionary dialogue story where {child.id} wants one more {item.label} before sleep.",
        f'Write a bedtime story with dialogue, a warning, and a cozy ending about "{item.label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    qa = [
        QAItem(
            question=f"What did {child.id} want to do with the {item.label} before sleeping?",
            answer=f"{child.id} wanted to {item.prompt}, because {child.pronoun('subject')} was not quite ready to let bedtime end.",
        ),
        QAItem(
            question=f"Why did the {parent.id} warn {child.id}?",
            answer=f"The {parent.id} warned {child.id} because {item.caution}. The warning was gentle, but it was still serious enough to slow the moment down.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"In the end, {child.id} became calmer and cozier, and the fourteenth little bedtime thing turned into the last safe one before sleep.",
        ),
    ]
    if item.id == "book":
        qa.append(QAItem(
            question=f"Why was the picture book important in the story?",
            answer=f"The picture book helped {child.id} linger over one last page, but it also made the child sleepier, which fit the bedtime ending.",
        ))
    elif item.id == "bear":
        qa.append(QAItem(
            question=f"Why did the stuffed bear matter to {child.id}?",
            answer=f"The stuffed bear was the soft friend {child.id} wanted nearby, so the parent let the bear stay tucked in as part of the calm bedtime routine.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    item = f["item"]
    out = [
        QAItem(
            question="What does bedtime mean?",
            answer="Bedtime is the part of the day when a child gets ready to sleep, usually with quiet voices, pajamas, and a comforting routine.",
        ),
        QAItem(
            question="Why do children need a bedtime routine?",
            answer="A bedtime routine helps a child feel safe and settled, so the body and mind can slow down and rest.",
        ),
    ]
    if item.id == "lamp":
        out.append(QAItem(
            question="What does a lamp do at night?",
            answer="A lamp gives off light in a room, which can make the dark feel less scary and help people see softly.",
        ))
    elif item.id == "blanket":
        out.append(QAItem(
            question="What is a blanket for?",
            answer="A blanket keeps a person warm and snug, especially when the room gets cool at night.",
        ))
    elif item.id == "book":
        out.append(QAItem(
            question="Why is a picture book good for bedtime?",
            answer="A picture book is good for bedtime because looking at the pictures and hearing the words can feel calm and sleepy.",
        ))
    elif item.id == "bear":
        out.append(QAItem(
            question="Why do children like stuffed animals?",
            answer="Children often like stuffed animals because they feel soft, familiar, and comforting to hug at bedtime.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary dialogue bedtime story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=BEDTIME_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.gender and args.name is None:
        pass
    item = args.item or rng.choice(list(BEDTIME_ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(["mother", "father"])
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(child_name=name, child_gender=gender, parent_type=parent, item=item, setting=place)


def generate(params: StoryParams) -> StorySample:
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


ASP_RULES = r"""
child(C) :- kid(C).
risk(Item) :- caution_item(Item).
resolved(C,Item) :- child(C), risk(Item).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for gender, names in NAMES.items():
        for name in names:
            lines.append(asp.fact("kid", name))
            lines.append(asp.fact("gender", name, gender))
    for item in BEDTIME_ITEMS.values():
        lines.append(asp.fact("caution_item", item.id))
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Minimal parity gate: facts and rule expansion should at least parse and solve.
    import asp
    model = asp.one_model(asp_program("#show resolved/2."))
    _ = model
    print("OK: ASP program solved.")
    return 0


CURATED = [
    StoryParams(child_name="Mina", child_gender="girl", parent_type="mother", item="book", setting="bedroom"),
    StoryParams(child_name="Theo", child_gender="boy", parent_type="father", item="lamp", setting="nursery"),
    StoryParams(child_name="Ivy", child_gender="girl", parent_type="mother", item="bear", setting="bedroom"),
    StoryParams(child_name="Noah", child_gender="boy", parent_type="father", item="blanket", setting="attic-room"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
