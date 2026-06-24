#!/usr/bin/env python3
"""
A bedtime-story world about a little quest, a cautionary barricade, and a
careful choice on Thursday.

Seed words: barricade, thursday, footed
Style: bedtime story
Features: cautionary, quest
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
    location: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "safe": 0.0, "blocked": 0.0, "scuffed": 0.0}
        if not self.memes:
            self.memes = {"curious": 0.0, "worry": 0.0, "hope": 0.0, "relief": 0.0, "bravery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the sleepy lane"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    search: str
    risk: str
    clue: str
    ending: str
    keyword: str = "quest"


@dataclass
class Guard:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def story_time(word: str) -> str:
    return {
        "barricade": "a little barricade of chair legs and ribbon",
        "thursday": "Thursday, when the moon looked like a small silver лод? no",
        "footed": "a footed path with tiny stone steps",
    }.get(word, word)


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was quiet and pale in the evening, like a room waiting for a lullaby."


def quest_delight(quest: Quest) -> str:
    return {
        "stars": "the stars felt close enough to count",
        "bell": "the tiny bell sounded like a promise",
        "key": "the key glimmered like a bit of dawn",
        "crown": "the paper crown shone like a joke from the moon",
    }.get(quest.id, "it felt like a small adventure")


def _r_blocked(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.children():
        if actor.meters["blocked"] < THRESHOLD:
            continue
        sig = ("blocked", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"The path held firm, and {actor.id}'s steps grew careful.")
    return out


def _r_scuffed(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.children():
        if actor.meters["scuffed"] < THRESHOLD:
            continue
        sig = ("scuffed", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] += 1
        out.append(f"That made {actor.id} feel a little worried.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_blocked, _r_scuffed):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, quest: Quest) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    return {
        "blocked": sim.get(actor.id).meters["blocked"] >= THRESHOLD,
        "scuffed": sim.get(actor.id).meters["scuffed"] >= THRESHOLD,
    }


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    actor.memes["curious"] += 1
    actor.meters["blocked"] += 1
    propagate(world, narrate=narrate)
    if quest.id == "stars":
        actor.meters["scuffed"] += 1
        propagate(world, narrate=narrate)


SETTING = Setting(place="the sleepy lane", affords={"stars", "bell", "key", "crown"})

QUESTS = {
    "stars": Quest(
        id="stars",
        title="the star quest",
        goal="count the stars beyond the barricade",
        search="look for a clear place to see the stars",
        risk="stubbed toes and a tumble in the dark",
        clue="the safest way is the bright path, not the blocked one",
        ending="counted the stars from the porch",
        keyword="quest",
    ),
    "bell": Quest(
        id="bell",
        title="the little bell quest",
        goal="find the hidden silver bell",
        search="follow the soft sound",
        risk="waking the sleepy cats and losing the way",
        clue="the bell is near, but the barricade says stop",
        ending="heard the bell from the garden gate",
        keyword="quest",
    ),
    "key": Quest(
        id="key",
        title="the garden key quest",
        goal="find the tiny brass key",
        search="peek beside the lantern",
        risk="scratched knees and a shut-out door",
        clue="keys belong where hands can reach safely",
        ending="found the key in the bowl by the door",
        keyword="quest",
    ),
    "crown": Quest(
        id="crown",
        title="the paper crown quest",
        goal="bring home the paper crown",
        search="ask the moonlit shelves",
        risk="a torn crown and a sad heart",
        clue="pretty things last longer when they are not rushed",
        ending="placed the crown on the pillow",
        keyword="cautionary",
    ),
}

GUARDS = {
    "lantern": Guard(
        id="lantern",
        label="a little lantern",
        covers={"dark"},
        guards={"blocked", "scuffed"},
        prep="carry a little lantern instead of climbing the barricade",
        tail="walked back with the lantern",
    ),
    "boots": Guard(
        id="boots",
        label="soft boots",
        covers={"feet"},
        guards={"scuffed"},
        prep="put on soft boots before they went out",
        tail="came home with clean feet",
        plural=True,
    ),
}


@dataclass
class StoryParams:
    quest: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Nora", "Lina", "June", "Poppy", "Iris"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Rowan", "Owen"]
TRAITS = ["gentle", "curious", "brave", "sleepy", "stubborn"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime cautionary quest storyworld.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    quest = args.quest or rng.choice(sorted(QUESTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(quest=quest, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    quest = QUESTS[params.quest]
    world.facts.update(hero=hero, parent=parent, quest=quest, params=params)

    world.say(f"On Thursday night, {hero.id} was a {params.trait} little {hero.type} who loved a quiet quest.")
    world.say(f"{hero.id} wanted {quest.goal}, and the idea felt as soft as a bedtime blanket.")

    world.para()
    world.say(setting_detail(world.setting))
    world.say(f"But a small barricade waited near the lane, and it looked like it meant no.")
    world.say(f"{hero.id} wanted to slip past it anyway, because {quest.search} sounded exciting.")

    hero.meters["blocked"] += 1
    hero.memes["curious"] += 1
    world.say(f"{parent.pronoun().capitalize()} gave a cautionary smile and said, 'Some doors stay closed for a reason.'")
    world.say(f"{hero.id} paused and listened, then admitted the barricade might mean danger in the dark.")
    hero.memes["worry"] += 1

    world.para()
    if quest.id == "stars":
        world.say(f"So they chose a safer quest: they sat on the porch and counted stars instead.")
        world.say(f"The sky answered with a patient twinkle, and {hero.id} felt brave for choosing the kinder way.")
        hero.memes["hope"] += 1
        hero.memes["relief"] += 1
    elif quest.id == "bell":
        world.say(f"They followed the soft sound around the barricade and found the bell near the garden gate.")
        hero.memes["hope"] += 1
        hero.memes["relief"] += 1
    elif quest.id == "key":
        world.say(f"They did not climb the barricade. Instead, they found the key in the bowl by the door.")
        hero.memes["hope"] += 1
        hero.memes["relief"] += 1
    else:
        world.say(f"They left the barricade alone and placed the paper crown gently on the pillow.")
        hero.memes["hope"] += 1
        hero.memes["relief"] += 1

    world.say(f"In the end, {hero.id} learned that a small caution can protect a big heart.")
    world.say(f"{hero.id} went to bed feeling safe, and the night felt footed and quiet under the moon.")
    hero.meters["safe"] += 1
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    q: Quest = f["quest"]
    return [
        f'Write a bedtime story about a child on Thursday who meets a barricade and chooses a safer quest.',
        f"Tell a gentle cautionary tale where {p.name} is a {p.trait} {p.gender} and learns what to do when a path is blocked.",
        f'Write a simple story that includes the words "barricade", "Thursday", and "footed" and ends peacefully.',
        f"Create a bedtime quest where a child wants {q.goal} but listens carefully and picks the safe way instead.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    q: Quest = f["quest"]
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"What was {p.name} trying to do on Thursday night?",
            answer=f"{p.name} wanted to {q.goal}. It was a small quest, but the barricade made the first path unsafe.",
        ),
        QAItem(
            question=f"Why did {parent.type} warn {p.name} about the barricade?",
            answer=f"{parent.pronoun('subject').capitalize()} warned {p.name} because the blocked path could lead to {q.risk}. That was a cautionary moment in the story.",
        ),
        QAItem(
            question=f"How did {p.name} end up finishing the quest safely?",
            answer=f"Instead of climbing the barricade, {p.name} chose the safer way and {q.ending}. That let {hero.id} go to bed calm and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barricade?",
            answer="A barricade is something placed across a path to stop people from going through.",
        ),
        QAItem(
            question="What does Thursday mean?",
            answer="Thursday is one of the days of the week, between Wednesday and Friday.",
        ),
        QAItem(
            question="What does footed mean?",
            answer="Footed can mean something has feet or stands on feet, like a footed stool or a footed pajamas outfit.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    return "\n".join(lines)


ASP_RULES = r"""
blocked(H) :- hero(H), path_blocked.
safe(H) :- hero(H), chooses_safe_way(H).
resolved(H) :- safe(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("hero", "hero")]
    lines.append(asp.fact("path_blocked"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/1."))
    atoms = set(asp.atoms(model, "resolved"))
    ok = atoms == {("hero",)}
    if ok:
        print("OK: ASP gate matches the simple cautionary resolution.")
        return 0
    print("MISMATCH: ASP gate did not resolve as expected.")
    return 1


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolved/1."))
        print(asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for q in sorted(QUESTS):
            p = StoryParams(
                quest=q,
                name="Mia" if q != "stars" else "Noah",
                gender="girl" if q != "stars" else "boy",
                parent="mother",
                trait="curious",
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
