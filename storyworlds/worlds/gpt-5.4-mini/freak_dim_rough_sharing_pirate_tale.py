#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/freak_dim_rough_sharing_pirate_tale.py
=======================================================================

A tiny standalone storyworld for a pirate-tale seed with the words
"freak-dim" and "rough" and the theme of sharing.

Premise:
- Two children are playing pirate style on a dim, rough evening.
- They find one special treasure, and one child wants to keep it.
- A calm sharing moment turns the tale from squabbling to teamwork.
- The ending image proves the change: both pirates share the treasure and set
  sail together.

This script follows the Storyweavers world contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
- includes Python reasoning gates plus an inline ASP twin
- uses a live world model with physical meters and emotional memes
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    takes: str = ""
    gives: str = ""
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


@dataclass
class Scene:
    id: str
    place: str
    dim_phrase: str
    rough_phrase: str
    pirate_frame: str
    quest: str
    ending: str
    shared_image: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    sharable: bool = True
    valuable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    can_share: bool = True
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


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.role == "child" and e.meters["snatched"] >= THRESHOLD:
            sig = ("hurt", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["hurt"] += 1
            e.memes["grumpy"] += 1
            out.append("__hurt__")
    return out


def _r_share_soften(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.role == "child" and e.meters["shared"] >= THRESHOLD:
            sig = ("soften", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["joy"] += 1
            e.memes["friendship"] += 1
            e.memes["hurt"] = 0.0
            out.append("__soften__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("hurt_feelings", "social", _r_hurt_feelings),
    Rule("share_soften", "social", _r_share_soften),
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


def story_at_risk(treasure: Treasure, item: Item) -> bool:
    return treasure.sharable and item.can_share


def sensible_actions() -> list[str]:
    return [a for a, cfg in ACTIONS.items() if cfg.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SCENES:
        for tid, t in TREASURES.items():
            for iid, item in ITEMS.items():
                if story_at_risk(t, item):
                    combos.append((sid, tid, iid))
    return combos


@dataclass
class Action:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    treasure: str
    item: str
    action: str
    hero1: str
    hero1_gender: str
    hero2: str
    hero2_gender: str
    seed: Optional[int] = None


def _rule_share(world: World, a: Entity, b: Entity, treasure: Entity, action: Action) -> None:
    a.meters["shared"] += 1
    b.meters["shared"] += 1
    a.memes["sharing"] += 1
    b.memes["sharing"] += 1
    world.say(
        f"{a.id} held up {treasure.label} in the freak-dim light, and "
        f"{b.id} stared at the same rough-glinting prize."
    )
    world.say(
        f'"Let\'s share it," {b.id} said. "A pirate crew is stronger together."'
    )
    if action.id == "offer_turns":
        world.say(
            f"{a.id} counted turns on little fingers, and the squabble began to fade."
        )
    else:
        world.say(
            f"{a.id} broke the treasure into two fair parts so both could try it."
        )
    propagate(world)


def _rule_sulk(world: World, a: Entity, b: Entity, treasure: Entity) -> None:
    a.meters["snatched"] += 1
    b.meters["snatched"] += 1
    a.memes["greedy"] += 1
    world.say(
        f"{a.id} grabbed the treasure first, and for a moment the deck felt rough and tense."
    )
    world.say(
        f"{b.id} frowned and crossed {b.pronoun('possessive')} arms, because no one likes being left out."
    )


def scene_intro(world: World, a: Entity, b: Entity, scene: Scene) -> None:
    a.memes["adventure"] += 1
    b.memes["adventure"] += 1
    world.say(
        f"On a {scene.rough_phrase} evening, {a.id} and {b.id} turned {scene.place} into {scene.pirate_frame}."
    )
    world.say(
        f"{scene.dim_phrase} made everything feel a little spooky, but also exciting."
    )
    world.say(f"They were searching for {scene.quest}.")


def want_treasure(world: World, a: Entity, b: Entity, treasure: Treasure) -> None:
    world.say(
        f"Then they found {treasure.phrase}, and both pirates wanted the same shiny thing."
    )
    world.say(
        f'"Mine!" one cried, and the other puffed up like a tiny captain.'
    )


def warn(world: World, b: Entity, treasure: Treasure, item: Item) -> None:
    b.memes["care"] += 1
    world.say(
        f'{b.id} pointed at the treasure. "If we keep tugging, we might break it," '
        f"{b.pronoun()} said."
    )
    world.say(
        f'"We can share {treasure.label} instead of fighting over it."'
    )


def resolve(world: World, a: Entity, b: Entity, treasure: Treasure, action: Action) -> None:
    a.meters["shared"] += 1
    b.meters["shared"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At last, {a.id} nodded. {b.id} smiled back, and they took turns with {treasure.label}."
    )
    world.say(
        f"{action.text.replace('{treasure}', treasure.label)}"
    )
    world.say(
        f"By the end, the treasure was still whole, and the two pirates were sailing side by side."
    )


def tell(scene: Scene, treasure: Treasure, item: Item, action: Action,
         hero1: str = "Mia", hero1_gender: str = "girl",
         hero2: str = "Ben", hero2_gender: str = "boy") -> World:
    world = World()
    a = world.add(Entity(id=hero1, kind="character", type=hero1_gender, role="child"))
    b = world.add(Entity(id=hero2, kind="character", type=hero2_gender, role="child"))
    tr = world.add(Entity(id="treasure", kind="thing", type=treasure.type, label=treasure.label))
    it = world.add(Entity(id="item", kind="thing", type=item.type, label=item.label))
    world.facts.update(scene=scene, treasure=treasure, item=item, action=action, a=a, b=b)

    scene_intro(world, a, b, scene)
    world.para()
    want_treasure(world, a, b, treasure)
    warn(world, b, treasure, item)

    if action.id == "snatch":
        _rule_sulk(world, a, b, tr)
        world.para()
        if action.power >= 2:
            resolve(world, a, b, treasure, action)
        else:
            world.say(
                f"The tugging stopped, and {b.id} offered a calmer way to divide it."
            )
            _rule_share(world, a, b, tr, ACTIONS["offer_turns"])
    else:
        _rule_share(world, a, b, tr, action)
        world.para()
        resolve(world, a, b, treasure, action)

    world.para()
    world.say(
        f"They carried the treasure back together, still in the freak-dim air, "
        f"with the rough boards creaking under their happy steps."
    )
    world.say(scene.shared_image)
    world.facts["outcome"] = "shared"
    return world


SCENES = {
    "deck": Scene(
        "deck",
        "the old deck",
        "The lantern was freak-dim, so the ropes and planks looked shadowy.",
        "The sea was rough, and the boards felt rough under their shoes.",
        "a pirate ship",
        "a hidden chest",
        "a bright team",
        "their lantern glowed like a brave little star",
    ),
    "cove": Scene(
        "cove",
        "the moon-cove",
        "The moon was freak-dim behind the clouds, so the rocks looked like shapes in a dream.",
        "The water was rough, and little waves slapped the shore.",
        "a secret pirate camp",
        "a buried shell box",
        "a sharing crew",
        "their little flag flapped while both pirates held the prize together",
    ),
    "island": Scene(
        "island",
        "the island path",
        "The sky was freak-dim with evening fog, so the path looked narrow and mysterious.",
        "The trail was rough with pebbles and roots.",
        "a treasure hunt",
        "a lost coin pouch",
        "a fair crew",
        "they marched home shoulder to shoulder, grinning at the shared treasure",
    ),
}

TREASURES = {
    "compass": Treasure("compass", "a brass compass", "compass", "thing", tags={"pirate", "tool"}),
    "pearl": Treasure("pearl", "a shiny pearl", "pearl", "thing", tags={"pirate", "shiny"}),
    "map": Treasure("map", "a folded treasure map", "map", "thing", tags={"pirate", "paper"}),
}

ITEMS = {
    "rope": Item("rope", "a rough rope", "rope", "thing", tags={"rough"}),
    "cloth": Item("cloth", "a small cloth bag", "cloth", "thing", tags={"rough"}),
}

ACTIONS = {
    "offer_turns": Action(
        "offer_turns", 3, 3,
        "They shared it kindly, taking turns until both could smile.",
        "They tried to share, but the treasure stayed in one stubborn hand.",
        "shared the {treasure} by taking turns",
        tags={"share"},
    ),
    "split_time": Action(
        "split_time", 3, 3,
        "They split their time with it and passed it back and forth.",
        "They tried to divide the time, but the arguing went on too long.",
        "shared the {treasure} by passing it back and forth",
        tags={"share"},
    ),
    "snatch": Action(
        "snatch", 2, 2,
        "They finally shared it by setting up a fair turn-taking game.",
        "They tugged too hard and the treasure nearly slipped away.",
        "shared the {treasure} after calming down",
        tags={"share"},
    ),
}


GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Tom", "Max", "Leo", "Noah", "Sam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene, treasure, action = f["scene"], f["treasure"], f["action"]
    return [
        f'Write a pirate-tale story for a 3-to-5-year-old that includes the words "freak-dim" and "rough" and focuses on sharing.',
        f"Tell a child-friendly pirate story where {f['a'].id} and {f['b'].id} find {treasure.phrase} in {scene.place} and learn to share it.",
        f"Write a short story about two pirates, a dim night, and a rough place, ending with both children sharing the treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, scene, treasure = f["a"], f["b"], f["scene"], f["treasure"]
    action = f["action"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two young pirates who were playing together."),
        ("What made the place feel strange?",
         f"The light was freak-dim, and the sea or path was rough, so everything felt extra pirate-like."),
        ("What did they find?",
         f'They found {treasure.phrase}, which both of them wanted at first.'),
    ]
    if world.facts.get("outcome") == "shared":
        qa.append((
            "How did they solve the problem?",
            f"They chose to share the treasure instead of fighting over it. That let both pirates stay friends and keep the prize safe."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with both children sailing or walking together, holding the treasure and smiling."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["treasure"].tags) | {"share", "pirate"}
    out = []
    if "share" in tags:
        out.append(QAItem(
            "What does sharing mean?",
            "Sharing means letting someone else use or enjoy something too. It helps people stay kind and play together."
        ))
    if "pirate" in tags:
        out.append(QAItem(
            "What is a pirate?",
            "A pirate is a pretend sea adventurer in stories. Pirate tales often have treasure, ships, maps, and brave crews."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
    return "\n".join(lines)


CURATED = [
    StoryParams("deck", "compass", "rope", "offer_turns", "Mia", "girl", "Ben", "boy"),
    StoryParams("cove", "pearl", "cloth", "split_time", "Lily", "girl", "Noah", "boy"),
    StoryParams("island", "map", "rope", "snatch", "Ava", "girl", "Sam", "boy"),
]


def explain_rejection(treasure: Treasure, item: Item) -> str:
    return f"(No story: {treasure.label} and {item.label} do not create a real sharing problem.)"


def explain_action(rid: str) -> str:
    r = ACTIONS[rid]
    better = " / ".join(sorted(sensible_actions()))
    return f"(Refusing action '{rid}': sense={r.sense} < {SENSE_MIN}. Try: {better}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, a.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,I) :- scene(S), treasure(T), item(I), sharable(T), can_share(I).
sensible(A) :- action(A), sense(A,S), sense_min(M), S >= M.
outcome(shared) :- chosen_action(A), sensible(A).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    else:
        print(f"OK: valid-combo parity ({len(valid_combos())} combos).")

    if set(asp_sensible()) != set(sensible_actions()):
        print("MISMATCH: ASP sensible actions differ from Python.")
        rc = 1
    else:
        print("OK: sensible-action parity.")

    try:
        sample = generate(resolve_params(argparse.Namespace(
            scene=None, treasure=None, item=None, action=None,
            hero1=None, hero1_gender=None, hero2=None, hero2_gender=None,
            seed=None, n=1, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False
        ), random.Random(777)))
        _ = sample.story
        print("OK: smoke-tested normal generate().")
    except Exception as exc:
        print(f"FAIL: generate() smoke test crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale sharing storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero1-gender", dest="hero1_gender", choices=["girl", "boy"])
    ap.add_argument("--hero2")
    ap.add_argument("--hero2-gender", dest="hero2_gender", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        raise StoryError(explain_action(args.action))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, treasure, item = rng.choice(sorted(combos))
    action = args.action or rng.choice(sorted(sensible_actions()))
    g1 = args.hero1_gender or rng.choice(["girl", "boy"])
    g2 = args.hero2_gender or ("boy" if g1 == "girl" else "girl")
    hero1 = args.hero1 or _pick_name(rng, g1)
    hero2 = args.hero2 or _pick_name(rng, g2, avoid=hero1)
    return StoryParams(scene, treasure, item, action, hero1, g1, hero2, g2)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene],
        TREASURES[params.treasure],
        ITEMS[params.item],
        ACTIONS[params.action],
        params.hero1, params.hero1_gender,
        params.hero2, params.hero2_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible actions: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} valid combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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


if __name__ == "__main__":
    main()
