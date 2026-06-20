#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/blond_news_music_room_suspense_folk_tale.py
============================================================================

A standalone story world for a small folk-tale suspense in a music room:
a blond child brings news that something precious is missing, the room grows
still and uncanny, and then the search reveals a safe, satisfying truth.

The domain is intentionally tiny and classical:
- characters have physical meters and emotional memes
- state drives the prose
- suspense comes from a brief search and a careful reveal
- the ending proves what changed

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/blond_news_music_room_suspense_folk_tale.py
    python storyworlds/worlds/gpt-5.4-mini/blond_news_music_room_suspense_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/blond_news_music_room_suspense_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/blond_news_music_room_suspense_folk_tale.py --verify
    python storyworlds/worlds/gpt-5.4-mini/blond_news_music_room_suspense_folk_tale.py --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    name: str
    echo: str
    secret: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class News:
    id: str
    title: str
    phrase: str
    tone: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    hide_place: str
    found_place: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    news: str
    missing: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.room: Optional[Room] = None
        self.news: Optional[News] = None
        self.missing: Optional[MissingThing] = None
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.room = copy.deepcopy(self.room)
        c.news = copy.deepcopy(self.news)
        c.missing = copy.deepcopy(self.missing)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    room = world.room
    if room and room.meters["stillness"] >= THRESHOLD and ("spook", "still") not in world.fired:
        world.fired.add(("spook", "still"))
        room.memes["unease"] += 1
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["unease"] += 1
        out.append("__silence__")
    return out


