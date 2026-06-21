#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/announce_friendship_sharing_heartwarming.py
============================================================================

A small standalone storyworld for a heartwarming friendship-and-sharing tale.

Premise
-------
A child wants to announce something kind: a plan to share a special item with a
friend. The story follows a few close variants where friendship grows through a
clear spoken announcement, a small tension about whether sharing is enough, and
a warm ending image that proves the relationship changed.

This script follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- state-driven narration
- QA generated from world state, not by parsing the rendered story
- Python reasonableness gate plus inline ASP twin
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
DELIGHT_MIN = 2
ANNOUNCE_WORD = "announce"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    shared: bool = False
    treasured: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class ItemSpec:
    id: str
    label: str
    phrase: str
    comfort: str
    share_kind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class GiftSpec:
    id: str
    label: str
    phrase: str
    delight: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Response:
    id: str
    warmth: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    giver = world.get("child")
    friend = world.get("friend")
    item = world.get("item")
    gift = world.get("gift")
    if giver.meters["shares"] < THRESHOLD:
        return out
    if friend.memes["doubt"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["hope"] += 1
    friend.memes["warmth"] += 1
    item.meters["shared"] += 1
    gift.meters["received"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("soften", "social", _r_soften)]


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


def choose_reasonable_response() -> list[Response]:
    return [r for r in RESPONSES.values() if r.warmth >= DELIGHT_MIN]


def story_can_work(item: ItemSpec, gift: GiftSpec) -> bool:
    return item.share_kind == gift.id or item.share_kind in gift.tags or gift.id in item.tags


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.warmth)


def announce_plan(world: World, child: Entity, friend: Entity, item: ItemSpec, gift: GiftSpec) -> None:
    child.memes["joy"] += 1
    child.meters["shares"] += 1
    world.say(
        f"On a bright afternoon, {child.id} found {friend.id} under the tree and smiled. "
        f"{child.id} held up {item.phrase} and {gift.phrase} and decided to {ANNOUNCE_WORD} a kind plan."
    )
    world.say(
        f'"I want to share {item.label} with you," {child.id} said. '
        f'"Then we can enjoy it together."'
    )


def wobble(world: World, friend: Entity, item: ItemSpec, gift: GiftSpec) -> None:
    friend.memes["doubt"] += 1
    world.say(
        f"{friend.id} looked surprised at first. {friend.id} worried that sharing might mean there would be less to enjoy."
    )
    world.say(
        f"Still, {friend.id} held the {item.label} carefully and listened."
    )


def reassure(world: World, child: Entity, friend: Entity, item: ItemSpec, gift: GiftSpec) -> None:
    friend.memes["trust"] += 1
    world.say(
        f"{child.id} took a small breath and {ANNOUNCE_WORD}d again, softer this time. "
        f'"We can take turns," {child.id} said. "Sharing means nobody is left out."'
    )
    world.say(
        f"That made {friend.id}'s face grow gentle, because {item.label} was still there and the fun was growing, too."
    )


def accept(world: World, child: Entity, friend: Entity, item: ItemSpec, gift: GiftSpec, response: Response) -> None:
    friend.memes["joy"] += 1
    child.memes["pride"] += 1
    child.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"{friend.id} smiled at last, and {response.text}."
    )
    world.say(
        f"Together they {response.qa_text.replace('{item}', item.label).replace('{gift}', gift.label)}."
    )


def end_image(world: World, child: Entity, friend: Entity, item: ItemSpec, gift: GiftSpec) -> None:
    world.say(
        f"By the end of the day, {child.id} and {friend.id} were sitting close together, "
        f"{item.label} between them, {gift.label} ready beside them, both of them laughing like old friends."
    )


