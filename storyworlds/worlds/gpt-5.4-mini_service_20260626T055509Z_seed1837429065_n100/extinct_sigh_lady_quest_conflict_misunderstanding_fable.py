#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"lady", "woman", "mother", "mom", "girl", "sister", "aunt"}
        male = {"man", "father", "dad", "boy", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old hill town"
    afford_quest: bool = True


@dataclass
class Quest:
    id: str
    goal: str
    path: str
    obstacle: str
    clue: str
    reward: str
    keyword: str = "quest"


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    brittle: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _mget(e: Entity, k: str) -> float:
    return e.meters.get(k, 0.0)


def _mem(e: Entity, k: str) -> float:
    return e.memes.get(k, 0.0)


def _add_meter(e: Entity, k: str, v: float = 1.0) -> None:
    e.meters[k] = _mget(e, k) + v


def _add_mem(e: Entity, k: str, v: float = 1.0) -> None:
    e.memes[k] = _mem(e, k) + v


def _set_mem(e: Entity, k: str, v: float) -> None:
    e.memes[k] = v


def _narrate_begin(world: World, lady: Entity, quest: Quest, artifact: Entity) -> None:
    world.say(
        f"On a quiet morning in {world.setting.place}, a lady named {lady.id} walked under a gray sky. "
        f"She loved a hard little quest: to find the {quest.goal}, a prize people said had gone extinct."
    )
    world.say(
        f"She carried a worn map, a small loaf, and a brave wish. "
        f"In her basket lay {artifact.phrase}, for she believed every quest should begin with care."
    )


def _narrate_misunderstanding(world: World, lady: Entity, neighbor: Entity, quest: Quest, artifact: Entity) -> None:
    _add_mem(lady, "hope", 1)
    _add_mem(lady, "purpose", 1)
    _add_mem(neighbor, "worry", 1)
    world.say(
        f"At the bridge, a neighbor saw the basket and frowned. "
        f'"That thing is extinct," {neighbor.id} said with a sigh, "so why waste a day on a quest?"'
    )
    world.say(
        f"{lady.id} thought the neighbor meant the basket itself was unwanted, and her cheeks warmed with conflict. "
        f"She held {artifact.they()} tighter and answered too sharply."
    )
    _add_mem(lady, "conflict", 1)
    _add_mem(lady, "misunderstanding", 1)


def _narrate_search(world: World, lady: Entity, quest: Quest, artifact: Entity) -> None:
    _add_meter(lady, "steps", 3)
    _add_mem(lady, "resolve", 1)
    world.say(
        f"Still, the lady kept going. She followed the clue along the willow road and listened for a thin song in the reeds."
    )
    world.say(
        f"The clue led her past a hollow tree and to a small pond where the water made a silver ring. "
        f"There she found the {quest.goal}, hiding where no one had looked."
    )
    _add_meter(artifact, "found", 1)
    _add_mem(artifact, "safe", 1)


def _narrate_turn(world: World, lady: Entity, neighbor: Entity, quest: Quest, artifact: Entity) -> None:
    world.say(
        f"The neighbor came after her, still worried, but then he saw the truth. "
        f"The word extinct had not meant useless; it had meant rare and nearly lost."
    )
    world.say(
        f"{neighbor.id} gave a slow sigh and bowed his head. "
        f'"I misunderstood your quest," he said. "I thought you were chasing a foolish dream."'
    )
    _add_mem(neighbor, "regret", 1)
    _set_mem(lady, "conflict", 0)
    _set_mem(lady, "misunderstanding", 0)
    _add_mem(lady, "forgiveness", 1)


def _narrate_end(world: World, lady: Entity, neighbor: Entity, quest: Quest, artifact: Entity) -> None:
    world.say(
        f"The lady smiled, and the two of them carried the {quest.goal} back to town. "
        f"By dusk, the basket was full of bread, and the little creature was safe."
    )
    world.say(
        f"That night, the town remembered the lesson: a quick sigh can build a conflict, "
        f"but a patient question can mend a misunderstanding and finish a quest kindly."
    )
    world.facts.update(
        lady=lady,
        neighbor=neighbor,
        quest=quest,
        artifact=artifact,
        resolved=True,
    )


def tell(setting: Setting, quest: Quest, artifact: Artifact, lady_name: str = "Mira", neighbor_name: str = "Hale") -> World:
    world = World(setting)
    lady = world.add(Entity(id=lady_name, kind="character", type="lady"))
    neighbor = world.add(Entity(id=neighbor_name, kind="character", type="man"))
    basket = world.add(Entity(id=artifact.id, type="basket", label=artifact.label, phrase=artifact.phrase, owner=lady.id, caretaker=lady.id))

    _narrate_begin(world, lady, quest, basket)
    world.para()
    _narrate_misunderstanding(world, lady, neighbor, quest, basket)
    world.para()
    _narrate_search(world, lady, quest, basket)
    _narrate_turn(world, lady, neighbor, quest, basket)
    world.para()
    _narrate_end(world, lady, neighbor, quest, basket)
    return world


SETTINGS = {
    "hill_town": Setting(place="the old hill town", afford_quest=True),
}

QUESTS = {
    "songbird": Quest(
        id="songbird",
        goal="songbird",
        path="willow road",
        obstacle="the reeds",
        clue="listen for a thin song in the reeds",
        reward="a living song in the trees",
        keyword="quest",
    ),
}

ARTIFACTS = {
    "loaf": Artifact(
        id="loaf",
        label="bread basket",
        phrase="a small loaf wrapped in cloth",
        region="hands",
        brittle=False,
    ),
}

CURATED = [
    ("hill_town", "songbird", "loaf"),
]


@dataclass
class StoryParams:
    setting: str
    quest: str
    artifact: str
    lady_name: str
    neighbor_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world of a lady, a quest, a conflict, and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--lady-name")
    ap.add_argument("--neighbor-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    lady_name = args.lady_name or rng.choice(["Mira", "Lina", "Nora", "Ada"])
    neighbor_name = args.neighbor_name or rng.choice(["Hale", "Bram", "Joss", "Otto"])
    return StoryParams(setting=setting, quest=quest, artifact=artifact, lady_name=lady_name, neighbor_name=neighbor_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable about a lady on a quest, a conflict, and a misunderstanding, and include the word "extinct".',
        f"Tell a gentle story where {f['lady'].id} tries to find the {f['quest'].goal} and a neighbor first gets it wrong.",
        'Write a child-friendly fable that uses a sigh to show a conflict can become understanding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lady = f["lady"]
    neighbor = f["neighbor"]
    quest = f["quest"]
    return [
        QAItem(
            question=f"Who went on the quest in {world.setting.place}?",
            answer=f"The lady named {lady.id} went on the quest, and she kept going even after the conflict began.",
        ),
        QAItem(
            question=f"Why did {neighbor.id} sigh when he heard about the quest?",
            answer=f"He sighed because he misunderstood the quest and thought the rare {quest.goal} was a foolish chase, not something worth saving.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer="The misunderstanding ended, the conflict softened, and the lady and her neighbor carried the rare creature home safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a long search for something important, usually with a goal to find, save, or learn.",
        ),
        QAItem(
            question="What does a sigh often show?",
            answer="A sigh often shows worry, tiredness, or sadness, like someone letting out a long breath because they feel upset.",
        ),
        QAItem(
            question="What does extinct mean?",
            answer="Extinct means something no longer exists in the world, like a kind of animal or plant that has disappeared completely.",
        ),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(quest).
setting(hill_town).
artifact(loaf).
lady(mira).
neighbor(hale).

has_conflict(L) :- lady(L), misunderstanding(L).
misunderstanding(L) :- lady(L), sigh(N), neighbor(N).
resolved(L) :- lady(L), quest_done(L), not has_conflict(L).

#show quest/1.
#show setting/1.
#show artifact/1.
#show lady/1.
#show neighbor/1.
#show has_conflict/1.
#show misunderstanding/1.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "hill_town"),
        asp.fact("quest", "quest"),
        asp.fact("artifact", "loaf"),
        asp.fact("lady", "mira"),
        asp.fact("neighbor", "hale"),
        asp.fact("extinct", "songbird"),
        asp.fact("sigh", "hale"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest/1. #show setting/1. #show artifact/1. #show lady/1. #show neighbor/1."))
    names = set(asp.atoms(model, "quest")) | set(asp.atoms(model, "setting")) | set(asp.atoms(model, "artifact")) | set(asp.atoms(model, "lady")) | set(asp.atoms(model, "neighbor"))
    expected = {("quest",), ("hill_town",), ("loaf",), ("mira",), ("hale",)}
    if names == expected:
        print("OK: ASP facts are readable and stable.")
        return 0
    print("MISMATCH in ASP verification.")
    print("got:", sorted(names))
    print("expected:", sorted(expected))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1. #show quest/1."))
    return sorted(set(asp.atoms(model, "setting")) | set(asp.atoms(model, "quest")))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], ARTIFACTS[params.artifact], params.lady_name, params.neighbor_name)
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


def explain_rejection() -> str:
    return "(No story: only one careful fable configuration exists for this world.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest/1. #show setting/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show setting/1. #show quest/1. #show artifact/1. #show lady/1. #show neighbor/1."))
        print("ASP atoms:")
        for name in ("setting", "quest", "artifact", "lady", "neighbor"):
            print(name, asp.atoms(model, name))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting, quest, artifact in CURATED:
            params = StoryParams(setting=setting, quest=quest, artifact=artifact, lady_name="Mira", neighbor_name="Hale")
            params.seed = base_seed
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 10):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lady_name}: {p.quest} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
