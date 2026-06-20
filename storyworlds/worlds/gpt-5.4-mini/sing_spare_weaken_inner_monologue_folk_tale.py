#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sing_spare_weaken_inner_monologue_folk_tale.py
==============================================================================

A standalone story world for a tiny folk-tale domain: a child, a harmed place,
and a wise inner monologue that leads to a gentle, sung solution.  The world is
small on purpose: one premise, one tension, one turn, one ending image.

Seed words: sing, spare, weaken
Style: folk tale
Feature: inner monologue
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Place:
    id: str
    label: str
    kind: str
    echo: str
    holds: str
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
class Threat:
    id: str
    label: str
    source: str
    place_required: str
    weaken_by: int
    makes_sad: str
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
class Song:
    id: str
    label: str
    tune: str
    courage: int
    soften: int
    spare_text: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["danger"] >= THRESHOLD and ("fear", e.id) not in world.fired:
            world.fired.add(("fear", e.id))
            e.memes["fear"] += 1
            out.append("")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_r_fear,):
            if fn(world):
                changed = True


PLACE = Place("grove", "the old grove", "grove", "the boughs whispered like old grandmothers", "the hollow heart of the trees", {"grove"})
THREAT = Threat("bramble", "the bramble curse", "brambles", "grove", 2, "it thorns over the path", {"thorn", "curse"})
SONGS = {
    "lullaby": Song("lullaby", "a lullaby", "soft as milk", 1, 2, "spare the small things and let them sleep", {"song", "gentle"}),
    "river_song": Song("river_song", "a river song", "clear as bells", 2, 3, "spare the brook and let it run free", {"song", "river"}),
    "harvest_song": Song("harvest_song", "a harvest song", "warm as bread", 2, 2, "spare the nest and let the birds stay", {"song", "harvest"}),
}


@dataclass
@dataclass
class StoryParams:
    song: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
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


def valid_combos() -> list[tuple[str]]:
    return [(sid,) for sid in SONGS]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("song", sid) for sid in SONGS]
    lines += [asp.fact("place", PLACE.id), asp.fact("threat", THREAT.id)]
    for sid, s in SONGS.items():
        lines.append(asp.fact("weaken", sid, s.soften))
        lines.append(asp.fact("courage", sid, s.courage))
    lines.append(asp.fact("threat_needs", THREAT.id, THREAT.place_required))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S) :- song(S).