def tell(item: ItemSpec, gift: GiftSpec, response: Response, child_name: str = "Mia",
         child_gender: str = "girl", friend_name: str = "Noah", friend_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    item_ent = world.add(Entity(id="item", type="thing", label=item.label, shared=False, treasured=True))
    gift_ent = world.add(Entity(id="gift", type="thing", label=gift.label, shared=True, treasured=True))

    world.facts.update(item=item, gift=gift, response=response, child=child, friend=friend,
                       item_ent=item_ent, gift_ent=gift_ent)

    announce_plan(world, child, friend, item, gift)
    world.para()
    wobble(world, friend, item, gift)
    reassure(world, child, friend, item, gift)
    world.para()
    response_line = response.text.replace("{item}", item.label).replace("{gift}", gift.label)
    world.say(response_line)
    propagate(world, narrate=True)
    accept(world, child, friend, item, gift, response)
    world.para()
    end_image(world, child, friend, item, gift)

    world.facts["outcome"] = "shared"
    return world


ITEMS = {
    "book": ItemSpec("book", "picture book", "a favorite picture book", "reading together", "book", {"book", "reading"}),
    "cookies": ItemSpec("cookies", "plate of cookies", "a plate of warm cookies", "snack time", "cookies", {"treat", "sharing"}),
    "blocks": ItemSpec("blocks", "box of blocks", "a box of bright blocks", "building together", "blocks", {"toy", "sharing"}),
    "crayons": ItemSpec("crayons", "box of crayons", "a box of shiny crayons", "drawing together", "crayons", {"art", "sharing"}),
}

GIFTS = {
    "book": GiftSpec("book", "bookmark", "a ribbon bookmark", "quiet delight", {"book", "reading"}),
    "cookies": GiftSpec("cookies", "napkins", "a stack of napkins", "helpful delight", {"treat", "sharing"}),
    "blocks": GiftSpec("blocks", "tray", "a little tray", "neat delight", {"toy", "sharing"}),
    "crayons": GiftSpec("crayons", "cup", "a little cup", "colorful delight", {"art", "sharing"}),
}

RESPONSES = {
    "gentle": Response("gentle", 3, "soon they both felt brave enough to try", "felt shy and did not know what to do", "shared the moment kindly"),
    "warm": Response("warm", 4, "the worry melted into a warm smile", "still felt worried and stepped back", "shared the moment kindly"),
    "joyful": Response("joyful", 5, "their laughter filled the yard like sunshine", "kept looking unsure", "shared the moment happily"),
}

NAMES_GIRL = ["Mia", "Lily", "Ava", "Zoe", "Nina", "Ella"]
NAMES_BOY = ["Noah", "Ben", "Eli", "Theo", "Finn", "Sam"]


@dataclass
@dataclass
class StoryParams:
    item: str
    gift: str
    response: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for item_id, item in ITEMS.items():
        for gift_id, gift in GIFTS.items():
            if story_can_work(item, gift):
                combos.append((item_id, gift_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming friendship and sharing storyworld.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.item and args.gift:
        if not story_can_work(ITEMS[args.item], GIFTS[args.gift]):
            raise StoryError("No story: this item and gift do not fit a real sharing moment.")
    combos = [c for c in valid_combos()
              if (args.item is None or c[0] == args.item)
              and (args.gift is None or c[1] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    item_id, gift_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    child_name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    friend_name = args.friend or rng.choice(NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)
    if friend_name == child_name:
        friend_name = (NAMES_BOY if friend_gender == "boy" else NAMES_GIRL)[0]
    return StoryParams(item_id, gift_id, response, child_name, gender, friend_name, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(ITEMS[params.item], GIFTS[params.gift], RESPONSES[params.response],
                 params.child_name, params.child_gender, params.friend_name, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item, gift = f["item"], f["gift"]
    child, friend = f["child"], f["friend"]
    return [
        f'Write a heartwarming story that includes the word "{ANNOUNCE_WORD}" and shows {child.id} wanting to share {item.label} with {friend.id}.',
        f"Tell a gentle friendship story where {child.id} {ANNOUNCE_WORD}s a sharing plan about {item.phrase} and {friend.id} learns that sharing can make the moment better.",
        f'Write a small story about friendship and sharing using "{ANNOUNCE_WORD}", ending with a warm image of {item.label} and {gift.label} being enjoyed together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, item, gift = f["child"], f["friend"], f["item"], f["gift"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two friends who learn how sharing can make a day feel warmer."),
        (f"What did {child.id} want to do?",
         f"{child.id} wanted to share {item.phrase} and {ANNOUNCE_WORD} a kind plan so {friend.id} could join in."),
        (f"How did {friend.id} feel at first?",
         f"{friend.id} felt a little unsure at first, because {friend.id} worried there might not be enough to enjoy."),
        (f"What helped the friendship grow?",
         f"{child.id} kept speaking gently and showed that sharing {item.label} did not take the joy away. It made the moment bigger for both friends."),
        (f"How did the story end?",
         f"It ended with {child.id} and {friend.id} sitting together, smiling, and enjoying {item.label} and {gift.label} like close friends."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item, gift = f["item"], f["gift"]
    out = []
    if item.id == "book":
        out.append(("What is a picture book?",
                     "A picture book is a book with lots of pictures and words that can be read aloud and enjoyed together."))
    if item.id == "cookies":
        out.append(("Why do people share cookies?",
                     "People share cookies so everyone can have a sweet snack and feel included."))
    if item.id == "blocks":
        out.append(("Why are blocks fun?",
                     "Blocks are fun because children can stack them, line them up, and build new things together."))
    if item.id == "crayons":
        out.append(("What are crayons for?",
                     "Crayons are for drawing and coloring, and they let children make bright pictures."))
    if gift.id == "bookmark":
        out.append(("What does a bookmark do?",
                     "A bookmark keeps your place in a book so you can stop and come back later."))
    if gift.id == "napkins":
        out.append(("Why are napkins helpful?",
                     "Napkins help clean little hands and keep snacks from making a big mess."))
    if gift.id == "tray":
        out.append(("What is a tray for?",
                     "A tray helps hold things together so they can be carried or shared neatly."))
    if gift.id == "cup":
        out.append(("What is a cup for?",
                     "A cup holds small things in one place, like crayons, markers, or little treasures."))
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("book", "book", "warm", "Mia", "girl", "Noah", "boy"),
    StoryParams("cookies", "cookies", "gentle", "Lily", "girl", "Ben", "boy"),
    StoryParams("blocks", "blocks", "joyful", "Theo", "boy", "Ava", "girl"),
    StoryParams("crayons", "crayons", "warm", "Nina", "girl", "Sam", "boy"),
]


def world_knowledge_tags(world: World) -> set[str]:
    return {world.facts["item"].id, world.facts["gift"].id}


def valid_story(params: StoryParams) -> bool:
    return story_can_work(ITEMS[params.item], GIFTS[params.gift])


ASP_RULES = r"""
valid(I, G) :- item(I), gift(G), fit(I, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("share_kind", iid, item.share_kind))
        for t in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, t))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for t in sorted(gift.tags):
            lines.append(asp.fact("gift_tag", gid, t))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("warmth", rid, resp.warmth))
    lines.append(asp.fact("delight_min", DELIGHT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: verify smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item, gift in asp_valid_combos():
            print(f"  {item} {gift}")
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for tag in world_knowledge_tags(world):
        if tag == "book":
            out.append(("What makes a picture book special?",
                        "A picture book lets children look at pictures while they hear the story."))
        elif tag == "cookies":
            out.append(("Why can sharing cookies be sweet?",
                        "Sharing cookies is sweet because a friend gets to enjoy a snack too."))
        elif tag == "blocks":
            out.append(("How do blocks help friends?",
                        "Blocks help friends build together, which makes play feel shared and fun."))
        elif tag == "crayons":
            out.append(("What do crayons help children do?",
                        "Crayons help children make colorful pictures and share art time."))
    return out


if __name__ == "__main__":
    main()