def _r_find(world: World) -> list[str]:
    room = world.room
    if not room or not world.missing:
        return []
    if room.meters["search"] < THRESHOLD or ("found", world.missing.id) in world.fired:
        return []
    world.fired.add(("found", world.missing.id))
    room.meters["reveal"] += 1
    return ["__reveal__"]


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("find", "physical", _r_find)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                out.extend(s for s in got if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness(news: News, missing: MissingThing) -> bool:
    return "news" in news.tags and (missing.gentle or "gentle" in missing.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid in ROOMS:
        for nid, n in NEWS.items():
            for mid, m in MISSING.items():
                if reasonableness(n, m):
                    combos.append((rid, nid, mid))
    return combos


def safe_news_id(nid: str) -> bool:
    return NEWS[nid].tone in {"calm", "hushed", "warm"}


def predict_reveal(world: World, missing_id: str) -> dict:
    sim = world.copy()
    sim.room.meters["search"] += 1
    propagate(sim, narrate=False)
    return {"revealed": sim.room.meters["reveal"] >= THRESHOLD}


def open_scene(world: World, child: Entity, elder: Entity, room: Room, news: News) -> None:
    child.memes["curiosity"] += 1
    room.meters["stillness"] += 1
    world.say(f"In the {room.name}, {child.id} came in with {child.pronoun('possessive')} blond hair shining like pale wheat.")
    world.say(f"{child.id} brought {news.phrase}, and the room seemed to listen.")
    world.say(f"{elder.id} turned from the instrument stand. {child.id} said, \"{news.title}\"")


def deepen_suspense(world: World, child: Entity, elder: Entity, missing: MissingThing, room: Room) -> None:
    child.memes["fear"] += 1
    room.meters["stillness"] += 1
    world.say(f"But something was wrong. {missing.label_word if hasattr(missing, 'label_word') else missing.label} was gone from {missing.hide_place}.")
    world.say(f"The little music room went quiet as a pond before rain.")
    world.say(f'"Where did it go?" {child.id} whispered, and {child.pronoun("possessive")} eyes went wide.')


def search(world: World, child: Entity, elder: Entity, missing: MissingThing, room: Room) -> None:
    room.meters["search"] += 1
    child.memes["bravery"] += 1
    elder.memes["calm"] += 1
    world.say(f"{elder.id} held up a candle-bright lamp and said, \"One careful step at a time.\"")
    world.say(f"They looked under the bench, behind the curtain, and inside the old music chest.")


def reveal(world: World, child: Entity, elder: Entity, missing: MissingThing, room: Room) -> None:
    room.meters["reveal"] += 1
    missing_f = world.get("missing")
    missing_f.meters["found"] += 1
    world.say(f"At last, they found the {missing.label} in {missing.found_place}, tucked safe and sound.")
    world.say(f"It had not been stolen at all; it had only been hiding where small hands could not see it at first.")


def ending(world: World, child: Entity, elder: Entity, missing: MissingThing) -> None:
    child.memes["relief"] += 1
    elder.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.id} laughed and hugged {elder.id}.")
    world.say(f"Then the room filled with music again, and the {missing.label} was set in its proper place.")
    world.say(f"This time the tune rang clear, and the blond child carried the news home with a smiling face.")


def tell(room_cfg: Room, news_cfg: News, missing_cfg: MissingThing,
         child: str = "Mina", child_gender: str = "girl",
         elder: str = "Grandma", elder_gender: str = "woman",
         parent: str = "mother") -> World:
    world = World()
    room = copy.deepcopy(room_cfg)
    news = copy.deepcopy(news_cfg)
    missing = copy.deepcopy(missing_cfg)
    world.room = room
    world.news = news
    world.missing = missing

    c = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    e = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder"))
    p = world.add(Entity(id=parent, kind="character", type=parent, role="parent"))

    open_scene(world, c, e, room, news)
    world.para()
    deepen_suspense(world, c, e, missing, room)
    search(world, c, e, missing, room)
    if predict_reveal(world, missing.id)["revealed"]:
        world.para()
        reveal(world, c, e, missing, room)
        ending(world, c, e, missing)
    world.facts.update(child=c, elder=e, parent=p, room=room, news=news, missing=missing)
    return world


ROOMS = {
    "music_room": Room("music_room", "music room", "the room held its breath", "a hidden latch behind the piano"),
}

NEWS = {
    "lost_song": News("lost_song", "I have news!", "news of a missing songbook", "hushed", "the songbook was found", {"news", "music"}),
    "storm_call": News("storm_call", "I have news!", "news that the rain was coming soon", "calm", "the lantern was lit", {"news"}),
    "midnight_note": News("midnight_note", "I have news!", "news of a mystery note in the music room", "hushed", "the note led them to the piano", {"news", "suspense"}),
}

MISSING = {
    "songbook": MissingThing("songbook", "songbook", "the songbook", "on the shelf", "inside the piano bench", True, {"gentle", "music"}),
    "bow": MissingThing("bow", "bow", "the fiddle bow", "by the window", "beneath the music stand", True, {"gentle", "music"}),
    "key": MissingThing("key", "little key", "the little key", "on the hook", "inside the lantern tin", True, {"gentle"}),
}

GIRL_NAMES = ["Mina", "Lila", "Elsa", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Finn", "Owen", "Eli", "Jude", "Theo", "Ben"]
TRAITS = ["careful", "quiet", "curious", "brave", "thoughtful"]


@dataclass
class StoryData:
    room: str
    news: str
    missing: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    parent: str
    trait: str = "curious"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale suspense storyworld in a music room.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--news", choices=NEWS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryData:
    if args.news and args.missing:
        if not reasonableness(NEWS[args.news], MISSING[args.missing]):
            raise StoryError("This news and missing thing do not make a gentle suspense tale.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.news is None or c[1] == args.news)
              and (args.missing is None or c[2] == args.missing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, nid, mid = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(["Grandma", "Grandpa", "Aunt Rose", "Uncle Will"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryData(room, nid, mid, child, child_gender, elder, elder_gender, parent, trait)


def generate(params: StoryData) -> StorySample:
    world = tell(ROOMS[params.room], NEWS[params.news], MISSING[params.missing],
                 params.child, params.child_gender, params.elder, params.elder_gender, params.parent)
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
    return [
        f'Write a folk-tale style suspense story in a music room that uses the words "blond" and "news".',
        f"Tell a gentle suspense story about {f['child'].id}, who brings news in the music room and then discovers what happened to the missing {f['missing'].label}.",
        f"Write a child-facing tale where a quiet mystery in the music room turns into a safe reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    missing = f["missing"]
    room = f["room"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {elder.id} in the {room.name}. The blond child brings the news, and the older helper listens carefully."),
        ("What news did the child bring?",
         f"{child.id} brought news about something missing in the music room. That news made the room feel still and a little spooky until they searched together."),
        ("What did they find?",
         f"They found {missing.phrase} where it had been hidden. Once they saw it, the mystery ended and the room could make music again."),
        ("How did the story end?",
         f"It ended safely, with relief and music. The missing thing was returned to its proper place, so the room no longer felt strange."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a music room?", "A music room is a room where people keep instruments and practice songs. It is a place for listening, playing, and careful hands."),
        QAItem("Why can a quiet room feel suspenseful?", "A very quiet room can make small sounds seem bigger than they are. That can make a mystery feel tense for a moment."),
        QAItem("What does news mean?", "News is new information about something that happened or was found. People share news when they want others to know something important."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    if world.room:
        lines.append(f"  room: {world.room.name}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, N, M) :- room(R), news(N), missing(M), gentle_missing(M), news_tag(N).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for nid, n in NEWS.items():
        lines.append(asp.fact("news", nid))
        lines.append(asp.fact("news_tag", nid))
    for mid, m in MISSING.items():
        lines.append(asp.fact("missing", mid))
        if m.gentle:
            lines.append(asp.fact("gentle_missing", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Story generation failed: {exc}")
        return 1
    print("OK: ASP and Python agree; story generation smoke test passed.")
    return 0


def explain_rejection() -> str:
    return "This combination would not make a gentle suspense story in the music room."


def explain_resolution(name: str) -> str:
    return f"(No story: could not resolve {name}.)"


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryData("music_room", "lost_song", "songbook", "Mina", "girl", "Grandma", "woman", "mother"),
            StoryData("music_room", "midnight_note", "bow", "Finn", "boy", "Grandpa", "man", "father"),
            StoryData("music_room", "storm_call", "key", "Lila", "girl", "Aunt Rose", "woman", "mother"),
        ]
        samples = [generate(p) for p in curated]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
