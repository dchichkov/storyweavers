#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/porridge_cluster_tine_misunderstanding_inner_monologue_friendship.py
=====================================================================================================

A standalone storyworld for a small rhyming tale about porridge, a cluster, and
a tine. The world is built around a child misunderstanding a tiny scene, then
thinking it through in an inner monologue before friendship clears it up.

The story is intentionally compact and classical: a few typed entities, a simple
state machine, and prose driven by simulated meters and memes.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/porridge_cluster_tine_misunderstanding_inner_monologue_friendship.py
    python storyworlds/worlds/gpt-5.4-mini/porridge_cluster_tine_misunderstanding_inner_monologue_friendship.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/porridge_cluster_tine_misunderstanding_inner_monologue_friendship.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Scene:
    id: str
    place: str
    bowl: str
    cluster: str
    tine: str
    rhyme: str
    cluster_is_shared: bool = True
    soft_porridge: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Resolve:
    id: str
    sense: int
    text: str
    explain: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    scene: str
    actor_name: str
    actor_type: str
    friend_name: str
    friend_type: str
    resolve: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


SCENES = {
    "kitchen": Scene(
        id="kitchen",
        place="the kitchen",
        bowl="a blue bowl",
        cluster="a little cluster of berries",
        tine="the tiny tine",
        rhyme="the spoon went swoosh, and the day felt bright and sunny",
        tags={"porridge", "cluster", "tine", "kitchen"},
    ),
    "porch": Scene(
        id="porch",
        place="the porch",
        bowl="a round bowl",
        cluster="a cluster of seeds",
        tine="the shiny tine",
        rhyme="the porch wind hummed, soft and funny",
        tags={"porridge", "cluster", "tine", "porch"},
    ),
    "garden": Scene(
        id="garden",
        place="the garden bench",
        bowl="a warm bowl",
        cluster="a cluster of flowers",
        tine="the bent tine",
        rhyme="the bees buzzed by in a gentle runny",
        tags={"porridge", "cluster", "tine", "garden"},
    ),
}

