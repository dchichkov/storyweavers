#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/snipper_significance_quest_bravery_rhyming_story.py
====================================================================================

A standalone storyworld for a tiny rhyming quest: a child brings a snipper on a
small adventure, learns the meaning of significance, and shows bravery by using
the right tool in the right way.

The world is built around a very small simulated domain:
- a quest map with a tucked-away ribbon, tag, or string to trim
- a snipper tool that can only safely cut small soft things
- a guide who explains why a thing matters
- a bravery turn where the child keeps going, then chooses the wise path

The prose is state-driven rather than template-swapped; meter state and emotion
state move the story forward, and the ending image proves what changed.
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
BRAVERY_START = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scene: str
    dark_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    uses: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snipper:
    id: str
    label: str
    phrase: str
    safe_targets: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_significance(world: World) -> list[str]:
    out: list[str] = []
    quest = world.entities.get("quest")
    token = world.entities.get("token")
    if not quest or not token:
        return out
    if quest.meters["uncertain"] >= THRESHOLD and token.meters["important"] >= THRESHOLD:
        sig = ("significance",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        quest.memes["meaning"] += 1
        out.append("__significance__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CAUSAL_RULES = [Rule("significance", _r_significance)]


def safe_to_snip(snipper: Snipper, item: QuestItem) -> bool:
    return item.id in snipper.safe_targets


def quest_risk(item: QuestItem, place: Place) -> bool:
    return item.id in place.tags


def story_begin(world: World, child: Entity, guide: Entity, place: Place, item: QuestItem, snipper: Snipper) -> None:
    child.memes["curiosity"] += 1
    child.memes["bravery"] += BRAVERY_START
    world.say(
        f"At {place.label}, under a sky soft and gray, {child.id} began a quest that "
        f"felt light as play."
    )
    world.say(
        f"{place.scene} Nearby, {item.phrase} waited in sight, and {snipper.phrase} "
        f"rested small and bright."
    )
    world.say(
        f'"Come on," said {guide.id}, "this little job has significance. '
        f"It means your quest can end with a better difference."'
    )


def wonder(world: World, child: Entity, item: QuestItem) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} looked at {item.label} and stood quite still, "
        f"feeling a tug of purpose and will."
    )


def tempt(world: World, child: Entity, snipper: Snipper, item: QuestItem) -> None:
    child.memes["want"] += 1
    world.say(
        f'{child.id} lifted the {snipper.label} with a careful grin, '
        f'and thought of the thing {snipper.label} could trim within.'
    )
    world.say(
        f'"Maybe this matters more than I knew," {child.id} said low, '
        f"as bravery warmed like a steady glow."
    )


def warn(world: World, guide: Entity, child: Entity, snipper: Snipper, item: QuestItem) -> None:
    world.say(
        f'"A brave heart helps," said {guide.id}, "but bravery must steer. '
        f'Use the {snipper.label} only where it is clear."'
    )
    if not safe_to_snip(snipper, item):
        world.say(
            f'"This {item.label} is not for the blades," {guide.id} said sweet. '
            f'"It is meant to be kept, not cut, and left complete."'
        )


def choose(world: World, child: Entity, guide: Entity, snipper: Snipper, item: QuestItem) -> bool:
    if not safe_to_snip(snipper, item):
        child.memes["bravery"] += 1
        child.memes["self_control"] += 1
        world.say(
            f'{child.id} took a breath and tucked the {snipper.label} away, '
            f"choosing the wiser part of the day."
        )
        return False
    child.memes["bravery"] += 1
    item.meters["trimmed"] += 1
    world.say(
        f"{child.id} clipped the loose ribbon with a tiny snip, "
        f"and the quest went forward without a slip."
    )
    propagate(world, narrate=False)
    return True


def ending(world: World, child: Entity, guide: Entity, item: QuestItem, snipper: Snipper, used: bool) -> None:
    if used:
        world.say(
            f"The ribbon lay neat, the path was clear, and significance felt "
            f"bright and near."
        )
        world.say(
            f"{child.id} smiled at {guide.id}, brave and true, because doing the small right thing was the quest to do."
        )
    else:
        world.say(
            f"The special thing stayed safe and sound, and meaning was found in "
            f"the choice {child.id} made around."
        )
        world.say(
            f"{guide.id} nodded with pride, and {child.id} stood tall: bravery was not cutting, but knowing when not to act at all."
        )


def tell(place: Place, item: QuestItem, snipper: Snipper, guide: Guide,
         child_name: str = "Mila", child_gender: str = "girl") -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="quester"))
    mentor = world.add(Entity(id=guide.id, kind="character", type="adult", role="guide", label=guide.label))
    token = world.add(Entity(id="token", type="thing", label=item.label))
    quest = world.add(Entity(id="quest", type="thing", label="quest"))

    quest.meters["uncertain"] += 1
    token.meters["important"] += 1
    world.facts.update(place=place, item=item, snipper=snipper, guide=guide)

    story_begin(world, child, mentor, place, item, snipper)
    world.para()
    wonder(world, child, item)
    tempt(world, child, snipper, item)
    warn(world, mentor, child, snipper, item)
    used = choose(world, child, mentor, snipper, item)
    world.para()
    ending(world, child, mentor, item, snipper, used)

    world.facts.update(
        child=child,
        guide_ent=mentor,
        token=token,
        quest=quest,
        used_snipper=used,
        significance=quest.memes["meaning"] >= THRESHOLD,
    )
    return world


