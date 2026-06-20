#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chubby_combine_spit_rhyme_detective_story.py
=============================================================================

A small standalone storyworld for a kid-friendly detective tale built from the
seed words "chubby", "combine", and "spit", with rhyme as a narrative instrument.

The world is a tiny investigation domain:
- a little detective looks for a lost item,
- clues accumulate in the world model,
- a spitting fountain/pipe makes a muddy clue,
- the detective combines clues in the right order,
- the final reveal gives a clear ending image.

The prose is state-driven: clues and suspicion are tracked in meters/memes, and
the ending changes based on whether enough clues were gathered.

Run it:
------
    python storyworlds/worlds/gpt-5.4-mini/chubby_combine_spit_rhyme_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/chubby_combine_spit_rhyme_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/chubby_combine_spit_rhyme_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def meter(self, name: str) -> float:
        return self.meters.get(name, 0.0)

    def meme(self, name: str) -> float:
        return self.memes.get(name, 0.0)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Scene:
    id: str
    place: str
    rhyme: str
    clue_kind: str
    clue_line: str
    spitter: str
    combine_goal: str
    reward_image: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Clue:
    id: str
    label: str
    kind: str
    source: str
    detail: str
    physical: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Suspect:
    id: str
    label: str
    clue_fit: str
    appearance: str
    alibi: str
    chubby: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _ensure_meters(ent: Entity) -> None:
    if not isinstance(ent.meters, dict):
        ent.meters = {}
    if not isinstance(ent.memes, dict):
        ent.memes = {}


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        detective = world.get("detective")
        if detective.meter("clues") >= 2 and ("combine",) not in world.fired:
            world.fired.add(("combine",))
            detective.memes["certainty"] = detective.meme("certainty") + 1
            world.say("The detective tapped a chin and grinned. The clues could combine.")
            changed = True
        if detective.meter("clues") >= 3 and ("solve",) not in world.fired:
            world.fired.add(("solve",))
            detective.memes["solve"] = 1
            changed = True


def gather_clue(world: World, detective: Entity, clue: Clue) -> None:
    detective.meters["clues"] = detective.meter("clues") + 1
    detective.memes["curious"] = detective.meme("curious") + 1
    world.say(f"{detective.id} found {clue.label} near the {clue.source}.")
    world.say(clue.detail)
    propagate(world)


def inspect_spit(world: World, detective: Entity, scene: Scene) -> None:
    detective.meters["mud"] = detective.meter("mud") + 1
    world.say(
        f"At the {scene.place}, a little pipe could spit a thin spray, and the wet spot "
        f"made a neat clue."
    )
    world.say(scene.clue_line)


def accuse(world: World, detective: Entity, suspect: Suspect, clue: Clue) -> None:
    detective.memes["suspicion"] = detective.meme("suspicion") + 1
    chubby_word = "chubby" if suspect.chubby else "round"
    world.say(
        f"{detective.id} studied the {chubby_word} {suspect.label} and the muddy mark."
    )
    world.say(
        f"But the {suspect.label} had an alibi: {suspect.alibi}. That meant the clue did not fit."
    )


def combine_clues(world: World, detective: Entity, scene: Scene, clues: list[Clue], suspect: Suspect) -> None:
    labels = " and ".join(c.label for c in clues[:2])
    world.say(
        f"Then {detective.id} did something clever: {detective.pronoun().capitalize()} "
        f"could combine {labels} with the wet mark."
    )
    world.say(
        f"The pieces matched {suspect.label}'s {suspect.clue_fit}, and the mystery became clear."
    )
    detective.memes["joy"] = detective.meme("joy") + 1
    detective.memes["solved"] = 1


def reveal(world: World, detective: Entity, scene: Scene, suspect: Suspect) -> None:
    world.say(
        f"In the end, {suspect.label} was not the thief after all. {scene.reward_image}."
    )
    world.say(
        f"The little detective stood in the {scene.place}, proud, calm, and sure."
    )


def tale_setup(world: World, detective: Entity, scene: Scene, suspect: Suspect) -> None:
    world.say(
        f"On a bright day, {detective.id} solved small mysteries at the {scene.place}."
    )
    world.say(
        f"{detective.pronoun().capitalize()} wore a tiny coat and kept a notebook for every rhyme."
    )
    world.say(
        f'The rhyme on the page said, "{scene.rhyme}."'
    )
    world.say(
        f"That was the sort of clue that made a detective smile."
    )


SCENES = {
    "market": Scene(
        "market",
        "market",
        "A tidy clue, a rhyming tune, a spitting pipe in the afternoon",
        "puddle",
        "The pipe spit a shiny splash on the stones, making a circle like a coin.",
        "fountain pipe",
        "find the missing bell",
        "The missing bell was hanging safely on a ribbon behind the fruit stand.",
        tags={"rhyme", "spit", "market"},
    ),
    "garden": Scene(
        "garden",
        "garden",
        "A little rhyme, a clue in time, a spitting hose made a perfect line",
        "mud",
        "The hose could spit a small arc of water, and the mud kept a footprint well.",
        "garden hose",
        "find the missing key",
        "The missing key was tucked into a flowerpot, gleaming like a star.",
        tags={"rhyme", "spit", "garden"},
    ),
    "museum": Scene(
        "museum",
        "museum",
        "A careful note, a trail to quote, a spitting marble gave a wet clean mote",
        "shine",
        "The marble fountain could spit a fine mist, and the mist left a fresh clue.",
        "water marble",
        "find the missing pin",
        "The missing pin sat in a display tray, safe and easy to see.",
        tags={"rhyme", "spit", "museum"},
    ),
}