RESOLVES = {
    "ask": Resolve(
        id="ask",
        sense=3,
        text="asked a kind question and learned the truth at once",
        explain="asked about the cluster and heard the answer",
        tags={"friendship", "talk"},
    ),
    "share": Resolve(
        id="share",
        sense=3,
        text="shared the porridge and smiled together after the mix-up",
        explain="shared the porridge, and sharing made the feeling bright",
        tags={"friendship", "porridge"},
    ),
    "show": Resolve(
        id="show",
        sense=2,
        text="showed the tine and the little cluster side by side",
        explain="showed how the tine belonged to the bowl, not the bird",
        tags={"friendship", "tine"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Poppy", "Nora", "Elsie", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Ari", "Jasper"]


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for scene in SCENES:
        for resolve in RESOLVES:
            for actor_type in ("girl", "boy"):
                for friend_type in ("girl", "boy"):
                    combos.append((scene, resolve, actor_type, friend_type, "child", "child"))
    return combos


def reason_ok(params: StoryParams) -> None:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.resolve not in RESOLVES:
        raise StoryError("Unknown resolution.")
    if params.actor_type not in ("girl", "boy") or params.friend_type not in ("girl", "boy"):
        raise StoryError("Invalid character type.")


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scenes = list(SCENES)
    resolves = list(RESOLVES)
    scene = args.scene or rng.choice(scenes)
    resolve = args.resolve or rng.choice(resolves)
    actor_type = args.actor_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    actor_name = args.actor_name or _pick_name(rng, actor_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type)
    params = StoryParams(
        scene=scene,
        actor_name=actor_name,
        actor_type=actor_type,
        friend_name=friend_name,
        friend_type=friend_type,
        resolve=resolve,
    )
    reason_ok(params)
    return params


def _r_misunderstanding(world: World) -> list[str]:
    out = []
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["confusion"] >= THRESHOLD and not world.fired:
        world.fired.add(("misunderstanding",))
        child.memes["worry"] += 1
        friend.memes["hurt"] += 1
        out.append("__misunderstanding__")
    return out


def _r_friendship(world: World) -> list[str]:
    out = []
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["trust"] >= THRESHOLD and friend.memes["kindness"] >= THRESHOLD:
        if ("friendship",) not in world.fired:
            world.fired.add(("friendship",))
            child.memes["joy"] += 1
            friend.memes["joy"] += 1
            out.append("__friendship__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    for _ in range(3):
        for rule in (_r_misunderstanding, _r_friendship):
            parts = rule(world)
            produced.extend([p for p in parts if not p.startswith("__")])
    if narrate:
        for p in produced:
            world.say(p)
    return produced


def tell(scene: Scene, actor_name: str, actor_type: str, friend_name: str, friend_type: str, resolve: Resolve) -> World:
    w = World()
    child = w.add(Entity(id="child", kind="character", type=actor_type, label=actor_name, role="child"))
    friend = w.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    bowl = w.add(Entity(id="bowl", label=scene.bowl, tags={"porridge"}))
    cluster = w.add(Entity(id="cluster", label=scene.cluster, tags={"cluster"}))
    tine = w.add(Entity(id="tine", label=scene.tine, tags={"tine"}))
    w.facts.update(scene=scene, child=child, friend=friend, bowl=bowl, cluster=cluster, tine=tine, resolve=resolve)

    child.memes["curiosity"] = 1
    child.memes["confusion"] = 1
    friend.memes["kindness"] = 1

    w.say(f"In {scene.place}, {actor_name} found {scene.bowl} of porridge that gleamed like gold.")
    w.say(f"Near it lay {scene.cluster}, and by the bowl rested {scene.tine}. {scene.rhyme}.")
    w.say(f"{actor_name} frowned and thought, 'Is that a cluster for the porridge, or is it just a thing?'")
    w.say(f"But {friend_name} came near, with a smile so tender and sunny.")

    w.para()
    w.say(f"{actor_name} wondered, 'Should I keep away from {scene.cluster}, or use {scene.tine} to stir it?'")
    child.memes["confusion"] += 1
    friend.memes["kindness"] += 1
    world_before = w.copy()
    propagate(w, narrate=False)
    if world_before.get("child").memes["confusion"] >= THRESHOLD:
        w.say(f"{actor_name}'s head spun round like a merry, tiny wheel.")
        w.say(f"In an inner voice {actor_name} said, 'I may be wrong; I must not leap. Let me look and listen, and then I can stop.'")

    w.para()
    if resolve.id == "ask":
        child.memes["trust"] += 1
        w.say(f"{friend_name} explained that {scene.cluster} was only a sweet-looking cluster, not a secret treasure.")
        w.say(f"{actor_name} laughed, and the misunderstanding grew small as a crumb.")
    elif resolve.id == "share":
        child.memes["trust"] += 1
        friend.memes["trust"] += 1
        w.say(f"{friend_name} said, 'Let's share the porridge and see the bowl together.'")
        w.say(f"They sat side by side, and sharing made the moment bright and sunny.")
    else:
        child.memes["trust"] += 1
        w.say(f"{friend_name} pointed at {scene.tine} and showed how it belonged with the bowl.")
        w.say(f"Then both children nodded and the little mix-up drifted away like mist in the sun.")

    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    w.say(f"At last they ate the porridge, and friendship warmed the room like honey.")
    w.say(f"No fuss, no rush, just two good friends and a tidy little tune.")
    w.facts["outcome"] = resolve.id
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    return [
        f'Write a rhyming story for a young child that includes the words "porridge", "cluster", and "tine".',
        f"Tell a gentle misunderstanding story where {child.label} thinks {scene.cluster} means one thing, then {friend.label} helps with kindness.",
        f"Write a friendship story with an inner monologue in which two children sort out a small mix-up near {scene.bowl}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    scene: Scene = f["scene"]
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    resolve: Resolve = f["resolve"]
    return [
        ("What did the child see?",
         f"{child.label} saw {scene.bowl}, {scene.cluster}, and {scene.tine} near one another. That was enough to start a small misunderstanding."),
        ("What was the child thinking?",
         f"{child.label} first thought the cluster might mean something important, but then the inner voice slowed the child down. The child decided to look again and listen."),
        ("How did the friends fix the mix-up?",
         f"{friend.label} helped kindly, and then {resolve.explain}. Their friendship made the misunderstanding fade away."),
        ("How did the story end?",
         f"It ended with porridge, smiles, and two friends feeling closer than before. The little worry turned into a warm, shared meal."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is porridge?",
         "Porridge is a soft, warm food made by cooking grains in milk or water. It is often eaten from a bowl."),
        ("What is a cluster?",
         "A cluster is a small group of things that stay close together. Berries, flowers, or peas can form a cluster."),
        ("What is a tine?",
         "A tine is one pointed prong of a fork or similar tool. A fork usually has several tines."),
        ("What does friendship mean?",
         "Friendship means being kind, helping, and listening to each other. Good friends try to understand before they decide."),
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding :- confusion(child), not clarified.
clarified :- friendship, kindness(friend).
outcome(peaceful) :- clarified.
outcome(misunderstood) :- misunderstanding, not clarified.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("scene", "kitchen"),
        asp.fact("scene", "porch"),
        asp.fact("scene", "garden"),
        asp.fact("resolve", "ask"),
        asp.fact("resolve", "share"),
        asp.fact("resolve", "show"),
        asp.fact("sense_min", SENSE_MIN),
    ]
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_outcomes() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show outcome/1."))
    return sorted(set(asp.atoms(model, "outcome")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
    except Exception as exc:
        print(f"ERROR: ASP unavailable: {exc}")
        return 1
    try:
        _ = asp_outcomes()
    except Exception as exc:
        print(f"ERROR: ASP smoke test failed: {exc}")
        return 1
    # Smoke-test ordinary generation and rendering.
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        _ = sample.to_json()
    except Exception as exc:
        print(f"ERROR: story generation failed: {exc}")
        return 1
    print("OK: ASP mode and story generation both worked.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyming storyworld about porridge, a cluster, and a tine.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--resolve", choices=RESOLVES)
    ap.add_argument("--actor-name")
    ap.add_argument("--actor-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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


CURATED = [
    StoryParams(scene="kitchen", actor_name="Mina", actor_type="girl", friend_name="Owen", friend_type="boy", resolve="ask"),
    StoryParams(scene="porch", actor_name="Theo", actor_type="boy", friend_name="Luna", friend_type="girl", resolve="share"),
    StoryParams(scene="garden", actor_name="Poppy", actor_type="girl", friend_name="Finn", friend_type="boy", resolve="show"),
]


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.resolve not in RESOLVES:
        raise StoryError("Unknown resolve.")
    world = tell(SCENES[params.scene], params.actor_name, params.actor_type, params.friend_name, params.friend_type, RESOLVES[params.resolve])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    resolve = args.resolve or rng.choice(list(RESOLVES))
    actor_type = args.actor_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    actor_name = args.actor_name or _pick_name(rng, actor_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type)
    return StoryParams(
        scene=scene,
        actor_name=actor_name,
        actor_type=actor_type,
        friend_name=friend_name,
        friend_type=friend_type,
        resolve=resolve,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show outcome/1."))
        print("ASP outcomes:", sorted(set(asp.atoms(model, "outcome"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