PLACES = {
    "mossy_path": Place(
        id="mossy_path",
        label="the mossy path",
        scene="The trail curled under pine boughs, and little stones glittered like beads.",
        dark_spot="a bend where the trail hid under leaves",
        tags={"ribbon", "quest"},
    ),
    "sunny_grove": Place(
        id="sunny_grove",
        label="the sunny grove",
        scene="The grove glowed gold, and the grass hummed softly in the warm air.",
        dark_spot="a stump-shadow beside the flowers",
        tags={"tag", "quest"},
    ),
}

ITEMS = {
    "ribbon": QuestItem(
        id="ribbon",
        label="ribbon",
        phrase="a bright ribbon tied to a little branch",
        uses={"decorate", "mark"},
    ),
    "tag": QuestItem(
        id="tag",
        label="tag",
        phrase="a paper tag hanging from a tiny box",
        uses={"label", "mark"},
    ),
    "string": QuestItem(
        id="string",
        label="string",
        phrase="a thin string wound around a wooden peg",
        uses={"tie", "mark"},
    ),
}

SNIPPERS = {
    "child_snipper": Snipper(
        id="child_snipper",
        label="snipper",
        phrase="a little snipper",
        safe_targets={"string", "ribbon"},
    ),
    "garden_snipper": Snipper(
        id="garden_snipper",
        label="snipper",
        phrase="a small garden snipper",
        safe_targets={"string", "ribbon", "tag"},
    ),
}

GUIDES = {
    "aunt": Guide(id="Aunt June", label="Aunt June", phrase="Aunt June"),
    "uncle": Guide(id="Uncle Ray", label="Uncle Ray", phrase="Uncle Ray"),
}

GIRL_NAMES = ["Mila", "Nora", "Lena", "Ivy", "Tia", "Pia"]
BOY_NAMES = ["Noel", "Ezra", "Theo", "Finn", "Milo", "Leo"]


@dataclass
class StoryParams:
    place: str
    item: str
    snipper: str
    guide: str
    name: str
    gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="mossy_path", item="ribbon", snipper="child_snipper", guide="aunt", name="Mila", gender="girl"),
    StoryParams(place="sunny_grove", item="tag", snipper="garden_snipper", guide="uncle", name="Noel", gender="boy"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            if not quest_risk(item, place):
                continue
            for sid, sn in SNIPPERS.items():
                if safe_to_snip(sn, item):
                    combos.append((pid, iid, sid))
    return combos


def explain_rejection(place: Place, item: QuestItem, snipper: Snipper) -> str:
    return (
        f"(No story: at {place.label}, the {item.label} is not a good match for the {snipper.label}. "
        f"This quest needs a real risk and a safe choice.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming quest about snipper, significance, and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--snipper", choices=SNIPPERS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              and (args.item is None or c[1] == args.item)
              and (args.snipper is None or c[2] == args.snipper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, snipper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(sorted(GUIDES))
    return StoryParams(place=place, item=item, snipper=snipper, guide=guide, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, item, guide = f["place"], f["item"], f["guide"]
    return [
        f'Write a rhyming story for a child about a quest, bravery, and the word "{f["snipper"].label}".',
        f"Tell a small adventure at {place.label} where {f['child'].id} learns what significance means.",
        f"Write a gentle quest story where {guide.id} helps a child use bravery wisely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, guide, item, used = f["child"], f["guide_ent"], f["item"], f["used_snipper"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {guide.id}, who went on a little quest together. The quest asked for bravery and a wise choice."),
        ("What was special about the thing they found?",
         f"It was {item.phrase}, and it mattered because the quest gave it significance. That means it was important enough to handle with care."),
        ("What did {0} do with the snipper?".format(child.id),
         f"{child.id} used the snipper only if it was safe, and the snip kept the quest moving. That choice showed bravery with self-control." if used else f"{child.id} did not cut it, because bravery also means stopping when a thing should stay whole. That was the wise ending."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a snipper?",
         "A snipper is a small cutting tool used on little soft things like string or ribbon. It should be used carefully."),
        ("What does significance mean?",
         "Significance means something matters. If a thing has significance, it is important and worth noticing."),
        ("What is bravery?",
         "Bravery means doing what is right even when you feel unsure or a little scared. A brave choice can also be a careful choice."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.item not in ITEMS or params.snipper not in SNIPPERS or params.guide not in GUIDES:
        raise StoryError("(Invalid parameters.)")
    place = PLACES[params.place]
    item = ITEMS[params.item]
    snipper = SNIPPERS[params.snipper]
    guide = GUIDES[params.guide]
    if not quest_risk(item, place) or not safe_to_snip(snipper, item):
        raise StoryError(explain_rejection(place, item, snipper))
    world = tell(place, item, snipper, guide, params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
quest_risk(P,I) :- place(P), item(I), risky(P,I).
safe_use(S,I) :- snipper(S), item(I), safe_target(S,I).
valid(P,I,S) :- quest_risk(P,I), safe_use(S,I).
meaning(quest) :- valid(P,I,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for sid in SNIPPERS:
        lines.append(asp.fact("snipper", sid))
    for pid, place in PLACES.items():
        for tag in place.tags:
            lines.append(asp.fact("risky", pid, tag))
    for sid, sn in SNIPPERS.items():
        for tgt in sn.safe_targets:
            lines.append(asp.fact("safe_target", sid, tgt))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between clingo and python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAIL: generate() smoke test failed: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
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
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