weakened(S) :- weaken(S, W), W >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in valid_combos():")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
        rc = 1

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: smoke-tested normal generation.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale story world about singing, sparing, and weakening a curse.")
    ap.add_argument("--song", choices=SONGS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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


NAMES_GIRL = ["Mira", "Nia", "Sera", "Lina", "Tova", "Anya"]
NAMES_BOY = ["Rowan", "Oren", "Milo", "Bram", "Eli", "Jonah"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.song and args.song not in SONGS:
        raise StoryError("Unknown song.")
    sid = args.song or rng.choice(list(SONGS))
    g = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if g == "girl" else NAMES_BOY)
    eg = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(NAMES_GIRL if eg == "woman" else NAMES_BOY)
    if child == elder:
        elder = (NAMES_GIRL if eg == "woman" else NAMES_BOY)[0]
    return StoryParams(sid, child, g, elder, eg)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child, "character", params.child_gender, role="child", traits=["small", "earnest"]))
    elder = world.add(Entity(params.elder, "character", params.elder_gender, role="elder", traits=["wise"]))
    world.add(Entity(PLACE.id, "place", "place", label=PLACE.label))
    curse = world.add(Entity(THREAT.id, "thing", "curse", label=THREAT.label))
    song = SONGS[params.song]

    child.memes["hope"] += 1
    world.say(
        f"In the old grove, {child.id} and {elder.id} walked where the boughs "
        f"whispered like old grandmothers. The hollow heart of the trees felt "
        f"full of secrets, and the path ahead was tangled by {THREAT.label}."
    )
    world.say(
        f'{child.id} felt a small tug of worry. "{child.id} wondered if the grove '
        f'would ever open its arms again," {child.pronoun()} thought.'
    )
    world.para()
    world.say(
        f"{elder.id} looked at the thorns and said the path was blocked. "
        f"{child.id} wanted to help, but the branches were stiff and mean."
    )
    child.memes["worry"] += 1
    world.say(
        f'Inside {child.pronoun("possessive")} own chest, {child.id} heard a quiet '
        f'voice: "{song.spare_text}. If I sing, maybe the bramble will weaken."'
    )
    world.say(
        f'{child.id} took a breath and began to sing {song.tune}.'
    )
    child.meters["song"] += 1
    curse.meters["danger"] += 1
    curse.meters["weakness"] += song.soften
    propagate(world)
    world.para()
    if curse.meters["weakness"] >= THRESHOLD:
        world.say(
            f"The song warmed the air. The bramble shivered, then weakened until "
            f'its thorns bent aside like tired fingers.'
        )
        world.say(
            f"{elder.id} smiled and lifted the last branch from the path. "
            f"{child.id} had sung, and the grove opened without being hurt."
        )
        world.say(
            f"At the end, the little singer walked on through the green hush, "
            f"and even the birds seemed to spare a note for {child.id}."
        )
    else:
        world.say(
            f"The song was brave, but the bramble only trembled. It did not weaken "
            f"enough to let the path open."
        )
        world.say(
            f"{elder.id} wrapped {child.id} in a cloak and led {child.id} home by "
            f"another trail, promising to return with better help."
        )
        world.say(
            f"That night the grove stayed closed, but {child.id} kept the tune in "
            f"{child.pronoun('possessive')} heart for another day."
        )
    world.facts.update(child=child, elder=elder, song=song, curse=curse, outcome="opened" if curse.meters["weakness"] >= THRESHOLD else "closed")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    song = f["song"]
    child = f["child"]
    return [
        f'Write a folk-tale style story for a child where {child.id} must '
        f'{song.label} to help a place, and include the words "sing", "spare", '
        f'and "weaken".',
        f'Tell a gentle inner-monologue story where {child.id} thinks, "If I '
        f'{song.label}, maybe I can spare the grove," and something begins to '
        f'weaken.',
        f'Write a short story about a brave child, a tangled path, and a song '
        f"that can weaken a curse without hurting the forest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    song = f["song"]
    curse = f["curse"]
    out = [
        QAItem(
            question="What problem did the child face?",
            answer=f"{child.id} faced {THREAT.label}, which tangled the path in the old grove. It made the way hard to pass, so the child had to think of a gentle fix."
        ),
        QAItem(
            question="What did the child think inside?",
            answer=f"{child.id} thought that if {child.pronoun('subject')} could sing {song.tune}, {song.spare_text}. That inner thought turned fear into a plan."
        ),
    ]
    if f["outcome"] == "opened":
        out.append(QAItem(
            question="How did the story end?",
            answer=f"The song weakened the bramble until the thorns bent aside, and the grove opened safely. {child.id} sang, {elder.id} smiled, and nothing in the forest had to be broken."
        ))
        out.append(QAItem(
            question="Why was singing a good choice?",
            answer=f"Singing fit the folk-tale spell of the world, and it weakened the curse without cutting or burning anything. That let the child spare the grove and still solve the problem."
        ))
    else:
        out.append(QAItem(
            question="How did the story end?",
            answer=f"The bramble did not weaken enough, so {elder.id} took {child.id} home by another path. The child kept the song for later, and the grove stayed safe and closed."
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    song = world.facts["song"]
    return [
        QAItem(
            question="What does it mean to spare something?",
            answer="To spare something means to leave it unharmed or to choose not to damage it. A kind person may spare a bird, a tree, or a tired friend."
        ),
        QAItem(
            question="How can a song weaken a curse in a folk tale?",
            answer="In a folk tale, a song can be part of old magic. A steady tune can weaken a curse by calming fear, loosening a spell, or helping a hidden truth wake up."
        ),
        QAItem(
            question="Why do people sing in folk tales?",
            answer="People sing in folk tales to show courage, ask for help, or mark a magic moment. A song can carry hope farther than plain words."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={meters} memes={memes}")
    return "\n".join(lines)


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
    StoryParams("lullaby", "Mira", "girl", "Grandmother", "woman"),
    StoryParams("river_song", "Rowan", "boy", "Mother", "woman"),
    StoryParams("harvest_song", "Nia", "girl", "Father", "man"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid songs:", ", ".join(s for (s,) in asp_valid_combos()))
        return

    rng0 = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(rng0.randint(0, 2**31 - 1)))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