CLUES = {
    "coin": Clue("coin", "a shiny coin", "metal", "fruit stand", "It had tiny scratches shaped like a smile."),
    "thread": Clue("thread", "a blue thread", "cloth", "bench", "It matched the ribbon on the box."),
    "leaf": Clue("leaf", "a green leaf", "plant", "hedge", "It had a wet edge and a bent stem."),
}

SUSPECTS = {
    "cat": Suspect("cat", "cat", "furry paws", "a soft round face", "it had been napping in the sun", chubby=False),
    "pigeon": Suspect("pigeon", "pigeon", "crumb trail", "a chubby belly and quick feet", "it had flown to the roof", chubby=True),
    "dog": Suspect("dog", "dog", "muddy nose", "a wagging tail", "it was tied near the gate", chubby=False),
}


@dataclass
@dataclass
class StoryParams:
    scene: str
    clue1: str
    clue2: str
    suspect: str
    detective_name: str
    detective_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SCENES:
        for c1 in CLUES:
            for c2 in CLUES:
                if c1 == c2:
                    continue
                for sus in SUSPECTS:
                    combos.append((s, c1, c2, sus))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming detective storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
              if (args.scene is None or c[0] == args.scene)
              and (args.clue1 is None or c[1] == args.clue1)
              and (args.clue2 is None or c[2] == args.clue2)
              and (args.suspect is None or c[3] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, clue1, clue2, suspect = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mia", "Nora", "Lena", "Toby", "Finn", "Noah"])
    return StoryParams(scene, clue1, clue2, suspect, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = World()
    detective = world.add(Entity("detective", kind="character", type=params.detective_gender, role="detective"))
    _ensure_meters(detective)
    scene = SCENES[params.scene]
    clue1 = CLUES[params.clue1]
    clue2 = CLUES[params.clue2]
    suspect = SUSPECTS[params.suspect]

    world.facts.update(scene=scene, clue1=clue1, clue2=clue2, suspect=suspect, detective=detective)

    tale_setup(world, detective, scene, suspect)
    world.para()
    inspect_spit(world, detective, scene)
    gather_clue(world, detective, clue1)
    gather_clue(world, detective, clue2)
    world.para()
    accuse(world, detective, suspect, clue1)
    combine_clues(world, detective, scene, [clue1, clue2], suspect)
    world.para()
    reveal(world, detective, scene, suspect)

    world.facts["solved"] = detective.meme("solved") >= THRESHOLD
    world.facts["rhyme"] = scene.rhyme
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    return [
        f'Write a short detective story for a young child that includes the word "combine" and a rhyme like "{scene.rhyme}".',
        f'Write a mystery story where a detective notices something that can spit water, gathers clues, and learns to combine them.',
        f'Write a gentle rhyming detective story with the words "chubby", "spit", and "combine".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    clue1: Clue = f["clue1"]
    clue2: Clue = f["clue2"]
    suspect: Suspect = f["suspect"]
    detective: Entity = f["detective"]
    return [
        ("Who is the story about?",
         f"It is about {detective.id}, a little detective who listened for clues and kept a rhyme in the notebook."),
        ("What made the clue show up?",
         f"The {scene.spitter} could spit a little spray, and that wet spot made the clue easy to notice."),
        ("What did the detective do with the clues?",
         f"{detective.id} learned to combine {clue1.label} and {clue2.label}. That helped the detective see that the first guess was wrong."),
        ("Who looked suspicious?",
         f"The {suspect.label} looked suspicious at first, especially because of {suspect.appearance}."),
        ("What was the real ending?",
         f"The mystery was solved, and the missing thing was found safely in the {scene.reward_image.lower().split(' was ')[0]}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    suspect: Suspect = f["suspect"]
    qas = [
        ("What does it mean to combine clues?",
         "It means to put two or more clues together and think about them at the same time."),
        ("What is a detective?",
         "A detective is someone who looks carefully for clues to solve a mystery."),
        ("What does spit mean here?",
         "Here, spit means to spray or send out a little bit of water or mist."),
    ]
    if suspect.chubby:
        qas.append(("What does chubby mean?",
                    "Chubby means round and soft-looking, with a little extra body to the shape."))
    if "rhyme" in scene.tags:
        qas.append(("What is a rhyme?",
                    "A rhyme is when words sound alike at the end, like tune and moon."))
    return qas


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
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C1,C2,P) :- scene(S), clue(C1), clue(C2), C1 != C2, suspect(P).
solved :- clue_count(N), N >= 3.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for pid in SUSPECTS:
        lines.append(asp.fact("suspect", pid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, clue1=None, clue2=None, suspect=None, name=None, gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams("market", "coin", "thread", "pigeon", "Mia", "girl"),
    StoryParams("garden", "leaf", "coin", "dog", "Toby", "boy"),
    StoryParams("museum", "thread", "leaf", "cat", "Nora", "girl"),
]


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
        print(asp_program("", "#show valid/4."))
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
