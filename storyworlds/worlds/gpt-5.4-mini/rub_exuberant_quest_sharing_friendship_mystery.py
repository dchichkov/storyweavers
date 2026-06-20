#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rub_exuberant_quest_sharing_friendship_mystery.py
=================================================================================

A small storyworld about a gentle mystery quest where friends share clues,
follow a trail, and discover what a strange little rubbing sound means.

Seed words / style:
- rub
- exuberant
- Quest
- Sharing
- Friendship
- Mystery

The world model is built around typed entities with physical meters and
emotional memes. A child-led quest begins with a puzzling sign, grows through a
careful shared investigation, and ends with a reveal that changes what the
characters know and feel.

This script is standalone, stdlib-only, and follows the Storyweavers contract:
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- Python reasonableness gate plus inline ASP twin
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Locale:
    id: str
    place: str
    hush: str
    clue_spot: str
    mystery_word: str
    trail_word: str
    end_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    seek: str
    clue_kind: str
    clue_label: str
    clue_where: str
    clue_action: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingItem:
    id: str
    label: str
    phrase: str
    helps_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FriendshipTool:
    id: str
    label: str
    phrase: str
    brightness: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_exuberant(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["excitement"] < THRESHOLD:
            continue
        sig = ("exuberant", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["exuberant"] += 1
        out.append(f"{e.id} grew exuberant about the quest.")
    return out


def _r_shared_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("clue")
    if clue is None:
        return out
    for e in world.characters():
        if e.memes["sharing"] < THRESHOLD:
            continue
        sig = ("share", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["shared_clue"] = clue
        e.memes["trust"] += 1
        out.append(f"By sharing the clue, the friends felt closer.")
    return out


def _r_reveal(world: World) -> list[str]:
    if world.facts.get("reveal_done"):
        return []
    if world.facts.get("shared_clue") and world.facts.get("quest_progress", 0) >= 2:
        world.facts["reveal_done"] = True
        world.facts["mystery_solved"] = True
        return ["__reveal__"]
    return []


CAUSAL_RULES = [
    Rule("exuberant", "emotional", _r_exuberant),
    Rule("share", "social", _r_shared_clue),
    Rule("reveal", "story", _r_reveal),
]


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


def is_reasonable(locale: Locale, quest: Quest, share: SharingItem) -> bool:
    return locale.mystery_word == quest.seek and quest.clue_kind == share.helps_with


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid in LOCALES:
        for qid, q in QUESTS.items():
            for sid, s in SHARING.items():
                if is_reasonable(LOCALES[lid], q, s):
                    combos.append((lid, qid, sid))
    return combos


def predict_reveal(world: World) -> bool:
    sim = world.copy()
    sim.facts["quest_progress"] = 2
    propagate(sim, narrate=False)
    return bool(sim.facts.get("mystery_solved"))


def begin(world: World, a: Entity, b: Entity, locale: Locale, quest: Quest) -> None:
    a.memes["excitement"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"At {locale.place}, {a.id} and {b.id} started a quiet Quest under {locale.hush}. "
        f"The day felt strange, like it was hiding a secret."
    )
    world.say(
        f"They were looking for {quest.goal}, because {quest.seek} had gone missing from {quest.clue_where}."
    )


def rub_clue(world: World, a: Entity, locale: Locale, quest: Quest) -> None:
    a.memes["focus"] += 1
    world.facts["clue"] = quest.clue_label
    world.say(
        f"{a.id} leaned closer and gave the surface a careful rub. "
        f"Then a tiny mark appeared near {locale.clue_spot}."
    )
    world.say(
        f'"{quest.clue_label}!" {a.id} said, sounding exuberant all at once.'
    )


def share_clue(world: World, b: Entity, item: SharingItem, quest: Quest) -> None:
    b.memes["sharing"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{b.id} took a breath and shared {item.phrase} with {quest.goal}. "
        f"That made the clue easier to understand."
    )


def search_together(world: World, a: Entity, b: Entity, locale: Locale, quest: Quest) -> None:
    world.facts["quest_progress"] = 2
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    world.say(
        f"Together they followed the small trail past {locale.trail_word}. "
        f"Each step made the mystery feel less lonely."
    )


def reveal(world: World, a: Entity, b: Entity, locale: Locale, quest: Quest, tool: FriendshipTool) -> None:
    world.say(
        f"At last, the mystery opened up: {quest.reveal}. "
        f"The answer had been waiting right where the clue said."
    )
    world.say(
        f"{a.id} and {b.id} laughed, then used {tool.phrase} to mark the spot so they would remember."
    )
    world.say(
        f"By the end, the Quest was solved, the Sharing had helped, and their Friendship shone bright in {locale.end_word}."
    )


def tell(locale: Locale, quest: Quest, share: SharingItem, tool: FriendshipTool,
         a_name: str = "Mia", a_gender: str = "girl",
         b_name: str = "Noah", b_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="quester"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="place", type="place", label=locale.place))
    world.facts["locale"] = locale
    world.facts["quest"] = quest
    world.facts["share"] = share
    world.facts["tool"] = tool
    world.facts["parent"] = parent

    begin(world, a, b, locale, quest)
    world.para()
    rub_clue(world, a, locale, quest)
    share_clue(world, b, share, quest)
    search_together(world, a, b, locale, quest)
    world.para()
    if predict_reveal(world):
        reveal(world, a, b, locale, quest, tool)
    world.facts["mystery_solved"] = True
    world.facts["quester"] = a
    world.facts["helper"] = b
    world.facts["parent"] = parent
    return world


LOCALES = {
    "museum": Locale("museum", "the old museum", "the hush of the hall", "the dusty frame", "mystery", "trail", "a bright ending", {"mystery", "quest"}),
    "garden": Locale("garden", "the moonlit garden", "soft leaves whispering", "the rose bush", "mystery", "path", "warm lantern light", {"mystery", "quest"}),
    "attic": Locale("attic", "the attic", "the creak of old boards", "the wooden trunk", "mystery", "steps", "a cozy doorway", {"mystery", "quest"}),
}

QUESTS = {
    "lost_note": Quest("lost_note", "a lost note", "mystery", "message", "the note", "under a stack of books", "rubbed until the pencil marks appeared", "a map to the treasure box", {"quest", "mystery"}),
    "hidden_key": Quest("hidden_key", "a hidden key", "mystery", "key", "the key", "behind the picture", "rubbed until the dust came off", "a key tucked inside a secret drawer", {"quest", "mystery"}),
    "secret_path": Quest("secret_path", "a secret path", "mystery", "path", "the path", "near the stone wall", "rubbed until the chalk line showed", "a trail leading to a small door", {"quest", "mystery"}),
}

SHARING = {
    "map": SharingItem("map", "a torn map", "a torn map", "message", {"sharing"}),
    "riddle": SharingItem("riddle", "a little riddle", "a little riddle", "key", {"sharing"}),
    "crumbs": SharingItem("crumbs", "some breadcrumbs", "some breadcrumbs", "path", {"sharing"}),
}

TOOLS = {
    "lantern": FriendshipTool("lantern", "lantern", "a little lantern", "bright", {"friendship"}),
    "sticker": FriendshipTool("sticker", "sticker", "a shiny sticker", "cheerful", {"friendship"}),
    "ribbon": FriendshipTool("ribbon", "ribbon", "a blue ribbon", "kind", {"friendship"}),
}


@dataclass
class StoryParams:
    locale: str
    quest: str
    share: str
    tool: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "mystery": [("What is a mystery?", "A mystery is something that is puzzling or not easy to understand right away. People solve it by looking carefully for clues.")],
    "quest": [("What is a quest?", "A quest is a search for something important. It often means following clues and trying not to give up.")],
    "sharing": [("What does sharing mean?", "Sharing means giving someone part of what you have, or letting them help with it, so you both can use it together.")],
    "friendship": [("What is friendship?", "Friendship means caring about someone, helping them, and enjoying time together.")],
    "rub": [("What does it mean to rub something?", "To rub something means to move your hand back and forth on it. That can sometimes make dust, marks, or shine appear.")],
    "exuberant": [("What does exuberant mean?", "Exuberant means very happy and full of energy. It is like being so excited that the feeling bubbles out.")],
}

KNOWLEDGE_ORDER = ["mystery", "quest", "sharing", "friendship", "rub", "exuberant"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    locale: Locale = f["locale"]
    quest: Quest = f["quest"]
    return [
        f'Write a child-friendly mystery about {locale.place} where friends search for {quest.goal}. Include the words "rub" and "exuberant".',
        f"Tell a short Quest story about Sharing and Friendship set in {locale.place}, with a clue that appears when someone rubs the right spot.",
        f"Write a cozy mystery where two friends solve {quest.goal} together and feel exuberant at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    locale: Locale = f["locale"]
    quest: Quest = f["quest"]
    a: Entity = f["quester"]
    b: Entity = f["helper"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {a.id} and {b.id}, two friends on a Quest. They also have {parent.label_word if parent.label_word else 'a grown-up'} nearby, but the friends do the solving."
        ),
        QAItem(
            question="What made the mystery start?",
            answer=f"The mystery started because {quest.seek} was missing from {quest.clue_where}. That made the place feel puzzling, so the friends had to look for clues."
        ),
        QAItem(
            question="What happened when {0} rubbed the spot?".format(a.id),
            answer=f"When {a.id} gave the spot a careful rub, a tiny clue appeared near {locale.clue_spot}. That was the first real sign that they were on the right trail."
        ),
        QAItem(
            question="How did Sharing help solve the Quest?",
            answer=f"{b.id} shared {f['share'].phrase}, and that made the clue easier to understand. Because they worked together, the search moved forward instead of stopping at one person's idea."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the mystery solved: {quest.reveal}. The friends felt exuberant because their sharing and friendship turned the strange clue into an answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["share"].tags) | set(world.facts["tool"].tags)
    tags |= {"rub", "exuberant", "sharing", "friendship", "quest", "mystery"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("museum", "lost_note", "map", "lantern", "Mia", "girl", "Noah", "boy", "mother"),
    StoryParams("garden", "secret_path", "crumbs", "sticker", "Ava", "girl", "Leo", "boy", "father"),
    StoryParams("attic", "hidden_key", "riddle", "ribbon", "Finn", "boy", "Ella", "girl", "mother"),
]


def explain_rejection(locale: Locale, quest: Quest, share: SharingItem) -> str:
    return (
        f"(No story: the shared item '{share.label}' does not help with {quest.clue_kind}, "
        f"so it would not make a clear clue for the {quest.seek} mystery in {locale.place}.)"
    )


def asp_facts() -> str:
    import asp
    lines = []
    for lid, loc in LOCALES.items():
        lines.append(asp.fact("locale", lid))
        lines.append(asp.fact("mystery_word", lid, loc.mystery_word))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("seek", qid, q.seek))
        lines.append(asp.fact("clue_kind", qid, q.clue_kind))
    for sid, s in SHARING.items():
        lines.append(asp.fact("sharing", sid))
        lines.append(asp.fact("helps_with", sid, s.helps_with))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(L,Q,S) :- locale(L), quest(Q), sharing(S),
                     mystery_word(L,M), seek(Q,M), clue_kind(Q,K), helps_with(S,K).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid_combos() parity.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(locale=None, quest=None, share=None, tool=None, hero=None, hero_gender=None, friend=None, friend_gender=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery quest world about sharing and friendship.")
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--share", choices=SHARING)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.locale is None or c[0] == args.locale)
              and (args.quest is None or c[1] == args.quest)
              and (args.share is None or c[2] == args.share)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    locale, quest, share = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(["Mia", "Ava", "Nora", "Leo", "Finn", "Noah"])
    friend = args.friend or rng.choice([n for n in ["Mia", "Ava", "Nora", "Leo", "Finn", "Noah"] if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(locale, quest, share, tool, hero, hero_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCALES[params.locale], QUESTS[params.quest], SHARING[params.share], TOOLS[params.tool], params.hero, params.hero_gender, params.friend, params.friend_gender, params.parent)
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
        print(asp_program("", "#show reasonable/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            i += 1
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
