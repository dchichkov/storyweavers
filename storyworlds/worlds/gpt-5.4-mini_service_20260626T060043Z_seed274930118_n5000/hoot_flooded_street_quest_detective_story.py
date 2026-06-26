#!/usr/bin/env python3
"""
storyworlds/worlds/hoot_flooded_street_quest_detective_story.py
===============================================================

A small classical storyworld in a detective-story style.

Premise:
- A child detective and a helpful owl are in a flooded street after a storm.
- A neighbor has lost something important.
- The flood hides clues, but the detective follows a tiny quest:
  notice, search, listen, and recover.

The world is intentionally small and constraint-checked. Every generated story
comes from a simulated state that changes through physical meters and emotional
memes.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "muddy": 0.0, "found": 0.0, "search": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "hope": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str = "the flooded street"
    water_depth: str = "ankle-deep"
    quest_friendly: bool = True


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    where_hint: str
    value_word: str
    searchable: bool = True


@dataclass
class Helper:
    id: str
    label: str = "an owl"
    sound: str = "hoot"
    role: str = "guide"


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone.facts = dict(self.facts)
        return clone


def valid_quests() -> list[str]:
    return list(QUESTS.keys())


def is_reasonable(quest: QuestItem) -> bool:
    return quest.searchable and bool(quest.where_hint)


def explain_rejection(quest: QuestItem) -> str:
    return f"(No story: the chosen quest item '{quest.label}' is not reasonable for a flooded-street detective search.)"


def find_gear_for_quest(quest: QuestItem) -> str:
    if quest.id in {"key", "map"}:
        return "a long stick"
    if quest.id == "balloon":
        return "a net"
    return "careful eyes"


def predict_resolution(world: World, detective: Entity, quest: QuestItem) -> dict:
    sim = world.copy()
    engage_search(sim, sim.get(detective.id), quest, narrate=False)
    item = sim.entities[quest.id]
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "hope": sim.get(detective.id).memes["hope"],
    }


def engage_search(world: World, detective: Entity, quest: QuestItem, narrate: bool = True) -> None:
    detective.meters["search"] += 1
    detective.memes["curiosity"] += 1
    if quest.where_hint == "drain":
        world.trace.append("search_drain")
        if narrate:
            world.say("The detective peered at the drain, where the floodwater swirled in a silver spiral.")
    elif quest.where_hint == "bench":
        world.trace.append("search_bench")
        if narrate:
            world.say("The detective looked under the wet bench, where the water had left a dark line.")
    else:
        world.trace.append("search_street")
        if narrate:
            world.say("The detective scanned the flooded street, watching for any tiny sign that did not belong.")

    item = world.get(quest.id)
    item.meters["found"] += 1
    detective.memes["hope"] += 1


def owl_hint(world: World, helper: Helper, detective: Entity, quest: QuestItem) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"Above the puddled road, the owl gave a quiet {helper.sound}. "
        f"It was not just a sound; it was a clue."
    )
    if quest.where_hint == "drain":
        world.say("The detective followed the hoot to the drain beside the curb.")
    elif quest.where_hint == "bench":
        world.say("The detective followed the hoot to the wet bench by the shop window.")
    else:
        world.say("The detective followed the hoot to a shiny trail near the curb.")


def speak_of_quest(world: World, detective: Entity, neighbor: Entity, quest: QuestItem) -> None:
    neighbor.memes["worry"] += 1
    world.say(
        f"\"I lost my {quest.label},\" said {neighbor.id}. "
        f"\"I need it for tonight, and the flooded street swallowed my last clue.\""
    )
    world.say(
        f"The young detective stood straighter. This was a quest now, and {detective.pronoun('subject')} loved a good one."
    )


def search_and_find(world: World, detective: Entity, helper: Helper, quest: QuestItem) -> None:
    owl_hint(world, helper, detective, quest)
    engage_search(world, detective, quest)
    item = world.get(quest.id)
    if quest.where_hint == "drain":
        world.say(
            f"At the drain, {detective.id} spotted {quest.phrase} caught on a little twig, just above the water."
        )
    elif quest.where_hint == "bench":
        world.say(
            f"Under the wet bench, {detective.id} spotted {quest.phrase}, safe from the deeper water."
        )
    else:
        world.say(
            f"Beside the curb, {detective.id} spotted {quest.phrase} glinting through the floodwater."
        )
    item.meters["found"] += 1


def resolve(world: World, detective: Entity, neighbor: Entity, quest: QuestItem) -> None:
    item = world.get(quest.id)
    detective.memes["hope"] += 1
    detective.memes["relief"] += 1
    neighbor.memes["worry"] = 0.0
    world.say(
        f"{detective.id} lifted the {quest.label} free and held it up high. "
        f"The water dripped from the edges like tiny glass beads."
    )
    world.say(
        f"\"You found it!\" said {neighbor.id}. \"That was a brave little quest.\""
    )
    world.say(
        f"{detective.id} smiled as the owl gave one last {world.facts['owl_sound']}. "
        f"The flooded street still shimmered, but now the lost thing was back where it belonged."
    )
    item.meters["found"] = max(item.meters["found"], THRESHOLD)


QUESTS: dict[str, QuestItem] = {
    "key": QuestItem(
        id="key",
        label="brass key",
        phrase="a brass key with a round head",
        where_hint="drain",
        value_word="important",
    ),
    "map": QuestItem(
        id="map",
        label="folded map",
        phrase="a folded map in a blue sleeve",
        where_hint="bench",
        value_word="special",
    ),
    "balloon": QuestItem(
        id="balloon",
        label="red balloon",
        phrase="a red balloon snagged on a twig",
        where_hint="curb",
        value_word="precious",
    ),
}

DETECTIVES = {
    "Mina": "girl",
    "Theo": "boy",
    "June": "girl",
    "Ari": "boy",
}

NEIGHBORS = {
    "Mrs. Pine": "mother",
    "Mr. Vale": "father",
    "Nia": "girl",
    "Owen": "boy",
}


@dataclass
class StoryParams:
    quest: str
    detective_name: str
    detective_type: str
    neighbor_name: str
    neighbor_type: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    place = Place()
    world = World(place)
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="detective",
    ))
    helper = Helper(id="owl", label="owl", sound="hoot")
    neighbor = world.add(Entity(
        id=params.neighbor_name,
        kind="character",
        type=params.neighbor_type,
        label="neighbor",
    ))
    quest = world.add(Entity(
        id=params.quest,
        kind="thing",
        type="quest-item",
        label=QUESTS[params.quest].label,
        phrase=QUESTS[params.quest].phrase,
        owner=neighbor.id,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        neighbor=neighbor,
        quest=QUESTS[params.quest],
        owl_sound=helper.sound,
    )

    world.say(
        f"The flooded street shone after the storm, and {detective.id} was already looking for clues."
    )
    world.say(
        f"Near a window with dripping shutters, an owl called {helper.sound}. That sound felt like a map made of air."
    )
    world.para()
    speak_of_quest(world, detective, neighbor, QUESTS[params.quest])
    world.para()
    search_and_find(world, detective, helper, QUESTS[params.quest])
    world.para()
    resolve(world, detective, neighbor, QUESTS[params.quest])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest: QuestItem = f["quest"]
    detective: Entity = f["detective"]
    neighbor: Entity = f["neighbor"]
    return [
        f'Write a short detective story for young children set in a flooded street, with the word "hoot" and a small quest to find {quest.phrase}.',
        f"Tell a gentle mystery about {detective.id} helping {neighbor.id} search a flooded street until the owl says hoot and the lost thing is found.",
        f'Write a child-friendly detective tale where a flooded street hides a clue, but an owl, a quest, and careful searching solve the problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    neighbor: Entity = f["neighbor"]
    quest: QuestItem = f["quest"]
    owl_sound = f["owl_sound"]
    return [
        QAItem(
            question=f"What kind of story is this?",
            answer=f"It is a detective story set in a flooded street, with a small quest to find {quest.label}.",
        ),
        QAItem(
            question=f"Who was looking for clues in the flooded street?",
            answer=f"{detective.id} was the young detective looking for clues while helping {neighbor.id}.",
        ),
        QAItem(
            question=f"What sound did the owl make?",
            answer=f"The owl made a quiet {owl_sound}. That sound helped guide the detective to the clue.",
        ),
        QAItem(
            question=f"What was the quest to find?",
            answer=f"The quest was to find {quest.phrase}. It had been lost in the flooded street.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {detective.id} finding the {quest.label} and giving it back so {neighbor.id} could relax.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an owl's hoot?",
            answer="A hoot is the low sound an owl makes, and people often notice it at night or in quiet places.",
        ),
        QAItem(
            question="What makes a street flooded?",
            answer="A street is flooded when there is so much water on it that puddles spread over the road.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to solve a problem by noticing small details.",
        ),
    ]


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    lines.append(f"  fired={sorted(world.fired)}")
    lines.extend(f"  {t}" for t in world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
quest_possible(Q) :- quest(Q).
good_story(Q) :- quest_possible(Q), searchable(Q), hint(Q).

#show good_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        if q.searchable:
            lines.append(asp.fact("searchable", qid))
        lines.append(asp.fact("hint", qid, q.where_hint))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/1."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import asp
    py = {(qid,) for qid, q in QUESTS.items() if is_reasonable(q)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python reasonableness gate ({len(py)} quests).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective storyworld set in a flooded street.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--neighbor")
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
    if args.quest and not is_reasonable(QUESTS[args.quest]):
        raise StoryError(explain_rejection(QUESTS[args.quest]))
    quest = args.quest or rng.choice(list(QUESTS))
    if not is_reasonable(QUESTS[quest]):
        raise StoryError(explain_rejection(QUESTS[quest]))
    detective_name = args.name or rng.choice(list(DETECTIVES))
    detective_type = DETECTIVES.get(detective_name, "girl")
    neighbor_name = args.neighbor or rng.choice(list(NEIGHBORS))
    neighbor_type = NEIGHBORS.get(neighbor_name, "mother")
    if detective_name == neighbor_name:
        raise StoryError("The detective and the neighbor must be different characters.")
    return StoryParams(
        quest=quest,
        detective_name=detective_name,
        detective_type=detective_type,
        neighbor_name=neighbor_name,
        neighbor_type=neighbor_type,
    )


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


CURATED = [
    StoryParams(quest="key", detective_name="Mina", detective_type="girl", neighbor_name="Mrs. Pine", neighbor_type="mother"),
    StoryParams(quest="map", detective_name="Theo", detective_type="boy", neighbor_name="Mr. Vale", neighbor_type="father"),
    StoryParams(quest="balloon", detective_name="June", detective_type="girl", neighbor_name="Nia", neighbor_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
